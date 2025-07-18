#!/usr/bin/env python3
"""
Real-time Trading Dashboard
==========================

Web-based real-time monitoring dashboard for the AI Trading Machine.

Features:
- Live trading signals display
- Real-time portfolio performance
- Interactive charts and metrics
- Risk monitoring
- System status monitoring
- Mobile-responsive design

Usage:
    python realtime_dashboard.py

Then open: http://localhost:8050

Author: AI Trading Machine
Licensed by SJ Trading
"""

import json
import os
import sys
import threading
import time
from datetime import datetime

import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

try:
    import dash
    import plotly.graph_objects as go
    from dash import Input, Output, dcc, html

    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
    print("⚠️ Dash not available. Install with: pip install dash plotly")


class TradingDashboard:
    """Real-time trading dashboard."""

    def __init__(self, port: int = 8050):
        """Initialize the dashboard."""
        if not DASH_AVAILABLE:
            raise ImportError("Dash and Plotly are required for the dashboard")

        self.port = port
        self.data_dir = os.path.join(project_root, "automated_data")
        self.app = dash.Dash(__name__)
        self.app.title = "AI Trading Machine - Live Dashboard"

        # Data storage
        self.latest_signals = []
        self.latest_trades = []
        self.performance_data = {}

        # Setup layout and callbacks
        self.setup_layout()
        self.setup_callbacks()

        # Start data refresh thread
        self.start_data_refresh()

    def setup_layout(self):
        """Setup the dashboard layout."""
        self.app.layout = html.Div(
            [
                # Header
                html.Div(
                    [
                        html.H1("🤖 AI Trading Machine", className="header-title"),
                        html.H3(
                            "Real-time Trading Dashboard", className="header-subtitle"
                        ),
                        html.Div(
                            [
                                html.Span("🟢 LIVE", className="status-live"),
                                html.Span(
                                    id="last-update",
                                    children="",
                                    className="last-update",
                                ),
                            ],
                            className="header-status",
                        ),
                    ],
                    className="header",
                ),
                # Auto refresh component
                dcc.Interval(
                    id="interval-component",
                    interval=5 * 1000,  # Update every 5 seconds
                    n_intervals=0,
                ),
                # Main content
                html.Div(
                    [
                        # Top row - Key metrics
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H4(
                                            "Portfolio Value", className="metric-title"
                                        ),
                                        html.H2(
                                            id="portfolio-value",
                                            children="₹0",
                                            className="metric-value positive",
                                        ),
                                    ],
                                    className="metric-card",
                                ),
                                html.Div(
                                    [
                                        html.H4(
                                            "Today's P&L", className="metric-title"
                                        ),
                                        html.H2(
                                            id="daily-pnl",
                                            children="₹0",
                                            className="metric-value",
                                        ),
                                    ],
                                    className="metric-card",
                                ),
                                html.Div(
                                    [
                                        html.H4("Win Rate", className="metric-title"),
                                        html.H2(
                                            id="win-rate",
                                            children="0%",
                                            className="metric-value",
                                        ),
                                    ],
                                    className="metric-card",
                                ),
                                html.Div(
                                    [
                                        html.H4(
                                            "Active Signals", className="metric-title"
                                        ),
                                        html.H2(
                                            id="active-signals",
                                            children="0",
                                            className="metric-value",
                                        ),
                                    ],
                                    className="metric-card",
                                ),
                            ],
                            className="metrics-row",
                        ),
                        # Second row - Charts
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H4("📈 Equity Curve"),
                                        dcc.Graph(id="equity-chart"),
                                    ],
                                    className="chart-card chart-hal",
                                ),
                                html.Div(
                                    [
                                        html.H4("📊 Signal Distribution"),
                                        dcc.Graph(id="signal-chart"),
                                    ],
                                    className="chart-card chart-hal",
                                ),
                            ],
                            className="charts-row",
                        ),
                        # Third row - Recent activity
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H4("🔔 Latest Signals"),
                                        html.Div(id="signals-table"),
                                    ],
                                    className="table-card table-hal",
                                ),
                                html.Div(
                                    [
                                        html.H4("💼 Recent Trades"),
                                        html.Div(id="trades-table"),
                                    ],
                                    className="table-card table-hal",
                                ),
                            ],
                            className="tables-row",
                        ),
                        # Fourth row - System status
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H4("⚙️ System Status"),
                                        html.Div(id="system-status"),
                                    ],
                                    className="status-card",
                                )
                            ],
                            className="status-row",
                        ),
                    ],
                    className="main-content",
                ),
            ],
            className="dashboard-container",
        )

        # Add CSS styling
        self.app.index_string = """
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    body { margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
                    .dashboard-container { padding: 20px; max-width: 1400px; margin: 0 auto; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
                    .header-title { margin: 0; font-size: 2.5em; }
                    .header-subtitle { margin: 5px 0 0 0; opacity: 0.9; }
                    .header-status { display: flex; justify-content: space-between; align-items: center; margin-top: 15px; }
                    .status-live { background: #4CAF50; padding: 5px 10px; border-radius: 15px; font-weight: bold; }
                    .last-update { opacity: 0.8; }
                    .metrics-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }
                    .metric-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
                    .metric-title { margin: 0; color: #666; font-size: 0.9em; }
                    .metric-value { margin: 10px 0 0 0; font-size: 2em; font-weight: bold; }
                    .metric-value.positive { color: #4CAF50; }
                    .metric-value.negative { color: #f44336; }
                    .charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
                    .chart-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .tables-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
                    .table-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .status-row { margin-bottom: 20px; }
                    .status-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .signal-item { padding: 10px; border-left: 4px solid #2196F3; margin: 5px 0; background: #f8f9fa; border-radius: 5px; }
                    .trade-item { padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px; }
                    .trade-profit { border-left: 4px solid #4CAF50; }
                    .trade-loss { border-left: 4px solid #f44336; }
                    .status-item { display: flex; justify-content: space-between; padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px; }
                    @media (max-width: 768px) {
                        .metrics-row { grid-template-columns: repeat(2, 1fr); }
                        .charts-row, .tables-row { grid-template-columns: 1fr; }
                    }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        """

    def setup_callbacks(self):
        """Setup dashboard callbacks."""

        @self.app.callback(
            [
                Output("portfolio-value", "children"),
                Output("daily-pnl", "children"),
                Output("daily-pnl", "className"),
                Output("win-rate", "children"),
                Output("active-signals", "children"),
                Output("last-update", "children"),
                Output("equity-chart", "figure"),
                Output("signal-chart", "figure"),
                Output("signals-table", "children"),
                Output("trades-table", "children"),
                Output("system-status", "children"),
            ],
            [Input("interval-component", "n_intervals")],
        )
        def update_dashboard(n):
            """Update all dashboard components."""
            # Refresh data
            self.refresh_data()

            # Calculate metrics
            portfolio_value = "₹1,00,000"  # Default or calculated value
            daily_pnl = 0
            win_rate = 0
            active_signals_count = len(self.latest_signals)

            if self.latest_trades:
                daily_pnl = sum(
                    trade.get("pnl", 0)
                    for trade in self.latest_trades
                    if self.is_today(trade.get("entry_time", ""))
                )
                completed_trades = [
                    t
                    for t in self.latest_trades
                    if t.get("status") in ["FILLED", "TARGET_HIT", "STOP_HIT"]
                ]
                if completed_trades:
                    wins = sum(1 for t in completed_trades if t.get("pnl", 0) > 0)
                    win_rate = (wins / len(completed_trades)) * 100

            # Format values
            daily_pnl_text = "₹{daily_pnl:,.2f}"
            daily_pnl_class = (
                "metric-value positive" if daily_pnl >= 0 else "metric-value negative"
            )
            win_rate_text = "{win_rate:.1f}%"
            active_signals_text = str(active_signals_count)
            last_update = "Last updated: {datetime.now().strftime('%H:%M:%S')}"

            # Create charts
            equity_chart = self.create_equity_chart()
            signal_chart = self.create_signal_chart()

            # Create tables
            signals_table = self.create_signals_table()
            trades_table = self.create_trades_table()

            # System status
            system_status = self.create_system_status()

            return (
                portfolio_value,
                daily_pnl_text,
                daily_pnl_class,
                win_rate_text,
                active_signals_text,
                last_update,
                equity_chart,
                signal_chart,
                signals_table,
                trades_table,
                system_status,
            )

    def refresh_data(self):
        """Refresh data from files."""
        try:
            # Load signals
            signals_dir = os.path.join(self.data_dir, "signals")
            if os.path.exists(signals_dir):
                self.latest_signals = []
                for file in sorted(os.listdir(signals_dir))[-5:]:  # Last 5 files
                    if file.endswith(".json"):
                        with open(os.path.join(signals_dir, file)) as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                self.latest_signals.extend(
                                    data[-10:]
                                )  # Last 10 signals
                            else:
                                self.latest_signals.append(data)

            # Load trades
            trades_dir = os.path.join(self.data_dir, "trades")
            if os.path.exists(trades_dir):
                self.latest_trades = []
                for file in sorted(os.listdir(trades_dir))[-5:]:  # Last 5 files
                    if file.endswith(".json"):
                        with open(os.path.join(trades_dir, file)) as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                self.latest_trades.extend(data[-20:])  # Last 20 trades
                            else:
                                self.latest_trades.append(data)

        except Exception as e:
            print("Error refreshing data: {e}")

    def is_today(self, timestamp_str: str) -> bool:
        """Check if timestamp is from today."""
        try:
            if not timestamp_str:
                return False
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", ""))
            return timestamp.date() == datetime.now().date()
        except Exception:
            return False

    def create_equity_chart(self) -> go.Figure:
        """Create equity curve chart."""
        fig = go.Figure()

        if self.latest_trades:
            completed_trades = [
                t
                for t in self.latest_trades
                if t.get("status") in ["FILLED", "TARGET_HIT", "STOP_HIT"]
            ]
            if completed_trades:
                pnl_values = [t.get("pnl", 0) for t in completed_trades]
                cumulative_pnl = [
                    sum(pnl_values[: i + 1]) for i in range(len(pnl_values))
                ]

                fig.add_trace(
                    go.Scatter(
                        x=list(range(1, len(cumulative_pnl) + 1)),
                        y=cumulative_pnl,
                        mode="lines+markers",
                        line=dict(color="#2196F3", width=3),
                        marker=dict(size=6),
                        name="Cumulative P&L",
                    )
                )

        fig.update_layout(
            height=300,
            margin=dict(line=0, r=0, t=0, b=0),
            xaxis_title="Trade Number",
            yaxis_title="Cumulative P&L (₹)",
            showlegend=False,
            plot_bgcolor="white",
            xaxis=dict(gridcolor="#f0f0f0"),
            yaxis=dict(gridcolor="#f0f0f0"),
        )

        return fig

    def create_signal_chart(self) -> go.Figure:
        """Create signal distribution chart."""
        fig = go.Figure()

        if self.latest_signals:
            actions = [s.get("action", "Unknown") for s in self.latest_signals]
            action_counts = pd.Series(actions).value_counts()

            colors = [
                (
                    "#4CAF50"
                    if action == "BUY"
                    else "#f44336" if action == "SELL" else "#FF9800"
                )
                for action in action_counts.index
            ]

            fig.add_trace(
                go.Bar(
                    x=action_counts.index,
                    y=action_counts.values,
                    marker_color=colors,
                    text=action_counts.values,
                    textposition="auto",
                )
            )

        fig.update_layout(
            height=300,
            margin=dict(line=0, r=0, t=0, b=0),
            xaxis_title="Signal Type",
            yaxis_title="Count",
            showlegend=False,
            plot_bgcolor="white",
            xaxis=dict(gridcolor="#f0f0f0"),
            yaxis=dict(gridcolor="#f0f0f0"),
        )

        return fig

    def create_signals_table(self) -> list[html.Div]:
        """Create signals table."""
        if not self.latest_signals:
            return [html.Div("No recent signals", className="text-muted")]

        signals_items = []
        for signal in self.latest_signals[-10:]:  # Last 10 signals
            timestamp = signal.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", ""))
                    time_str = dt.strftime("%H:%M:%S")
                except Exception:
                    time_str = timestamp
            else:
                time_str = "Unknown"

            symbol = signal.get("symbol", "Unknown")
            action = signal.get("action", "Unknown")
            confidence = signal.get("confidence", 0)

            signals_items.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Strong("{action} {symbol}"),
                                html.Span(
                                    " ({confidence:.1%})", style={"opacity": "0.7"}
                                ),
                            ]
                        ),
                        html.Small(time_str, style={"opacity": "0.6"}),
                    ],
                    className="signal-item",
                )
            )

        return signals_items

    def create_trades_table(self) -> list[html.Div]:
        """Create trades table."""
        if not self.latest_trades:
            return [html.Div("No recent trades", className="text-muted")]

        trade_items = []
        completed_trades = [
            t
            for t in self.latest_trades
            if t.get("status") in ["FILLED", "TARGET_HIT", "STOP_HIT"]
        ]

        for trade in completed_trades[-10:]:  # Last 10 trades
            symbol = trade.get("symbol", "Unknown")
            action = trade.get("action", "Unknown")
            pnl = trade.get("pnl", 0)
            status = trade.get("status", "Unknown")

            class_name = (
                "trade-item trade-profit" if pnl > 0 else "trade-item trade-loss"
            )

            trade_items.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Strong("{action} {symbol}"),
                                html.Span(" - {status}", style={"opacity": "0.7"}),
                            ]
                        ),
                        html.Div(
                            [
                                html.Strong(
                                    "₹{pnl:.2f}",
                                    style={
                                        "color": "#4CAF50" if pnl > 0 else "#f44336"
                                    },
                                )
                            ]
                        ),
                    ],
                    className=class_name,
                )
            )

        return trade_items

    def create_system_status(self) -> list[html.Div]:
        """Create system status display."""
        status_items = [
            html.Div(
                [
                    html.Span("Market Status"),
                    html.Span(
                        "🟢 Open" if self.is_market_hours() else "🔴 Closed",
                        style={"font-weight": "bold"},
                    ),
                ],
                className="status-item",
            ),
            html.Div(
                [
                    html.Span("Signal Generation"),
                    html.Span(
                        "🟢 Active", style={"font-weight": "bold", "color": "#4CAF50"}
                    ),
                ],
                className="status-item",
            ),
            html.Div(
                [
                    html.Span("Data Pipeline"),
                    html.Span(
                        "🟢 Running", style={"font-weight": "bold", "color": "#4CAF50"}
                    ),
                ],
                className="status-item",
            ),
            html.Div(
                [
                    html.Span("Last Signal"),
                    html.Span(
                        self.get_last_signal_time(), style={"font-weight": "bold"}
                    ),
                ],
                className="status-item",
            ),
        ]

        return status_items

    def is_market_hours(self) -> bool:
        """Check if market is currently open."""
        now = datetime.now()
        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)

        # Check if it's a weekday and within market hours
        return now.weekday() < 5 and market_start <= now <= market_end

    def get_last_signal_time(self) -> str:
        """Get the time of the last signal."""
        if not self.latest_signals:
            return "No signals"

        last_signal = self.latest_signals[-1]
        timestamp = last_signal.get("timestamp", "")

        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", ""))
            return dt.strftime("%H:%M:%S")
        except Exception:
            return "Unknown"

    def start_data_refresh(self):
        """Start background data refresh thread."""

        def refresh_loop():
            while True:
                try:
                    self.refresh_data()
                    time.sleep(10)  # Refresh every 10 seconds
                except Exception as e:
                    print("Error in data refresh: {e}")
                    time.sleep(30)  # Wait longer on error

        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()

    def run(self, debug: bool = False, host: str = "127.0.0.1"):
        """Run the dashboard server."""
        print("🚀 Starting AI Trading Machine Dashboard...")
        print("📱 Dashboard URL: http://{host}:{self.port}")
        print("📊 Data directory: {self.data_dir}")
        print("🔄 Auto-refresh: Every 5 seconds")
        print("=" * 50)

        self.app.run_server(debug=debug, host=host, port=self.port)


def main():
    """Main function to run the dashboard."""
    if not DASH_AVAILABLE:
        print("❌ Dash and Plotly are required for the dashboard")
        print("💻 Install with: pip install dash plotly")
        return

    try:
        dashboard = TradingDashboard()
        dashboard.run(debug=False, host="0.0.0.0")
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print("❌ Error running dashboard: {e}")


if __name__ == "__main__":
    main()
