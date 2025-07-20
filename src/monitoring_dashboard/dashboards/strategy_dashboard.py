"""
Strategy dashboard for performance visualization
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd

from ..utils.logger import DashboardLogger


class StrategyDashboard:
    """Strategy performance dashboard"""

    def __init__(self):
        self.logger = DashboardLogger("strategy_dashboard")
        self.data_sources = self._setup_data_sources()

    def _setup_data_sources(self) -> Dict[str, Path]:
        """Setup data source paths"""
        base_dir = Path(__file__).parent.parent.parent.parent.parent

        return {
            "strategy_engine": base_dir / "strategy-engine" / "data",
            "trading_engine": base_dir / "trading-execution-engine" / "data",
            "data_pipeline": base_dir / "trading-data-pipeline" / "data",
        }

    async def get_performance_data(self) -> Dict[str, List[Any]]:
        """Get performance chart data"""
        try:
            # Try to load from strategy engine data
            performance_data = await self._load_strategy_performance()

            if not performance_data:
                # Generate sample data for demo
                performance_data = self._generate_sample_performance()

            return performance_data

        except Exception as e:
            self.logger.error(f"Error getting performance data: {e}")
            return {"timestamps": [], "values": []}

    async def get_allocation_data(self) -> Dict[str, List[Any]]:
        """Get strategy allocation data"""
        try:
            allocation_data = await self._load_strategy_allocation()

            if not allocation_data:
                # Generate sample allocation
                allocation_data = {
                    "labels": [
                        "Momentum",
                        "Mean Reversion",
                        "Breakout",
                        "Trend Following",
                        "Statistical Arbitrage",
                    ],
                    "values": [25, 20, 15, 25, 15],
                }

            return allocation_data

        except Exception as e:
            self.logger.error(f"Error getting allocation data: {e}")
            return {"labels": [], "values": []}

    async def get_strategy_summary(self) -> List[Dict[str, Any]]:
        """Get strategy summary table data"""
        try:
            strategies = await self._load_strategy_details()

            if not strategies:
                # Generate sample strategies
                strategies = [
                    {
                        "name": "Momentum Strategy",
                        "status": "active",
                        "pnl": "+₹2,450",
                        "signals": "12",
                    },
                    {
                        "name": "Mean Reversion",
                        "status": "active",
                        "pnl": "+₹1,890",
                        "signals": "8",
                    },
                    {
                        "name": "Breakout Strategy",
                        "status": "active",
                        "pnl": "-₹560",
                        "signals": "15",
                    },
                    {
                        "name": "Trend Following",
                        "status": "active",
                        "pnl": "+₹3,210",
                        "signals": "10",
                    },
                    {
                        "name": "Statistical Arbitrage",
                        "status": "paused",
                        "pnl": "+₹890",
                        "signals": "5",
                    },
                ]

            return strategies

        except Exception as e:
            self.logger.error(f"Error getting strategy summary: {e}")
            return []

    async def _load_strategy_performance(self) -> Optional[Dict[str, List[Any]]]:
        """Load strategy performance from files"""
        try:
            strategy_data_dir = self.data_sources["strategy_engine"]

            if not strategy_data_dir.exists():
                return None

            # Look for performance files
            perf_files = list(strategy_data_dir.glob("*performance*.json"))

            if not perf_files:
                return None

            # Get the most recent file
            latest_file = max(perf_files, key=lambda f: f.stat().st_mtime)

            with open(latest_file, "r") as f:
                data = json.load(f)

            # Extract performance time series
            if "performance_history" in data:
                history = data["performance_history"]
                return {
                    "timestamps": [entry["timestamp"] for entry in history],
                    "values": [entry["portfolio_value"] for entry in history],
                }

            return None

        except Exception as e:
            self.logger.debug(f"Could not load strategy performance: {e}")
            return None

    async def _load_strategy_allocation(self) -> Optional[Dict[str, List[Any]]]:
        """Load strategy allocation from files"""
        try:
            strategy_data_dir = self.data_sources["strategy_engine"]

            if not strategy_data_dir.exists():
                return None

            # Look for allocation files
            allocation_files = list(strategy_data_dir.glob("*allocation*.json"))

            if not allocation_files:
                return None

            latest_file = max(allocation_files, key=lambda f: f.stat().st_mtime)

            with open(latest_file, "r") as f:
                data = json.load(f)

            if "strategy_allocation" in data:
                allocation = data["strategy_allocation"]
                return {
                    "labels": list(allocation.keys()),
                    "values": list(allocation.values()),
                }

            return None

        except Exception as e:
            self.logger.debug(f"Could not load strategy allocation: {e}")
            return None

    async def _load_strategy_details(self) -> Optional[List[Dict[str, Any]]]:
        """Load detailed strategy information"""
        try:
            strategy_data_dir = self.data_sources["strategy_engine"]

            if not strategy_data_dir.exists():
                return None

            # Look for strategy detail files
            detail_files = list(strategy_data_dir.glob("*strategy_details*.json"))

            if not detail_files:
                return None

            latest_file = max(detail_files, key=lambda f: f.stat().st_mtime)

            with open(latest_file, "r") as f:
                data = json.load(f)

            if "strategies" in data:
                return data["strategies"]

            return None

        except Exception as e:
            self.logger.debug(f"Could not load strategy details: {e}")
            return None

    def _generate_sample_performance(self) -> Dict[str, List[Any]]:
        """Generate sample performance data for demo"""
        try:
            # Generate last 30 days of sample data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            timestamps = []
            values = []

            current_date = start_date
            portfolio_value = 1000000  # Start with ₹10 lakh

            while current_date <= end_date:
                timestamps.append(current_date.strftime("%Y-%m-%d"))

                # Simulate some volatility
                import random

                daily_return = random.uniform(-0.02, 0.03)  # -2% to +3% daily
                portfolio_value *= 1 + daily_return
                values.append(round(portfolio_value, 2))

                current_date += timedelta(days=1)

            return {"timestamps": timestamps, "values": values}

        except Exception as e:
            self.logger.warning(f"Could not generate sample performance: {e}")
            return {"timestamps": [], "values": []}
