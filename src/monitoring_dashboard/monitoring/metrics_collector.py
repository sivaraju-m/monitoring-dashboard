"""
Metrics collector for monitoring dashboard
Collects performance and system metrics from various sources
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import requests

from ..utils.logger import DashboardLogger


class MetricsCollector:
    """Collects metrics from trading system components"""

    def __init__(self):
        self.logger = DashboardLogger("metrics")
        self.db_path = self._setup_database()

        # External service endpoints - Production URLs from environment variables
        self.endpoints = {
            "strategy_engine": os.getenv(
                "STRATEGY_ENGINE_URL", "https://strategy-engine-uc.a.run.app"
            )
            + "/api/metrics",
            "trading_engine": os.getenv(
                "TRADING_EXECUTION_ENGINE_URL",
                "https://trading-execution-engine-uc.a.run.app",
            )
            + "/api/metrics",
            "data_pipeline": os.getenv(
                "TRADING_DATA_PIPELINE_URL",
                "https://trading-data-pipeline-uc.a.run.app",
            )
            + "/api/metrics",
        }

    def _setup_database(self) -> str:
        """Setup local metrics database"""
        db_dir = Path(__file__).parent.parent.parent.parent / "data"
        db_dir.mkdir(parents=True, exist_ok=True)

        db_path = db_dir / "metrics.db"

        # Create tables if they don't exist
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL,
                    metadata TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON metrics(timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_metrics_source_type 
                ON metrics(source, metric_type)
            """
            )

        return str(db_path)

    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "online",
                "active_strategies": 0,
                "daily_pnl": 0.0,
                "total_pnl": 0.0,
                "active_alerts": 0,
                "data_quality": "good",
                "last_update": datetime.now().isoformat(),
            }

            # Collect from strategy engine
            strategy_metrics = await self._get_strategy_metrics()
            if strategy_metrics:
                metrics.update(
                    {
                        "active_strategies": strategy_metrics.get(
                            "active_strategies", 0
                        ),
                        "strategy_pnl": strategy_metrics.get("daily_pnl", 0.0),
                        "total_signals": strategy_metrics.get("total_signals", 0),
                    }
                )

            # Collect from trading engine
            trading_metrics = await self._get_trading_metrics()
            if trading_metrics:
                metrics.update(
                    {
                        "daily_pnl": trading_metrics.get("daily_pnl", 0.0),
                        "total_pnl": trading_metrics.get("total_pnl", 0.0),
                        "active_positions": trading_metrics.get("active_positions", 0),
                    }
                )

            # Collect system health metrics
            system_metrics = await self._get_system_metrics()
            metrics.update(system_metrics)

            # Store metrics
            await self._store_metrics("dashboard", "summary", metrics)

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting current metrics: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": "error",
                "error": str(e),
            }

    async def _get_strategy_metrics(self) -> Optional[Dict[str, Any]]:
        """Get metrics from strategy engine"""
        try:
            # Try to get from strategy engine API
            response = await self._make_request(self.endpoints["strategy_engine"])
            if response:
                return response

            # Fallback: read from local files
            return await self._read_strategy_files()

        except Exception as e:
            self.logger.warning(f"Could not get strategy metrics: {e}")
            return None

    async def _get_trading_metrics(self) -> Optional[Dict[str, Any]]:
        """Get metrics from trading engine"""
        try:
            # Try to get from trading engine API
            response = await self._make_request(self.endpoints["trading_engine"])
            if response:
                return response

            # Fallback: read from local files
            return await self._read_trading_files()

        except Exception as e:
            self.logger.warning(f"Could not get trading metrics: {e}")
            return None

    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            import psutil

            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "memory_available": memory.available / (1024**3),  # GB
                "disk_free": disk.free / (1024**3),  # GB
            }

        except ImportError:
            # Fallback if psutil not available
            return {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "memory_available": 0,
                "disk_free": 0,
            }
        except Exception as e:
            self.logger.warning(f"Could not get system metrics: {e}")
            return {}

    async def _make_request(
        self, url: str, timeout: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to service endpoint"""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.debug(f"Request to {url} failed: {e}")
        return None

    async def _read_strategy_files(self) -> Dict[str, Any]:
        """Read strategy metrics from local files"""
        try:
            # Look for strategy engine data
            strategy_dir = (
                Path(__file__).parent.parent.parent.parent.parent
                / "strategy-engine"
                / "data"
            )

            metrics = {"active_strategies": 0, "daily_pnl": 0.0, "total_signals": 0}

            # Check for recent performance files
            if strategy_dir.exists():
                perf_files = list(strategy_dir.glob("*performance*.json"))
                if perf_files:
                    # Get the most recent file
                    latest_file = max(perf_files, key=lambda f: f.stat().st_mtime)

                    with open(latest_file, "r") as f:
                        data = json.load(f)
                        metrics.update(
                            {
                                "active_strategies": len(data.get("strategies", [])),
                                "daily_pnl": data.get("daily_pnl", 0.0),
                                "total_signals": data.get("total_signals", 0),
                            }
                        )

            return metrics

        except Exception as e:
            self.logger.debug(f"Could not read strategy files: {e}")
            return {"active_strategies": 0, "daily_pnl": 0.0, "total_signals": 0}

    async def _read_trading_files(self) -> Dict[str, Any]:
        """Read trading metrics from local files"""
        try:
            # Look for trading engine data
            trading_dir = (
                Path(__file__).parent.parent.parent.parent.parent
                / "trading-execution-engine"
                / "data"
            )

            metrics = {"daily_pnl": 0.0, "total_pnl": 0.0, "active_positions": 0}

            # Check for recent trading files
            if trading_dir.exists():
                trading_files = list(trading_dir.glob("*trading*.json"))
                if trading_files:
                    # Get the most recent file
                    latest_file = max(trading_files, key=lambda f: f.stat().st_mtime)

                    with open(latest_file, "r") as f:
                        data = json.load(f)
                        metrics.update(
                            {
                                "daily_pnl": data.get("daily_pnl", 0.0),
                                "total_pnl": data.get("total_pnl", 0.0),
                                "active_positions": len(data.get("positions", [])),
                            }
                        )

            return metrics

        except Exception as e:
            self.logger.debug(f"Could not read trading files: {e}")
            return {"daily_pnl": 0.0, "total_pnl": 0.0, "active_positions": 0}

    async def _store_metrics(
        self, source: str, metric_type: str, metrics: Dict[str, Any]
    ):
        """Store metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        conn.execute(
                            """
                            INSERT INTO metrics (source, metric_type, metric_name, value, metadata)
                            VALUES (?, ?, ?, ?, ?)
                        """,
                            (
                                source,
                                metric_type,
                                key,
                                value,
                                json.dumps({"timestamp": metrics.get("timestamp")}),
                            ),
                        )

                conn.commit()

        except Exception as e:
            self.logger.warning(f"Could not store metrics: {e}")

    async def get_historical_metrics(self, days: int = 7) -> Dict[str, List[Any]]:
        """Get historical metrics for charts"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(
                    """
                    SELECT timestamp, metric_name, value
                    FROM metrics
                    WHERE timestamp >= ? AND source = 'dashboard'
                    ORDER BY timestamp
                """,
                    conn,
                    params=[start_date.isoformat()],
                )

            # Organize data for charts
            chart_data = {}

            for metric in ["daily_pnl", "total_pnl", "active_strategies"]:
                metric_data = df[df["metric_name"] == metric]
                chart_data[metric] = {
                    "timestamps": metric_data["timestamp"].tolist(),
                    "values": metric_data["value"].tolist(),
                }

            return chart_data

        except Exception as e:
            self.logger.error(f"Error getting historical metrics: {e}")
            return {}

    async def get_alert_count(self) -> int:
        """Get current alert count"""
        try:
            # Check for recent alerts in the system
            alert_sources = [
                Path(__file__).parent.parent.parent.parent.parent
                / "strategy-engine"
                / "logs",
                Path(__file__).parent.parent.parent.parent.parent
                / "trading-execution-engine"
                / "logs",
            ]

            alert_count = 0

            for source_dir in alert_sources:
                if source_dir.exists():
                    # Count recent error/warning log entries
                    log_files = list(source_dir.glob("*.log"))

                    for log_file in log_files[:3]:  # Check last 3 log files
                        try:
                            with open(log_file, "r") as f:
                                lines = f.readlines()[-100:]  # Last 100 lines

                            for line in lines:
                                if any(
                                    level in line.upper()
                                    for level in ["ERROR", "WARNING", "CRITICAL"]
                                ):
                                    alert_count += 1

                        except Exception:
                            pass

            return min(alert_count, 50)  # Cap at 50 to avoid overwhelming

        except Exception as e:
            self.logger.warning(f"Could not get alert count: {e}")
            return 0
