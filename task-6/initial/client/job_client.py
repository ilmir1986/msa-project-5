#!/usr/bin/env python3
"""
Simple client for triggering Spring Batch ETL job via REST API.
Demonstrates tracing context propagation (W3C traceparent header).
"""

import os
import sys
import uuid
import logging
import requests
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] trace_id=%(trace_id)s span_id=%(span_id)s — %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Конфигурация
API_BASE_URL = os.getenv("API_URL", "http://localhost:8080")
API_ENDPOINT = f"{API_BASE_URL}/api/v1/jobs/import"
TIMEOUT_SEC = 60


def generate_trace_context():
    """Генерирует W3C traceparent header для сквозного трейсинга."""
    trace_id = uuid.uuid4().hex  # 32 hex chars
    span_id = uuid.uuid4().hex[:16]  # 16 hex chars
    # Формат: version-traceId-spanId-flags (flags=01 = sampled)
    traceparent = f"00-{trace_id}-{span_id}-01"
    return trace_id, span_id, traceparent


def call_import_job():
    """Вызывает API запуска ETL-задачи с трейсинг-контекстом."""
    trace_id, span_id, traceparent = generate_trace_context()

    # Логируем начало запроса (это попадёт в Docker-логи → Filebeat → ELK)
    logger.info(
        "Calling ETL import job",
        extra={"trace_id": trace_id, "span_id": span_id}
    )

    headers = {
        "Content-Type": "application/json",
        "traceparent": traceparent,  # W3C propagation
        "User-Agent": "job-client/1.0"
    }

    try:
        start_ts = datetime.now()
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            timeout=TIMEOUT_SEC
        )
        duration_ms = (datetime.now() - start_ts).total_seconds() * 1000

        # Логируем ответ
        logger.info(
            f"Response received: {response.status_code}",
            extra={"trace_id": trace_id, "span_id": span_id}
        )

        if response.ok:
            data = response.json()
            print(f"\n✅ Job completed:")
            print(f"   Job ID: {data.get('jobId')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Records processed: {data.get('recordsProcessed')}")
            print(f"   Duration: {duration_ms:.0f} ms")
            return True
        else:
            print(f"\n❌ Error {response.status_code}: {response.text}")
            return False

    except requests.exceptions.Timeout:
        logger.error(
            f"Request timed out after {TIMEOUT_SEC}s",
            extra={"trace_id": trace_id, "span_id": span_id}
        )
        print(f"\n❌ Timeout waiting for response")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(
            f"Cannot connect to {API_BASE_URL}",
            extra={"trace_id": trace_id, "span_id": span_id}
        )
        print(f"\n❌ Connection error: is the app running at {API_BASE_URL}?")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Request failed: {e}",
            extra={"trace_id": trace_id, "span_id": span_id}
        )
        print(f"\n❌ Request error: {e}")
        return False


def main():
    print(f"🚀 Job Client — targeting {API_ENDPOINT}\n")
    success = call_import_job()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()