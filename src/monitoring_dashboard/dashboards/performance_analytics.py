#!/usr/bin/env python3
"""
Performance Analytics Dashboard
==============================

Advanced performance tracking and analytics for the AI Trading Machine.

Features:
- Real-time performance metrics
- Portfolio analysis
- Risk metrics calculation
- Signal performance tracking
- Interactive charts and reports
- Export capabilities

Usage:
    python performance_analytics.py

Author: AI Trading Machine
Licensed by SJ Trading
"""

import json
import os
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

warnings.filterwarnings("ignore")

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️ Plotly not available. Install with: pip install plotly")


@dataclass
class PerformanceMetrics:
    """Performance metrics for trading analysis."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    average_trade_duration: float = 0.0  # hours
    portfolio_value: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PerformanceAnalytics:
    """Advanced performance analytics for trading system."""

    def __init__(self):
        """Initialize the performance analytics system."""
        self.data_dir = os.path.join(project_root, "automated_data")
        self.reports_dir = os.path.join(project_root, "reports")
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure required directories exist."""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(os.path.join(self.reports_dir, "charts"), exist_ok=True)

    def load_trading_data(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load trading data from files."""
        trades_df = pd.DataFrame()
        signals_df = pd.DataFrame()
        performance_df = pd.DataFrame()

        try:
            # Load trades data
            trades_dir = os.path.join(self.data_dir, "trades")
            if os.path.exists(trades_dir):
                trade_files = [f for f in os.listdir(trades_dir) if f.endswith(".json")]
                trade_data = []

                for file in trade_files:
                    file_path = os.path.join(trades_dir, file)
                    with open(file_path) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            trade_data.extend(data)
                        else:
                            trade_data.append(data)

                if trade_data:
                    trades_df = pd.DataFrame(trade_data)
                    if "entry_time" in trades_df.columns:
                        trades_df["entry_time"] = pd.to_datetime(
                            trades_df["entry_time"]
                        )
                    if "exit_time" in trades_df.columns:
                        trades_df["exit_time"] = pd.to_datetime(trades_df["exit_time"])

            # Load signals data
            signals_dir = os.path.join(self.data_dir, "signals")
            if os.path.exists(signals_dir):
                signal_files = [
                    f for f in os.listdir(signals_dir) if f.endswith(".json")
                ]
                signal_data = []

                for file in signal_files:
                    file_path = os.path.join(signals_dir, file)
                    with open(file_path) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            signal_data.extend(data)
                        else:
                            signal_data.append(data)

                if signal_data:
                    signals_df = pd.DataFrame(signal_data)
                    if "timestamp" in signals_df.columns:
                        signals_df["timestamp"] = pd.to_datetime(
                            signals_df["timestamp"]
                        )

            # Load performance data
            performance_dir = os.path.join(self.data_dir, "performance")
            if os.path.exists(performance_dir):
                perf_files = [
                    f for f in os.listdir(performance_dir) if f.endswith(".json")
                ]
                perf_data = []

                for file in perf_files:
                    file_path = os.path.join(performance_dir, file)
                    with open(file_path) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            perf_data.extend(data)
                        else:
                            perf_data.append(data)

                if perf_data:
                    performance_df = pd.DataFrame(perf_data)
                    if "date" in performance_df.columns:
                        performance_df["date"] = pd.to_datetime(performance_df["date"])

        except Exception as e:
            print("⚠️ Error loading data: {e}")

        return trades_df, signals_df, performance_df

    def calculate_metrics(self, trades_df: pd.DataFrame) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if trades_df.empty:
            return PerformanceMetrics()

        # Filter completed trades
        completed_trades = trades_df[
            trades_df["status"].isin(["FILLED", "TARGET_HIT", "STOP_HIT"])
        ]

        if completed_trades.empty:
            return PerformanceMetrics()

        # Basic metrics
        total_trades = len(completed_trades)
        winning_trades = len(completed_trades[completed_trades["pnl"] > 0])
        losing_trades = len(completed_trades[completed_trades["pnl"] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # PnL metrics
        total_pnl = completed_trades["pnl"].sum()
        total_pnl_percent = completed_trades["pnl_percent"].sum()

        # Win/Loss metrics
        wins = completed_trades[completed_trades["pnl"] > 0]["pnl"]
        losses = completed_trades[completed_trades["pnl"] < 0]["pnl"]

        average_win = wins.mean() if len(wins) > 0 else 0
        average_loss = abs(losses.mean()) if len(losses) > 0 else 0

        # Profit factor
        total_wins = wins.sum() if len(wins) > 0 else 0
        total_losses = abs(losses.sum()) if len(losses) > 0 else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else float("in")

        # Best and worst trades
        best_trade = completed_trades["pnl"].max()
        worst_trade = completed_trades["pnl"].min()

        # Calculate drawdown
        cumulative_pnl = completed_trades["pnl"].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()

        # Sharpe ratio (simplified)
        returns = completed_trades["pnl_percent"]
        sharpe_ratio = (returns.mean() / returns.std()) if returns.std() > 0 else 0

        # Trade duration
        duration_trades = completed_trades.dropna(subset=["entry_time", "exit_time"])
        if not duration_trades.empty:
            durations = (
                duration_trades["exit_time"] - duration_trades["entry_time"]
            ).dt.total_seconds() / 3600
            average_trade_duration = durations.mean()
        else:
            average_trade_duration = 0

        # Date range
        start_date = (
            completed_trades["entry_time"].min()
            if "entry_time" in completed_trades.columns
            else None
        )
        end_date = (
            completed_trades["entry_time"].max()
            if "entry_time" in completed_trades.columns
            else None
        )

        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            best_trade=best_trade,
            worst_trade=worst_trade,
            average_trade_duration=average_trade_duration,
            start_date=start_date,
            end_date=end_date,
        )

    def create_equity_curve(self, trades_df: pd.DataFrame) -> str:
        """Create equity curve chart."""
        if trades_df.empty:
            return ""

        completed_trades = trades_df[
            trades_df["status"].isin(["FILLED", "TARGET_HIT", "STOP_HIT"])
        ]
        if completed_trades.empty:
            return ""

        # Calculate cumulative P&L
        cumulative_pnl = completed_trades["pnl"].cumsum()
        dates = (
            completed_trades["entry_time"]
            if "entry_time" in completed_trades.columns
            else range(len(completed_trades))
        )

        if PLOTLY_AVAILABLE:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=cumulative_pnl,
                    mode="lines",
                    name="Cumulative P&L",
                    line=dict(color="blue", width=2),
                )
            )

            fig.update_layout(
                title="Equity Curve - Cumulative P&L",
                xaxis_title="Date",
                yaxis_title="Cumulative P&L (₹)",
                template="plotly_white",
            )

            chart_path = os.path.join(self.reports_dir, "charts", "equity_curve.html")
            fig.write_html(chart_path)
            return chart_path
        else:
            # Fallback to matplotlib
            plt.figure(figsize=(12, 6))
            plt.plot(dates, cumulative_pnl, color="blue", linewidth=2)
            plt.title("Equity Curve - Cumulative P&L")
            plt.xlabel("Date")
            plt.ylabel("Cumulative P&L (₹)")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            chart_path = os.path.join(self.reports_dir, "charts", "equity_curve.png")
            plt.savefig(chart_path, dpi=300, bbox_inches="tight")
            plt.close()
            return chart_path

    def create_performance_dashboard(
        self, trades_df: pd.DataFrame, signals_df: pd.DataFrame
    ) -> str:
        """Create comprehensive performance dashboard."""
        if not PLOTLY_AVAILABLE:
            print("⚠️ Plotly required for dashboard. Using basic charts instead.")
            return self.create_basic_reports(trades_df, signals_df)

        # Calculate metrics
        metrics = self.calculate_metrics(trades_df)

        # Create subplots
        fig = make_subplots(
            rows=3,
            cols=2,
            subplot_titles=(
                "Equity Curve",
                "Win/Loss Distribution",
                "Trade P&L Distribution",
                "Daily Performance",
                "Signal Performance",
                "Risk Metrics",
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}],
            ],
        )

        completed_trades = trades_df[
            trades_df["status"].isin(["FILLED", "TARGET_HIT", "STOP_HIT"])
        ]

        if not completed_trades.empty:
            # Equity curve
            cumulative_pnl = completed_trades["pnl"].cumsum()
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(cumulative_pnl))),
                    y=cumulative_pnl,
                    mode="lines",
                    name="Cumulative P&L",
                ),
                row=1,
                col=1,
            )

            # Win/Loss pie chart
            fig.add_trace(
                go.Pie(
                    labels=["Wins", "Losses"],
                    values=[metrics.winning_trades, metrics.losing_trades],
                    name="Win/Loss",
                ),
                row=1,
                col=2,
            )

            # P&L distribution
            fig.add_trace(
                go.Histogram(
                    x=completed_trades["pnl"], name="P&L Distribution", nbinsx=20
                ),
                row=2,
                col=1,
            )

            # Daily performance (if we have date data)
            if "entry_time" in completed_trades.columns:
                daily_pnl = completed_trades.groupby(
                    completed_trades["entry_time"].dt.date
                )["pnl"].sum()
                fig.add_trace(
                    go.Bar(x=daily_pnl.index, y=daily_pnl.values, name="Daily P&L"),
                    row=2,
                    col=2,
                )

        # Signal performance
        if not signals_df.empty:
            signal_counts = signals_df["action"].value_counts()
            fig.add_trace(
                go.Bar(
                    x=signal_counts.index, y=signal_counts.values, name="Signal Counts"
                ),
                row=3,
                col=1,
            )

        # Risk metrics (text display)
        risk_text = """
        Max Drawdown: ₹{metrics.max_drawdown:.2f}<br>
        Sharpe Ratio: {metrics.sharpe_ratio:.2f}<br>
        Profit Factor: {metrics.profit_factor:.2f}<br>
        Avg Trade Duration: {metrics.average_trade_duration:.1f}h
        """
        fig.add_annotation(
            text=risk_text,
            xref="x domain",
            yref="y domain",
            x=0.5,
            y=0.5,
            showarrow=False,
            row=3,
            col=2,
        )

        # Update layout
        fig.update_layout(
            title_text="AI Trading Machine - Performance Dashboard",
            height=1000,
            showlegend=False,
        )

        # Save dashboard
        dashboard_path = os.path.join(self.reports_dir, "performance_dashboard.html")
        fig.write_html(dashboard_path)

        return dashboard_path

    def create_basic_reports(
        self, trades_df: pd.DataFrame, signals_df: pd.DataFrame
    ) -> str:
        """Create basic performance reports using matplotlib."""
        metrics = self.calculate_metrics(trades_df)

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle("AI Trading Machine - Performance Report", fontsize=16)

        completed_trades = trades_df[
            trades_df["status"].isin(["FILLED", "TARGET_HIT", "STOP_HIT"])
        ]

        if not completed_trades.empty:
            # Equity curve
            cumulative_pnl = completed_trades["pnl"].cumsum()
            axes[0, 0].plot(cumulative_pnl, color="blue", linewidth=2)
            axes[0, 0].set_title("Equity Curve")
            axes[0, 0].set_ylabel("Cumulative P&L (₹)")
            axes[0, 0].grid(True, alpha=0.3)

            # Win/Loss pie chart
            labels = ["Wins", "Losses"]
            sizes = [metrics.winning_trades, metrics.losing_trades]
            colors = ["green", "red"]
            axes[0, 1].pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%")
            axes[0, 1].set_title("Win/Loss Distribution")

            # P&L distribution
            axes[1, 0].hist(completed_trades["pnl"], bins=20, alpha=0.7, color="blue")
            axes[1, 0].set_title("P&L Distribution")
            axes[1, 0].set_xlabel("P&L (₹)")
            axes[1, 0].set_ylabel("Frequency")
            axes[1, 0].grid(True, alpha=0.3)

        # Metrics summary
        metrics_text = """
Performance Metrics:
Total Trades: {metrics.total_trades}
Win Rate: {metrics.win_rate:.1f}%
Total P&L: ₹{metrics.total_pnl:.2f}
Profit Factor: {metrics.profit_factor:.2f}
Sharpe Ratio: {metrics.sharpe_ratio:.2f}
Max Drawdown: ₹{metrics.max_drawdown:.2f}
Best Trade: ₹{metrics.best_trade:.2f}
Worst Trade: ₹{metrics.worst_trade:.2f}
        """
        axes[1, 1].text(
            0.1,
            0.9,
            metrics_text,
            fontsize=10,
            verticalalignment="top",
            transform=axes[1, 1].transAxes,
        )
        axes[1, 1].set_title("Performance Summary")
        axes[1, 1].axis("o")

        plt.tight_layout()

        # Save report
        report_path = os.path.join(self.reports_dir, "performance_report.png")
        plt.savefig(report_path, dpi=300, bbox_inches="tight")
        plt.close()

        return report_path

    def generate_detailed_report(
        self, trades_df: pd.DataFrame, signals_df: pd.DataFrame
    ) -> str:
        """Generate detailed text report."""
        metrics = self.calculate_metrics(trades_df)

        report = """
AI Trading Machine - Performance Report
======================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: {metrics.start_date.strftime('%Y-%m-%d') if metrics.start_date else 'N/A'} to {metrics.end_date.strftime('%Y-%m-%d') if metrics.end_date else 'N/A'}

OVERVIEW
--------
Total Trades: {metrics.total_trades}
Winning Trades: {metrics.winning_trades}
Losing Trades: {metrics.losing_trades}
Win Rate: {metrics.win_rate:.2f}%

FINANCIAL PERFORMANCE
-------------------
Total P&L: ₹{metrics.total_pnl:.2f}
Total P&L %: {metrics.total_pnl_percent:.2f}%
Average Win: ₹{metrics.average_win:.2f}
Average Loss: ₹{metrics.average_loss:.2f}
Best Trade: ₹{metrics.best_trade:.2f}
Worst Trade: ₹{metrics.worst_trade:.2f}

RISK METRICS
-----------
Profit Factor: {metrics.profit_factor:.2f}
Sharpe Ratio: {metrics.sharpe_ratio:.2f}
Max Drawdown: ₹{metrics.max_drawdown:.2f}
Average Trade Duration: {metrics.average_trade_duration:.1f} hours

SIGNAL ANALYSIS
--------------
"""

        if not signals_df.empty:
            signal_counts = signals_df["action"].value_counts()
            for action, count in signal_counts.items():
                report += "{action}: {count} signals\n"

        # Symbol performance
        if not trades_df.empty:
            completed_trades = trades_df[
                trades_df["status"].isin(["FILLED", "TARGET_HIT", "STOP_HIT"])
            ]
            if not completed_trades.empty and "symbol" in completed_trades.columns:
                symbol_performance = completed_trades.groupby("symbol")["pnl"].agg(
                    ["count", "sum", "mean"]
                )
                symbol_performance.columns = ["Trades", "Total P&L", "Avg P&L"]
                symbol_performance = symbol_performance.sort_values(
                    "Total P&L", ascending=False
                )

                report += "\nSYMBOL PERFORMANCE\n{'-' * 17}\n"
                report += symbol_performance.to_string()

        report += "\n\nReport generated by AI Trading Machine v2.0\n"

        # Save report
        report_path = os.path.join(self.reports_dir, "detailed_report.txt")
        with open(report_path, "w") as f:
            f.write(report)

        return report_path

    def run_analytics(self):
        """Run complete performance analytics."""
        print("📊 AI Trading Machine - Performance Analytics")
        print("=" * 50)

        # Load data
        print("📂 Loading trading data...")
        trades_df, signals_df, performance_df = self.load_trading_data()

        print("   • Trades: {len(trades_df)} records")
        print("   • Signals: {len(signals_df)} records")
        print("   • Performance: {len(performance_df)} records")

        if trades_df.empty:
            print("⚠️ No trading data found. Run some trades first.")
            return

        # Calculate metrics
        print("\n📈 Calculating performance metrics...")
        metrics = self.calculate_metrics(trades_df)

        # Display summary
        print("\n📊 PERFORMANCE SUMMARY")
        print("-" * 25)
        print("Total Trades: {metrics.total_trades}")
        print("Win Rate: {metrics.win_rate:.1f}%")
        print("Total P&L: ₹{metrics.total_pnl:.2f}")
        print("Profit Factor: {metrics.profit_factor:.2f}")
        print("Max Drawdown: ₹{metrics.max_drawdown:.2f}")

        # Generate reports
        print("\n📋 Generating reports...")

        # Equity curve
        equity_chart = self.create_equity_curve(trades_df)
        if equity_chart:
            print("   ✅ Equity curve: {equity_chart}")

        # Dashboard
        dashboard = self.create_performance_dashboard(trades_df, signals_df)
        print("   ✅ Dashboard: {dashboard}")

        # Detailed report
        detailed_report = self.generate_detailed_report(trades_df, signals_df)
        print("   ✅ Detailed report: {detailed_report}")

        print("\n🎉 Analytics complete! Reports saved to: {self.reports_dir}")


def main():
    """Main function to run performance analytics."""
    analytics = PerformanceAnalytics()
    analytics.run_analytics()


if __name__ == "__main__":
    main()
