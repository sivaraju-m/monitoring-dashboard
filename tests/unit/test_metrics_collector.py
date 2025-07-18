import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from monitoring_dashboard.dashboards.metrics_collector import MetricsCollector

@pytest.fixture
def metrics_collector():
    """Create a metrics collector for testing"""
    return MetricsCollector()

def test_metrics_collector_init(metrics_collector):
    """Test MetricsCollector initialization"""
    assert metrics_collector.metrics_buffer == []
    assert "data_fetch_latency_ms" in metrics_collector.sla_thresholds
    assert "api_response_latency_ms" in metrics_collector.sla_thresholds
    assert "strategy_execution_ms" in metrics_collector.sla_thresholds

@pytest.mark.asyncio
async def test_record_data_fetch_metrics(metrics_collector):
    """Test recording data fetch metrics"""
    # Create test metrics
    test_metrics = {
        "source": "yahoo",
        "symbol": "AAPL",
        "latency_ms": 50,
        "success": True,
        "data_points": 100
    }
    
    # Record metrics
    await metrics_collector.record_data_fetch_metrics(test_metrics)
    
    # Verify metrics were recorded
    assert len(metrics_collector.metrics_buffer) == 1
    recorded_metrics = metrics_collector.metrics_buffer[0]
    
    # Check that all original metrics are present
    for key, value in test_metrics.items():
        assert recorded_metrics[key] == value
    
    # Check that additional metadata was added
    assert "recorded_at" in recorded_metrics
    assert "metric_type" in recorded_metrics
    assert recorded_metrics["metric_type"] == "data_fetch"
    
    # Test SLA breach detection
    breach_metrics = {
        "source": "yahoo",
        "symbol": "MSFT",
        "latency_ms": 150,  # Above threshold of 100ms
        "success": True,
        "data_points": 100
    }
    
    # Record metrics that breach SLA
    await metrics_collector.record_data_fetch_metrics(breach_metrics)
    
    # Verify second metrics were recorded
    assert len(metrics_collector.metrics_buffer) == 2
