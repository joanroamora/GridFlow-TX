import pytest
from services.service_registry import get_all_services, get_service_by_id


def test_service_registry_count():
    services = get_all_services()
    assert len(services) >= 2


def test_service_registry_keys():
    services = get_all_services()
    for srv in services:
        assert "id" in srv
        assert "title_key" in srv
        assert "desc_key" in srv
        assert "icon" in srv
        assert "module_path" in srv
        assert "handler_func" in srv


def test_get_service_by_id():
    srv = get_service_by_id("bess_intelligence")
    assert srv["id"] == "bess_intelligence"
    assert srv["icon"] == "🔋"

    # Fallback to first service if invalid ID passed
    invalid_srv = get_service_by_id("non_existent_id")
    assert invalid_srv["id"] == "live_analytics"
