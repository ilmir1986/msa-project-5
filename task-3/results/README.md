# Задание 3. Реализация Distributed Scheduling с k8s CronJob

## Описание
Ежедневный экспорт данных из PostgreSQL в CSV для аналитики грузоперевозок.
Запускается через Kubernetes CronJob в 20:00 каждый день.


## Быстрый старт (MiniKube)

```bash
# 1. Запустить MiniKube
minikube start --driver=docker

# 2. Собрать и загрузить образ
cd app && docker build -t export-job:latest . && cd ..
minikube image load export-job:latest

# 3. Применить манифесты
kubectl apply -f k8s/

# 4. Запустить тестовый Job
kubectl create job --from=cronjob/export-job test-run -n analytics-export

# 5. Проверить результат
kubectl get pods -n analytics-export
kubectl logs job/test-run -n analytics-export
```

## Мониторинг
```bash
# Статус CronJob
kubectl get cronjob -n analytics-export

# Логи последнего запуска
kubectl logs job/test-run -n analytics-export

# События в namespace
kubectl get events -n analytics-export --sort-by='.lastTimestamp'
```

## Инициализация тестовых данных
```bash
# Найти Pod PostgreSQL
POD=$(kubectl get pods -n analytics-export -l app=postgres -o jsonpath='{.items[0].metadata.name}')

# Создать таблицу и данные
kubectl exec -it $POD -n analytics-export -- psql -U postgres -d analytics_db -c "
CREATE TABLE IF NOT EXISTS shipments (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50),
    driver_name VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
INSERT INTO shipments (order_number, driver_name, status) VALUES
('ORD-001', 'Ivan Petrov', 'COMPLETED'),
('ORD-002', 'Petr Ivanov', 'IN_PROGRESS');
"
```

## Тестирование
```bash
# Запустить Job вручную
kubectl create job --from=cronjob/export-job test-run -n analytics-export

# Мониторить выполнение
kubectl get jobs -n analytics-export -w
kubectl logs job/test-run -n analytics-export
```