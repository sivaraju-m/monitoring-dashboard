"""
Configuration loader for monitoring dashboard
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Configuration loader with fallback defaults"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)

    def load_dashboard_config(self) -> Dict[str, Any]:
        """Load dashboard configuration"""
        config_file = self.config_dir / "dashboard_config.yaml"

        # Default configuration
        default_config = {
            "server": {"host": "0.0.0.0", "port": 8000, "debug": False},
            "metrics": {"update_interval": 30, "history_days": 30},
            "alerts": {"max_alerts": 100, "retention_days": 7},
            "dashboard": {"refresh_rate": 30, "max_data_points": 100},
        }

        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    file_config = yaml.safe_load(f)
                    # Merge with defaults
                    return self._merge_configs(default_config, file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")

        return default_config

    def load_alert_config(self) -> Dict[str, Any]:
        """Load alert configuration"""
        config_file = self.config_dir / "alert_rules.yaml"

        default_config = {
            "rules": [
                {
                    "name": "High Loss Alert",
                    "condition": "daily_pnl < -10000",
                    "severity": "high",
                    "enabled": True,
                },
                {
                    "name": "System Down Alert",
                    "condition": "system_status != 'online'",
                    "severity": "critical",
                    "enabled": True,
                },
                {
                    "name": "Strategy Performance Alert",
                    "condition": "strategy_pnl < -5000",
                    "severity": "medium",
                    "enabled": True,
                },
            ],
            "notifications": {
                "email": {"enabled": False, "recipients": []},
                "slack": {"enabled": False, "webhook_url": ""},
            },
        }

        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    file_config = yaml.safe_load(f)
                    return self._merge_configs(default_config, file_config)
            except Exception as e:
                print(f"Warning: Could not load alert config {config_file}: {e}")

        return default_config

    def _merge_configs(
        self, default: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries"""
        result = default.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result
