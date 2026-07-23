"""
Central Service Registry for GridFlow-TX Platform.
Enables modular, dynamic registration of microservice cards and views.
Adding a new tool/microservice requires simply appending a configuration entry to SERVICES_REGISTRY.
"""

from typing import List, Dict, Any


SERVICES_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "live_analytics",
        "title_key": "service_live_analytics_title",
        "desc_key": "service_live_analytics_desc",
        "icon": "⚡",
        "status_badge": "LIVE OPERATIONAL",
        "badge_color": "#10B981", # Green
        "tags": ["ERCOT ISO", "Real-Time 15m LMP", "BESS Telemetry", "Fuel Mix", "System Load"],
        "module_path": "services.live_analytics",
        "handler_func": "render_live_analytics",
    },
    {
        "id": "bess_intelligence",
        "title_key": "service_bess_intelligence_title",
        "desc_key": "service_bess_intelligence_desc",
        "icon": "🔋",
        "status_badge": "ML AI PREDICTIVE",
        "badge_color": "#3B82F6", # Blue
        "tags": ["Arbitrage Engine", "3-6h ML Forecast", "SOC Curve", "Revenue $/MW-day", "Smart Dispatch"],
        "module_path": "services.bess_intelligence",
        "handler_func": "render_bess_intelligence",
    },
]


def get_all_services() -> List[Dict[str, Any]]:
    """Returns list of all registered microservices in the platform."""
    return SERVICES_REGISTRY


def get_service_by_id(service_id: str) -> Dict[str, Any]:
    """Finds and returns service configuration by ID."""
    for service in SERVICES_REGISTRY:
        if service["id"] == service_id:
            return service
    return SERVICES_REGISTRY[0]
