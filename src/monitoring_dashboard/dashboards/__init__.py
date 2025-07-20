"""
Dashboards package for strategy and performance visualization
"""

from .strategy_dashboard import StrategyDashboard

# Import advanced monitoring only if dependencies are available
try:
    from .advanced_monitoring import (
        AdvancedMonitoring,
        CircuitBreaker,
        CircuitBreakerState,
        MonitoringMetrics,
        TradingKillSwitch,
    )

    _advanced_available = True
except ImportError:
    _advanced_available = False

if _advanced_available:
    __all__ = [
        "StrategyDashboard",
        "AdvancedMonitoring",
        "CircuitBreaker",
        "CircuitBreakerState",
        "MonitoringMetrics",
        "TradingKillSwitch",
    ]
else:
    __all__ = [
        "StrategyDashboard",
    ]
