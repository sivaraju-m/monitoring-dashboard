"""
Advanced Monitoring and Error Recovery System
for AI Trading Machine

This module implements enhanced error recovery, monitoring & alerting,
and circuit breaker patterns for production resilience.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from google.cloud import firestore, monitoring_v3, pubsub_v1


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit breaker is open (blocking requests)
    HALF_OPEN = "half_open"  # Testing if service is recovered


@dataclass
class MonitoringMetrics:
    """Monitoring metrics for the trading system"""

    timestamp: datetime = field(default_factory=datetime.now)
    service_name: str = ""
    error_count: int = 0
    success_count: int = 0
    avg_response_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    active_strategies: int = 0
    total_trades: int = 0
    pnl: float = 0.0
    drawdown: float = 0.0


class CircuitBreaker:
    """Circuit breaker pattern implementation for service resilience"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        return (
            self.last_failure_time
            and datetime.now() - self.last_failure_time
            >= timedelta(seconds=self.recovery_timeout)
        )

    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class AdvancedMonitoring:
    """Advanced monitoring system with alerting and recovery"""

    def __init__(self, project_id: str, alert_topic: str = "trading-alerts"):
        self.project_id = project_id
        self.alert_topic = alert_topic
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.publisher = pubsub_v1.PublisherClient()
        self.firestore_client = firestore.Client()
        self.circuit_breakers = {}
        self.metrics_history = []

        # Alert thresholds
        self.thresholds = {
            "error_rate": 0.05,  # 5% error rate
            "response_time": 5.0,  # 5 seconds
            "memory_usage": 0.85,  # 85% memory usage
            "cpu_usage": 0.80,  # 80% CPU usage
            "drawdown": 0.10,  # 10% drawdown
        }

        self.logger = logging.getLogger(__name__)

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]

    async def collect_metrics(self, service_name: str) -> MonitoringMetrics:
        """Collect system metrics"""
        try:
            # This would integrate with actual monitoring systems
            # For now, we'll create a placeholder implementation
            metrics = MonitoringMetrics(
                service_name=service_name, timestamp=datetime.now()
            )

            # Store metrics in Firestore
            self.firestore_client.collection("monitoring_metrics").add(metrics.__dict__)

            self.metrics_history.append(metrics)

            # Keep only last 1000 metrics in memory
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]

            return metrics

        except Exception as e:
            self.logger.error("Failed to collect metrics: {e}")
            raise

    async def check_thresholds(self, metrics: MonitoringMetrics) -> list[str]:
        """Check if metrics exceed thresholds"""
        alerts = []

        # Calculate error rate
        total_requests = metrics.error_count + metrics.success_count
        if total_requests > 0:
            error_rate = metrics.error_count / total_requests
            if error_rate > self.thresholds["error_rate"]:
                alerts.append("High error rate: {error_rate:.2%}")

        # Check response time
        if metrics.avg_response_time > self.thresholds["response_time"]:
            alerts.append("High response time: {metrics.avg_response_time:.2f}s")

        # Check resource usage
        if metrics.memory_usage > self.thresholds["memory_usage"]:
            alerts.append("High memory usage: {metrics.memory_usage:.2%}")

        if metrics.cpu_usage > self.thresholds["cpu_usage"]:
            alerts.append("High CPU usage: {metrics.cpu_usage:.2%}")

        # Check trading metrics
        if metrics.drawdown > self.thresholds["drawdown"]:
            alerts.append("High drawdown: {metrics.drawdown:.2%}")

        return alerts

    async def send_alert(self, alert_message: str, severity: str = "WARNING"):
        """Send alert via Pub/Sub"""
        try:
            alert_data = {
                "message": alert_message,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "service": "ai-trading-machine",
            }

            topic_path = self.publisher.topic_path(self.project_id, self.alert_topic)
            message = json.dumps(alert_data).encode("utf-8")

            future = self.publisher.publish(topic_path, message)
            message_id = future.result()

            self.logger.info("Alert sent: {message_id}")

        except Exception as e:
            self.logger.error("Failed to send alert: {e}")

    async def auto_recovery(self, service_name: str, error_type: str):
        """Implement automatic recovery strategies"""
        try:
            recovery_strategies = {
                "high_memory": self._restart_service,
                "high_cpu": self._scale_service,
                "high_error_rate": self._rollback_deployment,
                "database_connection": self._reset_connections,
                "api_timeout": self._adjust_timeouts,
            }

            recovery_func = recovery_strategies.get(error_type)
            if recovery_func:
                await recovery_func(service_name)
                await self.send_alert(
                    "Auto-recovery initiated for {service_name}: {error_type}", "INFO"
                )
            else:
                await self.send_alert(
                    "No auto-recovery strategy for {error_type}", "WARNING"
                )

        except Exception as e:
            self.logger.error("Auto-recovery failed: {e}")
            await self.send_alert(
                "Auto-recovery failed for {service_name}: {e}", "ERROR"
            )

    async def _restart_service(self, service_name: str):
        """Restart Cloud Run service"""
        # Implementation would use Cloud Run Admin API
        self.logger.info("Restarting service: {service_name}")

    async def _scale_service(self, service_name: str):
        """Scale Cloud Run service"""
        # Implementation would use Cloud Run Admin API
        self.logger.info("Scaling service: {service_name}")

    async def _rollback_deployment(self, service_name: str):
        """Rollback to previous deployment"""
        # Implementation would use Cloud Run Admin API
        self.logger.info("Rolling back service: {service_name}")

    async def _reset_connections(self, service_name: str):
        """Reset database connections"""
        # Implementation would reset connection pools
        self.logger.info("Resetting connections for: {service_name}")

    async def _adjust_timeouts(self, service_name: str):
        """Adjust timeout configurations"""
        # Implementation would update service configuration
        self.logger.info("Adjusting timeouts for: {service_name}")

    async def health_check_loop(self, service_name: str, interval: int = 60):
        """Continuous health check loop"""
        while True:
            try:
                metrics = await self.collect_metrics(service_name)
                alerts = await self.check_thresholds(metrics)

                if alerts:
                    alert_message = (
                        "Health check alerts for {service_name}: " + "; ".join(alerts)
                    )
                    await self.send_alert(alert_message, "WARNING")

                    # Trigger auto-recovery for specific issues
                    for alert in alerts:
                        if "error rate" in alert:
                            await self.auto_recovery(service_name, "high_error_rate")
                        elif "memory usage" in alert:
                            await self.auto_recovery(service_name, "high_memory")
                        elif "CPU usage" in alert:
                            await self.auto_recovery(service_name, "high_cpu")

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error("Health check failed: {e}")
                await self.send_alert("Health check system error: {e}", "ERROR")
                await asyncio.sleep(interval)


class TradingKillSwitch:
    """Emergency kill switch for trading operations"""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.firestore_client = firestore.Client()
        self.kill_switch_doc = "system_controls/kill_switch"

    def is_trading_enabled(self) -> bool:
        """Check if trading is enabled"""
        try:
            doc = self.firestore_client.document(self.kill_switch_doc).get()
            if doc.exists:
                return doc.to_dict().get("trading_enabled", True)
            return True
        except Exception:
            # Default to safe mode (disabled) if we can't check
            return False

    def enable_trading(self, authorized_by: str):
        """Enable trading operations"""
        self.firestore_client.document(self.kill_switch_doc).set(
            {
                "trading_enabled": True,
                "last_changed_by": authorized_by,
                "last_changed_at": datetime.now(),
                "reason": "Trading enabled",
            }
        )

    def disable_trading(self, reason: str, authorized_by: str):
        """Disable trading operations (kill switch)"""
        self.firestore_client.document(self.kill_switch_doc).set(
            {
                "trading_enabled": False,
                "last_changed_by": authorized_by,
                "last_changed_at": datetime.now(),
                "reason": reason,
            }
        )

    def get_status(self) -> dict[str, Any]:
        """Get current kill switch status"""
        try:
            doc = self.firestore_client.document(self.kill_switch_doc).get()
            if doc.exists:
                return doc.to_dict()
            return {"trading_enabled": True, "reason": "Default state"}
        except Exception as e:
            return {"trading_enabled": False, "reason": f"Error checking status: {e}"}


# Example usage and testing
async def main():
    """Example usage of the monitoring system"""
    project_id = "ai-trading-gcp-459813"

    # Initialize monitoring
    monitoring = AdvancedMonitoring(project_id)
    kill_switch = TradingKillSwitch(project_id)

    # Example: Start health check loop
    # await monitoring.health_check_loop("ai-trading-machine")

    # Example: Use circuit breaker
    circuit_breaker = monitoring.get_circuit_breaker("backtest-api")

    def risky_operation():
        # Simulate an operation that might fail
        import random

        if random.random() < 0.3:  # 30% failure rate
            raise Exception("Operation failed")
        return "Success"

    try:
        result = circuit_breaker.call(risky_operation)
        print("Operation result: {result}")
    except Exception as e:
        print("Operation failed: {e}")

    # Example: Check kill switch
    if kill_switch.is_trading_enabled():
        print("Trading is enabled")
    else:
        print("Trading is disabled")


if __name__ == "__main__":
    # This would be run as a background service
    import asyncio

    asyncio.run(main())
