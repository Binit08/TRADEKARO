"""Standalone test script to verify the RAG system end-to-end."""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from strategy_parser.rag import get_rag_context
from strategy_parser.utils import load_dotenv

load_dotenv()

def main():
    print("========================================")
    print("Testing RAG Module in Isolation")
    print("========================================")
    
    test_prompts = [
        # Should typo-match "supertrenda" to "Supertrend" and retrieve Supertrend context
        "buy on the brakout of a cop and handl",
        "if the rsi is ovrbogt and macdee is crosing down",
        "execcute a shrtt stardle when implied voltlity drops",
        "sqaure of my postion if the suport level is brokn",
        "byu banknifty cee optin on wekly expiryy"
    ]
    
    for prompt in test_prompts:
        print(f"\n--- Prompt: '{prompt}' ---")
        try:
            context, is_confident = get_rag_context(prompt)
            print(f"Confidence: {is_confident}")
            if context:
                print("Context:")
                print(context)
            else:
                print("No context retrieved.")
        except Exception as e:
            print(f"Error testing RAG: {e}")

if __name__ == "__main__":
    main()
