"""
End-to-End Latency & Throughput Monitoring System
Comprehensive monitoring of signal generation, execution, and data pipeline performance
"""

import json
import logging
import sqlite3
import statistics
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline stages for latency tracking"""

    DATA_INGESTION = "data_ingestion"
    DATA_PROCESSING = "data_processing"
    FEATURE_EXTRACTION = "feature_extraction"
    SIGNAL_GENERATION = "signal_generation"
    RISK_VALIDATION = "risk_validation"
    ORDER_CREATION = "order_creation"
    ORDER_EXECUTION = "order_execution"
    TRADE_CONFIRMATION = "trade_confirmation"
    PORTFOLIO_UPDATE = "portfolio_update"


class MetricType(Enum):
    """Types of performance metrics"""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    QUEUE_DEPTH = "queue_depth"
    RESOURCE_UTILIZATION = "resource_utilization"


class SLOStatus(Enum):
    """SLO compliance status"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class LatencyMeasurement:
    """Individual latency measurement"""

    stage: PipelineStage
    start_time: datetime
    end_time: datetime
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass
class ThroughputMeasurement:
    """Throughput measurement for a time window"""

    stage: PipelineStage
    timestamp: datetime
    items_processed: int
    window_seconds: int
    throughput_per_second: float
    errors: int


@dataclass
class SLODefinition:
    """Service Level Objective definition"""

    name: str
    stage: PipelineStage
    metric_type: MetricType
    target_value: float
    warning_threshold: float
    critical_threshold: float
    measurement_window_minutes: int
    description: str


@dataclass
class SLOStatus:
    """Current SLO status"""

    slo_name: str
    status: SLOStatus
    current_value: float
    target_value: float
    compliance_percentage: float
    last_violation: Optional[datetime] = None
    violation_count_24h: int = 0


class PerformanceCollector:
    """Collects performance metrics from various pipeline stages"""

    def __init__(self):
        self.measurements: dict[PipelineStage, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        self.throughput_data: dict[PipelineStage, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.active_traces: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    @contextmanager
    def trace_stage(
        self,
        stage: PipelineStage,
        trace_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Context manager for tracing pipeline stage execution"""
        if trace_id is None:
            trace_id = "{stage.value}_{int(time.time() * 1000000)}"

        start_time = datetime.now()
        success = True
        error_message = None

        try:
            with self._lock:
                self.active_traces[trace_id] = {
                    "stage": stage,
                    "start_time": start_time,
                    "metadata": metadata or {},
                }

            yield trace_id

        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            measurement = LatencyMeasurement(
                stage=stage,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                metadata=metadata,
            )

            with self._lock:
                self.measurements[stage].append(measurement)
                if trace_id in self.active_traces:
                    del self.active_traces[trace_id]

    def record_throughput(
        self,
        stage: PipelineStage,
        items_processed: int,
        window_seconds: int = 60,
        errors: int = 0,
    ):
        """Record throughput measurement"""
        throughput_per_second = (
            items_processed / window_seconds if window_seconds > 0 else 0
        )

        measurement = ThroughputMeasurement(
            stage=stage,
            timestamp=datetime.now(),
            items_processed=items_processed,
            window_seconds=window_seconds,
            throughput_per_second=throughput_per_second,
            errors=errors,
        )

        with self._lock:
            self.throughput_data[stage].append(measurement)

    def get_latency_stats(
        self, stage: PipelineStage, minutes_back: int = 60
    ) -> dict[str, float]:
        """Get latency statistics for a stage"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes_back)

        with self._lock:
            recent_measurements = [
                m
                for m in self.measurements[stage]
                if m.start_time >= cutoff_time and m.success
            ]

        if not recent_measurements:
            return {}

        durations = [m.duration_ms for m in recent_measurements]

        return {
            "count": len(durations),
            "mean_ms": statistics.mean(durations),
            "median_ms": statistics.median(durations),
            "p95_ms": self._percentile(durations, 95),
            "p99_ms": self._percentile(durations, 99),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "success_rate": (
                len(durations) / len(self.measurements[stage])
                if self.measurements[stage]
                else 0
            ),
        }

    def get_throughput_stats(
        self, stage: PipelineStage, minutes_back: int = 60
    ) -> dict[str, float]:
        """Get throughput statistics for a stage"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes_back)

        with self._lock:
            recent_measurements = [
                m for m in self.throughput_data[stage] if m.timestamp >= cutoff_time
            ]

        if not recent_measurements:
            return {}

        throughputs = [m.throughput_per_second for m in recent_measurements]
        total_items = sum(m.items_processed for m in recent_measurements)
        total_errors = sum(m.errors for m in recent_measurements)

        return {
            "count": len(throughputs),
            "mean_throughput": statistics.mean(throughputs),
            "max_throughput": max(throughputs),
            "total_items": total_items,
            "total_errors": total_errors,
            "error_rate": total_errors / total_items if total_items > 0 else 0,
        }

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class SLOMonitor:
    """Monitors Service Level Objectives"""

    def __init__(self, config_path: str = "configs/slo_config.json"):
        self.config = self._load_config(config_path)
        self.slos = self._load_slos()
        self.violation_history: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load SLO configuration"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load SLO config: {e}")
            return self._get_default_slo_config()

    def _get_default_slo_config(self) -> dict[str, Any]:
        """Get default SLO configuration"""
        return {
            "slos": [
                {
                    "name": "signal_generation_latency",
                    "stage": "signal_generation",
                    "metric_type": "latency",
                    "target_value": 1000.0,
                    "warning_threshold": 1500.0,
                    "critical_threshold": 3000.0,
                    "measurement_window_minutes": 15,
                    "description": "Signal generation should complete within 1 second",
                },
                {
                    "name": "order_execution_latency",
                    "stage": "order_execution",
                    "metric_type": "latency",
                    "target_value": 2000.0,
                    "warning_threshold": 5000.0,
                    "critical_threshold": 10000.0,
                    "measurement_window_minutes": 15,
                    "description": "Order execution should complete within 2 seconds",
                },
                {
                    "name": "data_processing_throughput",
                    "stage": "data_processing",
                    "metric_type": "throughput",
                    "target_value": 100.0,
                    "warning_threshold": 50.0,
                    "critical_threshold": 20.0,
                    "measurement_window_minutes": 5,
                    "description": "Data processing should handle 100 items/second",
                },
            ]
        }

    def _load_slos(self) -> list[SLODefinition]:
        """Load SLO definitions from config"""
        slos = []

        for slo_config in self.config.get("slos", []):
            slo = SLODefinition(
                name=slo_config["name"],
                stage=PipelineStage(slo_config["stage"]),
                metric_type=MetricType(slo_config["metric_type"]),
                target_value=slo_config["target_value"],
                warning_threshold=slo_config["warning_threshold"],
                critical_threshold=slo_config["critical_threshold"],
                measurement_window_minutes=slo_config["measurement_window_minutes"],
                description=slo_config["description"],
            )
            slos.append(slo)

        return slos

    def check_slos(
        self, performance_collector: PerformanceCollector
    ) -> list[SLOStatus]:
        """Check all SLOs against current performance"""
        slo_statuses = []

        for slo in self.slos:
            status = self._check_single_slo(slo, performance_collector)
            slo_statuses.append(status)

            # Track violations
            if status.status in [SLOStatus.WARNING, SLOStatus.CRITICAL]:
                self._record_violation(slo, status)

        return slo_statuses

    def _check_single_slo(
        self, slo: SLODefinition, performance_collector: PerformanceCollector
    ) -> SLOStatus:
        """Check a single SLO"""
        try:
            if slo.metric_type == MetricType.LATENCY:
                stats = performance_collector.get_latency_stats(
                    slo.stage, slo.measurement_window_minutes
                )
                current_value = stats.get("p95_ms", float("in"))

            elif slo.metric_type == MetricType.THROUGHPUT:
                stats = performance_collector.get_throughput_stats(
                    slo.stage, slo.measurement_window_minutes
                )
                current_value = stats.get("mean_throughput", 0.0)

            else:
                current_value = 0.0

            # Determine status
            if slo.metric_type == MetricType.LATENCY:
                # For latency, lower is better
                if current_value <= slo.target_value:
                    status = SLOStatus.HEALTHY
                elif current_value <= slo.warning_threshold:
                    status = SLOStatus.WARNING
                else:
                    status = SLOStatus.CRITICAL
            else:
                # For throughput, higher is better
                if current_value >= slo.target_value:
                    status = SLOStatus.HEALTHY
                elif current_value >= slo.warning_threshold:
                    status = SLOStatus.WARNING
                else:
                    status = SLOStatus.CRITICAL

            # Calculate compliance percentage
            if slo.metric_type == MetricType.LATENCY:
                compliance = (
                    min(100.0, (slo.target_value / current_value) * 100)
                    if current_value > 0
                    else 100.0
                )
            else:
                compliance = (
                    min(100.0, (current_value / slo.target_value) * 100)
                    if slo.target_value > 0
                    else 100.0
                )

            return SLOStatus(
                slo_name=slo.name,
                status=status,
                current_value=current_value,
                target_value=slo.target_value,
                compliance_percentage=compliance,
                violation_count_24h=self._get_violation_count_24h(slo.name),
            )

        except Exception as e:
            logger.error("Failed to check SLO {slo.name}: {e}")
            return SLOStatus(
                slo_name=slo.name,
                status=SLOStatus.UNKNOWN,
                current_value=0.0,
                target_value=slo.target_value,
                compliance_percentage=0.0,
                violation_count_24h=0,
            )

    def _record_violation(self, slo: SLODefinition, status: SLOStatus):
        """Record SLO violation"""
        violation = {
            "timestamp": datetime.now(),
            "slo_name": slo.name,
            "status": status.status.value,
            "current_value": status.current_value,
            "target_value": status.target_value,
            "compliance_percentage": status.compliance_percentage,
        }

        with self._lock:
            self.violation_history.append(violation)

            # Keep only last 1000 violations
            if len(self.violation_history) > 1000:
                self.violation_history = self.violation_history[-1000:]

    def _get_violation_count_24h(self, slo_name: str) -> int:
        """Get violation count for SLO in last 24 hours"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        with self._lock:
            return len(
                [
                    v
                    for v in self.violation_history
                    if v["slo_name"] == slo_name and v["timestamp"] >= cutoff_time
                ]
            )


class PipelineMonitor:
    """End-to-end pipeline monitoring system"""

    def __init__(self, config_path: str = "configs/pipeline_monitoring_config.json"):
        self.config = self._load_config(config_path)
        self.db_path = self.config.get("database", {}).get(
            "path", "data/pipeline_monitoring.db"
        )

        self.performance_collector = PerformanceCollector()
        self.slo_monitor = SLOMonitor()

        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None

        self._init_database()

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load pipeline monitoring configuration"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load pipeline monitoring config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration"""
        return {
            "monitoring": {
                "check_interval_seconds": 30,
                "metric_retention_hours": 24,
                "alert_cooldown_minutes": 5,
            },
            "database": {"path": "data/pipeline_monitoring.db", "retention_days": 7},
            "alerting": {"enabled": True, "webhook_url": None, "email_recipients": []},
        }

    def _init_database(self):
        """Initialize monitoring database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Latency measurements table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS latency_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    success INTEGER NOT NULL,
                    error_message TEXT,
                    metadata TEXT
                )
            """
            )

            # Throughput measurements table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS throughput_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    items_processed INTEGER NOT NULL,
                    window_seconds INTEGER NOT NULL,
                    throughput_per_second REAL NOT NULL,
                    errors INTEGER NOT NULL
                )
            """
            )

            # SLO violations table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS slo_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    slo_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    target_value REAL NOT NULL,
                    compliance_percentage REAL NOT NULL
                )
            """
            )

            conn.commit()
            conn.close()
            logger.info("Pipeline monitoring database initialized")
        except Exception as e:
            logger.error("Failed to initialize pipeline monitoring database: {e}")

    def start_monitoring(self):
        """Start background monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Pipeline monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Pipeline monitoring stopped")

    def _monitoring_loop(self):
        """Background monitoring loop"""
        check_interval = self.config.get("monitoring", {}).get(
            "check_interval_seconds", 30
        )

        while self.monitoring_active:
            try:
                # Check SLOs
                slo_statuses = self.slo_monitor.check_slos(self.performance_collector)

                # Store metrics
                self._store_current_metrics()

                # Send alerts for violations
                violations = [
                    s
                    for s in slo_statuses
                    if s.status in [SLOStatus.WARNING, SLOStatus.CRITICAL]
                ]
                if violations:
                    self._send_slo_alerts(violations)

                time.sleep(check_interval)

            except Exception as e:
                logger.error("Error in monitoring loop: {e}")
                time.sleep(check_interval)

    def _store_current_metrics(self):
        """Store current metrics to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Store recent latency measurements
            for stage in PipelineStage:
                measurements = list(self.performance_collector.measurements[stage])
                for measurement in measurements[-100:]:  # Store last 100 measurements
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO latency_measurements
                        (stage, start_time, end_time, duration_ms, success, error_message, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            measurement.stage.value,
                            measurement.start_time.isoformat(),
                            measurement.end_time.isoformat(),
                            measurement.duration_ms,
                            int(measurement.success),
                            measurement.error_message,
                            (
                                json.dumps(measurement.metadata)
                                if measurement.metadata
                                else None
                            ),
                        ),
                    )

            # Store recent throughput measurements
            for stage in PipelineStage:
                measurements = list(self.performance_collector.throughput_data[stage])
                for measurement in measurements[-50:]:  # Store last 50 measurements
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO throughput_measurements
                        (stage, timestamp, items_processed, window_seconds, throughput_per_second, errors)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            measurement.stage.value,
                            measurement.timestamp.isoformat(),
                            measurement.items_processed,
                            measurement.window_seconds,
                            measurement.throughput_per_second,
                            measurement.errors,
                        ),
                    )

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to store metrics: {e}")

    def _send_slo_alerts(self, violations: list[SLOStatus]):
        """Send alerts for SLO violations"""
        if not self.config.get("alerting", {}).get("enabled"):
            return

        try:
            alert_message = self._format_slo_alert(violations)

            # Send webhook alert
            webhook_url = self.config.get("alerting", {}).get("webhook_url")
            if webhook_url:
                self._send_webhook_alert(webhook_url, alert_message)

            # Log violations
            for violation in violations:
                logger.warning(
                    "SLO violation: {violation.slo_name} - {violation.status.value}"
                )

        except Exception as e:
            logger.error("Failed to send SLO alerts: {e}")

    def _format_slo_alert(self, violations: list[SLOStatus]) -> str:
        """Format SLO violations into alert message"""
        lines = [
            "🚨 SLO Violations Detected",
            "Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "Violations: {len(violations)}",
            "",
        ]

        for violation in violations:
            lines.extend(
                [
                    "• {violation.slo_name}:",
                    "  Status: {violation.status.value.upper()}",
                    "  Current: {violation.current_value:.2f}",
                    "  Target: {violation.target_value:.2f}",
                    "  Compliance: {violation.compliance_percentage:.1f}%",
                    "",
                ]
            )

        return "\n".join(lines)

    def _send_webhook_alert(self, webhook_url: str, message: str):
        """Send webhook alert"""
        try:
            import requests

            payload = {
                "text": message,
                "timestamp": datetime.now().isoformat(),
                "alert_type": "slo_violation",
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.error("Failed to send webhook alert: {e}")

    def get_pipeline_health_summary(self) -> dict[str, Any]:
        """Get comprehensive pipeline health summary"""
        slo_statuses = self.slo_monitor.check_slos(self.performance_collector)

        # Calculate overall health
        healthy_slos = len([s for s in slo_statuses if s.status == SLOStatus.HEALTHY])
        total_slos = len(slo_statuses)
        overall_health = (healthy_slos / total_slos * 100) if total_slos > 0 else 100.0

        # Get stage-wise performance
        stage_performance = {}
        for stage in PipelineStage:
            latency_stats = self.performance_collector.get_latency_stats(stage, 60)
            throughput_stats = self.performance_collector.get_throughput_stats(
                stage, 60
            )

            stage_performance[stage.value] = {
                "latency": latency_stats,
                "throughput": throughput_stats,
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health_percentage": overall_health,
            "slo_summary": {
                "total": total_slos,
                "healthy": healthy_slos,
                "warning": len(
                    [s for s in slo_statuses if s.status == SLOStatus.WARNING]
                ),
                "critical": len(
                    [s for s in slo_statuses if s.status == SLOStatus.CRITICAL]
                ),
            },
            "slo_details": [asdict(status) for status in slo_statuses],
            "stage_performance": stage_performance,
        }


# Convenience functions for easy integration
_global_monitor = None


def init_pipeline_monitoring(config_path: Optional[str] = None):
    """Initialize global pipeline monitoring"""
    global _global_monitor
    _global_monitor = PipelineMonitor(
        config_path or "configs/pipeline_monitoring_config.json"
    )
    _global_monitor.start_monitoring()


def trace_pipeline_stage(
    stage: PipelineStage,
    trace_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
):
    """Trace a pipeline stage execution"""
    if _global_monitor is None:
        init_pipeline_monitoring()

    return _global_monitor.performance_collector.trace_stage(stage, trace_id, metadata)


def record_throughput(
    stage: PipelineStage,
    items_processed: int,
    window_seconds: int = 60,
    errors: int = 0,
):
    """Record throughput for a pipeline stage"""
    if _global_monitor is None:
        init_pipeline_monitoring()

    _global_monitor.performance_collector.record_throughput(
        stage, items_processed, window_seconds, errors
    )


def get_health_summary() -> dict[str, Any]:
    """Get current pipeline health summary"""
    if _global_monitor is None:
        init_pipeline_monitoring()

    return _global_monitor.get_pipeline_health_summary()


if __name__ == "__main__":
    # Example usage
    monitor = PipelineMonitor()
    monitor.start_monitoring()

    # Simulate some pipeline activity
    with monitor.performance_collector.trace_stage(
        PipelineStage.SIGNAL_GENERATION
    ) as trace_id:
        time.sleep(0.5)  # Simulate signal generation

    with monitor.performance_collector.trace_stage(
        PipelineStage.ORDER_EXECUTION
    ) as trace_id:
        time.sleep(1.0)  # Simulate order execution

    # Record throughput
    monitor.performance_collector.record_throughput(
        PipelineStage.DATA_PROCESSING, 150, 60
    )

    # Get health summary
    health = monitor.get_pipeline_health_summary()
    print("Overall health: {health['overall_health_percentage']:.1f}%")
    print("SLO status: {health['slo_summary']}")

    time.sleep(2)
    monitor.stop_monitoring()
