"""
OpenTelemetry Tracing & RED Metrics Instrumentation Module for GridFlow-TX.
Enables distributed tracing via Tempo and RED metrics (Rate, Errors, Duration) via Prometheus.
"""

import time
import functools
import logging
from typing import Callable, Any, Dict

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger("GridFlow-Observability")

# 1. OPENTELEMETRY TRACER CONFIGURATION
resource = Resource(attributes={SERVICE_NAME: "gridflow-tx-platform"})
provider = TracerProvider(resource=resource)

# OTLP Exporter pointing to Tempo / OTel Collector HTTP endpoint (default http://tempo:4318/v1/traces)
try:
    otlp_exporter = OTLPSpanExporter(endpoint="http://tempo:4318/v1/traces", timeout=3)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
except Exception as e:
    logger.warning(f"Could not connect to OTLP Tempo exporter, using fallback console trace: {e}")
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

trace.set_tracer_provider(provider)
tracer = trace.get_tracer("gridflow.telemetry", "2.5.0")

# 2. PROMETHEUS RED METRICS (Rate, Errors, Duration)
REQUEST_COUNT = Counter(
    "gridflow_requests_total",
    "Total count of service requests handled by GridFlow-TX",
    ["service_id", "status"]
)

REQUEST_LATENCY = Histogram(
    "gridflow_request_duration_seconds",
    "Request latency in seconds for GridFlow-TX microservices",
    ["service_id"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

ERCOT_API_LATENCY = Histogram(
    "gridflow_ercot_api_latency_seconds",
    "Latency of external ERCOT ISO API telemetry fetching in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
)

ML_FORECAST_DURATION = Histogram(
    "gridflow_ml_forecast_duration_seconds",
    "Time taken by ML Ridge Regression model to generate price and demand forecast",
    ["horizon_hours"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 3.0, 10.0]
)

ACTIVE_WORKER_HEALTH = Gauge(
    "gridflow_worker_health_status",
    "Health status of active application containers (1 = Healthy, 0 = Degraded)",
    ["container_name"]
)
ACTIVE_WORKER_HEALTH.labels(container_name="gridflow-dashboard").set(1)


# 3. TRACING DECORATOR & SPAN CONTEXT MANAGER
def trace_span(name: str):
    """
    Decorator for wrapping functions in OpenTelemetry spans and recording metrics.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            with tracer.start_as_current_span(name) as span:
                span.set_attribute("app.component", "gridflow-service")
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    span.set_attribute("app.execution_time_sec", duration)
                    REQUEST_COUNT.labels(service_id=name, status="success").inc()
                    REQUEST_LATENCY.labels(service_id=name).observe(duration)
                    return result
                except Exception as err:
                    duration = time.time() - start_time
                    span.record_exception(err)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(err)))
                    REQUEST_COUNT.labels(service_id=name, status="error").inc()
                    REQUEST_LATENCY.labels(service_id=name).observe(duration)
                    raise err
        return wrapper
    return decorator


def get_prometheus_metrics_bytes() -> tuple[bytes, str]:
    """Generates latest Prometheus RED metrics payload."""
    return generate_latest(), CONTENT_TYPE_LATEST
