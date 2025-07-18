"""
Metrics Collector for AI Trading Machine
Handles performance monitoring and SLA tracking.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Performance metrics collector and SLA monitor."""

    def __init__(self):
        self.metrics_buffer = []
        self.sla_thresholds = {
            "data_fetch_latency_ms": 100,
            "api_response_latency_ms": 100,
            "strategy_execution_ms": 5000,
        }

        logger.info("📊 Metrics Collector initialized")

    async def record_data_fetch_metrics(self, metrics: dict[str, Any]):
        """Record data fetching performance metrics."""
        try:
            metrics["recorded_at"] = datetime.now().isoformat()
            metrics["metric_type"] = "data_fetch"

            self.metrics_buffer.append(metrics)

            # Check SLA thresholds
            latency = metrics.get("latency_ms", 0)
            if latency > self.sla_thresholds["data_fetch_latency_ms"]:
                logger.warning(
                    "🚨 SLA breach: Data fetch latency {latency}ms > {self.sla_thresholds['data_fetch_latency_ms']}ms"
                )

            # Flush buffer if it gets too large
            if len(self.metrics_buffer) > 1000:
                await self._flush_metrics()

        except Exception as e:
            logger.error("Error recording metrics: {e}")

    async def record_strategy_metrics(self, metrics: dict[str, Any]):
        """Record strategy execution metrics."""
        try:
            metrics["recorded_at"] = datetime.now().isoformat()
            metrics["metric_type"] = "strategy_execution"

            self.metrics_buffer.append(metrics)

        except Exception as e:
            logger.error("Error recording strategy metrics: {e}")

    async def _flush_metrics(self):
        """Flush metrics buffer to storage."""
        if not self.metrics_buffer:
            return

        try:
            # In production, this would send to Prometheus/CloudWatch
            logger.info("📊 Flushing {len(self.metrics_buffer)} metrics")
            self.metrics_buffer.clear()

        except Exception as e:
            logger.error("Error flushing metrics: {e}")

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current metrics summary."""
        return {
            "buffer_size": len(self.metrics_buffer),
            "last_updated": datetime.now().isoformat(),
            "sla_thresholds": self.sla_thresholds,
        }
