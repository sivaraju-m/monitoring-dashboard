"""
Monitoring Dashboard Package
Real-time monitoring and alerting for AI Trading Machine
"""

__version__ = "1.0.0"
__author__ = "AI Trading Machine Team"

from .monitoring.metrics_collector import MetricsCollector
from .dashboards.strategy_dashboard import StrategyDashboard
from .alerts.alert_manager import AlertManager
from .reports.performance_reporter import PerformanceReporter
from .utils.logger import setup_logger, DashboardLogger
from .utils.config_loader import ConfigLoader

__all__ = [
    "MetricsCollector",
    "StrategyDashboard",
    "AlertManager",
    "PerformanceReporter",
    "setup_logger",
    "DashboardLogger",
    "ConfigLoader",
]
