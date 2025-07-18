#!/usr/bin/env python3
"""
Automated Cost Monitoring and Optimization System
=================================================

Automated system for monitoring GCP costs and implementing optimizations:
- Real-time cost tracking
- Budget alerts and notifications
- Resource usage analysis
- Automated cost optimization recommendations
- Unused resource detection and cleanup suggestions

Author: AI Trading Machine
Licensed by SJ Trading
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

from apps.monitoring.smart_alerting_system import (
    AlertLevel,
    AlertType,
    SmartAlertingSystem,
)

from src.ai_trading_machine.utils.logger import setup_logger

logger = setup_logger(__name__)


class CostOptimizationLevel(Enum):
    """Cost optimization aggressiveness levels"""

    CONSERVATIVE = "conservative"  # Only safe, minimal-impact optimizations
    BALANCED = "balanced"  # Moderate optimizations with some risk
    AGGRESSIVE = "aggressive"  # All possible optimizations


@dataclass
class CostOptimization:
    """Cost optimization recommendation"""

    id: str
    category: str
    resource_type: str
    resource_name: str
    current_cost: float
    potential_savings: float
    risk_level: str
    implementation_effort: str
    description: str
    action_required: str
    automation_possible: bool
    priority: int  # 1-5, where 1 is highest priority


@dataclass
class CostReport:
    """Comprehensive cost report"""

    timestamp: datetime
    period: str
    total_cost: float
    budget_limit: float
    budget_utilization: float
    cost_trend: str  # "increasing", "decreasing", "stable"
    top_cost_services: list[dict[str, Any]]
    optimizations: list[CostOptimization]
    alerts_triggered: list[str]
    estimated_monthly_cost: float
    cost_per_trade: float
    roi_analysis: dict[str, float]


class AutomatedCostOptimizer:
    """Automated cost monitoring and optimization system"""

    def __init__(
        self,
        monthly_budget: float = 200.0,
        optimization_level: CostOptimizationLevel = CostOptimizationLevel.BALANCED,
    ):
        """Initialize cost optimizer"""
        self.monthly_budget = monthly_budget
        self.optimization_level = optimization_level
        self.project_root = project_root
        self.cost_data_dir = os.path.join(project_root, "cost_data")
        self.optimization_dir = os.path.join(project_root, "cost_optimizations")

        # Ensure directories exist
        os.makedirs(self.cost_data_dir, exist_ok=True)
        os.makedirs(self.optimization_dir, exist_ok=True)

        # Initialize alerting
        self.alerting_system = SmartAlertingSystem()

        # Cost thresholds
        self.cost_thresholds = {
            "daily_limit": monthly_budget / 30,
            "warning_threshold": 0.8,  # 80% of budget
            "critical_threshold": 0.95,  # 95% of budget
            "anomaly_multiplier": 2.0,  # 2x normal daily cost
        }

        # GCP service cost patterns (simplified for demo)
        self.service_patterns = {
            "cloud_run": {
                "base_cost": 0,
                "per_request": 0.0000004,
                "per_gb_hour": 0.00001125,
            },
            "bigquery": {"storage_gb_month": 0.02, "query_tb": 5.0},
            "cloud_storage": {"standard_gb_month": 0.02, "operations_per_1000": 0.005},
            "firestore": {
                "storage_gb_month": 0.18,
                "reads_per_100000": 0.06,
                "writes_per_100000": 0.18,
            },
            "pub_sub": {"message_mb": 0.04, "storage_gb_month": 0.27},
            "compute_engine": {"n1_standard_1_hour": 0.0475, "storage_gb_month": 0.04},
        }

        logger.info(
            "Cost optimizer initialized (budget: ${monthly_budget}, level: {optimization_level.value})"
        )

    def analyze_current_costs(self) -> CostReport:
        """Analyze current costs and generate report"""
        logger.info("Analyzing current costs...")

        try:
            # Simulate cost data collection (in real implementation, this would query GCP Billing API)
            current_costs = self._collect_cost_data()

            # Calculate metrics
            budget_utilization = (
                current_costs["monthly_cost"] / self.monthly_budget
            ) * 100

            # Determine cost trend
            cost_trend = self._analyze_cost_trend(current_costs)

            # Generate optimizations
            optimizations = self._generate_optimizations(current_costs)

            # Check for alerts
            alerts_triggered = self._check_cost_alerts(current_costs)

            # Calculate ROI metrics
            roi_analysis = self._calculate_roi_analysis(current_costs)

            # Create report
            report = CostReport(
                timestamp=datetime.now(),
                period="current_month",
                total_cost=current_costs["monthly_cost"],
                budget_limit=self.monthly_budget,
                budget_utilization=budget_utilization,
                cost_trend=cost_trend,
                top_cost_services=current_costs["services"],
                optimizations=optimizations,
                alerts_triggered=alerts_triggered,
                estimated_monthly_cost=current_costs["projected_monthly"],
                cost_per_trade=current_costs.get("cost_per_trade", 0.0),
                roi_analysis=roi_analysis,
            )

            # Send alerts if needed
            self._send_cost_alerts(report)

            return report

        except Exception as e:
            logger.error("Error analyzing costs: {e}")
            raise

    def implement_optimizations(
        self, optimizations: list[CostOptimization], auto_apply: bool = False
    ) -> dict[str, Any]:
        """Implement cost optimizations"""
        logger.info(
            "Implementing {len(optimizations)} optimizations (auto_apply: {auto_apply})"
        )

        results = {
            "timestamp": datetime.now().isoformat(),
            "optimizations_applied": [],
            "optimizations_skipped": [],
            "total_savings": 0.0,
            "implementation_log": [],
        }

        for optimization in optimizations:
            try:
                if auto_apply and optimization.automation_possible:
                    # Apply automated optimization
                    success = self._apply_optimization(optimization)
                    if success:
                        results["optimizations_applied"].append(optimization.id)
                        results["total_savings"] += optimization.potential_savings
                        results["implementation_log"].append(
                            "✅ Applied: {optimization.description}"
                        )
                    else:
                        results["optimizations_skipped"].append(optimization.id)
                        results["implementation_log"].append(
                            "❌ Failed: {optimization.description}"
                        )
                else:
                    # Manual optimization required
                    results["optimizations_skipped"].append(optimization.id)
                    results["implementation_log"].append(
                        "⚠️ Manual action required: {optimization.description}"
                    )

            except Exception as e:
                logger.error("Error implementing optimization {optimization.id}: {e}")
                results["optimizations_skipped"].append(optimization.id)
                results["implementation_log"].append(
                    "❌ Error: {optimization.description} - {str(e)}"
                )

        # Save implementation results
        results_file = os.path.join(
            self.optimization_dir,
            "optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("Optimization results saved: {results_file}")
        return results

    def generate_cost_dashboard(self) -> str:
        """Generate cost monitoring dashboard"""
        logger.info("Generating cost dashboard...")

        try:
            # Analyze costs
            report = self.analyze_current_costs()

            # Create dashboard HTML
            dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Trading Machine - Cost Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .metric-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .metric-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
        .metric-value.good {{ color: #4CAF50; }}
        .metric-value.warning {{ color: #FF9800; }}
        .metric-value.critical {{ color: #f44336; }}
        .optimization {{ background: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #2196F3; }}
        .optimization.high {{ border-left-color: #f44336; }}
        .optimization.medium {{ border-left-color: #FF9800; }}
        .optimization.low {{ border-left-color: #4CAF50; }}
        .service-item {{ display: flex; justify-content: space-between; padding: 10px; background: #f8f9fa; margin: 5px 0; border-radius: 5px; }}
        .alert {{ background: #ffebee; border: 1px solid #f44336; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #4CAF50 0%, #FF9800 70%, #f44336 90%); transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Cost Monitoring Dashboard</h1>
            <p>Real-time cost tracking and optimization for AI Trading Machine</p>
            <p><strong>Last Updated:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="metric-row">
            <div class="metric-card">
                <h3>📊 Budget Status</h3>
                <div class="metric-value {'good' if report.budget_utilization < 70 else 'warning' if report.budget_utilization < 90 else 'critical'}">${report.total_cost:.2f}</div>
                <p>of ${report.budget_limit:.2f} budget ({report.budget_utilization:.1f}%)</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {min(report.budget_utilization, 100):.1f}%"></div>
                </div>
            </div>

            <div class="metric-card">
                <h3>📈 Cost Trend</h3>
                <div class="metric-value {'good' if report.cost_trend == 'decreasing' else 'warning' if report.cost_trend == 'stable' else 'critical'}">{report.cost_trend.title()}</div>
                <p>Projected monthly: ${report.estimated_monthly_cost:.2f}</p>
            </div>

            <div class="metric-card">
                <h3>💹 Cost per Trade</h3>
                <div class="metric-value">${report.cost_per_trade:.4f}</div>
                <p>Infrastructure cost efficiency</p>
            </div>

            <div class="metric-card">
                <h3>🎯 Potential Savings</h3>
                <div class="metric-value good">${sum(opt.potential_savings for opt in report.optimizations):.2f}</div>
                <p>Available optimizations: {len(report.optimizations)}</p>
            </div>
        </div>

        <div class="metric-card">
            <h3>🏷️ Top Cost Services</h3>
            {''.join([f'<div class="service-item"><span>{service["name"]}</span><span><strong>${service["cost"]:.2f}</strong></span></div>' for service in report.top_cost_services[:5]])}
        </div>

        {'''
        <div class="metric-card">
            <h3>🚨 Cost Alerts</h3>
            {''.join([f'<div class="alert">{alert}</div>' for alert in report.alerts_triggered])}
        </div>
        ''' if report.alerts_triggered else ''}

        <div class="metric-card">
            <h3>💡 Cost Optimization Opportunities</h3>
            {''.join(['''
            <div class="optimization {'high' if opt.priority <= 2 else 'medium' if opt.priority <= 3 else 'low'}">
                <h4>{opt.description}</h4>
                <p><strong>Potential Savings:</strong> ${opt.potential_savings:.2f}/month |
                   <strong>Risk:</strong> {opt.risk_level} |
                   <strong>Effort:</strong> {opt.implementation_effort}</p>
                <p><strong>Action:</strong> {opt.action_required}</p>
            </div>
            ''' for opt in sorted(report.optimizations, key=lambda x: x.priority)[:10]])}
        </div>

        <div class="metric-card">
            <h3>📊 ROI Analysis</h3>
            <div class="metric-row">
                <div>
                    <h4>Trading Performance</h4>
                    <p>Daily P&L: ${report.roi_analysis.get('daily_pnl', 0):.2f}</p>
                    <p>ROI: {report.roi_analysis.get('roi_percentage', 0):.1f}%</p>
                </div>
                <div>
                    <h4>Cost Efficiency</h4>
                    <p>Cost-to-Revenue Ratio: {report.roi_analysis.get('cost_ratio', 0):.1f}%</p>
                    <p>Break-even Point: {report.roi_analysis.get('breakeven_days', 0):.0f} days</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
            """

            # Save dashboard
            dashboard_file = os.path.join(self.optimization_dir, "cost_dashboard.html")
            with open(dashboard_file, "w") as f:
                f.write(dashboard_html)

            logger.info("Cost dashboard generated: {dashboard_file}")
            return dashboard_file

        except Exception as e:
            logger.error("Error generating cost dashboard: {e}")
            return ""

    def run_automated_optimization(self) -> dict[str, Any]:
        """Run full automated cost optimization cycle"""
        logger.info("Running automated cost optimization cycle...")

        try:
            # Analyze costs
            report = self.analyze_current_costs()

            # Filter optimizations by level
            applicable_optimizations = self._filter_optimizations_by_level(
                report.optimizations
            )

            # Implement automated optimizations
            implementation_results = self.implement_optimizations(
                applicable_optimizations, auto_apply=True
            )

            # Generate dashboard
            dashboard_file = self.generate_cost_dashboard()

            # Create summary
            summary = {
                "timestamp": datetime.now().isoformat(),
                "analysis": {
                    "budget_utilization": report.budget_utilization,
                    "cost_trend": report.cost_trend,
                    "alerts_triggered": len(report.alerts_triggered),
                    "optimizations_found": len(report.optimizations),
                },
                "implementation": implementation_results,
                "dashboard": dashboard_file,
                "recommendations": [
                    opt.description
                    for opt in applicable_optimizations
                    if not opt.automation_possible
                ][
                    :5
                ],  # Top 5 manual recommendations
            }

            # Send summary alert
            self._send_optimization_summary(summary)

            return summary

        except Exception as e:
            logger.error("Error in automated optimization: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    # Helper methods
    def _collect_cost_data(self) -> dict[str, Any]:
        """Collect current cost data (simulated)"""
        # In real implementation, this would query GCP Billing API
        return {
            "daily_cost": 8.50,
            "monthly_cost": 165.30,
            "projected_monthly": 185.20,
            "cost_per_trade": 0.0425,
            "services": [
                {"name": "Cloud Run", "cost": 85.20, "percentage": 51.6},
                {"name": "BigQuery", "cost": 42.30, "percentage": 25.6},
                {"name": "Cloud Storage", "cost": 18.90, "percentage": 11.4},
                {"name": "Firestore", "cost": 12.60, "percentage": 7.6},
                {"name": "Pub/Sub", "cost": 6.30, "percentage": 3.8},
            ],
        }

    def _analyze_cost_trend(self, current_costs: dict[str, Any]) -> str:
        """Analyze cost trend"""
        # Simplified trend analysis
        if current_costs["projected_monthly"] > current_costs["monthly_cost"] * 1.1:
            return "increasing"
        elif current_costs["projected_monthly"] < current_costs["monthly_cost"] * 0.9:
            return "decreasing"
        else:
            return "stable"

    def _generate_optimizations(
        self, current_costs: dict[str, Any]
    ) -> list[CostOptimization]:
        """Generate cost optimization recommendations"""
        optimizations = []

        # Cloud Run optimizations
        if any(
            s["name"] == "Cloud Run" and s["cost"] > 50
            for s in current_costs["services"]
        ):
            optimizations.append(
                CostOptimization(
                    id="cloudrun_scaling",
                    category="compute",
                    resource_type="cloud_run",
                    resource_name="trading-service",
                    current_cost=85.20,
                    potential_savings=25.56,
                    risk_level="low",
                    implementation_effort="low",
                    description="Optimize Cloud Run auto-scaling settings",
                    action_required="Reduce max instances from 10 to 5, increase min instances to 1",
                    automation_possible=True,
                    priority=1,
                )
            )

        # BigQuery optimizations
        if any(
            s["name"] == "BigQuery" and s["cost"] > 30
            for s in current_costs["services"]
        ):
            optimizations.append(
                CostOptimization(
                    id="bigquery_partitioning",
                    category="storage",
                    resource_type="bigquery",
                    resource_name="trading_data",
                    current_cost=42.30,
                    potential_savings=12.69,
                    risk_level="medium",
                    implementation_effort="medium",
                    description="Implement table partitioning and clustering",
                    action_required="Add date partitioning to large tables, implement clustering on symbol columns",
                    automation_possible=False,
                    priority=2,
                )
            )

        # Storage optimizations
        optimizations.append(
            CostOptimization(
                id="storage_lifecycle",
                category="storage",
                resource_type="cloud_storage",
                resource_name="data-bucket",
                current_cost=18.90,
                potential_savings=7.56,
                risk_level="low",
                implementation_effort="low",
                description="Implement storage lifecycle policies",
                action_required="Move files older than 30 days to Nearline, 90 days to Coldline",
                automation_possible=True,
                priority=3,
            )
        )

        # Firestore optimizations
        optimizations.append(
            CostOptimization(
                id="firestore_indexing",
                category="database",
                resource_type="firestore",
                resource_name="signals-collection",
                current_cost=12.60,
                potential_savings=3.78,
                risk_level="medium",
                implementation_effort="medium",
                description="Optimize Firestore indexes",
                action_required="Remove unused composite indexes, optimize query patterns",
                automation_possible=False,
                priority=4,
            )
        )

        return optimizations

    def _check_cost_alerts(self, current_costs: dict[str, Any]) -> list[str]:
        """Check for cost-related alerts"""
        alerts = []

        budget_utilization = (current_costs["monthly_cost"] / self.monthly_budget) * 100

        if budget_utilization > 95:
            alerts.append("🔴 CRITICAL: Budget utilization exceeds 95%")
        elif budget_utilization > 80:
            alerts.append("🟡 WARNING: Budget utilization exceeds 80%")

        if current_costs["daily_cost"] > self.cost_thresholds["daily_limit"] * 1.5:
            alerts.append("🔴 CRITICAL: Daily cost anomaly detected (50% above normal)")

        if current_costs["projected_monthly"] > self.monthly_budget:
            alerts.append("🟡 WARNING: Projected monthly cost exceeds budget")

        return alerts

    def _calculate_roi_analysis(
        self, current_costs: dict[str, Any]
    ) -> dict[str, float]:
        """Calculate ROI analysis"""
        # Simplified ROI calculation
        daily_revenue = 50.0  # Placeholder
        daily_cost = current_costs["daily_cost"]

        return {
            "daily_pnl": daily_revenue,
            "daily_cost": daily_cost,
            "roi_percentage": (
                ((daily_revenue - daily_cost) / daily_cost) * 100
                if daily_cost > 0
                else 0
            ),
            "cost_ratio": (
                (daily_cost / daily_revenue) * 100 if daily_revenue > 0 else 100
            ),
            "breakeven_days": (
                abs(daily_cost / daily_revenue) if daily_revenue != 0 else float("in")
            ),
        }

    def _send_cost_alerts(self, report: CostReport):
        """Send cost-related alerts"""
        if report.alerts_triggered:
            for alert in report.alerts_triggered:
                if "CRITICAL" in alert:
                    level = AlertLevel.CRITICAL
                elif "WARNING" in alert:
                    level = AlertLevel.HIGH
                else:
                    level = AlertLevel.MEDIUM

                self.alerting_system.send_alert(
                    self.alerting_system.create_alert(
                        level, AlertType.SYSTEM, "Cost Alert", alert
                    )
                )

    def _filter_optimizations_by_level(
        self, optimizations: list[CostOptimization]
    ) -> list[CostOptimization]:
        """Filter optimizations by optimization level"""
        if self.optimization_level == CostOptimizationLevel.CONSERVATIVE:
            return [
                opt
                for opt in optimizations
                if opt.risk_level == "low" and opt.automation_possible
            ]
        elif self.optimization_level == CostOptimizationLevel.BALANCED:
            return [opt for opt in optimizations if opt.risk_level in ["low", "medium"]]
        else:  # AGGRESSIVE
            return optimizations

    def _apply_optimization(self, optimization: CostOptimization) -> bool:
        """Apply an automated optimization"""
        logger.info("Applying optimization: {optimization.id}")

        try:
            # Simulate optimization implementation
            if optimization.id == "cloudrun_scaling":
                # Would update Cloud Run service configuration
                return True
            elif optimization.id == "storage_lifecycle":
                # Would create storage lifecycle policy
                return True
            else:
                # Manual optimization required
                return False

        except Exception as e:
            logger.error("Error applying optimization {optimization.id}: {e}")
            return False

    def _send_optimization_summary(self, summary: dict[str, Any]):
        """Send optimization summary alert"""
        analysis = summary["analysis"]
        implementation = summary["implementation"]

        message = """Cost Optimization Summary:
Budget Utilization: {analysis['budget_utilization']:.1f}%
Optimizations Applied: {len(implementation['optimizations_applied'])}
Total Savings: ${implementation['total_savings']:.2f}/month
Manual Actions Needed: {len(summary['recommendations'])}
"""

        level = (
            AlertLevel.LOW if analysis["budget_utilization"] < 80 else AlertLevel.MEDIUM
        )

        self.alerting_system.send_alert(
            self.alerting_system.create_alert(
                level, AlertType.SYSTEM, "Cost Optimization Complete", message
            )
        )


def main():
    """Main function for command line usage"""
    print("💰 AI Trading Machine - Automated Cost Optimizer")
    print("=" * 55)

    # Initialize optimizer
    optimizer = AutomatedCostOptimizer(
        monthly_budget=200.0, optimization_level=CostOptimizationLevel.BALANCED
    )

    print("1. 📊 Analyzing current costs...")
    cost_report = optimizer.analyze_current_costs()

    print("\n📈 Cost Analysis Results:")
    print("   Budget Utilization: {cost_report.budget_utilization:.1f}%")
    print("   Current Monthly Cost: ${cost_report.total_cost:.2f}")
    print("   Cost Trend: {cost_report.cost_trend}")
    print("   Optimization Opportunities: {len(cost_report.optimizations)}")

    if cost_report.alerts_triggered:
        print("\n🚨 Alerts Triggered: {len(cost_report.alerts_triggered)}")
        for alert in cost_report.alerts_triggered:
            print("   • {alert}")

    # Show top optimizations
    if cost_report.optimizations:
        print("\n💡 Top Optimization Opportunities:")
        for opt in sorted(cost_report.optimizations, key=lambda x: x.priority)[:3]:
            print("   • {opt.description} (${opt.potential_savings:.2f}/month)")

    # Generate dashboard
    print("\n2. 📋 Generating cost dashboard...")
    dashboard_file = optimizer.generate_cost_dashboard()
    print("   Dashboard saved: {dashboard_file}")

    # Ask about optimization
    response = input("\n3. 🚀 Run automated optimizations? (y/n): ").lower().strip()
    if response == "y":
        print("   Running automated optimizations...")
        results = optimizer.run_automated_optimization()

        if "error" not in results:
            implementation = results["implementation"]
            print("\n✅ Optimization Results:")
            print(
                "   Applied: {len(implementation['optimizations_applied'])} optimizations"
            )
            print("   Potential Savings: ${implementation['total_savings']:.2f}/month")
            print("   Manual Actions: {len(results['recommendations'])}")

            if results["recommendations"]:
                print("\n📝 Manual Actions Required:")
                for rec in results["recommendations"]:
                    print("   • {rec}")
        else:
            print("   ❌ Error: {results['error']}")

    print("\n🎉 Cost optimization analysis complete!")


if __name__ == "__main__":
    main()
