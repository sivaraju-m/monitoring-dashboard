# 🖥️ Monitoring Dashboard - Real-time Trading System Monitor

## 📋 Overview

The Monitoring Dashboard provides comprehensive real-time monitoring, alerting, and reporting capabilities for the AI Trading Machine ecosystem. It offers a centralized view of all system components including strategy performance, trading execution, data pipeline health, and system metrics.

## 🏗️ Architecture

### Core Components

1. **Dashboard Server** (`bin/dashboard_server.py`)
   - FastAPI-based web server with real-time WebSocket updates
   - Responsive HTML5 dashboard with Bootstrap styling
   - Real-time charts using Chart.js
   - RESTful API endpoints for data access

2. **Metrics Collector** (`src/monitoring_dashboard/monitoring/metrics_collector.py`)
   - Collects performance metrics from all trading system components
   - SQLite database for local metrics storage
   - HTTP API integration with other services
   - System health monitoring with psutil

3. **Alert Manager** (`src/monitoring_dashboard/alerts/alert_manager.py`)
   - Rule-based alerting system with configurable thresholds
   - Email and Slack notification support
   - Alert deduplication and escalation
   - SQLite database for alert history

4. **Performance Reporter** (`src/monitoring_dashboard/reports/performance_reporter.py`)
   - Daily and weekly performance reports
   - Risk metrics calculation
   - Strategy performance attribution
   - Automated report generation

## 🚀 Quick Start

### Installation

```bash
cd /Users/sivarajumalladi/Documents/GitHub/monitoring-dashboard

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Configuration

1. **Dashboard Configuration**: `config/dashboard_config.yaml`
   - Server settings (host, port, CORS)
   - Metrics collection intervals
   - Database paths
   - Security settings

2. **Alert Rules**: `config/alert_rules.yaml`
   - Alert conditions and thresholds
   - Notification settings
   - Email and Slack configuration

### Starting the Dashboard

```bash
# Start the main dashboard server
python bin/dashboard_server.py

# Start with custom settings
python bin/dashboard_server.py --host 0.0.0.0 --port 8000 --debug

# Access dashboard at: http://localhost:8000
```

### Running Alert Manager

```bash
# Start alert manager service
python bin/alert_manager.py

# Run in debug mode
python bin/alert_manager.py --debug

# Create test alert
python bin/alert_manager.py --test
```

### Generating Reports

```bash
# Generate daily report
python bin/report_generator.py --type daily

# Generate weekly report
python bin/report_generator.py --type weekly

# Save report to file
python bin/report_generator.py --type daily --output reports/daily_report.json

# Generate custom date range report
python bin/report_generator.py --type custom --start-date 2025-01-01 --end-date 2025-01-07
```

## 📊 Features

### Real-time Dashboard

**System Status Panel**
- System health indicator (Online/Offline)
- Active strategies count
- Daily P&L summary
- Active alerts count

**Performance Charts**
- Real-time portfolio value chart
- Strategy allocation pie chart
- Historical performance trends
- Interactive data visualization

**Strategy Performance Table**
- Individual strategy P&L
- Signal generation counts
- Strategy status monitoring
- Performance rankings

**Recent Alerts Panel**
- Color-coded alert severity
- Real-time alert updates
- Alert acknowledgment
- Source tracking

### Alert System

**Pre-configured Alert Rules**
- High daily loss (>₹10,000)
- Extreme daily loss (>₹25,000)
- Low win rate (<40%)
- Strategy underperformance
- System health issues
- Data quality problems

**Alert Notifications**
- Email notifications with SMTP
- Slack webhook integration
- Alert escalation rules
- Duplicate suppression

### Performance Reporting

**Daily Reports**
- Portfolio performance summary
- Strategy breakdown
- Risk metrics
- System health status
- Actionable recommendations

**Weekly Reports**
- Weekly return analysis
- Risk-adjusted performance
- Strategy correlation analysis
- Performance attribution
- Comprehensive risk metrics

## 📁 Directory Structure

```
monitoring-dashboard/
├── bin/                          # Executable scripts
│   ├── dashboard_server.py       # Main dashboard server
│   ├── alert_manager.py          # Alert management service
│   └── report_generator.py       # Report generation tool
├── config/                       # Configuration files
│   ├── dashboard_config.yaml     # Dashboard settings
│   └── alert_rules.yaml          # Alert rules and notifications
├── src/monitoring_dashboard/     # Source code
│   ├── __init__.py
│   ├── monitoring/               # Metrics collection
│   │   ├── __init__.py
│   │   └── metrics_collector.py
│   ├── dashboards/               # Dashboard components
│   │   ├── __init__.py
│   │   └── strategy_dashboard.py
│   ├── alerts/                   # Alert management
│   │   ├── __init__.py
│   │   └── alert_manager.py
│   ├── reports/                  # Performance reporting
│   │   ├── __init__.py
│   │   └── performance_reporter.py
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── logger.py
│       └── config_loader.py
├── data/                         # Data storage
│   ├── metrics.db               # Metrics database
│   ├── alerts.db                # Alerts database
│   └── dashboard.db             # Dashboard data
├── reports/                      # Generated reports
│   ├── daily_report_*.json
│   └── weekly_report_*.json
└── tests/                        # Test files
    ├── unit/
    ├── integration/
    └── e2e/
```

## 🔧 Configuration

### Dashboard Settings

```yaml
# Dashboard Configuration Example
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

metrics:
  update_interval: 30  # seconds
  history_days: 30
  max_data_points: 1000

alerts:
  max_alerts: 100
  retention_days: 7
  check_interval: 60
```

### Alert Rules

```yaml
# Alert Rules Example
rules:
  - name: "High Daily Loss"
    condition: "daily_pnl < -10000"
    severity: "high"
    enabled: true
    cooldown: 3600

notifications:
  email:
    enabled: true
    recipients: ["trader@example.com"]
  slack:
    enabled: true
    webhook_url: "your_slack_webhook_url"
```

## 🔌 API Integration

### Metrics Collection Endpoints

The dashboard collects metrics from:
- **Strategy Engine**: `http://localhost:8001/api/metrics`
- **Trading Engine**: `http://localhost:8002/api/metrics`
- **Data Pipeline**: `http://localhost:8003/api/metrics`

### Dashboard API Endpoints

- `GET /` - Main dashboard interface
- `GET /api/dashboard-data` - Current dashboard data
- `GET /api/health` - Health check endpoint
- `WebSocket /ws` - Real-time updates

## 📈 Metrics Tracked

### Performance Metrics
- Daily/Weekly P&L
- Total trades and signals
- Win rate and average trade
- Sharpe ratio and volatility
- Maximum drawdown

### System Metrics
- CPU and memory usage
- Disk space utilization
- Data pipeline health
- Strategy execution status
- Alert counts

### Risk Metrics
- Value at Risk (VaR)
- Expected Shortfall
- Beta and Alpha
- Strategy correlation
- Position concentration

## 🚨 Alert Management

### Alert Severities
- **Low**: Informational alerts
- **Medium**: Performance warnings
- **High**: System issues requiring attention
- **Critical**: Immediate action required

### Alert Types
- Performance alerts (P&L thresholds)
- System health alerts (CPU, memory, disk)
- Data quality alerts (missing/stale data)
- Trading alerts (execution issues)
- Strategy alerts (underperformance)

## 📊 Reporting Features

### Automated Reports
- Daily performance summaries
- Weekly analytical reports
- Monthly strategy reviews
- Quarterly risk assessments

### Report Content
- Executive summary
- Detailed performance metrics
- Strategy attribution analysis
- Risk assessment
- Actionable recommendations

## 🔐 Security Features

### Access Control
- Optional API key authentication
- Rate limiting protection
- CORS configuration
- SSL/HTTPS support

### Data Protection
- Local SQLite databases
- Encrypted sensitive data
- Audit logging
- Backup and recovery

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=monitoring_dashboard

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Test Coverage
- Unit tests for all components
- Integration tests for API endpoints
- End-to-end dashboard testing
- Performance and load testing

## 🚀 Deployment

### Development Deployment

```bash
# Start dashboard server
python bin/dashboard_server.py --debug

# Start alert manager
python bin/alert_manager.py --debug
```

### Production Deployment

```bash
# Use production configuration
export MONITORING_CONFIG=/path/to/production/config.yaml

# Start with gunicorn (recommended for production)
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 dashboard_server:app

# Or use Docker
docker build -t monitoring-dashboard .
docker run -p 8000:8000 monitoring-dashboard
```

### Environment Variables

- `MONITORING_CONFIG`: Path to configuration file
- `MONITORING_DEBUG`: Enable debug mode
- `MONITORING_LOG_LEVEL`: Logging level
- `MONITORING_DATA_DIR`: Data directory path

## 🔄 Integration with Other Services

### Strategy Engine Integration
- Receives strategy performance metrics
- Monitors signal generation
- Tracks strategy execution status

### Trading Engine Integration  
- Collects trading performance data
- Monitors order execution
- Tracks position management

### Data Pipeline Integration
- Monitors data quality
- Tracks data freshness
- Alerts on pipeline failures

## 📝 Troubleshooting

### Common Issues

**Dashboard not loading**
```bash
# Check if server is running
curl http://localhost:8000/api/health

# Check logs
tail -f logs/dashboard.log
```

**Metrics not updating**
```bash
# Verify data sources are accessible
python -c "import requests; print(requests.get('http://localhost:8001/api/metrics').status_code)"

# Check metrics collector
python bin/alert_manager.py --test
```

**Alerts not firing**
```bash
# Test alert system
python bin/alert_manager.py --test

# Check alert configuration
python -c "from monitoring_dashboard.utils.config_loader import ConfigLoader; print(ConfigLoader().load_alert_config())"
```

### Performance Optimization

- Increase metrics collection interval for better performance
- Use database indexing for faster queries
- Enable data compression for storage efficiency
- Implement caching for frequently accessed data

## 🔮 Future Enhancements

### Planned Features
- Machine learning-based anomaly detection
- Advanced data visualization with D3.js
- Mobile-responsive dashboard interface
- Integration with cloud monitoring services
- Multi-tenant support for multiple portfolios

### Plugin Architecture
- Custom alert rule plugins
- Third-party notification integrations
- Custom report generators
- External data source connectors

## 📞 Support and Maintenance

### Monitoring Health
- Dashboard self-monitoring
- Automated health checks
- Performance metrics tracking
- Resource utilization monitoring

### Maintenance Tasks
- Database cleanup and optimization
- Log rotation and archival
- Configuration updates
- Security patches and updates

---

**Monitoring Dashboard Status**: ✅ **FULLY OPERATIONAL**
- Real-time monitoring with WebSocket updates
- Comprehensive alerting with email/Slack notifications
- Automated daily and weekly reporting
- Production-ready deployment with Docker support
- Complete test coverage and documentation
