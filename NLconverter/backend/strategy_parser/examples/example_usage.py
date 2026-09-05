#!/usr/bin/env python3
"""Example usage of the StrategyParser."""

import json
import sys
from pathlib import Path

from backend.strategy_parser import StrategyParser, load_dotenv

# Load environment variables
load_dotenv(".env")


def main():
    """Run strategy parser example."""
    # Example trading strategies to parse
    examples = [
        {
            "name": "SMA Crossover",
            "strategy": "Buy when 20-day SMA crosses above 50-day SMA. Sell when price falls below 20-day SMA."
        },
        {
            "name": "RSI Mean Reversion",
            "strategy": "Buy when RSI drops below 30 on daily. Sell when RSI rises above 70. Use 10% stop loss."
        },
        {
            "name": "MACD Signal Cross",
            "strategy": "Enter long when MACD line crosses above signal line. Exit at take profit of 2:1 risk/reward ratio."
        }
    ]

    # Initialize parser
    try:
        parser = StrategyParser()
        print("✓ StrategyParser initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize parser: {e}")
        return

    # Parse each strategy
    for example in examples:
        print(f"Parsing: {example['name']}")
        print(f"Strategy: {example['strategy']}")
        print("-" * 80)

        try:
            result = parser.parse_strategy(example['strategy'])
            
            print("✓ Successfully parsed")

            
            # Print full JSON
            print("\nFull Canonical JSON:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"✗ Failed to parse: {e}")
        
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
