#!/usr/bin/env python3
"""
Daily Report Generator for Monitoring Dashboard
Generates comprehensive daily performance and system reports
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from monitoring_dashboard.reports.performance_reporter import PerformanceReporter
from monitoring_dashboard.monitoring.metrics_collector import MetricsCollector
from monitoring_dashboard.utils.logger import setup_logger

class DailyReportGenerator:
    """Daily report generation service"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.performance_reporter = PerformanceReporter()
        self.metrics_collector = MetricsCollector()
    
    async def generate_daily_report(self):
        """Generate comprehensive daily report"""
        try:
            self.logger.info("Starting daily report generation")
            
            # Generate daily report
            report = await self.performance_reporter.generate_daily_report()
            
            # Print summary to console
            self._print_report_summary(report)
            
            self.logger.info("Daily report generated successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
            raise
    
    async def generate_weekly_report(self):
        """Generate comprehensive weekly report"""
        try:
            self.logger.info("Starting weekly report generation")
            
            # Generate weekly report
            report = await self.performance_reporter.generate_weekly_report()
            
            # Print summary to console
            self._print_weekly_summary(report)
            
            self.logger.info("Weekly report generated successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating weekly report: {e}")
            raise
    
    def _print_report_summary(self, report: dict):
        """Print daily report summary to console"""
        print("\n" + "="*60)
        print(f"📊 DAILY TRADING REPORT - {report.get('report_date', 'N/A')}")
        print("="*60)
        
        summary = report.get('summary', {})
        
        print(f"💰 Total P&L: ₹{summary.get('total_pnl', 0):,.2f}")
        print(f"📈 Total Trades: {summary.get('total_trades', 0)}")
        print(f"🎯 Total Signals: {summary.get('total_signals', 0)}")
        print(f"⚡ Active Strategies: {summary.get('active_strategies', 0)}")
        print(f"🏆 Win Rate: {summary.get('win_rate', 0):.1f}%")
        print(f"🌟 Best Strategy: {summary.get('best_strategy', 'N/A')}")
        print(f"⚠️  Worst Strategy: {summary.get('worst_strategy', 'N/A')}")
        print(f"🔄 Status: {summary.get('status', 'Unknown')}")
        
        # System health
        system_health = report.get('system_health', {})
        if system_health:
            print(f"\n🖥️  SYSTEM HEALTH:")
            print(f"   CPU Usage: {system_health.get('cpu_usage', 0):.1f}%")
            print(f"   Memory Usage: {system_health.get('memory_usage', 0):.1f}%")
            print(f"   Disk Usage: {system_health.get('disk_usage', 0):.1f}%")
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("="*60)
    
    def _print_weekly_summary(self, report: dict):
        """Print weekly report summary to console"""
        print("\n" + "="*70)
        print(f"📊 WEEKLY TRADING REPORT - {report.get('report_period', 'N/A')}")
        print("="*70)
        
        summary = report.get('weekly_summary', {})
        
        print(f"📈 Weekly Return: {summary.get('weekly_return', 0):.2f}%")
        print(f"📊 Volatility: {summary.get('volatility', 0):.2f}%")
        print(f"📉 Max Drawdown: {summary.get('max_drawdown', 0):.2f}%")
        print(f"⚡ Sharpe Ratio: {summary.get('sharpe_ratio', 0):.2f}")
        print(f"🔄 Total Trades: {summary.get('total_trades', 0)}")
        print(f"🏆 Win Rate: {summary.get('win_rate', 0):.1f}%")
        print(f"💰 Average Trade: ₹{summary.get('average_trade', 0):,.2f}")
        
        # Strategy analysis
        strategy_analysis = report.get('strategy_analysis', {})
        if strategy_analysis:
            print(f"\n🎯 STRATEGY ANALYSIS:")
            print(f"   Best Performing: {strategy_analysis.get('best_performing', 'N/A')}")
            print(f"   Worst Performing: {strategy_analysis.get('worst_performing', 'N/A')}")
            print(f"   Most Active: {strategy_analysis.get('most_active', 'N/A')}")
            print(f"   Least Active: {strategy_analysis.get('least_active', 'N/A')}")
        
        # Risk metrics
        risk_metrics = report.get('risk_metrics', {})
        if risk_metrics:
            print(f"\n⚠️  RISK METRICS:")
            print(f"   VaR (95%): ₹{risk_metrics.get('var_95', 0):,.2f}")
            print(f"   VaR (99%): ₹{risk_metrics.get('var_99', 0):,.2f}")
            print(f"   Expected Shortfall: ₹{risk_metrics.get('expected_shortfall', 0):,.2f}")
            print(f"   Beta: {risk_metrics.get('beta', 0):.2f}")
            print(f"   Alpha: {risk_metrics.get('alpha', 0):.2f}")
        
        print("="*70)
    
    async def generate_custom_report(self, start_date: str, end_date: str):
        """Generate custom date range report"""
        self.logger.info(f"Generating custom report for {start_date} to {end_date}")
        
        # This would implement custom date range reporting
        # For now, return a placeholder
        return {
            "report_type": "custom",
            "start_date": start_date,
            "end_date": end_date,
            "message": "Custom reporting feature coming soon"
        }

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Trading Machine Report Generator")
    parser.add_argument("--type", choices=["daily", "weekly", "custom"], default="daily",
                       help="Type of report to generate")
    parser.add_argument("--start-date", help="Start date for custom report (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date for custom report (YYYY-MM-DD)")
    parser.add_argument("--output", help="Output file path (JSON format)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create report generator
    generator = DailyReportGenerator()
    
    try:
        # Generate report based on type
        if args.type == "daily":
            report = await generator.generate_daily_report()
        elif args.type == "weekly":
            report = await generator.generate_weekly_report()
        elif args.type == "custom":
            if not args.start_date or not args.end_date:
                print("Error: Custom reports require --start-date and --end-date")
                return 1
            report = await generator.generate_custom_report(args.start_date, args.end_date)
        
        # Save to file if specified
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"\n📁 Report saved to: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
