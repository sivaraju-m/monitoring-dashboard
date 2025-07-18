#!/usr/bin/env python3
"""
Smart Alerting System for AI Trading Machine
===========================================

Intelligent notification system that sends alerts for:
- High-confidence trading signals
- Portfolio performance updates
- Risk management warnings
- System status alerts
- Daily performance summaries

Supports multiple notification channels:
- Email alerts
- Console notifications
- Log file alerts
- Webhook notifications (for future integration)

Usage:
    python smart_alerting_system.py

Author: AI Trading Machine
Licensed by SJ Trading
"""

import json
import os
import smtplib
import sys
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.ai_trading_machine.utils.logger import setup_logger

logger = setup_logger(__name__)


class AlertLevel(Enum):
    """Alert priority levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    """Types of alerts."""

    SIGNAL = "SIGNAL"
    RISK = "RISK"
    PERFORMANCE = "PERFORMANCE"
    SYSTEM = "SYSTEM"
    ERROR = "ERROR"


@dataclass
class Alert:
    """Alert data structure."""

    id: str
    level: AlertLevel
    type: AlertType
    title: str
    message: str
    timestamp: datetime
    data: dict[str, Any] = None
    sent: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "level": self.level.value,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data or {},
            "sent": self.sent,
        }


class SmartAlertingSystem:
    """Intelligent alerting system for trading events."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the alerting system."""
        self.config_path = config_path or os.path.join(
            project_root, "alerting_config.json"
        )
        self.config = self.load_config()
        self.alerts_dir = os.path.join(project_root, "alerts")
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.alerts_dir, exist_ok=True)

    def load_config(self) -> dict[str, Any]:
        """Load alerting configuration."""
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "to_addresses": [],
            },
            "console": {"enabled": True, "min_level": "MEDIUM"},
            "file": {
                "enabled": True,
                "min_level": "LOW",
                "file_path": "alerts/alerts.log",
            },
            "signal_thresholds": {"confidence_high": 0.8, "confidence_critical": 0.9},
            "risk_thresholds": {
                "max_drawdown_warning": 0.05,
                "max_drawdown_critical": 0.10,
                "daily_loss_warning": 0.02,
                "daily_loss_critical": 0.05,
            },
        }

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path) as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logger.warning("Error loading config: {e}. Using defaults.")

        return default_config

    def save_config(self):
        """Save current configuration."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error("Error saving config: {e}")

    def create_alert(
        self,
        level: AlertLevel,
        alert_type: AlertType,
        title: str,
        message: str,
        data: dict[str, Any] = None,
    ) -> Alert:
        """Create a new alert."""
        alert_id = "{alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        alert = Alert(
            id=alert_id,
            level=level,
            type=alert_type,
            title=title,
            message=message,
            timestamp=datetime.now(),
            data=data or {},
        )

        return alert

    def should_send_alert(self, alert: Alert, channel: str) -> bool:
        """Determine if alert should be sent on given channel."""
        channel_config = self.config.get(channel, {})

        if not channel_config.get("enabled", False):
            return False

        min_level = channel_config.get("min_level", "LOW")
        level_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        alert_level_index = level_order.index(alert.level.value)
        min_level_index = level_order.index(min_level)

        return alert_level_index >= min_level_index

    def send_console_alert(self, alert: Alert):
        """Send alert to console."""
        if not self.should_send_alert(alert, "console"):
            return

        level_icons = {"LOW": "ℹ️", "MEDIUM": "⚠️", "HIGH": "🚨", "CRITICAL": "🔥"}

        icon = level_icons.get(alert.level.value, "📢")
        timestamp = alert.timestamp.strftime("%H:%M:%S")

        print("\n{icon} ALERT [{alert.level.value}] - {timestamp}")
        print("📋 {alert.title}")
        print("💬 {alert.message}")

        if alert.data:
            print("📊 Data:")
            for key, value in alert.data.items():
                print("   • {key}: {value}")
        print("-" * 50)

    def send_file_alert(self, alert: Alert):
        """Send alert to log file."""
        if not self.should_send_alert(alert, "file"):
            return

        log_file = self.config["file"]["file_path"]
        log_path = os.path.join(project_root, log_file)

        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        with open(log_path, "a") as f:
            f.write(
                "{alert.timestamp.isoformat()} [{alert.level.value}] {alert.type.value}: {alert.title}\n"
            )
            f.write("Message: {alert.message}\n")
            if alert.data:
                f.write("Data: {json.dumps(alert.data)}\n")
            f.write("-" * 80 + "\n")

    def send_email_alert(self, alert: Alert):
        """Send alert via email."""
        if not self.should_send_alert(alert, "email"):
            return

        email_config = self.config["email"]

        if not email_config.get("username") or not email_config.get("to_addresses"):
            logger.warning("Email not configured properly")
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = email_config["username"]
            msg["To"] = ", ".join(email_config["to_addresses"])
            msg["Subject"] = "[AI Trading] {alert.level.value}: {alert.title}"

            # Email body
            body = """
AI Trading Machine Alert

Level: {alert.level.value}
Type: {alert.type.value}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Title: {alert.title}

Message:
{alert.message}
"""

            if alert.data:
                body += "\n\nAdditional Data:\n"
                for key, value in alert.data.items():
                    body += "• {key}: {value}\n"

            body += "\n\n---\nAI Trading Machine Alert System"

            msg.attach(MIMEText(body, "plain"))

            # Send email
            server = smtplib.SMTP(
                email_config["smtp_server"], email_config["smtp_port"]
            )
            server.starttls()
            server.login(email_config["username"], email_config["password"])

            text = msg.as_string()
            server.sendmail(
                email_config["username"], email_config["to_addresses"], text
            )
            server.quit()

            logger.info("Email alert sent: {alert.title}")

        except Exception as e:
            logger.error("Error sending email alert: {e}")

    def save_alert(self, alert: Alert):
        """Save alert to file."""
        alert_file = os.path.join(self.alerts_dir, "alert_{alert.id}.json")

        try:
            with open(alert_file, "w") as f:
                json.dump(alert.to_dict(), f, indent=2)
        except Exception as e:
            logger.error("Error saving alert: {e}")

    def send_alert(self, alert: Alert):
        """Send alert through all configured channels."""
        logger.info("Sending alert: {alert.title}")

        # Send through all channels
        self.send_console_alert(alert)
        self.send_file_alert(alert)
        self.send_email_alert(alert)

        # Save alert
        self.save_alert(alert)
        alert.sent = True

        # Update statistics
        self.update_alert_stats(alert)

    def update_alert_stats(self, alert: Alert):
        """Update alert statistics."""
        stats_file = os.path.join(self.alerts_dir, "alert_stats.json")

        try:
            stats = {}
            if os.path.exists(stats_file):
                with open(stats_file) as f:
                    stats = json.load(f)

            today = datetime.now().date().isoformat()
            if today not in stats:
                stats[today] = {"total": 0, "by_level": {}, "by_type": {}}

            stats[today]["total"] += 1

            level = alert.level.value
            if level not in stats[today]["by_level"]:
                stats[today]["by_level"][level] = 0
            stats[today]["by_level"][level] += 1

            alert_type = alert.type.value
            if alert_type not in stats[today]["by_type"]:
                stats[today]["by_type"][alert_type] = 0
            stats[today]["by_type"][alert_type] += 1

            with open(stats_file, "w") as f:
                json.dump(stats, f, indent=2)

        except Exception as e:
            logger.error("Error updating alert stats: {e}")

    def alert_signal(self, signal_data: dict[str, Any]):
        """Send signal-based alert."""
        confidence = signal_data.get("confidence", 0)
        symbol = signal_data.get("symbol", "Unknown")
        action = signal_data.get("action", "Unknown")

        if confidence >= self.config["signal_thresholds"]["confidence_critical"]:
            level = AlertLevel.CRITICAL
        elif confidence >= self.config["signal_thresholds"]["confidence_high"]:
            level = AlertLevel.HIGH
        else:
            level = AlertLevel.MEDIUM

        title = "Trading Signal: {action} {symbol}"
        message = "High confidence {action} signal detected for {symbol} (Confidence: {confidence:.1%})"

        alert = self.create_alert(level, AlertType.SIGNAL, title, message, signal_data)
        self.send_alert(alert)

    def alert_risk(self, risk_data: dict[str, Any]):
        """Send risk-based alert."""
        risk_type = risk_data.get("type", "Unknown")
        value = risk_data.get("value", 0)

        thresholds = self.config["risk_thresholds"]

        if risk_type == "drawdown":
            if value >= thresholds["max_drawdown_critical"]:
                level = AlertLevel.CRITICAL
            elif value >= thresholds["max_drawdown_warning"]:
                level = AlertLevel.HIGH
            else:
                level = AlertLevel.MEDIUM
        elif risk_type == "daily_loss":
            if value >= thresholds["daily_loss_critical"]:
                level = AlertLevel.CRITICAL
            elif value >= thresholds["daily_loss_warning"]:
                level = AlertLevel.HIGH
            else:
                level = AlertLevel.MEDIUM
        else:
            level = AlertLevel.MEDIUM

        title = "Risk Alert: {risk_type.title()}"
        message = "Risk threshold exceeded: {risk_type} = {value:.1%}"

        alert = self.create_alert(level, AlertType.RISK, title, message, risk_data)
        self.send_alert(alert)

    def alert_performance(self, performance_data: dict[str, Any]):
        """Send performance-based alert."""
        pnl = performance_data.get("pnl", 0)
        win_rate = performance_data.get("win_rate", 0)

        if pnl > 1000:  # Good performance
            level = AlertLevel.LOW
            title = "Performance Update: Strong Performance"
            message = "Excellent trading performance today: P&L = ₹{pnl:.2f}, Win Rate = {win_rate:.1f}%"
        elif pnl < -500:  # Poor performance
            level = AlertLevel.HIGH
            title = "Performance Alert: Poor Performance"
            message = "Trading performance below expectations: P&L = ₹{pnl:.2f}, Win Rate = {win_rate:.1f}%"
        else:
            level = AlertLevel.LOW
            title = "Performance Update: Daily Summary"
            message = "Daily performance summary: P&L = ₹{pnl:.2f}, Win Rate = {win_rate:.1f}%"

        alert = self.create_alert(
            level, AlertType.PERFORMANCE, title, message, performance_data
        )
        self.send_alert(alert)

    def alert_system(self, system_data: dict[str, Any]):
        """Send system-based alert."""
        status = system_data.get("status", "Unknown")
        message_text = system_data.get("message", "")

        if status == "error":
            level = AlertLevel.HIGH
            title = "System Error"
        elif status == "warning":
            level = AlertLevel.MEDIUM
            title = "System Warning"
        else:
            level = AlertLevel.LOW
            title = "System Update"

        alert = self.create_alert(
            level, AlertType.SYSTEM, title, message_text, system_data
        )
        self.send_alert(alert)

    def get_alert_stats(self) -> dict[str, Any]:
        """Get alert statistics."""
        stats_file = os.path.join(self.alerts_dir, "alert_stats.json")

        try:
            if os.path.exists(stats_file):
                with open(stats_file) as f:
                    return json.load(f)
        except Exception as e:
            logger.error("Error loading alert stats: {e}")

        return {}

    def test_alerting_system(self):
        """Test the alerting system."""
        print("🧪 Testing Smart Alerting System")
        print("=" * 40)

        # Test different alert levels
        test_alerts = [
            (
                AlertLevel.LOW,
                AlertType.SYSTEM,
                "Test Low Priority",
                "This is a low priority test alert",
            ),
            (
                AlertLevel.MEDIUM,
                AlertType.SIGNAL,
                "Test Medium Priority",
                "This is a medium priority test alert",
            ),
            (
                AlertLevel.HIGH,
                AlertType.RISK,
                "Test High Priority",
                "This is a high priority test alert",
            ),
            (
                AlertLevel.CRITICAL,
                AlertType.ERROR,
                "Test Critical Priority",
                "This is a critical priority test alert",
            ),
        ]

        for level, alert_type, title, message in test_alerts:
            alert = self.create_alert(level, alert_type, title, message)
            self.send_alert(alert)

        print("\n✅ Alert testing completed!")
        print("📊 Check alerts directory: {self.alerts_dir}")


def main():
    """Main function to run alerting system."""
    print("📢 AI Trading Machine - Smart Alerting System")
    print("=" * 50)

    alerting = SmartAlertingSystem()

    # Run test
    alerting.test_alerting_system()

    # Show stats
    stats = alerting.get_alert_stats()
    if stats:
        print("\n📊 Alert Statistics:")
        for date, data in stats.items():
            print("   {date}: {data['total']} alerts")


if __name__ == "__main__":
    main()
