# Обоснование выбора технологического решения

## 1. Выбор инструмента: Apache Airflow
**Выбор:** Apache Airflow.
**Причина:**
- **Orchestration over Execution:** Airflow идеально разделяет логику оркестрации (workflow) и исполнения задач. Это соответствует принципу единственной ответственности (SRP).
- **DAG as Code:** Пайплайны описываются кодом (Python), что позволяет версионировать логику, тестировать и ревьювить изменения как в любом ПО.
- **Масштабируемость:** Поддержка распределенного выполнения задач через Celery/Kubernetes Executor.
- **Сообщество:** Наибольшая экосистема готовых коннекторов среди открытых решений.

## 2. Интеграция с внешними системами
Airflow использует архитектуру **Providers**. Для каждой системы существует готовый пакет, ускоряющий разработку:

| Система | Пакет (Provider) | Ключевые компоненты |
| :--- | :--- | :--- |
| **Kafka** | `apache-airflow-providers-apache-kafka` | `KafkaProducerOperator`, `KafkaConsumerSensor` |
| **Spark** | `apache-airflow-providers-apache-spark` | `SparkSubmitOperator` (запуск jobs на кластере) |
| **BigQuery** | `apache-airflow-providers-google` | `BigQueryInsertJobOperator`, `BigQueryCheckOperator` |
| **Redshift** | `apache-airflow-providers-amazon` | `RedshiftDataOperator`, `RedshiftSQLOperator` |

**Вывод:** Интеграция осуществляется через готовые Operators и Hooks, что снижает время разработки (Time-to-Market) и минимизирует риски ошибок подключения.

## 3. Логика управления потоком (Workflow Logic)
- **Ветвление:** Реализуется через `BranchPythonOperator`. Позволяет динамически выбирать путь выполнения на основе данных предыдущего шага.
- **Условные операторы:** `ShortCircuitOperator` позволяет прерывать ветку, если условие не выполнено.
- **Event-Triggers:** Реализуются через **Sensors** (например, `S3KeySensor`, `SqlSensor`). Они polling-ом или через deferrable mode ожидают появления данных или событий.

## 4. Надежность и мониторинг (Reliability & Observability)
- **Retry Policy:** Настраивается на уровне DAG или задачи (`retries`, `retry_delay`, `exponential_backoff`).
- **Fallback-logic:** Реализуется через ветвление: при ошибке можно запустить компенсирующую задачу (через `trigger_rule='one_failed'`).
- **Уведомления:** Встроенная поддержка `email_on_failure`, `email_on_success`. Также возможна интеграция со Slack/Telegram через Webhook-operators.
- **Мониторинг:** Встроенный UI предоставляет статус задач, логи, длительность выполнения и графики зависимостей.

## 5. Стратегия развертывания в облаке
Решение контейнеризировано (Docker), что обеспечивает переносимость (Portability).

**Варианты деплоя:**
1.  **Managed Services (Рекомендуемый):**
    - AWS: **MWAA** (Managed Workflows for Apache Airflow).
    - GCP: **Cloud Composer**.
    - *Преимущество:* Минимум операционных затрат, автоматическое масштабирование.
2.  **Self-Managed на Kubernetes:**
    - Развертывание через **Helm Chart** (`airflow-chart`).
    - *Преимущество:* Полный контроль, возможность использования `KubernetesExecutor` для изоляции задач в отдельных подах.

**Обоснование для продакшена:** Для нагрузки в 1 млн записей рекомендуется использовать `KubernetesExecutor` или `CeleryExecutor`, чтобы задачи обработки данных выполнялись параллельно на отдельных воркерах, не блокируя планировщик.