#!/usr/bin/env python3
"""
Validation Metrics Tracking System
=================================

Track validation metrics over time and provide trend analysis.
"""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ValidationMetricsEntry:
    """Single validation metrics entry"""

    timestamp: datetime
    success_rate: float
    total_issues: int
    critical_issues: int
    error_issues: int
    warning_issues: int
    total_signals: int
    avg_confidence: float
    low_confidence_signals: int
    alert_count: int


class ValidationMetricsTracker:
    """Track validation metrics over time"""

    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.db_path = self.logs_dir / "validation_metrics.db"
        self.metrics_dir = self.logs_dir / "validation_metrics"
        self.metrics_dir.mkdir(exist_ok=True)

        self._init_database()
        logger.info("Validation metrics tracker initialized")

    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS validation_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        success_rate REAL NOT NULL,
                        total_issues INTEGER NOT NULL,
                        critical_issues INTEGER NOT NULL,
                        error_issues INTEGER NOT NULL,
                        warning_issues INTEGER NOT NULL,
                        total_signals INTEGER NOT NULL,
                        avg_confidence REAL NOT NULL,
                        low_confidence_signals INTEGER NOT NULL,
                        alert_count INTEGER NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create index for faster queries
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_timestamp
                    ON validation_metrics(timestamp)
                """
                )

                conn.commit()

        except Exception as e:
            logger.error("Error initializing database: {e}")

    def record_metrics(self, metrics: ValidationMetricsEntry) -> bool:
        """Record validation metrics to database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO validation_metrics (
                        timestamp, success_rate, total_issues, critical_issues,
                        error_issues, warning_issues, total_signals, avg_confidence,
                        low_confidence_signals, alert_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.timestamp.isoformat(),
                        metrics.success_rate,
                        metrics.total_issues,
                        metrics.critical_issues,
                        metrics.error_issues,
                        metrics.warning_issues,
                        metrics.total_signals,
                        metrics.avg_confidence,
                        metrics.low_confidence_signals,
                        metrics.alert_count,
                    ),
                )
                conn.commit()

            logger.info("Recorded metrics for {metrics.timestamp}")
            return True

        except Exception as e:
            logger.error("Error recording metrics: {e}")
            return False

    def get_metrics_history(self, days: int = 30) -> list[ValidationMetricsEntry]:
        """Get validation metrics history"""
        try:
            since_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    """
                    SELECT timestamp, success_rate, total_issues, critical_issues,
                           error_issues, warning_issues, total_signals, avg_confidence,
                           low_confidence_signals, alert_count
                    FROM validation_metrics
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """,
                    (since_date.isoformat(),),
                )

                metrics_list = []
                for row in cursor.fetchall():
                    metrics = ValidationMetricsEntry(
                        timestamp=datetime.fromisoformat(row[0]),
                        success_rate=row[1],
                        total_issues=row[2],
                        critical_issues=row[3],
                        error_issues=row[4],
                        warning_issues=row[5],
                        total_signals=row[6],
                        avg_confidence=row[7],
                        low_confidence_signals=row[8],
                        alert_count=row[9],
                    )
                    metrics_list.append(metrics)

                return metrics_list

        except Exception as e:
            logger.error("Error getting metrics history: {e}")
            return []

    def analyze_trends(self, days: int = 30) -> dict[str, Any]:
        """Analyze validation metrics trends"""
        try:
            metrics_history = self.get_metrics_history(days)

            if len(metrics_history) < 2:
                return {
                    "status": "insufficient_data",
                    "message": "Need at least 2 data points for trend analysis",
                    "data_points": len(metrics_history),
                }

            # Calculate trends
            recent_metrics = metrics_history[:7]  # Last 7 entries
            older_metrics = (
                metrics_history[7:14]
                if len(metrics_history) > 7
                else metrics_history[1:]
            )

            trends = {
                "timestamp": datetime.now().isoformat(),
                "analysis_period_days": days,
                "data_points": len(metrics_history),
                "trends": {},
                "alerts": [],
                "recommendations": [],
            }

            # Success rate trend
            recent_success = sum(m.success_rate for m in recent_metrics) / len(
                recent_metrics
            )
            older_success = sum(m.success_rate for m in older_metrics) / len(
                older_metrics
            )
            success_trend = recent_success - older_success

            trends["trends"]["success_rate"] = {
                "recent_avg": recent_success,
                "older_avg": older_success,
                "change": success_trend,
                "direction": (
                    "improving"
                    if success_trend > 0
                    else "declining" if success_trend < 0 else "stable"
                ),
            }

            # Confidence trend
            recent_confidence = sum(m.avg_confidence for m in recent_metrics) / len(
                recent_metrics
            )
            older_confidence = sum(m.avg_confidence for m in older_metrics) / len(
                older_metrics
            )
            confidence_trend = recent_confidence - older_confidence

            trends["trends"]["confidence"] = {
                "recent_avg": recent_confidence,
                "older_avg": older_confidence,
                "change": confidence_trend,
                "direction": (
                    "improving"
                    if confidence_trend > 0
                    else "declining" if confidence_trend < 0 else "stable"
                ),
            }

            # Issues trend
            recent_issues = sum(m.total_issues for m in recent_metrics) / len(
                recent_metrics
            )
            older_issues = sum(m.total_issues for m in older_metrics) / len(
                older_metrics
            )
            issues_trend = recent_issues - older_issues

            trends["trends"]["issues"] = {
                "recent_avg": recent_issues,
                "older_avg": older_issues,
                "change": issues_trend,
                "direction": (
                    "improving"
                    if issues_trend < 0
                    else "declining" if issues_trend > 0 else "stable"
                ),
            }

            # Critical issues trend
            recent_critical = sum(m.critical_issues for m in recent_metrics) / len(
                recent_metrics
            )
            older_critical = sum(m.critical_issues for m in older_metrics) / len(
                older_metrics
            )
            critical_trend = recent_critical - older_critical

            trends["trends"]["critical_issues"] = {
                "recent_avg": recent_critical,
                "older_avg": older_critical,
                "change": critical_trend,
                "direction": (
                    "improving"
                    if critical_trend < 0
                    else "declining" if critical_trend > 0 else "stable"
                ),
            }

            # Generate alerts based on trends
            if success_trend < -5.0:  # Success rate dropped by 5% or more
                trends["alerts"].append(
                    {
                        "type": "DECLINING_SUCCESS_RATE",
                        "severity": "WARNING",
                        "message": f"Success rate declining: {success_trend:.1f}% change",
                    }
                )

            if confidence_trend < -0.1:  # Confidence dropped by 0.1 or more
                trends["alerts"].append(
                    {
                        "type": "DECLINING_CONFIDENCE",
                        "severity": "WARNING",
                        "message": f"Average confidence declining: {confidence_trend:.3f} change",
                    }
                )

            if critical_trend > 0.5:  # Critical issues increasing
                trends["alerts"].append(
                    {
                        "type": "INCREASING_CRITICAL_ISSUES",
                        "severity": "ERROR",
                        "message": f"Critical issues trending up: {critical_trend:.1f} average increase",
                    }
                )

            # Generate recommendations
            if trends["trends"]["success_rate"]["direction"] == "declining":
                trends["recommendations"].append(
                    "🔍 Investigate causes of success rate decline"
                )

            if trends["trends"]["confidence"]["direction"] == "declining":
                trends["recommendations"].append(
                    "🎯 Consider model retraining or feature engineering"
                )

            if trends["trends"]["issues"]["direction"] == "declining":
                trends["recommendations"].append(
                    "🔧 Review validation rules and data quality"
                )

            if not trends["alerts"]:
                trends["recommendations"].append(
                    "✅ Validation metrics trends are stable"
                )

            # Save trend analysis
            analysis_file = (
                self.metrics_dir
                / "trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(analysis_file, "w") as f:
                json.dump(trends, f, indent=2)

            logger.info("Trend analysis saved: {analysis_file}")
            return trends

        except Exception as e:
            logger.error("Error analyzing trends: {e}")
            return {
                "status": "error",
                "message": f"Trend analysis failed: {e}",
                "timestamp": datetime.now().isoformat(),
            }

    def generate_metrics_report(self, days: int = 7) -> dict[str, Any]:
        """Generate comprehensive metrics report"""
        try:
            metrics_history = self.get_metrics_history(days)
            trends = self.analyze_trends(days)

            if not metrics_history:
                return {
                    "status": "no_data",
                    "message": "No validation metrics available",
                    "timestamp": datetime.now().isoformat(),
                }

            # Calculate summary statistics
            success_rates = [m.success_rate for m in metrics_history]
            confidences = [m.avg_confidence for m in metrics_history]
            issues = [m.total_issues for m in metrics_history]

            report = {
                "timestamp": datetime.now().isoformat(),
                "reporting_period_days": days,
                "data_points": len(metrics_history),
                "summary": {
                    "avg_success_rate": sum(success_rates) / len(success_rates),
                    "min_success_rate": min(success_rates),
                    "max_success_rate": max(success_rates),
                    "avg_confidence": sum(confidences) / len(confidences),
                    "min_confidence": min(confidences),
                    "max_confidence": max(confidences),
                    "avg_issues": sum(issues) / len(issues),
                    "max_issues": max(issues),
                    "total_critical_issues": sum(
                        m.critical_issues for m in metrics_history
                    ),
                },
                "trends": trends.get("trends", {}),
                "trend_alerts": trends.get("alerts", []),
                "recommendations": trends.get("recommendations", []),
                "latest_metrics": (
                    {
                        **asdict(metrics_history[0]),
                        "timestamp": metrics_history[0].timestamp.isoformat(),
                    }
                    if metrics_history
                    else None
                ),
            }

            # Save metrics report
            report_file = (
                self.metrics_dir
                / "metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

            logger.info("Metrics report generated: {report_file}")
            return report

        except Exception as e:
            logger.error("Error generating metrics report: {e}")
            return {
                "status": "error",
                "message": f"Report generation failed: {e}",
                "timestamp": datetime.now().isoformat(),
            }


def main():
    """Test validation metrics tracking"""
    tracker = ValidationMetricsTracker()

    # Generate sample metrics entry (in production, this would come from the monitor)
    sample_metrics = ValidationMetricsEntry(
        timestamp=datetime.now(),
        success_rate=100.0,
        total_issues=0,
        critical_issues=0,
        error_issues=0,
        warning_issues=0,
        total_signals=4,
        avg_confidence=0.537,
        low_confidence_signals=2,
        alert_count=2,
    )

    # Record metrics
    tracker.record_metrics(sample_metrics)

    # Generate report
    report = tracker.generate_metrics_report(days=7)

    print("\n📊 Validation Metrics Report")
    print("============================")
    print("Period: {report.get('reporting_period_days')} days")
    print("Data Points: {report.get('data_points')}")

    summary = report.get("summary", {})
    print("\n📈 Summary:")
    print("  Avg Success Rate: {summary.get('avg_success_rate', 0):.1f}%")
    print("  Avg Confidence: {summary.get('avg_confidence', 0):.3f}")
    print("  Total Critical Issues: {summary.get('total_critical_issues', 0)}")

    trend_alerts = report.get("trend_alerts", [])
    if trend_alerts:
        print("\n⚠️ Trend Alerts:")
        for alert in trend_alerts:
            print("  • {alert['severity']}: {alert['message']}")

    recommendations = report.get("recommendations", [])
    if recommendations:
        print("\n💡 Recommendations:")
        for rec in recommendations:
            print("  {rec}")


if __name__ == "__main__":
    main()
