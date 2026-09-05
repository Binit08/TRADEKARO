#!/usr/bin/env python3
"""
Strategy file to send natural language prompt to LLM with system prompt and schema.
This demonstrates the complete flow from NL input → LLM → parsed JSON output.
"""

import json
from backend.strategy_parser import StrategyParser, load_dotenv

# Load environment variables (API key from .env)
load_dotenv(".env")


def send_strategy_to_llm(strategy_text: str) -> dict:
    """
    Send natural language strategy to LLM with system prompt and schema.
    
    Args:
        strategy_text: Natural language strategy description
        
    Returns:
        Parsed strategy as JSON dictionary
    """
    # Initialize parser (loads system prompt + schema automatically)
    parser = StrategyParser()
    
    print("=" * 80)
    print("SENDING TO LLM")
    print("=" * 80)
    print(f"\n📝 Natural Language Prompt:\n{strategy_text}\n")
    
    # Send to LLM with system prompt and schema
    result = parser.parse_strategy(strategy_text)
    
    print("\n✓ Response from LLM (parsed to JSON):\n")
    print(json.dumps(result, indent=2))
    
    return result


def main():
    """Main function - write your strategy here."""
    
    # ============================================
    # WRITE YOUR NATURAL LANGUAGE STRATEGY HERE ↓
    # ============================================
    my_strategy = """
    Buy signal:
    - When RSI drops below 30 on daily timeframe
    - AND MACD histogram crosses above zero
    - Entry position size: 1% of portfolio
    
    Sell signal:
    - When RSI rises above 70
    - OR price hits 2% stop loss
    - Take profit at 3:1 risk/reward ratio
    """
    # ============================================
    
    try:
        result = send_strategy_to_llm(my_strategy)
        
        # Save to file (optional)
        with open("parsed_strategy_output.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\n✓ Saved to parsed_strategy_output.json")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
