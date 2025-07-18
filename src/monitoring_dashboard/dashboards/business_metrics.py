#!/usr/bin/env python3
"""
Business Metrics Monitoring and Alerting System
==============================================

Monitors business-level trading metrics and generates actionable alerts.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Set up logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of business metrics"""

    PNL = "pnl"
    RISK = "risk"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"


@dataclass
class BusinessMetric:
    """Business metric definition"""

    name: str
    metric_type: MetricType
    description: str
    calculation_method: str
    target_value: Optional[float]
    warning_threshold: Optional[float]
    critical_threshold: Optional[float]
    frequency: str  # "real-time", "hourly", "daily", etc.
    data_source: str


@dataclass
class MetricAlert:
    """Business metric alert"""

    metric_name: str
    current_value: float
    threshold_breached: str
    severity: str
    timestamp: datetime
    context: dict[str, Any]


class BusinessMetricsMonitor:
    """Monitor business-level trading metrics"""

    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.metrics_dir = self.logs_dir / "business_metrics"
        self.metrics_dir.mkdir(exist_ok=True)

        # Database for metrics storage
        self.db_path = self.metrics_dir / "business_metrics.db"
        self._init_database()

        # Define business metrics to monitor
        self.business_metrics = [
            # P&L Metrics
            BusinessMetric(
                name="daily_pnl",
                metric_type=MetricType.PNL,
                description="Daily profit and loss",
                calculation_method="sum(realized_pnl + unrealized_pnl)",
                target_value=1000.0,  # Target $1000 daily profit
                warning_threshold=-2000.0,  # Warn at $2000 loss
                critical_threshold=-5000.0,  # Critical at $5000 loss
                frequency="real-time",
                data_source="trading_signals",
            ),
            BusinessMetric(
                name="monthly_pnl",
                metric_type=MetricType.PNL,
                description="Monthly profit and loss",
                calculation_method="sum(daily_pnl) for current month",
                target_value=20000.0,  # Target $20K monthly profit
                warning_threshold=-10000.0,  # Warn at $10K monthly loss
                critical_threshold=-25000.0,  # Critical at $25K monthly loss
                frequency="daily",
                data_source="trading_signals",
            ),
            BusinessMetric(
                name="win_rate",
                metric_type=MetricType.PERFORMANCE,
                description="Percentage of profitable trades",
                calculation_method="(winning_trades / total_trades) * 100",
                target_value=55.0,  # Target 55% win rate
                warning_threshold=45.0,  # Warn below 45%
                critical_threshold=35.0,  # Critical below 35%
                frequency="daily",
                data_source="trading_signals",
            ),
            BusinessMetric(
                name="sharpe_ratio",
                metric_type=MetricType.PERFORMANCE,
                description="Risk-adjusted return metric",
                calculation_method="(mean_return - risk_free_rate) / std_return",
                target_value=1.5,  # Target Sharpe ratio of 1.5
                warning_threshold=0.8,  # Warn below 0.8
                critical_threshold=0.5,  # Critical below 0.5
                frequency="weekly",
                data_source="performance_analysis",
            ),
            BusinessMetric(
                name="max_drawdown",
                metric_type=MetricType.RISK,
                description="Maximum peak-to-trough decline",
                calculation_method="min((current_value - peak_value) / peak_value)",
                target_value=-0.05,  # Target max 5% drawdown
                warning_threshold=-0.10,  # Warn at 10% drawdown
                critical_threshold=-0.20,  # Critical at 20% drawdown
                frequency="real-time",
                data_source="portfolio_analysis",
            ),
            BusinessMetric(
                name="portfolio_concentration",
                metric_type=MetricType.RISK,
                description="Maximum position concentration",
                calculation_method="max(position_value / total_portfolio_value)",
                target_value=0.10,  # Target max 10% concentration
                warning_threshold=0.15,  # Warn at 15% concentration
                critical_threshold=0.25,  # Critical at 25% concentration
                frequency="real-time",
                data_source="portfolio_analysis",
            ),
            BusinessMetric(
                name="sector_exposure",
                metric_type=MetricType.RISK,
                description="Maximum sector exposure",
                calculation_method="max(sector_allocation)",
                target_value=0.30,  # Target max 30% per sector
                warning_threshold=0.40,  # Warn at 40% sector exposure
                critical_threshold=0.50,  # Critical at 50% sector exposure
                frequency="hourly",
                data_source="sector_analysis",
            ),
            BusinessMetric(
                name="signal_quality_score",
                metric_type=MetricType.OPERATIONAL,
                description="Average signal confidence score",
                calculation_method="avg(signal_confidence)",
                target_value=0.75,  # Target 75% confidence
                warning_threshold=0.60,  # Warn below 60%
                critical_threshold=0.50,  # Critical below 50%
                frequency="hourly",
                data_source="signal_validation",
            ),
            BusinessMetric(
                name="execution_latency",
                metric_type=MetricType.OPERATIONAL,
                description="Average signal-to-execution time",
                calculation_method="avg(execution_time - signal_time)",
                target_value=30.0,  # Target 30 seconds
                warning_threshold=60.0,  # Warn at 1 minute
                critical_threshold=120.0,  # Critical at 2 minutes
                frequency="real-time",
                data_source="execution_analysis",
            ),
            BusinessMetric(
                name="compliance_violations",
                metric_type=MetricType.COMPLIANCE,
                description="Number of compliance violations",
                calculation_method="count(compliance_violations)",
                target_value=0,  # Target zero violations
                warning_threshold=1,  # Warn at 1 violation
                critical_threshold=3,  # Critical at 3 violations
                frequency="real-time",
                data_source="compliance_monitoring",
            ),
            BusinessMetric(
                name="sebi_limit_utilization",
                metric_type=MetricType.COMPLIANCE,
                description="SEBI position limit utilization",
                calculation_method="(current_position / sebi_limit) * 100",
                target_value=70.0,  # Target 70% utilization
                warning_threshold=85.0,  # Warn at 85%
                critical_threshold=95.0,  # Critical at 95%
                frequency="real-time",
                data_source="compliance_monitoring",
            ),
            BusinessMetric(
                name="data_quality_score",
                metric_type=MetricType.OPERATIONAL,
                description="Data quality and completeness score",
                calculation_method="avg(data_completeness_score)",
                target_value=95.0,  # Target 95% data quality
                warning_threshold=90.0,  # Warn below 90%
                critical_threshold=85.0,  # Critical below 85%
                frequency="hourly",
                data_source="data_validation",
            ),
        ]

        logger.info(
            "Business metrics monitor initialized with {len(self.business_metrics)} metrics"
        )

    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS business_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        context TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS metric_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        current_value REAL NOT NULL,
                        threshold_breached TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        context TEXT,
                        resolved BOOLEAN DEFAULT FALSE,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON business_metrics(metric_name, timestamp)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_alerts_name_timestamp ON metric_alerts(metric_name, timestamp)"
                )

                conn.commit()

        except Exception as e:
            logger.error("Error initializing database: {e}")

    def calculate_metric_value(self, metric: BusinessMetric) -> Optional[float]:
        """Calculate current value for a business metric"""
        try:
            # This is a placeholder for actual metric calculation
            # In production, this would integrate with actual data sources

            # Simulate metric values for demonstration
            metric_simulations = {
                "daily_pnl": 1500.0,  # Positive day
                "monthly_pnl": 15000.0,  # Good month so far
                "win_rate": 52.5,  # Slightly above target
                "sharpe_ratio": 1.2,  # Below target but acceptable
                "max_drawdown": -0.08,  # Within warning range
                "portfolio_concentration": 0.12,  # Slightly above target
                "sector_exposure": 0.28,  # Within target
                "signal_quality_score": 0.68,  # Below target, needs attention
                "execution_latency": 45.0,  # Slightly above target
                "compliance_violations": 0,  # Good
                "sebi_limit_utilization": 75.0,  # Slightly above target
                "data_quality_score": 92.0,  # Within warning range
            }

            return metric_simulations.get(metric.name)

        except Exception as e:
            logger.error("Error calculating metric {metric.name}: {e}")
            return None

    def evaluate_metric_thresholds(
        self, metric: BusinessMetric, value: float
    ) -> Optional[MetricAlert]:
        """Evaluate if metric value breaches thresholds"""
        try:
            alert = None

            # Check critical threshold
            if metric.critical_threshold is not None:
                if (
                    metric.metric_type in [MetricType.PNL, MetricType.PERFORMANCE]
                    and value <= metric.critical_threshold
                ) or (
                    metric.metric_type
                    in [MetricType.RISK, MetricType.COMPLIANCE, MetricType.OPERATIONAL]
                    and value >= metric.critical_threshold
                ):
                    alert = MetricAlert(
                        metric_name=metric.name,
                        current_value=value,
                        threshold_breached="critical",
                        severity="CRITICAL",
                        timestamp=datetime.now(),
                        context={
                            "threshold": metric.critical_threshold,
                            "metric_type": metric.metric_type.value,
                            "target_value": metric.target_value,
                        },
                    )

            # Check warning threshold (if no critical alert)
            elif metric.warning_threshold is not None:
                if (
                    metric.metric_type in [MetricType.PNL, MetricType.PERFORMANCE]
                    and value <= metric.warning_threshold
                ) or (
                    metric.metric_type
                    in [MetricType.RISK, MetricType.COMPLIANCE, MetricType.OPERATIONAL]
                    and value >= metric.warning_threshold
                ):
                    alert = MetricAlert(
                        metric_name=metric.name,
                        current_value=value,
                        threshold_breached="warning",
                        severity="WARNING",
                        timestamp=datetime.now(),
                        context={
                            "threshold": metric.warning_threshold,
                            "metric_type": metric.metric_type.value,
                            "target_value": metric.target_value,
                        },
                    )

            return alert

        except Exception as e:
            logger.error("Error evaluating thresholds for {metric.name}: {e}")
            return None

    def record_metric_value(
        self, metric_name: str, value: float, context: dict[str, Any] = None
    ) -> bool:
        """Record metric value to database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO business_metrics (metric_name, metric_value, timestamp, context)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        metric_name,
                        value,
                        datetime.now().isoformat(),
                        json.dumps(context) if context else None,
                    ),
                )
                conn.commit()

            return True

        except Exception as e:
            logger.error("Error recording metric {metric_name}: {e}")
            return False

    def record_metric_alert(self, alert: MetricAlert) -> bool:
        """Record metric alert to database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO metric_alerts (metric_name, current_value, threshold_breached,
                                             severity, timestamp, context)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        alert.metric_name,
                        alert.current_value,
                        alert.threshold_breached,
                        alert.severity,
                        alert.timestamp.isoformat(),
                        json.dumps(alert.context),
                    ),
                )
                conn.commit()

            return True

        except Exception as e:
            logger.error("Error recording alert for {alert.metric_name}: {e}")
            return False

    def get_metric_history(
        self, metric_name: str, days: int = 7
    ) -> list[dict[str, Any]]:
        """Get historical values for a metric"""
        try:
            since_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    """
                    SELECT metric_value, timestamp, context
                    FROM business_metrics
                    WHERE metric_name = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """,
                    (metric_name, since_date.isoformat()),
                )

                history = []
                for row in cursor.fetchall():
                    history.append(
                        {
                            "value": row[0],
                            "timestamp": row[1],
                            "context": json.loads(row[2]) if row[2] else {},
                        }
                    )

                return history

        except Exception as e:
            logger.error("Error getting history for {metric_name}: {e}")
            return []

    def generate_business_metrics_report(self) -> dict[str, Any]:
        """Generate comprehensive business metrics report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "metrics_summary": {
                    "total_metrics": len(self.business_metrics),
                    "by_type": {},
                    "alerts_generated": 0,
                    "critical_alerts": 0,
                    "warning_alerts": 0,
                },
                "current_metrics": [],
                "active_alerts": [],
                "metric_trends": {},
                "recommendations": [],
            }

            # Count metrics by type
            for metric in self.business_metrics:
                metric_type = metric.metric_type.value
                report["metrics_summary"]["by_type"][metric_type] = (
                    report["metrics_summary"]["by_type"].get(metric_type, 0) + 1
                )

            # Calculate current metrics and check for alerts
            for metric in self.business_metrics:
                current_value = self.calculate_metric_value(metric)

                if current_value is not None:
                    # Record metric value
                    self.record_metric_value(metric.name, current_value)

                    # Evaluate thresholds
                    alert = self.evaluate_metric_thresholds(metric, current_value)

                    metric_data = {
                        "name": metric.name,
                        "type": metric.metric_type.value,
                        "current_value": current_value,
                        "target_value": metric.target_value,
                        "warning_threshold": metric.warning_threshold,
                        "critical_threshold": metric.critical_threshold,
                        "status": "healthy",
                    }

                    if alert:
                        self.record_metric_alert(alert)
                        metric_data["status"] = alert.severity.lower()
                        metric_data["alert"] = {
                            "severity": alert.severity,
                            "threshold_breached": alert.threshold_breached,
                            "context": alert.context,
                        }

                        report["active_alerts"].append(
                            {
                                "metric_name": alert.metric_name,
                                "severity": alert.severity,
                                "current_value": alert.current_value,
                                "threshold_breached": alert.threshold_breached,
                                "context": alert.context,
                            }
                        )

                        report["metrics_summary"]["alerts_generated"] += 1
                        if alert.severity == "CRITICAL":
                            report["metrics_summary"]["critical_alerts"] += 1
                        elif alert.severity == "WARNING":
                            report["metrics_summary"]["warning_alerts"] += 1

                    report["current_metrics"].append(metric_data)

                    # Get trend data
                    history = self.get_metric_history(metric.name, days=7)
                    if len(history) > 1:
                        recent_avg = sum(h["value"] for h in history[:3]) / min(
                            3, len(history)
                        )
                        older_avg = sum(h["value"] for h in history[-3:]) / min(
                            3, len(history[-3:])
                        )
                        trend = (
                            "improving"
                            if recent_avg > older_avg
                            else "declining" if recent_avg < older_avg else "stable"
                        )

                        report["metric_trends"][metric.name] = {
                            "trend": trend,
                            "recent_avg": recent_avg,
                            "older_avg": older_avg,
                            "data_points": len(history),
                        }

            # Generate recommendations
            if report["metrics_summary"]["critical_alerts"] > 0:
                report["recommendations"].append(
                    "🚨 URGENT: Address critical business metric alerts immediately"
                )

            if report["metrics_summary"]["warning_alerts"] > 0:
                report["recommendations"].append(
                    "⚠️ Review business metrics with warning alerts"
                )

            # Specific recommendations based on metrics
            for metric_data in report["current_metrics"]:
                if (
                    metric_data["name"] == "daily_pnl"
                    and metric_data.get("status") == "warning"
                ):
                    report["recommendations"].append(
                        "📉 Daily P&L below target - review trading strategy"
                    )

                if (
                    metric_data["name"] == "win_rate"
                    and metric_data.get("status") == "warning"
                ):
                    report["recommendations"].append(
                        "🎯 Win rate declining - analyze losing trades"
                    )

                if (
                    metric_data["name"] == "max_drawdown"
                    and metric_data.get("status") == "warning"
                ):
                    report["recommendations"].append(
                        "🛡️ Drawdown exceeding limits - consider risk reduction"
                    )

                if (
                    metric_data["name"] == "signal_quality_score"
                    and metric_data.get("status") == "warning"
                ):
                    report["recommendations"].append(
                        "🔧 Signal quality degraded - review model performance"
                    )

            if not report["active_alerts"]:
                report["recommendations"].append(
                    "✅ All business metrics within acceptable ranges"
                )

            # Save report
            report_file = (
                self.metrics_dir
                / "business_metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

            logger.info("Business metrics report saved: {report_file}")
            return report

        except Exception as e:
            logger.error("Error generating business metrics report: {e}")
            return {"timestamp": datetime.now().isoformat(), "error": str(e)}

    def run_business_metrics_monitoring(self) -> bool:
        """Run complete business metrics monitoring cycle"""
        try:
            logger.info("Starting business metrics monitoring")

            # Generate metrics report
            report = self.generate_business_metrics_report()

            if report.get("error"):
                print("❌ Business metrics monitoring failed: {report.get('error')}")
                return False

            # Print summary
            summary = report.get("metrics_summary", {})

            print("\n📊 Business Metrics Monitoring")
            print("===============================")
            print("Total Metrics: {summary.get('total_metrics')}")
            print("Active Alerts: {summary.get('alerts_generated')}")
            print("Critical: {summary.get('critical_alerts')}")
            print("Warning: {summary.get('warning_alerts')}")

            # Print metrics by type
            by_type = summary.get("by_type", {})
            if by_type:
                print("\n📈 Metrics by Type:")
                for metric_type, count in by_type.items():
                    print("  {metric_type.capitalize()}: {count}")

            # Print active alerts
            active_alerts = report.get("active_alerts", [])
            if active_alerts:
                print("\n🚨 Active Alerts:")
                for alert in active_alerts:
                    print(
                        "  • {alert['severity']}: {alert['metric_name']} = {alert['current_value']:.2f}"
                    )
            else:
                print("\n✅ No active alerts")

            # Print recommendations
            recommendations = report.get("recommendations", [])
            if recommendations:
                print("\n💡 Recommendations:")
                for rec in recommendations:
                    print("  {rec}")

            # Print trend summary
            trends = report.get("metric_trends", {})
            if trends:
                improving = len(
                    [t for t in trends.values() if t["trend"] == "improving"]
                )
                declining = len(
                    [t for t in trends.values() if t["trend"] == "declining"]
                )
                stable = len([t for t in trends.values() if t["trend"] == "stable"])

                print("\n📈 Metric Trends (7-day):")
                print("  Improving: {improving}")
                print("  Declining: {declining}")
                print("  Stable: {stable}")

            return summary.get("critical_alerts", 0) == 0

        except Exception as e:
            logger.error("Error running business metrics monitoring: {e}")
            print("❌ Business metrics monitoring error: {e}")
            return False


def main():
    """Run business metrics monitoring"""
    monitor = BusinessMetricsMonitor()
    success = monitor.run_business_metrics_monitoring()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
