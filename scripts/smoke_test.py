#!/usr/bin/env python3
"""
Minimal end-to-end smoke test for the LangGraph agent.

- Creates (or reuses) a user + conversation
- Asks for weather
- Asks for a stock quote and risk suggestion
- Prints the assistant responses

Usage:
  python scripts/smoke_test.py
  python scripts/smoke_test.py --user ray@example.com --city "Austin,US" --symbol AAPL
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.graph import run_agent_turn


def run_once(user: str, conv_id: Optional[int], text: str) -> tuple[int, str]:
    out = run_agent_turn(user, conv_id, text)
    cid = out["conversation_id"]
    msg = out["assistant"]
    print(f"\n--- Assistant ({cid}) ---\n{msg}\n")
    return cid, msg


def main():
    parser = argparse.ArgumentParser(description="LangGraph agent smoke test")
    parser.add_argument(
        "--user", default="demo@example.com", help="External user id/email"
    )
    parser.add_argument("--city", default="Austin,US", help="City for weather lookups")
    parser.add_argument("--symbol", default="AAPL", help="Stock ticker symbol")
    parser.add_argument(
        "--units",
        default="metric",
        choices=["metric", "imperial"],
        help="Weather units",
    )
    args = parser.parse_args()

    print("🔧 Running smoke test...")
    print(
        "ℹ️  Make sure your .env has OPENWEATHER_API_KEY and ALPHAVANTAGE_API_KEY (or you’ll see helpful errors)."
    )

    # Turn 1: weather
    weather_q = f"What's the weather in {args.city} right now? Use {args.units} units."
    cid, _ = run_once(args.user, None, weather_q)

    # Turn 2: stock + risk hint
    stock_q = f"Check {args.symbol} price and tell me if today looks low/medium/high risk to buy."
    cid, _ = run_once(args.user, cid, stock_q)

    print("✅ Smoke test completed.")
    print(f"Conversation ID: {cid}")
    print(
        "Tip: re-run with the same --user and (optionally) add prompts to continue the same conversation."
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
