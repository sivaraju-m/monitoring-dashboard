#!/usr/bin/env python3
"""
Validation Monitoring System
==========================

Automated monitoring and alerting for validation reports and signal quality.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ValidationMetrics:
    """Validation metrics for monitoring"""

    timestamp: datetime
    success_rate: float
    total_issues: int
    critical_issues: int
    error_issues: int
    warning_issues: int
    total_signals: int
    avg_confidence: float
    low_confidence_signals: int


@dataclass
class ValidationAlert:
    """Validation alert definition"""

    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    metrics: dict[str, Any]


class ValidationMonitor:
    """Monitor validation reports and generate alerts"""

    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.validation_reports_dir = self.logs_dir / "validation_reports"
        self.monitoring_dir = self.logs_dir / "validation_monitoring"
        self.monitoring_dir.mkdir(exist_ok=True)

        # Alert thresholds
        self.thresholds: dict[str, float] = {
            "min_success_rate": 95.0,
            "max_critical_issues": 0,
            "max_error_issues": 2,
            "max_warning_issues": 10,
            "min_avg_confidence": 0.6,
            "max_low_confidence_pct": 20.0,  # Max % of signals with confidence < 0.5
        }

        # Issue priority mapping
        self.priority_map = {"CRITICAL": 1, "ERROR": 2, "WARNING": 3, "INFO": 4}

        logger.info("Validation monitor initialized")

    def get_latest_validation_report(self) -> Optional[dict[str, Any]]:
        """Get the most recent validation report"""
        try:
            if not self.validation_reports_dir.exists():
                logger.warning("Validation reports directory not found")
                return None

            # Find latest production report
            production_report = (
                self.validation_reports_dir / "production_signals_validation.json"
            )
            if production_report.exists():
                with open(production_report) as f:
                    return json.load(f)

            # Fall back to latest timestamped report
            report_files = list(
                self.validation_reports_dir.glob("validation_report_*.json")
            )
            if not report_files:
                logger.warning("No validation reports found")
                return None

            latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
            with open(latest_report) as f:
                return json.load(f)

        except Exception as e:
            logger.error("Error reading validation report: {e}")
            return None

    def extract_metrics_from_report(self, report: dict[str, Any]) -> ValidationMetrics:
        """Extract key metrics from validation report"""
        try:
            summary = report.get("validation_summary", {})
            issue_breakdown = report.get("issue_breakdown", {})
            file_results = report.get("file_results", [])

            # Basic metrics
            timestamp = datetime.fromisoformat(
                summary.get("timestamp", datetime.now().isoformat())
            )
            success_rate = summary.get("success_rate", 0.0)
            total_issues = summary.get("total_issues", 0)

            # Issue breakdown
            by_severity = issue_breakdown.get("by_severity", {})
            critical_issues = by_severity.get("CRITICAL", 0)
            error_issues = by_severity.get("ERROR", 0)
            warning_issues = by_severity.get("WARNING", 0)

            # Signal quality metrics
            total_signals = len(file_results)
            confidences: list[float] = []

            for result in file_results:
                if result.get("success") and "signal" in result:
                    confidence = float(result["signal"].get("confidence", 0.0))
                    confidences.append(confidence)

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            low_confidence_signals = len([c for c in confidences if c < 0.5])

            return ValidationMetrics(
                timestamp=timestamp,
                success_rate=success_rate,
                total_issues=total_issues,
                critical_issues=critical_issues,
                error_issues=error_issues,
                warning_issues=warning_issues,
                total_signals=total_signals,
                avg_confidence=avg_confidence,
                low_confidence_signals=low_confidence_signals,
            )

        except Exception as e:
            logger.error("Error extracting metrics: {e}")
            # Return empty metrics
            return ValidationMetrics(
                timestamp=datetime.now(),
                success_rate=0.0,
                total_issues=999,
                critical_issues=999,
                error_issues=999,
                warning_issues=999,
                total_signals=0,
                avg_confidence=0.0,
                low_confidence_signals=999,
            )

    def check_alert_conditions(
        self, metrics: ValidationMetrics
    ) -> list[ValidationAlert]:
        """Check if any alert conditions are met"""
        alerts = []

        try:
            # Success rate alert
            if metrics.success_rate < self.thresholds["min_success_rate"]:
                alerts.append(
                    ValidationAlert(
                        alert_type="LOW_SUCCESS_RATE",
                        severity="ERROR",
                        message="Validation success rate {metrics.success_rate:.1f}% below threshold {self.thresholds['min_success_rate']}%",
                        timestamp=metrics.timestamp,
                        metrics={"success_rate": metrics.success_rate},
                    )
                )

            # Critical issues alert
            if metrics.critical_issues > self.thresholds["max_critical_issues"]:
                alerts.append(
                    ValidationAlert(
                        alert_type="CRITICAL_ISSUES",
                        severity="CRITICAL",
                        message="{metrics.critical_issues} critical validation issues found",
                        timestamp=metrics.timestamp,
                        metrics={"critical_issues": metrics.critical_issues},
                    )
                )

            # Error issues alert
            if metrics.error_issues > self.thresholds["max_error_issues"]:
                alerts.append(
                    ValidationAlert(
                        alert_type="ERROR_ISSUES",
                        severity="ERROR",
                        message="{metrics.error_issues} error validation issues found (threshold: {self.thresholds['max_error_issues']})",
                        timestamp=metrics.timestamp,
                        metrics={"error_issues": metrics.error_issues},
                    )
                )

            # Warning issues alert
            if metrics.warning_issues > self.thresholds["max_warning_issues"]:
                alerts.append(
                    ValidationAlert(
                        alert_type="WARNING_ISSUES",
                        severity="WARNING",
                        message="{metrics.warning_issues} warning validation issues found (threshold: {self.thresholds['max_warning_issues']})",
                        timestamp=metrics.timestamp,
                        metrics={"warning_issues": metrics.warning_issues},
                    )
                )

            # Low confidence alert
            if metrics.avg_confidence < self.thresholds["min_avg_confidence"]:
                alerts.append(
                    ValidationAlert(
                        alert_type="LOW_CONFIDENCE",
                        severity="WARNING",
                        message="Average signal confidence {metrics.avg_confidence:.3f} below threshold {self.thresholds['min_avg_confidence']}",
                        timestamp=metrics.timestamp,
                        metrics={"avg_confidence": metrics.avg_confidence},
                    )
                )

            # High percentage of low confidence signals
            if metrics.total_signals > 0:
                low_confidence_pct = (
                    metrics.low_confidence_signals / metrics.total_signals
                ) * 100
                if low_confidence_pct > self.thresholds["max_low_confidence_pct"]:
                    alerts.append(
                        ValidationAlert(
                            alert_type="HIGH_LOW_CONFIDENCE_PCT",
                            severity="WARNING",
                            message="{low_confidence_pct:.1f}% of signals have low confidence (threshold: {self.thresholds['max_low_confidence_pct']}%)",
                            timestamp=metrics.timestamp,
                            metrics={"low_confidence_pct": low_confidence_pct},
                        )
                    )

        except Exception as e:
            logger.error("Error checking alert conditions: {e}")
            alerts.append(
                ValidationAlert(
                    alert_type="MONITORING_ERROR",
                    severity="ERROR",
                    message="Error in validation monitoring: {e}",
                    timestamp=datetime.now(),
                    metrics={},
                )
            )

        return alerts

    def categorize_validation_issues(
        self, report: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """Categorize validation issues by priority and type"""
        categorized = {
            "critical": [],
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
        }

        try:
            file_results = report.get("file_results", [])

            for result in file_results:
                if not result.get("success"):
                    issues = result.get("issues", [])
                    for issue in issues:
                        severity = issue.get("severity", "INFO")

                        issue_data = {
                            "file": result.get("file_path"),
                            "ticker": result.get("ticker"),
                            "rule": issue.get("rule"),
                            "message": issue.get("message"),
                            "severity": severity,
                            "timestamp": result.get("timestamp"),
                        }

                        if severity == "CRITICAL":
                            categorized["critical"].append(issue_data)
                        elif severity == "ERROR":
                            categorized["high_priority"].append(issue_data)
                        elif severity == "WARNING":
                            categorized["medium_priority"].append(issue_data)
                        else:
                            categorized["low_priority"].append(issue_data)

        except Exception as e:
            logger.error("Error categorizing issues: {e}")

        return categorized

    def generate_monitoring_report(self) -> dict[str, Any]:
        """Generate comprehensive monitoring report"""
        try:
            report = self.get_latest_validation_report()
            if not report:
                return {
                    "status": "ERROR",
                    "message": "No validation report available",
                    "timestamp": datetime.now().isoformat(),
                }

            metrics = self.extract_metrics_from_report(report)
            alerts = self.check_alert_conditions(metrics)
            categorized_issues = self.categorize_validation_issues(report)

            monitoring_report = {
                "timestamp": datetime.now().isoformat(),
                "status": "HEALTHY" if not alerts else "ISSUES_DETECTED",
                "metrics": {
                    "success_rate": metrics.success_rate,
                    "total_issues": metrics.total_issues,
                    "total_signals": metrics.total_signals,
                    "avg_confidence": metrics.avg_confidence,
                    "low_confidence_signals": metrics.low_confidence_signals,
                    "issue_breakdown": {
                        "critical": metrics.critical_issues,
                        "error": metrics.error_issues,
                        "warning": metrics.warning_issues,
                    },
                },
                "alerts": [
                    {
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "metrics": alert.metrics,
                    }
                    for alert in alerts
                ],
                "issue_categories": categorized_issues,
                "thresholds": self.thresholds,
                "recommendations": self._generate_recommendations(
                    metrics, alerts, categorized_issues
                ),
            }

            # Save monitoring report
            report_file = (
                self.monitoring_dir
                / "validation_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(monitoring_report, f, indent=2)

            logger.info("Monitoring report generated: {report_file}")
            return monitoring_report

        except Exception as e:
            logger.error("Error generating monitoring report: {e}")
            return {
                "status": "ERROR",
                "message": f"Error generating report: {e}",
                "timestamp": datetime.now().isoformat(),
            }

    def _generate_recommendations(
        self,
        metrics: ValidationMetrics,
        alerts: list[ValidationAlert],
        issues: dict[str, list[dict[str, Any]]],
    ) -> list[str]:
        """Generate actionable recommendations based on monitoring results"""
        recommendations = []

        try:
            # Critical issues
            if metrics.critical_issues > 0:
                recommendations.append(
                    "🚨 URGENT: Address critical validation issues immediately - these may block trading"
                )

            # Success rate issues
            if metrics.success_rate < 95.0:
                recommendations.append(
                    "📉 Investigate validation failures - review signal generation logic"
                )

            # Confidence issues
            if metrics.avg_confidence < 0.6:
                recommendations.append(
                    "🎯 Review signal confidence calculation - consider model retraining"
                )

            # High low-confidence percentage
            if (
                metrics.total_signals > 0
                and (metrics.low_confidence_signals / metrics.total_signals) > 0.2
            ):
                recommendations.append(
                    "⚠️ High percentage of low-confidence signals - review data quality and model inputs"
                )

            # Error trends
            if metrics.error_issues > 2:
                recommendations.append("🔧 Review and fix recurring validation errors")

            # If everything is healthy
            if not alerts:
                recommendations.append(
                    "✅ Validation system operating normally - continue monitoring"
                )

        except Exception as e:
            logger.error("Error generating recommendations: {e}")
            recommendations.append(
                "❌ Error generating recommendations - review monitoring system"
            )

        return recommendations

    def run_monitoring_check(self) -> bool:
        """Run a complete monitoring check and return status"""
        try:
            logger.info("Running validation monitoring check")

            report = self.generate_monitoring_report()
            status = report.get("status")
            alerts = report.get("alerts", [])

            # Log summary
            logger.info("Validation monitoring status: {status}")
            if alerts:
                logger.warning("Found {len(alerts)} alerts")
                for alert in alerts:
                    logger.warning("Alert: {alert['type']} - {alert['message']}")
            else:
                logger.info("No validation alerts detected")

            # Print summary to console
            print("\n🔍 Validation Monitoring Report")
            print("===============================")
            print("Status: {status}")
            print("Alerts: {len(alerts)}")
            print(
                "Success Rate: {report.get('metrics', {}).get('success_rate', 0):.1f}%"
            )
            print("Total Signals: {report.get('metrics', {}).get('total_signals', 0)}")
            print(
                "Avg Confidence: {report.get('metrics', {}).get('avg_confidence', 0):.3f}"
            )

            if alerts:
                print("\n⚠️ Active Alerts:")
                for alert in alerts:
                    print("  • {alert['severity']}: {alert['message']}")

            recommendations = report.get("recommendations", [])
            if recommendations:
                print("\n💡 Recommendations:")
                for rec in recommendations:
                    print("  {rec}")

            return status == "HEALTHY"

        except Exception as e:
            logger.error("Error running monitoring check: {e}")
            return False


def main():
    """Run validation monitoring"""
    monitor = ValidationMonitor()
    success = monitor.run_monitoring_check()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
