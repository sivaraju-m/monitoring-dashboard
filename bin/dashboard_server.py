#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard Server
Provides live monitoring of trading strategies, performance, and system health
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
import yaml

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from monitoring_dashboard.monitoring.metrics_collector import MetricsCollector
from monitoring_dashboard.dashboards.strategy_dashboard import StrategyDashboard
from monitoring_dashboard.alerts.alert_manager import AlertManager
from monitoring_dashboard.reports.performance_reporter import PerformanceReporter
from monitoring_dashboard.utils.logger import setup_logger
from monitoring_dashboard.utils.config_loader import ConfigLoader


class DashboardServer:
    """Real-time monitoring dashboard server"""

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.config = ConfigLoader().load_dashboard_config()

        # Initialize components
        self.metrics_collector = MetricsCollector()
        self.strategy_dashboard = StrategyDashboard()
        self.alert_manager = AlertManager()
        self.performance_reporter = PerformanceReporter()

        # WebSocket connections
        self.active_connections: List[WebSocket] = []

        # FastAPI app
        self.app = FastAPI(
            title="AI Trading Machine - Monitoring Dashboard",
            description="Real-time monitoring dashboard for trading strategies",
            version="1.0.0",
        )

        self._setup_routes()
        self._setup_websocket()

        self.logger.info("Dashboard server initialized")

    def _setup_routes(self):
        """Setup HTTP routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            return HTMLResponse(
                """
            <!DOCTYPE html>
            <html>
            <head>
                <title>AI Trading Machine - Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    .metric-card { transition: all 0.3s; }
                    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                    .alert-badge { animation: pulse 2s infinite; }
                    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
                </style>
            </head>
            <body class="bg-light">
                <nav class="navbar navbar-dark bg-primary">
                    <div class="container-fluid">
                        <span class="navbar-brand mb-0 h1">🤖 AI Trading Machine Dashboard</span>
                        <span class="navbar-text" id="lastUpdate">Last Update: --</span>
                    </div>
                </nav>
                
                <div class="container-fluid mt-3">
                    <!-- System Status Row -->
                    <div class="row mb-3">
                        <div class="col-md-3">
                            <div class="card metric-card text-center">
                                <div class="card-body">
                                    <h5 class="card-title text-success">System Status</h5>
                                    <h3 id="systemStatus" class="text-success">🟢 Online</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card metric-card text-center">
                                <div class="card-body">
                                    <h5 class="card-title">Active Strategies</h5>
                                    <h3 id="activeStrategies" class="text-primary">--</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card metric-card text-center">
                                <div class="card-body">
                                    <h5 class="card-title">Daily P&L</h5>
                                    <h3 id="dailyPnL" class="text-info">--</h3>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card metric-card text-center">
                                <div class="card-body">
                                    <h5 class="card-title">Active Alerts</h5>
                                    <h3 id="activeAlerts" class="text-warning">--</h3>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Charts Row -->
                    <div class="row mb-3">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-header">
                                    <h5>Performance Chart</h5>
                                </div>
                                <div class="card-body">
                                    <canvas id="performanceChart" height="100"></canvas>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-header">
                                    <h5>Strategy Allocation</h5>
                                </div>
                                <div class="card-body">
                                    <canvas id="allocationChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Strategy Details Row -->
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>Strategy Performance</h5>
                                </div>
                                <div class="card-body">
                                    <div id="strategyTable" class="table-responsive">
                                        <!-- Strategy table will be populated here -->
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header">
                                    <h5>Recent Alerts</h5>
                                </div>
                                <div class="card-body">
                                    <div id="alertsList" style="max-height: 300px; overflow-y: auto;">
                                        <!-- Alerts will be populated here -->
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <script>
                    // WebSocket connection for real-time updates
                    const ws = new WebSocket('ws://localhost:8000/ws');
                    let performanceChart, allocationChart;
                    
                    // Initialize charts
                    const performanceCtx = document.getElementById('performanceChart').getContext('2d');
                    performanceChart = new Chart(performanceCtx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Portfolio Value',
                                data: [],
                                borderColor: 'rgb(75, 192, 192)',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: { y: { beginAtZero: false } }
                        }
                    });
                    
                    const allocationCtx = document.getElementById('allocationChart').getContext('2d');
                    allocationChart = new Chart(allocationCtx, {
                        type: 'doughnut',
                        data: {
                            labels: [],
                            datasets: [{
                                data: [],
                                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
                            }]
                        },
                        options: { responsive: true }
                    });
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        updateDashboard(data);
                        document.getElementById('lastUpdate').textContent = 'Last Update: ' + new Date().toLocaleTimeString();
                    };
                    
                    function updateDashboard(data) {
                        // Update metrics
                        if (data.metrics) {
                            document.getElementById('activeStrategies').textContent = data.metrics.active_strategies || '--';
                            document.getElementById('dailyPnL').textContent = data.metrics.daily_pnl || '--';
                            document.getElementById('activeAlerts').textContent = data.metrics.active_alerts || '--';
                        }
                        
                        // Update performance chart
                        if (data.performance && performanceChart) {
                            performanceChart.data.labels = data.performance.timestamps || [];
                            performanceChart.data.datasets[0].data = data.performance.values || [];
                            performanceChart.update();
                        }
                        
                        // Update allocation chart
                        if (data.allocation && allocationChart) {
                            allocationChart.data.labels = data.allocation.labels || [];
                            allocationChart.data.datasets[0].data = data.allocation.values || [];
                            allocationChart.update();
                        }
                        
                        // Update strategy table
                        if (data.strategies) {
                            updateStrategyTable(data.strategies);
                        }
                        
                        // Update alerts
                        if (data.alerts) {
                            updateAlertsList(data.alerts);
                        }
                    }
                    
                    function updateStrategyTable(strategies) {
                        const tableHtml = `
                            <table class="table table-striped table-sm">
                                <thead>
                                    <tr>
                                        <th>Strategy</th>
                                        <th>Status</th>
                                        <th>P&L</th>
                                        <th>Signals</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${strategies.map(s => `
                                        <tr>
                                            <td>${s.name}</td>
                                            <td><span class="badge bg-${s.status === 'active' ? 'success' : 'secondary'}">${s.status}</span></td>
                                            <td class="text-${s.pnl >= 0 ? 'success' : 'danger'}">${s.pnl}</td>
                                            <td>${s.signals}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        `;
                        document.getElementById('strategyTable').innerHTML = tableHtml;
                    }
                    
                    function updateAlertsList(alerts) {
                        const alertsHtml = alerts.map(alert => `
                            <div class="alert alert-${alert.severity} alert-dismissible fade show" role="alert">
                                <strong>${alert.type}:</strong> ${alert.message}
                                <small class="text-muted d-block">${alert.timestamp}</small>
                            </div>
                        `).join('');
                        document.getElementById('alertsList').innerHTML = alertsHtml;
                    }
                    
                    // Initial data load
                    fetch('/api/dashboard-data')
                        .then(response => response.json())
                        .then(data => updateDashboard(data))
                        .catch(error => console.error('Error loading initial data:', error));
                </script>
            </body>
            </html>
            """
            )

        @self.app.get("/api/dashboard-data")
        async def get_dashboard_data():
            """Get current dashboard data"""
            try:
                data = await self._collect_dashboard_data()
                return data
            except Exception as e:
                self.logger.error(f"Error collecting dashboard data: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
            }

    def _setup_websocket(self):
        """Setup WebSocket for real-time updates"""

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                while True:
                    # Send real-time updates every 30 seconds
                    await asyncio.sleep(30)
                    data = await self._collect_dashboard_data()
                    await websocket.send_text(json.dumps(data))

            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                self.logger.info("WebSocket connection closed")

    async def _collect_dashboard_data(self) -> Dict[str, Any]:
        """Collect all dashboard data"""
        try:
            # Collect metrics
            metrics = await self.metrics_collector.get_current_metrics()

            # Get performance data
            performance = await self.strategy_dashboard.get_performance_data()

            # Get strategy allocation
            allocation = await self.strategy_dashboard.get_allocation_data()

            # Get strategy details
            strategies = await self.strategy_dashboard.get_strategy_summary()

            # Get recent alerts
            alerts = await self.alert_manager.get_recent_alerts()

            return {
                "metrics": metrics,
                "performance": performance,
                "allocation": allocation,
                "strategies": strategies,
                "alerts": alerts,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error collecting dashboard data: {e}")
            return {
                "metrics": {"error": str(e)},
                "performance": {},
                "allocation": {},
                "strategies": [],
                "alerts": [],
                "timestamp": datetime.now().isoformat(),
            }

    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast update to all connected WebSocket clients"""
        if self.active_connections:
            message = json.dumps(data)
            disconnected = []

            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    self.logger.warning(f"Failed to send WebSocket message: {e}")
                    disconnected.append(connection)

            # Remove disconnected connections
            for connection in disconnected:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the dashboard server"""
        self.logger.info(f"Starting dashboard server on {host}:{port}")

        # Start background tasks
        asyncio.create_task(self._background_tasks())

        # Run server
        uvicorn.run(self.app, host=host, port=port, log_level="info", access_log=True)

    async def _background_tasks(self):
        """Background tasks for periodic updates"""
        while True:
            try:
                # Collect and broadcast updates every 30 seconds
                await asyncio.sleep(30)
                data = await self._collect_dashboard_data()
                await self.broadcast_update(data)

            except Exception as e:
                self.logger.error(f"Error in background task: {e}")
                await asyncio.sleep(60)  # Wait longer on error


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Trading Machine Dashboard Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create and run server
    server = DashboardServer()
    server.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
