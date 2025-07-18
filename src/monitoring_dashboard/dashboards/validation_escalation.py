#!/usr/bin/env python3
"""
Validation Issue Escalation System
=================================

Escalates serious validation issues through defined channels.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Set up logging
logger = logging.getLogger(__name__)


class EscalationLevel(Enum):
    """Escalation levels for validation issues"""

    NONE = "none"
    TEAM_LEAD = "team_lead"
    ENGINEERING_MANAGER = "engineering_manager"
    INCIDENT_RESPONSE = "incident_response"
    EMERGENCY = "emergency"


@dataclass
class EscalationRule:
    """Rule for escalating validation issues"""

    name: str
    condition: str
    level: EscalationLevel
    description: str
    timeout_minutes: int
    notify_channels: list[str]


@dataclass
class EscalationEvent:
    """Escalation event record"""

    timestamp: datetime
    rule_name: str
    level: EscalationLevel
    description: str
    metrics: dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class ValidationEscalationManager:
    """Manage escalation of validation issues"""

    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.escalation_dir = self.logs_dir / "validation_escalations"
        self.escalation_dir.mkdir(exist_ok=True)

        # Define escalation rules
        self.escalation_rules = [
            EscalationRule(
                name="critical_issues_detected",
                condition="critical_issues > 0",
                level=EscalationLevel.INCIDENT_RESPONSE,
                description="Critical validation issues require immediate attention",
                timeout_minutes=15,
                notify_channels=["slack-alerts", "email-oncall", "pager"],
            ),
            EscalationRule(
                name="success_rate_critical",
                condition="success_rate < 50.0",
                level=EscalationLevel.EMERGENCY,
                description="Validation success rate critically low - system may be broken",
                timeout_minutes=5,
                notify_channels=["slack-emergency", "email-oncall", "pager", "phone"],
            ),
            EscalationRule(
                name="success_rate_low",
                condition="success_rate < 80.0",
                level=EscalationLevel.ENGINEERING_MANAGER,
                description="Validation success rate below acceptable threshold",
                timeout_minutes=60,
                notify_channels=["slack-alerts", "email-team"],
            ),
            EscalationRule(
                name="high_error_count",
                condition="error_issues > 10",
                level=EscalationLevel.TEAM_LEAD,
                description="High number of validation errors detected",
                timeout_minutes=30,
                notify_channels=["slack-alerts", "email-team"],
            ),
            EscalationRule(
                name="confidence_degradation",
                condition="avg_confidence < 0.3",
                level=EscalationLevel.TEAM_LEAD,
                description="Signal confidence severely degraded",
                timeout_minutes=45,
                notify_channels=["slack-alerts", "email-team"],
            ),
            EscalationRule(
                name="no_signals_generated",
                condition="total_signals == 0",
                level=EscalationLevel.INCIDENT_RESPONSE,
                description="No signals being generated - possible pipeline failure",
                timeout_minutes=20,
                notify_channels=["slack-alerts", "email-oncall", "pager"],
            ),
        ]

        logger.info(
            "Escalation manager initialized with {len(self.escalation_rules)} rules"
        )

    def evaluate_escalation_rules(
        self, metrics: dict[str, Any]
    ) -> list[EscalationRule]:
        """Evaluate which escalation rules are triggered"""
        triggered_rules = []

        try:
            for rule in self.escalation_rules:
                try:
                    # Create a safe evaluation context
                    eval_context = {
                        "critical_issues": metrics.get("critical_issues", 0),
                        "success_rate": metrics.get("success_rate", 100.0),
                        "error_issues": metrics.get("error_issues", 0),
                        "avg_confidence": metrics.get("avg_confidence", 1.0),
                        "total_signals": metrics.get("total_signals", 1),
                        "warning_issues": metrics.get("warning_issues", 0),
                        "total_issues": metrics.get("total_issues", 0),
                    }

                    # Evaluate the condition
                    if eval(rule.condition, {"__builtins__": {}}, eval_context):
                        triggered_rules.append(rule)
                        logger.warning("Escalation rule triggered: {rule.name}")

                except Exception as e:
                    logger.error("Error evaluating rule {rule.name}: {e}")

        except Exception as e:
            logger.error("Error evaluating escalation rules: {e}")

        return triggered_rules

    def create_escalation_event(
        self, rule: EscalationRule, metrics: dict[str, Any]
    ) -> EscalationEvent:
        """Create an escalation event"""
        return EscalationEvent(
            timestamp=datetime.now(),
            rule_name=rule.name,
            level=rule.level,
            description=rule.description,
            metrics=metrics.copy(),
        )

    def send_escalation_notification(
        self, event: EscalationEvent, rule: EscalationRule
    ) -> bool:
        """Send escalation notification (placeholder for actual implementation)"""
        try:
            # In production, this would integrate with actual notification systems
            notification_payload = {
                "event_id": "{event.rule_name}_{event.timestamp.strftime('%Y%m%d_%H%M%S')}",
                "level": event.level.value,
                "title": f"Validation Escalation: {event.rule_name}",
                "description": event.description,
                "timestamp": event.timestamp.isoformat(),
                "metrics": event.metrics,
                "channels": rule.notify_channels,
                "timeout_minutes": rule.timeout_minutes,
            }

            # Save notification to file (simulating sending)
            notification_file = (
                self.escalation_dir
                / "notification_{event.timestamp.strftime('%Y%m%d_%H%M%S')}_{event.rule_name}.json"
            )
            with open(notification_file, "w") as f:
                json.dump(notification_payload, f, indent=2)

            logger.info("Escalation notification sent: {notification_file}")

            # Log the escalation details
            logger.warning("🚨 ESCALATION: {event.level.value.upper()}")
            logger.warning("Rule: {event.rule_name}")
            logger.warning("Description: {event.description}")
            logger.warning("Channels: {', '.join(rule.notify_channels)}")
            logger.warning("Timeout: {rule.timeout_minutes} minutes")

            return True

        except Exception as e:
            logger.error("Error sending escalation notification: {e}")
            return False

    def record_escalation_event(self, event: EscalationEvent) -> bool:
        """Record escalation event to history"""
        try:
            event_data = {
                "timestamp": event.timestamp.isoformat(),
                "rule_name": event.rule_name,
                "level": event.level.value,
                "description": event.description,
                "metrics": event.metrics,
                "resolved": event.resolved,
                "resolution_time": (
                    event.resolution_time.isoformat() if event.resolution_time else None
                ),
            }

            # Save to escalation history
            history_file = (
                self.escalation_dir
                / "escalation_history_{datetime.now().strftime('%Y%m%d')}.json"
            )

            history = []
            if history_file.exists():
                with open(history_file) as f:
                    history = json.load(f)

            history.append(event_data)

            with open(history_file, "w") as f:
                json.dump(history, f, indent=2)

            logger.info("Escalation event recorded: {event.rule_name}")
            return True

        except Exception as e:
            logger.error("Error recording escalation event: {e}")
            return False

    def check_and_escalate(self, validation_metrics: dict[str, Any]) -> dict[str, Any]:
        """Check metrics and escalate if needed"""
        try:
            escalation_report = {
                "timestamp": datetime.now().isoformat(),
                "metrics_evaluated": validation_metrics,
                "triggered_rules": [],
                "escalation_events": [],
                "notifications_sent": 0,
                "status": "no_escalation",
            }

            # Evaluate escalation rules
            triggered_rules = self.evaluate_escalation_rules(validation_metrics)

            if not triggered_rules:
                escalation_report["status"] = "no_escalation"
                return escalation_report

            escalation_report["status"] = "escalation_triggered"
            escalation_report["triggered_rules"] = [
                rule.name for rule in triggered_rules
            ]

            # Process each triggered rule
            for rule in triggered_rules:
                # Create escalation event
                event = self.create_escalation_event(rule, validation_metrics)

                # Record the event
                if self.record_escalation_event(event):
                    escalation_report["escalation_events"].append(
                        {
                            "rule_name": rule.name,
                            "level": rule.level.value,
                            "timestamp": event.timestamp.isoformat(),
                        }
                    )

                # Send notification
                if self.send_escalation_notification(event, rule):
                    escalation_report["notifications_sent"] += 1

            # Save escalation report
            report_file = (
                self.escalation_dir
                / "escalation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_file, "w") as f:
                json.dump(escalation_report, f, indent=2)

            logger.info(
                "Escalation check complete: {len(triggered_rules)} rules triggered"
            )
            return escalation_report

        except Exception as e:
            logger.error("Error in escalation check: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error_message": str(e),
                "metrics_evaluated": validation_metrics,
            }

    def get_active_escalations(self) -> list[dict[str, Any]]:
        """Get currently active escalations"""
        try:
            active_escalations = []

            # Check today's escalation history
            today = datetime.now().strftime("%Y%m%d")
            history_file = self.escalation_dir / "escalation_history_{today}.json"

            if history_file.exists():
                with open(history_file) as f:
                    history = json.load(f)

                # Find unresolved escalations
                for event_data in history:
                    if not event_data.get("resolved", False):
                        event_time = datetime.fromisoformat(event_data["timestamp"])

                        # Find the rule for timeout info
                        rule_timeout = 60  # Default timeout
                        for rule in self.escalation_rules:
                            if rule.name == event_data["rule_name"]:
                                rule_timeout = rule.timeout_minutes
                                break

                        # Check if still within escalation window
                        time_elapsed = (
                            datetime.now() - event_time
                        ).total_seconds() / 60
                        if time_elapsed < rule_timeout:
                            active_escalations.append(
                                {
                                    **event_data,
                                    "time_remaining_minutes": rule_timeout
                                    - time_elapsed,
                                }
                            )

            return active_escalations

        except Exception as e:
            logger.error("Error getting active escalations: {e}")
            return []

    def generate_escalation_summary(self, days: int = 7) -> dict[str, Any]:
        """Generate escalation summary report"""
        try:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "period_days": days,
                "total_escalations": 0,
                "escalations_by_level": {},
                "escalations_by_rule": {},
                "active_escalations": 0,
                "recent_escalations": [],
            }

            # Check escalation history for the past days
            for i in range(days):
                check_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
                history_file = (
                    self.escalation_dir / "escalation_history_{check_date}.json"
                )

                if history_file.exists():
                    with open(history_file) as f:
                        history = json.load(f)

                    for event_data in history:
                        summary["total_escalations"] += 1

                        # Count by level
                        level = event_data.get("level", "unknown")
                        summary["escalations_by_level"][level] = (
                            summary["escalations_by_level"].get(level, 0) + 1
                        )

                        # Count by rule
                        rule = event_data.get("rule_name", "unknown")
                        summary["escalations_by_rule"][rule] = (
                            summary["escalations_by_rule"].get(rule, 0) + 1
                        )

                        # Add to recent escalations
                        if i < 2:  # Last 2 days
                            summary["recent_escalations"].append(event_data)

            # Get active escalations
            active_escalations = self.get_active_escalations()
            summary["active_escalations"] = len(active_escalations)

            return summary

        except Exception as e:
            logger.error("Error generating escalation summary: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "period_days": days,
            }


def main():
    """Test escalation system with sample metrics"""
    escalation_manager = ValidationEscalationManager()

    # Test with problematic metrics
    test_metrics = {
        "success_rate": 45.0,  # Should trigger emergency escalation
        "critical_issues": 2,  # Should trigger incident response
        "error_issues": 15,  # Should trigger team lead escalation
        "avg_confidence": 0.25,  # Should trigger team lead escalation
        "total_signals": 0,  # Should trigger incident response
        "warning_issues": 5,
        "total_issues": 22,
    }

    print("\n🚨 Validation Escalation Test")
    print("=============================")
    print("Testing with problematic metrics:")
    print("  Success Rate: {test_metrics['success_rate']}%")
    print("  Critical Issues: {test_metrics['critical_issues']}")
    print("  Error Issues: {test_metrics['error_issues']}")
    print("  Avg Confidence: {test_metrics['avg_confidence']}")
    print("  Total Signals: {test_metrics['total_signals']}")

    # Run escalation check
    escalation_report = escalation_manager.check_and_escalate(test_metrics)

    print("\n📊 Escalation Results:")
    print("Status: {escalation_report.get('status')}")
    print("Triggered Rules: {len(escalation_report.get('triggered_rules', []))}")
    print("Notifications Sent: {escalation_report.get('notifications_sent', 0)}")

    triggered_rules = escalation_report.get("triggered_rules", [])
    if triggered_rules:
        print("\n⚠️ Triggered Rules:")
        for rule_name in triggered_rules:
            print("  • {rule_name}")

    # Generate summary
    summary = escalation_manager.generate_escalation_summary(days=1)
    print("\n📈 Escalation Summary:")
    print("Total Escalations: {summary.get('total_escalations', 0)}")
    print("Active Escalations: {summary.get('active_escalations', 0)}")


if __name__ == "__main__":
    from datetime import timedelta

    main()
