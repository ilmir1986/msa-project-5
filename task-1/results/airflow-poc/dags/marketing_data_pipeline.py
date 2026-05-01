from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.email import EmailOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import csv
import random

# --- Конфигурация ---
DEFAULT_ARGS = {
    'owner': 'ilmir',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_success': True,
    'email': ['admin@example.com'],  # Замени на свой email для тестов
    'retries': 2,                     # Retry policy
    'retry_delay': timedelta(minutes=1),
    'retry_exponential_backoff': True,
}

# --- Функции ---

def read_csv_data(**context):
    """Чтение данных из CSV (статусы доставок)"""
    try:
        with open('/opt/airflow/data/deliveries.csv', 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            print(f"Read {len(data)} records from CSV")
            context['ti'].xcom_push(key='csv_count', value=len(data))
            return len(data)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        raise

def read_postgres_data(**context):
    """Чтение данных из PostgreSQL (заказы)"""
    # В реальном проекте используем PostgresOperator с xcom_push
    # Для POC эмулируем чтение
    order_count = random.randint(100, 500)
    print(f"Read {order_count} orders from PostgreSQL")
    context['ti'].xcom_push(key='order_count', value=order_count)
    return order_count

def check_data_quality(**context):
    """Анализ данных и выбор ветки"""
    ti = context['ti']
    csv_count = ti.xcom_pull(key='csv_count', task_ids='read_csv')
    order_count = ti.xcom_pull(key='order_count', task_ids='read_postgres')

    print(f"CSV Records: {csv_count}, Orders: {order_count}")

    # Ветвление: если данных достаточно (>50), идем по пути успеха
    if csv_count > 0 and order_count > 50:
        return 'process_data'
    else:
        return 'handle_low_data'

def process_data(**context):
    """Основная обработка данных"""
    print("Processing data...")
    # Здесь была бы логика агрегации, трансформации
    return "Data processed successfully"

def handle_low_data(**context):
    """Обработка случая с малым объемом данных"""
    print("Low data volume detected. Skipping heavy processing.")
    return "Handled low data scenario"

def validate_results(**context):
    """Валидация результатов (может упасть для теста retry)"""
    # Для демонстрации retry можно иногда генерировать ошибку
    # if random.random() < 0.3:
    #     raise Exception("Temporary validation error")
    print("Validation passed")
    return True

# --- Определение DAG ---

dag = DAG(
    'marketing_data_pipeline',
    default_args=DEFAULT_ARGS,
    description='POC: Marketing Data Processing Pipeline',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['poc', 'marketing', 'batch'],
)

# --- Задачи ---

read_csv = PythonOperator(
    task_id='read_csv',
    python_callable=read_csv_data,
    dag=dag,
)

read_postgres = PythonOperator(
    task_id='read_postgres',
    python_callable=read_postgres_data,
    dag=dag,
)

# Ветвление на основе качества данных
branch_check = BranchPythonOperator(
    task_id='check_data_quality',
    python_callable=check_data_quality,
    dag=dag,
)

process_data = PythonOperator(
    task_id='process_data',
    python_callable=process_data,
    dag=dag,
)

handle_low_data = PythonOperator(
    task_id='handle_low_data',
    python_callable=handle_low_data,
    dag=dag,
)

# Валидация с retry политикой
validate = PythonOperator(
    task_id='validate_results',
    python_callable=validate_results,
    retries=3,
    retry_delay=timedelta(seconds=30),
    trigger_rule='none_failed',  # Выполнится, если ни одна из upstream не упала
    dag=dag,
)

# Уведомления (EmailOperator требует настроенный SMTP)
email_success = EmailOperator(
    task_id='email_success',
    to='admin@example.com',
    subject='Pipeline Completed Successfully',
    html_content='Pipeline <b>marketing_data_pipeline</b> completed successfully.',
    dag=dag,
)

email_failure = EmailOperator(
    task_id='email_failure',
    to='admin@example.com',
    subject='Pipeline Failed',
    html_content='Pipeline <b>marketing_data_pipeline</b> failed. Check logs.',
    dag=dag,
    trigger_rule='one_failed',
)

# --- Зависимости ---

[read_csv, read_postgres] >> branch_check
branch_check >> [process_data, handle_low_data]
[process_data, handle_low_data] >> validate
validate >> email_success
validate >> email_failure