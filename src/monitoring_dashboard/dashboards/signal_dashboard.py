#!/usr/bin/env python3
"""
AI Trading Signal Dashboard
===========================

A comprehensive signal generation and monitoring dashboard for manual trading.
This system generates buy/sell signals and provides clear recommendations for manual execution.

Usage:
    python signal_dashboard.py

Features:
- Real-time signal generation
- Risk management recommendations
- Signal confidence scoring
- Manual trading instructions
- Portfolio impact analysis

Author: AI Trading Machine
Licensed by SJ Trading
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv(".env")

from src.ai_trading_machine.ingest.kite_loader import KiteDataLoader
from src.ai_trading_machine.utils.logger import setup_logger

logger = setup_logger(__name__)


class SignalDashboard:
    """Signal generation dashboard for manual trading."""

    def __init__(self):
        """Initialize the signal dashboard."""
        self.kite_loader = None
        self.portfolio_value = 100000  # Default
        self.max_risk_per_trade = 0.02  # 2%
        self.watchlist = [
            "RELIANCE",
            "TCS",
            "HDFCBANK",
            "INFY",
            "ITC",
            "HINDUNILVR",
            "ICICIBANK",
            "KOTAKBANK",
            "BHARTIARTL",
            "SBIN",
            "BAJFINANCE",
            "ASIANPAINT",
            "MARUTI",
            "HCLTECH",
        ]

    def initialize_kite_connection(self) -> bool:
        """Initialize KiteConnect."""
        try:
            logger.info("🔌 Initializing KiteConnect for signal generation...")
            self.kite_loader = KiteDataLoader()

            if self.kite_loader.is_authenticated:
                logger.info("✅ KiteConnect authenticated successfully")
                return True
            else:
                logger.error("❌ KiteConnect authentication failed")
                return False

        except Exception as e:
            logger.error("❌ Failed to initialize KiteConnect: {e}")
            return False

    def setup_portfolio(self):
        """Setup portfolio parameters."""
        print("\n💰 PORTFOLIO SETUP")
        print("=" * 30)

        try:
            portfolio_input = input("Enter your portfolio value (₹) [100000]: ").strip()
            self.portfolio_value = float(portfolio_input) if portfolio_input else 100000

            risk_input = input("Enter max risk per trade (2% = 0.02) [0.02]: ").strip()
            self.max_risk_per_trade = float(risk_input) if risk_input else 0.02

            print("✅ Portfolio: ₹{self.portfolio_value:,.2f}")
            print("✅ Max Risk: {self.max_risk_per_trade*100}% per trade")

        except ValueError:
            print("⚠️ Using default values")
            self.portfolio_value = 100000
            self.max_risk_per_trade = 0.02

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> int:
        """Calculate position size based on risk management."""
        risk_per_share = abs(entry_price - stop_loss)
        max_risk_amount = self.portfolio_value * self.max_risk_per_trade

        if risk_per_share > 0:
            return max(1, int(max_risk_amount / risk_per_share))
        return 1

    def analyze_stock_rsi(self, symbol: str) -> dict[str, Any]:
        """Analyze stock using RSI."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            df = self.kite_loader.fetch_historical_data(
                symbol, start_date, end_date, interval="day"
            )
            if df.empty or len(df) < 15:
                return None

            # Simple RSI calculation
            period = 14
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            current_rsi = rsi.iloc[-1]
            current_price = df["close"].iloc[-1]
            prev_close = df["close"].iloc[-2]
            price_change = (current_price - prev_close) / prev_close * 100

            # Signal logic
            signal = "HOLD"
            confidence = "LOW"
            reason = "No clear signal"

            if current_rsi < 30:
                signal = "BUY"
                confidence = "HIGH" if current_rsi < 25 else "MEDIUM"
                reason = "Oversold (RSI: {current_rsi:.1f})"
            elif current_rsi > 70:
                signal = "SELL"
                confidence = "HIGH" if current_rsi > 75 else "MEDIUM"
                reason = "Overbought (RSI: {current_rsi:.1f})"

            return {
                "symbol": symbol,
                "signal": signal,
                "confidence": confidence,
                "current_price": current_price,
                "rsi": current_rsi,
                "price_change": price_change,
                "reason": reason,
                "volume": df["volume"].iloc[-1],
            }

        except Exception as e:
            logger.error("Error analyzing {symbol}: {e}")
            return None

    def generate_trading_signal(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate detailed trading signal."""
        if not analysis or analysis["signal"] == "HOLD":
            return None

        symbol = analysis["symbol"]
        signal = analysis["signal"]
        current_price = analysis["current_price"]

        # Calculate entry, target, and stop loss
        if signal == "BUY":
            entry_price = current_price
            target_price = current_price * 1.03  # 3% target
            stop_loss = current_price * 0.98  # 2% stop
        else:  # SELL
            entry_price = current_price
            target_price = current_price * 0.97  # 3% target (short)
            stop_loss = current_price * 1.02  # 2% stop (short)

        quantity = self.calculate_position_size(entry_price, stop_loss)
        risk_amount = abs(entry_price - stop_loss) * quantity
        potential_profit = abs(target_price - entry_price) * quantity
        risk_reward = potential_profit / risk_amount if risk_amount > 0 else 0

        return {
            "symbol": symbol,
            "signal": signal,
            "confidence": analysis["confidence"],
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "quantity": quantity,
            "risk_amount": risk_amount,
            "potential_profit": potential_profit,
            "risk_reward_ratio": risk_reward,
            "reason": analysis["reason"],
            "rsi": analysis["rsi"],
            "price_change": analysis["price_change"],
        }

    def scan_watchlist(self) -> list[dict[str, Any]]:
        """Scan watchlist for trading signals."""
        print("\n🔍 SCANNING WATCHLIST ({len(self.watchlist)} stocks)")
        print("=" * 50)

        signals = []
        for i, symbol in enumerate(self.watchlist, 1):
            print("[{i:2d}/{len(self.watchlist)}] Analyzing {symbol}...", end=" ")

            analysis = self.analyze_stock_rsi(symbol)
            if analysis:
                signal = self.generate_trading_signal(analysis)
                if signal and signal["confidence"] in ["MEDIUM", "HIGH"]:
                    signals.append(signal)
                    print("✅ {signal['signal']} signal found!")
                else:
                    print("📊 No signal")
            else:
                print("❌ Error")

            time.sleep(0.5)  # Rate limiting

        return signals

    def display_signals(self, signals: list[dict[str, Any]]):
        """Display trading signals in a formatted way."""
        if not signals:
            print("\n📊 NO TRADING SIGNALS FOUND")
            print("   All stocks in watchlist are in HOLD status")
            return

        print("\n🎯 TRADING SIGNALS FOUND: {len(signals)}")
        print("=" * 80)

        total_risk = 0
        for i, signal in enumerate(signals, 1):
            total_risk += signal["risk_amount"]

            print("\n📈 SIGNAL #{i}: {signal['symbol']}")
            print(
                "   🎯 Action: {signal['signal']} ({signal['confidence']} confidence)"
            )
            print(
                "   💰 Current Price: ₹{signal['current_price']:.2f} ({signal['price_change']:+.1f}%)"
            )
            print("   🎯 Entry: ₹{signal['entry_price']:.2f}")
            print("   🏆 Target: ₹{signal['target_price']:.2f}")
            print("   🛑 Stop Loss: ₹{signal['stop_loss']:.2f}")
            print("   📊 Quantity: {signal['quantity']} shares")
            print("   💸 Risk: ₹{signal['risk_amount']:.2f}")
            print("   💰 Potential Profit: ₹{signal['potential_profit']:.2f}")
            print("   📈 Risk:Reward = 1:{signal['risk_reward_ratio']:.2f}")
            print("   🔍 Reason: {signal['reason']}")
            print("   📊 RSI: {signal['rsi']:.1f}")

        portfolio_risk_pct = (total_risk / self.portfolio_value) * 100

        print("\n💰 PORTFOLIO IMPACT:")
        print(
            "   Total Risk: ₹{total_risk:,.2f} ({portfolio_risk_pct:.1f}% of portfolio)"
        )
        print(
            "   Signals within risk limits: {'✅ Yes' if portfolio_risk_pct <= 10 else '⚠️ No - Consider reducing position sizes'}"
        )

    def save_signals(self, signals: list[dict[str, Any]]) -> str:
        """Save signals to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "signals/trading_signals_{timestamp}.json"

        os.makedirs("signals", exist_ok=True)

        data = {
            "generated_at": datetime.now().isoformat(),
            "portfolio_value": self.portfolio_value,
            "max_risk_per_trade": self.max_risk_per_trade,
            "watchlist": self.watchlist,
            "signals_count": len(signals),
            "signals": signals,
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        return filename

    def print_trading_instructions(self, signals: list[dict[str, Any]]):
        """Print manual trading instructions."""
        if not signals:
            return

        print("\n📋 MANUAL TRADING INSTRUCTIONS")
        print("=" * 50)
        print("1. Open your trading app (Zerodha Kite, etc.)")
        print("2. For each signal below:")
        print("   - Place the order at or near the entry price")
        print("   - Set stop-loss orders immediately")
        print("   - Set target price alerts")
        print("3. Monitor positions regularly")
        print("4. Exit at target or stop-loss as planned")

        for i, signal in enumerate(signals, 1):
            print("\n🔵 Order #{i}: {signal['symbol']}")
            if signal["signal"] == "BUY":
                print("   📱 Action: BUY {signal['quantity']} shares")
                print("   💰 At price: ₹{signal['entry_price']:.2f} or lower")
                print("   🛑 Set SL at: ₹{signal['stop_loss']:.2f}")
                print("   🎯 Set target at: ₹{signal['target_price']:.2f}")
            else:
                print("   📱 Action: SELL {signal['quantity']} shares")
                print("   💰 At price: ₹{signal['entry_price']:.2f} or higher")
                print("   🛑 Set SL at: ₹{signal['stop_loss']:.2f}")
                print("   🎯 Set target at: ₹{signal['target_price']:.2f}")

    def run_dashboard(self):
        """Run the main signal dashboard."""
        print("🚀 AI TRADING SIGNAL DASHBOARD")
        print("=" * 50)
        print("📊 Manual Trading Signal Generator")
        print("⚠️  For educational and manual trading purposes only")

        # Setup
        if not self.initialize_kite_connection():
            return

        self.setup_portfolio()

        # Main loop
        while True:
            print(
                "\n📅 Signal Generation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            try:
                # Scan for signals
                signals = self.scan_watchlist()

                # Display results
                self.display_signals(signals)

                if signals:
                    # Save signals
                    filename = self.save_signals(signals)
                    print("\n💾 Signals saved to: {filename}")

                    # Print trading instructions
                    self.print_trading_instructions(signals)

                print("\n⏰ Next scan in 5 minutes...")
                print("   Press Ctrl+C to exit")

                # Wait for next scan
                time.sleep(300)  # 5 minutes

            except KeyboardInterrupt:
                print("\n🛑 Dashboard stopped by user")
                break
            except Exception as e:
                logger.error("❌ Error in dashboard: {e}")
                print("❌ Error: {e}")
                print("Retrying in 1 minute...")
                time.sleep(60)


def main():
    """Main function."""
    dashboard = SignalDashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()
