"""Distributed tracing with OpenTelemetry + Jaeger."""

from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import uuid
import logging


logger = logging.getLogger(__name__)


def init_tracing(service_name: str = "sellia-backend", jaeger_host: str = "localhost"):
    """
    Initialize OpenTelemetry tracing.

    Configuration:
    - Exports to Jaeger (for distributed tracing)
    - Instruments FastAPI, SQLAlchemy, Redis, HTTP
    - Batch export for performance
    """

    # Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=6831,
    )

    # Tracer provider with batch processor
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    trace.set_tracer_provider(trace_provider)

    # Prometheus metrics reader
    prometheus_reader = PrometheusMetricReader()
    metrics_provider = MeterProvider(metric_readers=[prometheus_reader])
    metrics.set_meter_provider(metrics_provider)

    # Auto-instrument key libraries
    FastAPIInstrumentor.instrument_app(None)  # Instrumented separately
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    logger.info(f"OpenTelemetry tracing initialized for {service_name}")
    return trace_provider, metrics_provider


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Add correlation ID to every request for tracing.

    Generates UUID if not provided, adds to response headers.
    All logs include correlation_id for easy filtering.
    """

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )

        # Store in request state for use in handlers
        request.state.correlation_id = correlation_id

        # Get tracer + create span with correlation ID
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}"
        ) as span:
            # Add attributes to span
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("correlation_id", correlation_id)
            span.set_attribute("client_ip", request.client.host if request.client else "unknown")

            try:
                response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)

                # Add correlation ID to response
                response.headers["X-Correlation-ID"] = correlation_id

                return response
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                raise


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Track request duration for performance monitoring."""

    async def dispatch(self, request: Request, call_next):
        import time

        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Log slow requests
        if duration_ms > 1000:  # > 1 second
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            logger.warning(
                "Slow request detected",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                }
            )

        return response


def get_tracer(name: str = "sellia"):
    """Get tracer for creating spans in business logic."""
    return trace.get_tracer(name)


def get_meter(name: str = "sellia"):
    """Get meter for custom metrics."""
    return metrics.get_meter(name)
