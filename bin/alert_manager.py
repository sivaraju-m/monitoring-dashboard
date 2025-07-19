#!/usr/bin/env python3
"""
Alert Manager for Monitoring Dashboard
Manages real-time alerting and notifications
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from monitoring_dashboard.alerts.alert_manager import AlertManager
from monitoring_dashboard.monitoring.metrics_collector import MetricsCollector
from monitoring_dashboard.utils.logger import setup_logger

class AlertManagerService:
    """Alert manager service for continuous monitoring"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.alert_manager = AlertManager()
        self.metrics_collector = MetricsCollector()
        
        self.running = False
        
    async def start(self):
        """Start the alert manager service"""
        self.logger.info("Starting Alert Manager Service")
        self.running = True
        
        try:
            while self.running:
                await self._check_alerts()
                await asyncio.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Alert manager error: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the alert manager service"""
        self.logger.info("Stopping Alert Manager Service")
        self.running = False
    
    async def _check_alerts(self):
        """Check system metrics against alert rules"""
        try:
            # Collect current metrics
            metrics = await self.metrics_collector.get_current_metrics()
            
            # Check for alert conditions
            new_alerts = await self.alert_manager.check_system_alerts(metrics)
            
            if new_alerts:
                self.logger.info(f"Generated {len(new_alerts)} new alerts")
                
                for alert in new_alerts:
                    self.logger.warning(f"Alert: {alert['type']} - {alert['message']}")
            
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
    
    async def create_test_alert(self):
        """Create a test alert for verification"""
        await self.alert_manager.create_alert(
            alert_type="Test Alert",
            severity="low",
            message="This is a test alert from the alert manager",
            source="test_service"
        )
        self.logger.info("Test alert created successfully")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Trading Machine Alert Manager")
    parser.add_argument("--test", action="store_true", help="Create a test alert and exit")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create alert manager service
    service = AlertManagerService()
    
    if args.test:
        # Create test alert and exit
        await service.create_test_alert()
        print("Test alert created successfully")
        return
    
    # Start the service
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
