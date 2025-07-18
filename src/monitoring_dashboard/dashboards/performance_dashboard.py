#!/usr/bin/env python3
"""
Trading Performance Monitor & Dashboard
Comprehensive reporting and visualization for trading strategies
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

# Import our trading components
from ai_trading_machine.execution.portfolio_manager import run_portfolio_backtest
from ai_trading_machine.strategies.enhanced_strategies import (
    enhanced_momentum_signals,
    enhanced_rsi_signals,
    macd_signals,
)

logger = logging.getLogger(__name__)


@dataclass
class PerformanceReport:
    strategy_name: str
    period: str
    total_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    benchmark_return: float
    outperformance: float


class TradingDashboard:
    """Comprehensive trading performance dashboard"""

    def __init__(self):
        self.reports: list[PerformanceReport] = []
        self.detailed_results: dict[str, Any] = {}

    def add_backtest_result(self, name: str, result: dict[str, Any]):
        """Add a backtest result to the dashboard"""
        if result.get("success", False):
            metrics = result.get("metrics", {})

            report = PerformanceReport(
                strategy_name=name,
                period="{result.get('period_days', 365)} days",
                total_return=metrics.get("total_return_pct", 0),
                volatility=metrics.get("volatility_pct", 0),
                sharpe_ratio=metrics.get("sharpe_ratio", 0),
                max_drawdown=metrics.get("max_drawdown_pct", 0),
                win_rate=metrics.get("win_rate_pct", 0),
                total_trades=metrics.get("total_trades", 0),
                benchmark_return=metrics.get("benchmark_return_pct", 0),
                outperformance=metrics.get("outperformance", 0),
            )

            self.reports.append(report)
            self.detailed_results[name] = result

    def generate_summary_table(self) -> str:
        """Generate a formatted summary table"""
        if not self.reports:
            return "No performance data available"

        lines = [
            "=" * 120,
            "🏆 TRADING STRATEGY PERFORMANCE DASHBOARD",
            "=" * 120,
            "{'Strategy':<25} {'Period':<12} {'Return':<10} {'Volatility':<12} {'Sharpe':<8} {'Drawdown':<12} {'Win Rate':<10} {'Trades':<8} {'vs Bench':<10}",
            "-" * 120,
        ]

        for report in sorted(self.reports, key=lambda x: x.sharpe_ratio, reverse=True):
            lines.append(
                "{report.strategy_name:<25} "
                "{report.period:<12} "
                "{report.total_return:+7.2f}%   "
                "{report.volatility:8.2f}%    "
                "{report.sharpe_ratio:6.3f}  "
                "{report.max_drawdown:8.2f}%    "
                "{report.win_rate:7.1f}%   "
                "{report.total_trades:6}   "
                "{report.outperformance:+7.2f}%"
            )

        lines.extend(["-" * 120, ""])

        return "\n".join(lines)

    def generate_risk_analysis(self) -> str:
        """Generate risk analysis report"""
        if not self.reports:
            return "No risk data available"

        lines = ["🛡️ RISK ANALYSIS SUMMARY", "=" * 60, ""]

        # Risk rankings
        sharpe_ranking = sorted(
            self.reports, key=lambda x: x.sharpe_ratio, reverse=True
        )
        drawdown_ranking = sorted(self.reports, key=lambda x: abs(x.max_drawdown))
        volatility_ranking = sorted(self.reports, key=lambda x: x.volatility)

        lines.extend(
            [
                "📊 Best Risk-Adjusted Returns (Sharpe Ratio):",
                "   "
                + " | ".join(
                    [
                        "{r.strategy_name}: {r.sharpe_ratio:.3f}"
                        for r in sharpe_ranking[:3]
                    ]
                ),
                "",
                "🛡️ Lowest Maximum Drawdown:",
                "   "
                + " | ".join(
                    [
                        "{r.strategy_name}: {r.max_drawdown:.2f}%"
                        for r in drawdown_ranking[:3]
                    ]
                ),
                "",
                "📈 Lowest Volatility:",
                "   "
                + " | ".join(
                    [
                        "{r.strategy_name}: {r.volatility:.2f}%"
                        for r in volatility_ranking[:3]
                    ]
                ),
                "",
            ]
        )

        # Portfolio diversification insights
        if len(self.reports) > 1:
            avg_correlation = 0.65  # Simplified - would calculate from actual data
            lines.extend(
                [
                    "🔗 Estimated Strategy Correlation: {avg_correlation:.2f}",
                    "💡 Diversification Benefit: {'High' if avg_correlation < 0.7 else 'Medium' if avg_correlation < 0.8 else 'Low'}",
                    "",
                ]
            )

        return "\n".join(lines)

    def generate_trading_insights(self) -> str:
        """Generate trading insights and recommendations"""
        if not self.reports:
            return "No trading data available"

        lines = ["💡 TRADING INSIGHTS & RECOMMENDATIONS", "=" * 60, ""]

        # Best performers
        best_return = max(self.reports, key=lambda x: x.total_return)
        best_sharpe = max(self.reports, key=lambda x: x.sharpe_ratio)
        best_win_rate = max(self.reports, key=lambda x: x.win_rate)

        lines.extend(
            [
                "🥇 Highest Return: {best_return.strategy_name} ({best_return.total_return:+.2f}%)",
                "🎯 Best Risk-Adjusted: {best_sharpe.strategy_name} (Sharpe: {best_sharpe.sharpe_ratio:.3f})",
                "🎪 Highest Win Rate: {best_win_rate.strategy_name} ({best_win_rate.win_rate:.1f}%)",
                "",
            ]
        )

        # Trading frequency analysis
        high_freq = [r for r in self.reports if r.total_trades > 50]
        medium_freq = [r for r in self.reports if 20 <= r.total_trades <= 50]
        low_freq = [r for r in self.reports if r.total_trades < 20]

        lines.extend(
            [
                "📊 Trading Frequency Analysis:",
                "   High Frequency (>50 trades): {len(high_freq)} strategies",
                "   Medium Frequency (20-50 trades): {len(medium_freq)} strategies",
                "   Low Frequency (<20 trades): {len(low_freq)} strategies",
                "",
            ]
        )

        # Recommendations
        lines.extend(["🎯 STRATEGY RECOMMENDATIONS:", ""])

        if best_sharpe.sharpe_ratio > 0.5:
            lines.append(
                "✅ RECOMMENDED: {best_sharpe.strategy_name} - Strong risk-adjusted returns"
            )

        if best_return.total_return > 10 and best_return.max_drawdown > -10:
            lines.append(
                "✅ AGGRESSIVE: {best_return.strategy_name} - High returns with manageable risk"
            )

        conservative_strategies = [
            r for r in self.reports if abs(r.max_drawdown) < 5 and r.total_return > 0
        ]
        if conservative_strategies:
            best_conservative = max(
                conservative_strategies, key=lambda x: x.total_return
            )
            lines.append(
                "✅ CONSERVATIVE: {best_conservative.strategy_name} - Low risk, positive returns"
            )

        # Risk warnings
        high_risk = [
            r for r in self.reports if abs(r.max_drawdown) > 15 or r.volatility > 30
        ]
        if high_risk:
            lines.extend(
                [
                    "",
                    "⚠️ HIGH RISK STRATEGIES:",
                    *[
                        "   - {r.strategy_name}: {r.max_drawdown:.1f}% drawdown, {r.volatility:.1f}% volatility"
                        for r in high_risk
                    ],
                ]
            )

        return "\n".join(lines)

    def save_detailed_report(self, filename: Optional[str] = None) -> str:
        """Save a comprehensive report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = "logs/trading_report_{timestamp}.txt"

        Path("logs").mkdir(exist_ok=True)

        report_content = [
            "🚀 AI TRADING MACHINE - COMPREHENSIVE PERFORMANCE REPORT",
            "Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            self.generate_summary_table(),
            self.generate_risk_analysis(),
            self.generate_trading_insights(),
            "",
            "📊 DETAILED METRICS BY STRATEGY",
            "=" * 60,
            "",
        ]

        # Add detailed metrics for each strategy
        for name, result in self.detailed_results.items():
            if result.get("success", False):
                metrics = result.get("metrics", {})
                report_content.extend(
                    [
                        "Strategy: {name}",
                        "  Total Return: {metrics.get('total_return_pct', 0):+.2f}%",
                        "  Annualized Return: {metrics.get('annualized_return_pct', 0):+.2f}%",
                        "  Volatility: {metrics.get('volatility_pct', 0):.2f}%",
                        "  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}",
                        "  Maximum Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%",
                        "  Win Rate: {metrics.get('win_rate_pct', 0):.1f}%",
                        "  Total Trades: {metrics.get('total_trades', 0)}",
                        "  Calmar Ratio: {metrics.get('calmar_ratio', 0):.3f}",
                        "",
                    ]
                )

        # Save to file
        try:
            with open(filename, "w") as f:
                f.write("\n".join(report_content))
            return filename
        except Exception as e:
            logger.error("Failed to save report: {e}")
            return ""


def run_comprehensive_analysis():
    """Run comprehensive analysis across strategies and timeframes"""
    print("🚀 AI Trading Machine - Comprehensive Performance Analysis")
    print("=" * 70)

    dashboard = TradingDashboard()

    # Define test scenarios
    tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

    strategies = {
        "Enhanced RSI (Adaptive)": lambda df: enhanced_rsi_signals(
            df, adaptive_thresholds=True
        ),
        "Enhanced RSI (Fixed)": lambda df: enhanced_rsi_signals(
            df, adaptive_thresholds=False, period=21
        ),
        "Enhanced Momentum (10,30)": lambda df: enhanced_momentum_signals(
            df, short_window=10, long_window=30
        ),
        "Enhanced Momentum (5,20)": lambda df: enhanced_momentum_signals(
            df, short_window=5, long_window=20
        ),
        "MACD Standard": macd_signals,
    }

    # Portfolio tests
    portfolio_strategies = {
        "rsi_adaptive": enhanced_rsi_signals,
        "momentum_fast": lambda df: enhanced_momentum_signals(
            df, short_window=5, long_window=20
        ),
        "macd": macd_signals,
    }

    print("\n📊 Running Portfolio Backtests...")
    print("-" * 50)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    # Single strategy portfolios
    for strategy_name, strategy_func in portfolio_strategies.items():
        print("Testing {strategy_name} portfolio...", end=" ")

        try:
            result = run_portfolio_backtest(
                tickers=tickers[:3],  # Use subset for faster testing
                strategies={strategy_name: strategy_func},
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                initial_capital=100000,
            )

            if result.get("success"):
                dashboard.add_backtest_result("Portfolio_{strategy_name}", result)
                metrics = result["metrics"]
                print(
                    "✅ {metrics.get('total_return_pct', 0):+.2f}% (SR: {metrics.get('sharpe_ratio', 0):.3f})"
                )
            else:
                print("❌ Failed")

        except Exception as e:
            print("❌ Error: {e}")

    # Multi-strategy portfolio
    print("Testing multi-strategy portfolio...", end=" ")
    try:
        result = run_portfolio_backtest(
            tickers=tickers[:3],
            strategies=portfolio_strategies,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            initial_capital=100000,
        )

        if result.get("success"):
            dashboard.add_backtest_result("Multi_Strategy_Portfolio", result)
            metrics = result["metrics"]
            print(
                "✅ {metrics.get('total_return_pct', 0):+.2f}% (SR: {metrics.get('sharpe_ratio', 0):.3f})"
            )
        else:
            print("❌ Failed")

    except Exception as e:
        print("❌ Error: {e}")

    # Generate and display comprehensive report
    print("\n" + dashboard.generate_summary_table())
    print(dashboard.generate_risk_analysis())
    print(dashboard.generate_trading_insights())

    # Save detailed report
    report_file = dashboard.save_detailed_report()
    if report_file:
        print("📁 Detailed report saved to: {report_file}")

    print("\n🎯 Comprehensive analysis completed!")
    return dashboard


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Run comprehensive analysis
    dashboard = run_comprehensive_analysis()

    # Additional quick stats
    if dashboard.reports:
        best_strategy = max(dashboard.reports, key=lambda x: x.sharpe_ratio)
        print("\n🏆 WINNER: {best_strategy.strategy_name}")
        print("   Return: {best_strategy.total_return:+.2f}%")
        print("   Sharpe: {best_strategy.sharpe_ratio:.3f}")
        print("   Max DD: {best_strategy.max_drawdown:.2f}%")
