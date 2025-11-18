"""
Monitoring module for Kosmos AI Scientist.

Provides metrics collection, alerting, and observability.
"""

from kosmos.monitoring.metrics import (
    get_metrics_collector,
    export_metrics,
    get_metrics_content_type,
    MetricsCollector
)

from kosmos.monitoring.alerts import (
    get_alert_manager,
    evaluate_alerts,
    get_active_alerts,
    get_alert_history,
    Alert,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    AlertManager
)

__all__ = [
    # Metrics
    "get_metrics_collector",
    "export_metrics",
    "get_metrics_content_type",
    "MetricsCollector",
    # Alerts
    "get_alert_manager",
    "evaluate_alerts",
    "get_active_alerts",
    "get_alert_history",
    "Alert",
    "AlertRule",
    "AlertSeverity",
    "AlertStatus",
    "AlertManager"
]
