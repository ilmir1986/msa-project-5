#!/usr/bin/env python3
"""
PostgreSQL to CSV Export Script for Kubernetes CronJob.
Exports a table from PostgreSQL to CSV file.
"""

import os
import sys
import csv
import logging
import psycopg2
import psycopg2
from datetime import datetime

# Настройка логирования в stdout (для сбора логов K8s)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_env_config() -> dict:
    """Чтение конфигурации из environment variables."""
    required_vars = [
        'DB_HOST', 'DB_PORT', 'DB_NAME',
        'DB_USER', 'DB_PASSWORD', 'TABLE_NAME',
        'EXPORT_PATH', 'EXPORT_FILENAME'
    ]

    config = {}
    missing = []

    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing.append(var)
        else:
            config[var] = value

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    # Опциональные параметры
    config['CHUNK_SIZE'] = int(os.getenv('CHUNK_SIZE', '10000'))
    config['WHERE_CLAUSE'] = os.getenv('WHERE_CLAUSE', '')

    return config


def connect_to_db(config: dict) -> psycopg2.extensions.connection:
    """Установка соединения с PostgreSQL."""
    logger.info(f"Connecting to {config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}")

    try:
        conn = psycopg2.connect(
            host=config['DB_HOST'],
            port=config['DB_PORT'],
            dbname=config['DB_NAME'],
            user=config['DB_USER'],
            password=config['DB_PASSWORD'],
            connect_timeout=30
        )
        logger.info("Database connection established")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def export_table_to_csv(conn: psycopg2.extensions.connection, config: dict) -> int:
    """
    Экспорт таблицы в CSV с использованием server-side cursor для больших данных.
    Возвращает количество экспортированных строк.
    """
    table_name = config['TABLE_NAME']
    chunk_size = config['CHUNK_SIZE']
    where_clause = config['WHERE_CLAUSE']

    # Формируем запрос
    query = f"SELECT * FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"

    logger.info(f"Starting export: {query[:100]}...")

    row_count = 0
    output_path = os.path.join(config['EXPORT_PATH'], config['EXPORT_FILENAME'])

    try:
        # Создаем директорию если не существует
        os.makedirs(config['EXPORT_PATH'], exist_ok=True)

        # Именованный курсор = server-side cursor
        with conn.cursor(name='export_cursor') as cursor:
            cursor.itersize = chunk_size
            cursor.execute(query)

            # Получаем заголовки колонок (с проверкой на None)
            if cursor.description is None:
                logger.warning("Query returned no columns. Table might be empty.")
                return 0

            column_names = [desc[0] for desc in cursor.description]
            logger.info(f"Columns: {column_names}")

            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=column_names)
                writer.writeheader()

                # Читаем данные чанками
                while True:
                    rows = cursor.fetchmany(chunk_size)
                    if not rows:
                        break

                    for row in rows:
                        # Безопасное преобразование строки в dict
                        row_dict = dict(zip(column_names, row))
                        writer.writerow(row_dict)
                        row_count += 1

                    # Лог прогресса каждые 10к строк
                    if row_count % 10000 == 0:
                        logger.info(f"Exported {row_count} rows...")

        logger.info(f"Export completed: {row_count} rows written to {output_path}")
        return row_count

    except psycopg2.Error as e:
        logger.error(f"Database error during export: {e}")
        raise
    except IOError as e:
        logger.error(f"File I/O error: {e}")
        raise
    except TypeError as e:
        logger.error(f"Data processing error: {e}")
        logger.error(f"cursor.description: {cursor.description if 'cursor' in locals() else 'N/A'}")
        raise


def main() -> int:
    """
    Главная функция.
    Возвращает: 0 - успех, 1 - ошибка.
    """
    start_time = datetime.now()
    logger.info(f"=== Export Job Started at {start_time.isoformat()} ===")

    try:
        # 1. Чтение конфигурации
        config = get_env_config()
        logger.info(f"Configuration loaded. Exporting table: {config['TABLE_NAME']}")

        # 2. Подключение к БД
        conn = connect_to_db(config)

        # 3. Экспорт данных
        row_count = export_table_to_csv(conn, config)

        # 4. Закрытие соединения
        conn.close()
        logger.info("Database connection closed")

        # 5. Финальный лог
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"=== Job Completed Successfully ===")
        logger.info(f"Rows exported: {row_count}")
        logger.info(f"Duration: {duration:.2f} seconds")

        return 0  # Success

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        return 1
    finally:
        # Убедимся, что логи флешнутся перед завершением
        logging.shutdown()


if __name__ == '__main__':
    sys.exit(main())