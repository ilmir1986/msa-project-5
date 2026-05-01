# app/Dockerfile
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем скрипт экспорта
COPY export.py .

# Создаем директорию для экспорта
RUN mkdir -p /output

# Создаем non-root пользователя для безопасности
RUN useradd -m -u 1000 exportuser && chown -R exportuser:exportuser /output
USER exportuser

# Переменные окружения по умолчанию (можно переопределить в K8s)
ENV DB_HOST=localhost \
    DB_PORT=5432 \
    DB_NAME=postgres \
    DB_USER=postgres \
    DB_PASSWORD=postgres \
    TABLE_NAME=shipments \
    EXPORT_PATH=/output \
    EXPORT_FILENAME=export.csv \
    CHUNK_SIZE=10000

# Запускаем скрипт экспорта
CMD ["python3", "export.py"]