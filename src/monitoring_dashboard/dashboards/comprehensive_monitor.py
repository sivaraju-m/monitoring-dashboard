#!/usr/bin/env python3
"""
Comprehensive Monitoring & Alerting System
==========================================

Unified monitoring system that integrates:
- System health monitoring
- Performance tracking
- Cost monitoring
- Alert aggregation and prioritization
- Dashboard metrics
- SLA monitoring

Author: AI Trading Machine
Licensed by SJ Trading
"""

import json
import os
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import pandas as pd

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

from apps.monitoring.performance_analytics import PerformanceAnalytics
from apps.monitoring.smart_alerting_system import SmartAlertingSystem

from src.ai_trading_machine.utils.cost_monitor import GCPCostMonitor
from src.ai_trading_machine.utils.logger import setup_logger

logger = setup_logger(__name__)


class MonitoringLevel(Enum):
    """Monitoring detail levels"""

    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class SystemStatus(Enum):
    """System health status"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"


@dataclass
class SystemMetrics:
    """System health metrics"""

    timestamp: datetime
    status: SystemStatus
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    error_rate: float
    signal_generation_rate: float
    trade_execution_latency: float
    data_freshness_minutes: float
    uptime_hours: float


@dataclass
class PerformanceSnapshot:
    """Trading performance snapshot"""

    timestamp: datetime
    total_pnl: float
    daily_pnl: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    active_trades: int
    active_signals: int
    portfolio_value: float
    risk_utilization: float


@dataclass
class CostSnapshot:
    """Cost monitoring snapshot"""

    timestamp: datetime
    daily_cost: float
    monthly_cost: float
    budget_utilization: float
    cost_anomaly_score: float
    top_cost_services: list[dict[str, Any]]
    optimization_opportunities: list[str]


class ComprehensiveMonitor:
    """Unified monitoring and alerting system"""

    def __init__(self, monitoring_level: MonitoringLevel = MonitoringLevel.STANDARD):
        """Initialize comprehensive monitoring"""
        self.monitoring_level = monitoring_level
        self.project_root = project_root
        self.monitoring_dir = os.path.join(project_root, "monitoring_data")
        self.reports_dir = os.path.join(project_root, "reports", "monitoring")

        # Ensure directories exist
        os.makedirs(self.monitoring_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

        # Initialize components
        self.alerting_system = SmartAlertingSystem()
        self.performance_analytics = PerformanceAnalytics()

        # Try to initialize cost monitor if GCP is available
        try:
            self.cost_monitor = GCPCostMonitor(
                project_id=os.getenv("GCP_PROJECT_ID", "ai-trading-machine"),
                monthly_budget=200.0,
            )
        except Exception as e:
            logger.warning("Cost monitor initialization failed: {e}")
            self.cost_monitor = None

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None

        # Metrics storage
        self.system_metrics_history: list[SystemMetrics] = []
        self.performance_history: list[PerformanceSnapshot] = []
        self.cost_history: list[CostSnapshot] = []

        # SLA thresholds
        self.sla_thresholds = {
            "signal_generation_latency_ms": 5000,  # 5 seconds max
            "trade_execution_latency_ms": 1000,  # 1 second max
            "system_uptime_pct": 99.0,  # 99% uptime
            "data_freshness_minutes": 5,  # 5 minutes max
            "error_rate_pct": 1.0,  # 1% max error rate
            "response_time_ms": 2000,  # 2 seconds max response
        }

        logger.info(
            "Comprehensive monitoring initialized (level: {monitoring_level.value})"
        )

    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous monitoring"""
        if self.is_monitoring:
            logger.warning("Monitoring is already running")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval_seconds,), daemon=True
        )
        self.monitoring_thread.start()

        logger.info("Started continuous monitoring (interval: {interval_seconds}s)")

        # Send startup alert
        self.alerting_system.alert_system_status(
            {
                "event": "monitoring_started",
                "level": "info",
                "timestamp": datetime.now().isoformat(),
            }
        )

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        logger.info("Stopped continuous monitoring")

        # Send shutdown alert
        self.alerting_system.alert_system_status(
            {
                "event": "monitoring_stopped",
                "level": "warning",
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect all metrics
                system_metrics = self.collect_system_metrics()
                performance_snapshot = self.collect_performance_metrics()
                cost_snapshot = self.collect_cost_metrics()

                # Store metrics
                self.system_metrics_history.append(system_metrics)
                self.performance_history.append(performance_snapshot)
                if cost_snapshot:
                    self.cost_history.append(cost_snapshot)

                # Trim history to last 24 hours
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.system_metrics_history = [
                    m for m in self.system_metrics_history if m.timestamp > cutoff_time
                ]
                self.performance_history = [
                    p for p in self.performance_history if p.timestamp > cutoff_time
                ]
                self.cost_history = [
                    c for c in self.cost_history if c.timestamp > cutoff_time
                ]

                # Check SLAs and generate alerts
                self.check_sla_violations(system_metrics, performance_snapshot)

                # Generate periodic reports
                if datetime.now().minute == 0:  # Every hour
                    self.generate_hourly_report()

                # Save metrics to file
                self.save_metrics_snapshot()

            except Exception as e:
                logger.error("Error in monitoring loop: {e}")

                # Send error alert
                self.alerting_system.alert_system_status(
                    {
                        "event": "monitoring_error",
                        "level": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            time.sleep(interval_seconds)

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system health metrics"""
        try:
            import psutil

            # Basic system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Calculate uptime (simplified)
            boot_time = psutil.boot_time()
            uptime_hours = (time.time() - boot_time) / 3600

            # Trading-specific metrics (simulated for now)
            signal_generation_rate = self._calculate_signal_rate()
            trade_execution_latency = self._calculate_execution_latency()
            data_freshness_minutes = self._calculate_data_freshness()
            error_rate = self._calculate_error_rate()
            network_latency = self._measure_network_latency()

            # Determine overall status
            status = self._determine_system_status(
                cpu_usage, memory.percent, disk.percent, error_rate
            )

            return SystemMetrics(
                timestamp=datetime.now(),
                status=status,
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_latency=network_latency,
                error_rate=error_rate,
                signal_generation_rate=signal_generation_rate,
                trade_execution_latency=trade_execution_latency,
                data_freshness_minutes=data_freshness_minutes,
                uptime_hours=uptime_hours,
            )

        except ImportError:
            logger.warning("psutil not available, using basic system metrics")
            return SystemMetrics(
                timestamp=datetime.now(),
                status=SystemStatus.WARNING,
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_latency=0.0,
                error_rate=0.0,
                signal_generation_rate=0.0,
                trade_execution_latency=0.0,
                data_freshness_minutes=0.0,
                uptime_hours=0.0,
            )
        except Exception as e:
            logger.error("Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                status=SystemStatus.CRITICAL,
                cpu_usage=100.0,
                memory_usage=100.0,
                disk_usage=100.0,
                network_latency=1000.0,
                error_rate=100.0,
                signal_generation_rate=0.0,
                trade_execution_latency=5000.0,
                data_freshness_minutes=60.0,
                uptime_hours=0.0,
            )

    def collect_performance_metrics(self) -> PerformanceSnapshot:
        """Collect trading performance metrics"""
        try:
            # Load trading data
            trades_df, signals_df, _ = self.performance_analytics.load_trading_data()

            # Calculate metrics
            metrics = self.performance_analytics.calculate_metrics(trades_df)

            # Get current snapshot
            active_trades = (
                len(trades_df[trades_df["status"] == "ACTIVE"])
                if not trades_df.empty
                else 0
            )
            active_signals = (
                len(
                    signals_df[
                        signals_df.get("timestamp", pd.Timestamp.now())
                        > pd.Timestamp.now() - pd.Timedelta(hours=1)
                    ]
                )
                if not signals_df.empty
                else 0
            )

            # Calculate daily P&L
            today = datetime.now().date()
            daily_trades = (
                trades_df[
                    pd.to_datetime(trades_df.get("entry_time", pd.NaT)).dt.date == today
                ]
                if not trades_df.empty
                else pd.DataFrame()
            )
            daily_pnl = daily_trades["pnl"].sum() if not daily_trades.empty else 0.0

            # Calculate risk utilization (simplified)
            portfolio_value = 100000.0  # Default portfolio value
            total_risk = active_trades * 2000  # Simplified risk calculation
            risk_utilization = (
                (total_risk / portfolio_value) * 100 if portfolio_value > 0 else 0
            )

            return PerformanceSnapshot(
                timestamp=datetime.now(),
                total_pnl=metrics.total_pnl,
                daily_pnl=daily_pnl,
                win_rate=metrics.win_rate,
                sharpe_ratio=metrics.sharpe_ratio,
                max_drawdown=metrics.max_drawdown,
                active_trades=active_trades,
                active_signals=active_signals,
                portfolio_value=portfolio_value,
                risk_utilization=risk_utilization,
            )

        except Exception as e:
            logger.error("Error collecting performance metrics: {e}")
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                total_pnl=0.0,
                daily_pnl=0.0,
                win_rate=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                active_trades=0,
                active_signals=0,
                portfolio_value=100000.0,
                risk_utilization=0.0,
            )

    def collect_cost_metrics(self) -> Optional[CostSnapshot]:
        """Collect cost monitoring metrics"""
        if not self.cost_monitor:
            return None

        try:
            # Get cost data (simplified implementation)
            daily_cost = 10.0  # Placeholder
            monthly_cost = 150.0  # Placeholder
            budget_utilization = (monthly_cost / 200.0) * 100
            cost_anomaly_score = 0.1  # Placeholder

            top_cost_services = [
                {"service": "Cloud Run", "cost": 80.0},
                {"service": "BigQuery", "cost": 40.0},
                {"service": "Cloud Storage", "cost": 20.0},
                {"service": "Firestore", "cost": 10.0},
            ]

            optimization_opportunities = [
                "Consider downscaling Cloud Run during off-hours",
                "Review BigQuery query optimization",
                "Implement storage lifecycle policies",
            ]

            return CostSnapshot(
                timestamp=datetime.now(),
                daily_cost=daily_cost,
                monthly_cost=monthly_cost,
                budget_utilization=budget_utilization,
                cost_anomaly_score=cost_anomaly_score,
                top_cost_services=top_cost_services,
                optimization_opportunities=optimization_opportunities,
            )

        except Exception as e:
            logger.error("Error collecting cost metrics: {e}")
            return None

    def check_sla_violations(
        self, system_metrics: SystemMetrics, performance_snapshot: PerformanceSnapshot
    ):
        """Check for SLA violations and trigger alerts"""
        violations = []

        # Check system SLAs
        if system_metrics.error_rate > self.sla_thresholds["error_rate_pct"]:
            violations.append("Error rate too high: {system_metrics.error_rate:.1f}%")

        if (
            system_metrics.data_freshness_minutes
            > self.sla_thresholds["data_freshness_minutes"]
        ):
            violations.append(
                "Data too stale: {system_metrics.data_freshness_minutes:.1f} minutes"
            )

        if (
            system_metrics.trade_execution_latency
            > self.sla_thresholds["trade_execution_latency_ms"]
        ):
            violations.append(
                "Trade execution slow: {system_metrics.trade_execution_latency:.0f}ms"
            )

        # Check performance SLAs
        if performance_snapshot.risk_utilization > 80:  # 80% max risk utilization
            violations.append(
                "Risk utilization too high: {performance_snapshot.risk_utilization:.1f}%"
            )

        if performance_snapshot.daily_pnl < -5000:  # $5000 daily loss limit
            violations.append(
                "Daily loss limit exceeded: ₹{performance_snapshot.daily_pnl:.2f}"
            )

        # Send alerts for violations
        for violation in violations:
            self.alerting_system.alert_risk_warning(
                {
                    "violation": violation,
                    "timestamp": datetime.now().isoformat(),
                    "system_status": system_metrics.status.value,
                }
            )

    def generate_hourly_report(self):
        """Generate hourly monitoring report"""
        try:
            if not self.system_metrics_history:
                return

            # Get recent metrics
            recent_metrics = self.system_metrics_history[-60:]  # Last hour
            recent_performance = self.performance_history[-60:]

            # Calculate averages
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(
                recent_metrics
            )
            avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(
                recent_metrics
            )

            # Create report
            report = {
                "timestamp": datetime.now().isoformat(),
                "period": "last_hour",
                "system_health": {
                    "status": recent_metrics[-1].status.value,
                    "avg_cpu_usage": avg_cpu,
                    "avg_memory_usage": avg_memory,
                    "avg_error_rate": avg_error_rate,
                    "uptime_hours": recent_metrics[-1].uptime_hours,
                },
                "performance": {
                    "active_trades": (
                        recent_performance[-1].active_trades
                        if recent_performance
                        else 0
                    ),
                    "active_signals": (
                        recent_performance[-1].active_signals
                        if recent_performance
                        else 0
                    ),
                    "current_pnl": (
                        recent_performance[-1].total_pnl if recent_performance else 0
                    ),
                    "win_rate": (
                        recent_performance[-1].win_rate if recent_performance else 0
                    ),
                },
                "alerts_sent": len(
                    [m for m in recent_metrics if m.status != SystemStatus.HEALTHY]
                ),
            }

            # Save report
            report_file = os.path.join(
                self.reports_dir,
                "hourly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            )
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

            # Send summary alert if needed
            if avg_error_rate > 5 or avg_cpu > 80:
                self.alerting_system.alert_system_status(
                    {
                        "event": "hourly_summary_warning",
                        "avg_cpu": avg_cpu,
                        "avg_error_rate": avg_error_rate,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            logger.info("Generated hourly report: {report_file}")

        except Exception as e:
            logger.error("Error generating hourly report: {e}")

    def save_metrics_snapshot(self):
        """Save current metrics snapshot to file"""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": [
                    asdict(m) for m in self.system_metrics_history[-10:]
                ],
                "performance_metrics": [
                    asdict(p) for p in self.performance_history[-10:]
                ],
                "cost_metrics": [asdict(c) for c in self.cost_history[-10:]],
            }

            snapshot_file = os.path.join(self.monitoring_dir, "latest_metrics.json")
            with open(snapshot_file, "w") as f:
                json.dump(snapshot, f, indent=2, default=str)

        except Exception as e:
            logger.error("Error saving metrics snapshot: {e}")

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get data for real-time dashboard"""
        try:
            latest_system = (
                self.system_metrics_history[-1] if self.system_metrics_history else None
            )
            latest_performance = (
                self.performance_history[-1] if self.performance_history else None
            )
            latest_cost = self.cost_history[-1] if self.cost_history else None

            return {
                "timestamp": datetime.now().isoformat(),
                "status": latest_system.status.value if latest_system else "unknown",
                "system": asdict(latest_system) if latest_system else {},
                "performance": asdict(latest_performance) if latest_performance else {},
                "cost": asdict(latest_cost) if latest_cost else {},
                "alerts_24h": len(
                    [
                        m
                        for m in self.system_metrics_history
                        if m.status != SystemStatus.HEALTHY
                    ]
                ),
                "uptime_pct": self._calculate_uptime_percentage(),
            }

        except Exception as e:
            logger.error("Error getting dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def run_health_check(self) -> dict[str, Any]:
        """Run comprehensive health check"""
        logger.info("Running comprehensive health check...")

        # Collect current metrics
        system_metrics = self.collect_system_metrics()
        performance_snapshot = self.collect_performance_metrics()
        cost_snapshot = self.collect_cost_metrics()

        # Check component health
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": system_metrics.status.value,
            "components": {
                "system": {
                    "status": (
                        "healthy"
                        if system_metrics.cpu_usage < 80
                        and system_metrics.memory_usage < 80
                        else "warning"
                    ),
                    "cpu_usage": system_metrics.cpu_usage,
                    "memory_usage": system_metrics.memory_usage,
                    "disk_usage": system_metrics.disk_usage,
                },
                "trading": {
                    "status": (
                        "healthy"
                        if performance_snapshot.active_trades > 0
                        or performance_snapshot.active_signals > 0
                        else "warning"
                    ),
                    "active_trades": performance_snapshot.active_trades,
                    "active_signals": performance_snapshot.active_signals,
                    "daily_pnl": performance_snapshot.daily_pnl,
                },
                "cost": {
                    "status": (
                        "healthy"
                        if cost_snapshot and cost_snapshot.budget_utilization < 80
                        else "warning"
                    ),
                    "budget_utilization": (
                        cost_snapshot.budget_utilization if cost_snapshot else 0
                    ),
                    "monthly_cost": cost_snapshot.monthly_cost if cost_snapshot else 0,
                },
                "monitoring": {
                    "status": "healthy" if self.is_monitoring else "critical",
                    "metrics_collected": len(self.system_metrics_history),
                    "last_collection": (
                        self.system_metrics_history[-1].timestamp.isoformat()
                        if self.system_metrics_history
                        else None
                    ),
                },
            },
            "sla_compliance": self._check_sla_compliance(),
            "recommendations": self._generate_health_recommendations(
                system_metrics, performance_snapshot
            ),
        }

        return health_status

    # Helper methods
    def _calculate_signal_rate(self) -> float:
        """Calculate signals generated per hour"""
        try:
            signals_file = os.path.join(
                self.project_root, "automated_data", "latest_signals.json"
            )
            if os.path.exists(signals_file):
                with open(signals_file) as f:
                    signals = json.load(f)
                # Count signals from last hour
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_signals = [
                    s
                    for s in signals
                    if datetime.fromisoformat(s.get("timestamp", "2020-01-01"))
                    > one_hour_ago
                ]
                return len(recent_signals)
        except Exception as e:
            logger.debug("Error calculating signal rate: {e}")
        return 0.0

    def _calculate_execution_latency(self) -> float:
        """Calculate average trade execution latency in ms"""
        # Placeholder implementation
        return 250.0  # 250ms average

    def _calculate_data_freshness(self) -> float:
        """Calculate data freshness in minutes"""
        # Placeholder implementation
        return 2.0  # 2 minutes average

    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage"""
        # Placeholder implementation
        return 0.1  # 0.1% error rate

    def _measure_network_latency(self) -> float:
        """Measure network latency in ms"""
        # Placeholder implementation
        return 50.0  # 50ms latency

    def _determine_system_status(
        self, cpu: float, memory: float, disk: float, error_rate: float
    ) -> SystemStatus:
        """Determine overall system status"""
        if error_rate > 5 or cpu > 90 or memory > 90 or disk > 95:
            return SystemStatus.CRITICAL
        elif error_rate > 1 or cpu > 80 or memory > 80 or disk > 85:
            return SystemStatus.WARNING
        else:
            return SystemStatus.HEALTHY

    def _calculate_uptime_percentage(self) -> float:
        """Calculate uptime percentage for last 24 hours"""
        if not self.system_metrics_history:
            return 100.0

        healthy_count = sum(
            1 for m in self.system_metrics_history if m.status == SystemStatus.HEALTHY
        )
        total_count = len(self.system_metrics_history)
        return (healthy_count / total_count) * 100 if total_count > 0 else 100.0

    def _check_sla_compliance(self) -> dict[str, Any]:
        """Check SLA compliance"""
        compliance = {}
        if self.system_metrics_history:
            latest = self.system_metrics_history[-1]
            compliance = {
                "uptime": self._calculate_uptime_percentage()
                >= self.sla_thresholds["system_uptime_pct"],
                "error_rate": latest.error_rate
                <= self.sla_thresholds["error_rate_pct"],
                "data_freshness": latest.data_freshness_minutes
                <= self.sla_thresholds["data_freshness_minutes"],
                "execution_latency": latest.trade_execution_latency
                <= self.sla_thresholds["trade_execution_latency_ms"],
            }
        return compliance

    def _generate_health_recommendations(
        self, system_metrics: SystemMetrics, performance_snapshot: PerformanceSnapshot
    ) -> list[str]:
        """Generate health recommendations"""
        recommendations = []

        if system_metrics.cpu_usage > 80:
            recommendations.append("Consider scaling up compute resources")

        if system_metrics.memory_usage > 80:
            recommendations.append("Monitor memory usage and consider optimization")

        if performance_snapshot.risk_utilization > 70:
            recommendations.append("Reduce position sizes to manage risk")

        if performance_snapshot.win_rate < 40:
            recommendations.append("Review trading strategies for poor performance")

        if system_metrics.error_rate > 1:
            recommendations.append("Investigate and fix recurring errors")

        return recommendations


def main():
    """Main function for command line usage"""
    print("🔍 AI Trading Machine - Comprehensive Monitoring System")
    print("=" * 60)

    # Initialize monitor
    monitor = ComprehensiveMonitor(MonitoringLevel.COMPREHENSIVE)

    try:
        # Run health check
        health_status = monitor.run_health_check()
        print("\n📊 System Health Status: {health_status['overall_status'].upper()}")

        # Display component status
        for component, status in health_status["components"].items():
            print("   {component.capitalize()}: {status['status'].upper()}")

        # Display SLA compliance
        sla_compliance = health_status["sla_compliance"]
        compliant_count = sum(1 for v in sla_compliance.values() if v)
        total_slas = len(sla_compliance)
        print(
            "\n📈 SLA Compliance: {compliant_count}/{total_slas} ({(compliant_count/total_slas)*100:.1f}%)"
        )

        # Display recommendations
        recommendations = health_status["recommendations"]
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations:
                print("   • {rec}")

        # Ask if user wants to start continuous monitoring
        response = input("\nStart continuous monitoring? (y/n): ").lower().strip()
        if response == "y":
            print("\n🚀 Starting continuous monitoring...")
            monitor.start_monitoring(interval_seconds=30)

            try:
                # Keep running until user interrupts
                while True:
                    time.sleep(10)
                    # Display live status
                    dashboard_data = monitor.get_dashboard_data()
                    print(
                        "\r⏱️  {datetime.now().strftime('%H:%M:%S')} | "
                        "Status: {dashboard_data.get('status', 'unknown').upper()} | "
                        "Alerts: {dashboard_data.get('alerts_24h', 0)} | "
                        "Uptime: {dashboard_data.get('uptime_pct', 0):.1f}%",
                        end="",
                    )

            except KeyboardInterrupt:
                print("\n\n🛑 Stopping monitoring...")
                monitor.stop_monitoring()
                print("✅ Monitoring stopped successfully")

    except Exception as e:
        logger.error("Error in monitoring system: {e}")
        print("❌ Error: {e}")


if __name__ == "__main__":
    main()
