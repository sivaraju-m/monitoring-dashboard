"""
Alert management system for monitoring dashboard
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..utils.logger import DashboardLogger
from ..utils.config_loader import ConfigLoader


class AlertManager:
    """Alert management and notification system"""

    def __init__(self):
        self.logger = DashboardLogger("alert_manager")
        self.config = ConfigLoader().load_alert_config()
        self.db_path = self._setup_database()

        # Alert severity levels
        self.severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    def _setup_database(self) -> str:
        """Setup alert database"""
        db_dir = Path(__file__).parent.parent.parent.parent / "data"
        db_dir.mkdir(parents=True, exist_ok=True)

        db_path = db_dir / "alerts.db"

        with sqlite3.connect(str(db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    metadata TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
                ON alerts(timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alerts_severity 
                ON alerts(severity)
            """
            )

        return str(db_path)

    async def get_recent_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent alerts for dashboard"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT type, severity, message, timestamp, source, acknowledged, resolved
                    FROM alerts 
                    WHERE timestamp >= datetime('now', '-24 hours')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (limit,),
                )

                alerts = []
                for row in cursor.fetchall():
                    alert = {
                        "type": row[0],
                        "severity": row[1],
                        "message": row[2],
                        "timestamp": row[3],
                        "source": row[4],
                        "acknowledged": bool(row[5]),
                        "resolved": bool(row[6]),
                    }
                    alerts.append(alert)

                return alerts

        except Exception as e:
            self.logger.error(f"Error getting recent alerts: {e}")
            return self._get_sample_alerts()

    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a new alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO alerts (type, severity, message, source, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        alert_type,
                        severity,
                        message,
                        source,
                        json.dumps(metadata) if metadata else None,
                    ),
                )

                conn.commit()

            self.logger.info(f"Created {severity} alert: {message}")

            # Send notifications if configured
            await self._send_notifications(alert_type, severity, message, source)

            return True

        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            return False

    async def check_system_alerts(
        self, metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check system metrics against alert rules"""
        new_alerts = []

        try:
            for rule in self.config.get("rules", []):
                if not rule.get("enabled", True):
                    continue

                # Evaluate rule condition
                if self._evaluate_condition(rule["condition"], metrics):
                    alert = {
                        "type": rule["name"],
                        "severity": rule["severity"],
                        "message": f"Alert triggered: {rule['name']}",
                        "source": "auto_monitor",
                    }

                    # Check if we already have this alert recently
                    if not await self._is_duplicate_alert(alert):
                        await self.create_alert(**alert)
                        new_alerts.append(alert)

            return new_alerts

        except Exception as e:
            self.logger.error(f"Error checking system alerts: {e}")
            return []

    def _evaluate_condition(self, condition: str, metrics: Dict[str, Any]) -> bool:
        """Evaluate alert condition against metrics"""
        try:
            # Simple condition evaluation
            # Replace metric names with actual values
            eval_condition = condition

            for key, value in metrics.items():
                if key in condition and isinstance(value, (int, float)):
                    eval_condition = eval_condition.replace(key, str(value))

            # Handle string comparisons
            if "!=" in eval_condition:
                parts = eval_condition.split("!=")
                if len(parts) == 2:
                    left = parts[0].strip().strip("'\"")
                    right = parts[1].strip().strip("'\"")
                    return str(metrics.get(left, "")).strip("'\"") != right

            # Handle numeric comparisons
            if any(op in eval_condition for op in ["<", ">", "=="]):
                try:
                    return eval(eval_condition)
                except:
                    return False

            return False

        except Exception as e:
            self.logger.debug(f"Error evaluating condition '{condition}': {e}")
            return False

    async def _is_duplicate_alert(self, alert: Dict[str, Any]) -> bool:
        """Check if similar alert exists recently"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM alerts 
                    WHERE type = ? AND severity = ? 
                    AND timestamp >= datetime('now', '-1 hour')
                    AND resolved = FALSE
                """,
                    (alert["type"], alert["severity"]),
                )

                count = cursor.fetchone()[0]
                return count > 0

        except Exception as e:
            self.logger.debug(f"Error checking duplicate alert: {e}")
            return False

    async def _send_notifications(
        self, alert_type: str, severity: str, message: str, source: str
    ):
        """Send alert notifications"""
        try:
            notifications = self.config.get("notifications", {})

            # Email notifications
            if notifications.get("email", {}).get("enabled", False):
                await self._send_email_notification(alert_type, severity, message)

            # Slack notifications
            if notifications.get("slack", {}).get("enabled", False):
                await self._send_slack_notification(alert_type, severity, message)

        except Exception as e:
            self.logger.warning(f"Error sending notifications: {e}")

    async def _send_email_notification(
        self, alert_type: str, severity: str, message: str
    ):
        """Send email notification (placeholder)"""
        # This would integrate with actual email service
        self.logger.info(f"Email notification would be sent: {severity} - {message}")

    async def _send_slack_notification(
        self, alert_type: str, severity: str, message: str
    ):
        """Send Slack notification (placeholder)"""
        # This would integrate with actual Slack webhook
        self.logger.info(f"Slack notification would be sent: {severity} - {message}")

    async def acknowledge_alert(self, alert_id: int) -> bool:
        """Acknowledge an alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE alerts 
                    SET acknowledged = TRUE 
                    WHERE id = ?
                """,
                    (alert_id,),
                )

                conn.commit()

            return True

        except Exception as e:
            self.logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False

    async def resolve_alert(self, alert_id: int) -> bool:
        """Resolve an alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE alerts 
                    SET resolved = TRUE, acknowledged = TRUE 
                    WHERE id = ?
                """,
                    (alert_id,),
                )

                conn.commit()

            return True

        except Exception as e:
            self.logger.error(f"Error resolving alert {alert_id}: {e}")
            return False

    def _get_sample_alerts(self) -> List[Dict[str, Any]]:
        """Get sample alerts for demo"""
        return [
            {
                "type": "Performance Alert",
                "severity": "medium",
                "message": "Strategy performance below threshold",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "strategy_monitor",
                "acknowledged": False,
                "resolved": False,
            },
            {
                "type": "System Health",
                "severity": "low",
                "message": "High CPU usage detected",
                "timestamp": (datetime.now() - timedelta(minutes=30)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "source": "system_monitor",
                "acknowledged": True,
                "resolved": False,
            },
            {
                "type": "Data Quality",
                "severity": "high",
                "message": "Missing market data for 5 symbols",
                "timestamp": (datetime.now() - timedelta(hours=1)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "source": "data_pipeline",
                "acknowledged": False,
                "resolved": False,
            },
        ]
