import pytest
import time
from observability.telemetry_tracer import trace_span, get_prometheus_metrics_bytes


def test_observability_tracing_decorator():
    @trace_span("test_dummy_function")
    def dummy_func(x, y):
        time.sleep(0.01)
        return x + y

    res = dummy_func(10, 20)
    assert res == 30


def test_prometheus_metrics_export():
    metrics_bytes, content_type = get_prometheus_metrics_bytes()
    assert isinstance(metrics_bytes, bytes)
    assert len(metrics_bytes) > 0
    assert "text/plain" in content_type
