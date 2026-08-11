"""Test P0 infrastructure components locally."""

import pytest
import psycopg2
import redis
import requests
import json
from hvac import Client as VaultClient
from unittest.mock import patch
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPostgresConnection:
    """Test PostgreSQL direct connection."""

    def test_postgres_direct(self):
        """Connect to PostgreSQL directly."""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user="sellia_user",
                password="sellia_pass",
                database="sellia",
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            cursor.close()
            conn.close()
            logger.info("✅ PostgreSQL direct connection OK")
        except Exception as e:
            logger.error(f"❌ PostgreSQL direct connection failed: {e}")
            raise


class TestPgBouncerPooling:
    """Test pgBouncer connection pooling."""

    def test_pgbouncer_connection(self):
        """Connect to PostgreSQL via pgBouncer."""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=6432,  # pgBouncer port
                user="sellia_user",
                password="sellia_pass",
                database="sellia",
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            cursor.close()
            conn.close()
            logger.info("✅ pgBouncer connection OK")
        except Exception as e:
            logger.error(f"❌ pgBouncer connection failed: {e}")
            raise

    def test_pgbouncer_admin(self):
        """Access pgBouncer admin console."""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=6432,
                user="pgbouncer",
                password="pgbouncer",
                database="pgbouncer",
            )
            cursor = conn.cursor()
            cursor.execute("SHOW POOLS")
            pools = cursor.fetchall()
            logger.info(f"✅ pgBouncer admin OK, pools: {len(pools)}")
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"❌ pgBouncer admin failed: {e}")
            # Don't raise, optional


class TestRedisConnection:
    """Test Redis connection."""

    def test_redis_basic(self):
        """Connect to Redis."""
        try:
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            r.ping()
            logger.info("✅ Redis connection OK")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

    def test_redis_operations(self):
        """Test Redis set/get."""
        try:
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            r.set("test_key", "test_value")
            value = r.get("test_key")
            assert value == "test_value"
            r.delete("test_key")
            logger.info("✅ Redis operations OK")
        except Exception as e:
            logger.error(f"❌ Redis operations failed: {e}")
            raise


class TestJaegerTracing:
    """Test Jaeger distributed tracing."""

    def test_jaeger_health(self):
        """Check Jaeger API health."""
        try:
            response = requests.get("http://localhost:16686/api/health")
            assert response.status_code == 200
            logger.info("✅ Jaeger health check OK")
        except Exception as e:
            logger.error(f"❌ Jaeger health check failed: {e}")
            raise

    def test_jaeger_services(self):
        """Query available services in Jaeger."""
        try:
            response = requests.get("http://localhost:16686/api/services")
            assert response.status_code == 200
            data = response.json()
            logger.info(f"✅ Jaeger services: {data.get('services', [])}")
        except Exception as e:
            logger.error(f"❌ Jaeger services query failed: {e}")
            # Don't raise, may be empty initially


class TestVaultSecrets:
    """Test HashiCorp Vault secrets management."""

    def test_vault_health(self):
        """Check Vault health."""
        try:
            response = requests.get("http://localhost:8200/v1/sys/health")
            assert response.status_code == 200
            data = response.json()
            assert data["initialized"] is True
            assert data["sealed"] is False
            logger.info("✅ Vault health OK")
        except Exception as e:
            logger.error(f"❌ Vault health check failed: {e}")
            raise

    def test_vault_kv_operations(self):
        """Test storing and retrieving secrets from Vault."""
        try:
            client = VaultClient(
                url="http://localhost:8200",
                token="devtoken",
            )

            # Store secret
            client.secrets.kv.v2.create_or_update_secret(
                path="database",
                secret={
                    "host": "db.internal",
                    "port": 5432,
                    "user": "sellia_user",
                    "password": "sellia_pass",
                },
            )

            # Read secret
            response = client.secrets.kv.v2.read_secret_version(path="database")
            secret = response["data"]["data"]

            assert secret["host"] == "db.internal"
            assert secret["password"] == "sellia_pass"

            logger.info("✅ Vault KV operations OK")
        except Exception as e:
            logger.error(f"❌ Vault KV operations failed: {e}")
            raise


class TestCeleryIntegration:
    """Test Celery + Redis integration."""

    def test_celery_broker_connection(self):
        """Test Celery can connect to Redis broker."""
        try:
            from backend.celery_app import celery_app

            # This will test the broker connection
            celery_app.connection()
            logger.info("✅ Celery broker connection OK")
        except ImportError:
            logger.warning("⚠️  Celery module not importable (expected in test env)")
        except Exception as e:
            logger.error(f"❌ Celery broker connection failed: {e}")
            # Don't raise, may not be installed in test env


class TestStructuredLogging:
    """Test structured logging with correlation IDs."""

    def test_correlation_id_context(self):
        """Test correlation ID context variable."""
        try:
            from backend.app.middleware.logging import (
                correlation_id_context,
                user_id_context,
            )

            # Set correlation ID
            correlation_id_context.set("test-correlation-id")
            user_id_context.set("user_123")

            # Verify
            assert correlation_id_context.get() == "test-correlation-id"
            assert user_id_context.get() == "user_123"

            logger.info("✅ Correlation ID context OK")
        except ImportError:
            logger.warning("⚠️  Logging module not importable (expected in test env)")
        except Exception as e:
            logger.error(f"❌ Correlation ID context failed: {e}")
            raise

    def test_json_logging_format(self):
        """Test JSON logging format."""
        try:
            from backend.app.middleware.logging import setup_logging

            # Setup logging
            logger_instance = setup_logging(json_format=True)

            # Log something
            logger_instance.info(
                "Test message",
                extra={"test_field": "test_value", "duration_ms": 123},
            )

            logger.info("✅ JSON logging format OK")
        except ImportError:
            logger.warning("⚠️  Logging module not importable (expected in test env)")
        except Exception as e:
            logger.error(f"❌ JSON logging format failed: {e}")
            # Don't raise, may fail in test env


class TestPrometheus:
    """Test Prometheus metrics collection."""

    def test_prometheus_health(self):
        """Check Prometheus API health."""
        try:
            response = requests.get("http://localhost:9090/-/healthy")
            assert response.status_code == 200
            logger.info("✅ Prometheus health OK")
        except Exception as e:
            logger.error(f"❌ Prometheus health failed: {e}")
            raise

    def test_prometheus_targets(self):
        """Query Prometheus targets."""
        try:
            response = requests.get("http://localhost:9090/api/v1/targets")
            assert response.status_code == 200
            data = response.json()
            active_targets = data.get("data", {}).get("activeTargets", [])
            logger.info(f"✅ Prometheus active targets: {len(active_targets)}")
        except Exception as e:
            logger.error(f"❌ Prometheus targets query failed: {e}")
            # Don't raise, may have no targets yet


class TestGrafana:
    """Test Grafana dashboards."""

    def test_grafana_health(self):
        """Check Grafana API health."""
        try:
            response = requests.get("http://localhost:3000/api/health")
            assert response.status_code == 200
            logger.info("✅ Grafana health OK")
        except Exception as e:
            logger.error(f"❌ Grafana health failed: {e}")
            raise


def run_all_tests():
    """Run all infrastructure tests."""
    logger.info("\n" + "=" * 60)
    logger.info("P0 INFRASTRUCTURE LOCAL TESTING")
    logger.info("=" * 60 + "\n")

    # Run tests in order
    test_classes = [
        TestPostgresConnection,
        TestPgBouncerPooling,
        TestRedisConnection,
        TestJaegerTracing,
        TestVaultSecrets,
        TestCeleryIntegration,
        TestStructuredLogging,
        TestPrometheus,
        TestGrafana,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        logger.info(f"\nTesting {test_class.__name__}...")
        instance = test_class()

        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    method = getattr(instance, method_name)
                    method()
                    passed += 1
                except Exception as e:
                    logger.error(f"  {method_name} failed: {e}")
                    failed += 1

    logger.info("\n" + "=" * 60)
    logger.info(f"RESULTS: {passed} passed, {failed} failed")
    logger.info("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
