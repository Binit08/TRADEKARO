"""
Script to generate TA-Lib indicators and patterns corpus using Gemini, processed individually.
"""

import os
import json
import time
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from strategy_parser.utils import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

def fetch_single_item(item_name, category_type):
    model = genai.GenerativeModel('gemini-3.1-flash-lite')
    
    prompt = f"""
    You are a financial data extractor. Generate a single JSON `KnowledgeDoc` object for the following TA-Lib item: '{item_name}'.
    
    Schema:
    - id: A unique string starting with "ind_" (e.g., ind_cdl3blackcrows)
    - type: "indicator" or "pattern"
    - canonical_name: The official full name of the item.
    - aliases: An array of 3-5 strings including abbreviations, common typos, and slang.
    - maps_to_field: null
    - embedding_text: A dense 1-2 sentence description of what the item is and what it signals.
    - metadata: A dictionary with a "category" field ("pattern", "momentum", "trend", etc.).
    
    Output ONLY a valid JSON object. No markdown blocks, no explanations.
    """
    
    # Retry logic
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            if attempt == 2:
                print(f"Failed to generate {item_name}: {e}")
                return None
            time.sleep(2)
            
def main():
    patterns = [
        "Two Crows", "Three Black Crows", "Three Inside Up/Down", "Three-Line Strike",
        "Three Outside Up/Down", "Three Stars In The South", "Three Advancing White Soldiers",
        "Abandoned Baby", "Advance Block", "Belt-hold", "Breakaway", "Closing Marubozu",
        "Concealing Baby Swallow", "Counterattack", "Dark Cloud Cover", "Doji", "Doji Star",
        "Dragonfly Doji", "Engulfing Pattern", "Evening Doji Star", "Evening Star",
        "Up/Down-gap side-by-side white lines", "Gravestone Doji", "Hammer", "Hanging Man",
        "Harami Pattern", "Harami Cross Pattern", "High-Wave Candle", "Hikkake Pattern",
        "Modified Hikkake Pattern", "Homing Pigeon", "Identical Three Crows", "In-Neck Pattern",
        "Inverted Hammer", "Kicking", "Kicking - bull/bear determined by the longer marubozu",
        "Ladder Bottom", "Long Legged Doji", "Long Line Candle", "Marubozu", "Matching Low",
        "Mat Hold", "Morning Doji Star", "Morning Star", "On-Neck Pattern", "Piercing Pattern",
        "Rickshaw Man", "Rising/Falling Three Methods", "Separating Lines", "Shooting Star",
        "Short Line Candle", "Spinning Top", "Stalled Pattern", "Stick Sandwich", "Takuri (Dragonfly Doji with very long lower shadow)",
        "Tasuki Gap", "Thrusting Pattern", "Tristar Pattern", "Unique 3 River", "Upside Gap Two Crows",
        "Upside/Downside Gap Three Methods"
    ]
    
    talib_indicators = [
        "Double Exponential Moving Average (DEMA)", "Triple Exponential Moving Average (TEMA)",
        "Triangular Moving Average (TRIMA)", "MESA Adaptive Moving Average (MAMA)",
        "Triple Exponential Moving Average (T3)", "Absolute Price Oscillator (APO)",
        "Chande Momentum Oscillator (CMO)", "Directional Movement Index (DX)",
        "Minus Directional Indicator (MINUS_DI)", "Minus Directional Movement (MINUS_DM)",
        "Plus Directional Indicator (PLUS_DI)", "Plus Directional Movement (PLUS_DM)",
        "Hilbert Transform - Dominant Cycle Period", "Hilbert Transform - Dominant Cycle Phase",
        "Hilbert Transform - Phasor Components", "Hilbert Transform - SineWave",
        "Hilbert Transform - Trend vs Cycle Mode"
    ]
    
    all_items = patterns + talib_indicators
    corpus = []
    output_file = backend_dir / "data" / "talib_corpus.json"
    
    print(f"Starting extraction of {len(all_items)} items...")
    for i, item in enumerate(all_items):
        print(f"[{i+1}/{len(all_items)}] Processing: {item}")
        cat_type = "pattern" if item in patterns else "indicator"
        result = fetch_single_item(item, cat_type)
        if result:
            corpus.append(result)
        time.sleep(1) # rate limiting
            
        # Incremental save just in case
        if i % 10 == 0:
            with open(output_file, "w") as f:
                json.dump(corpus, f, indent=2)
                
    # Final save
    with open(output_file, "w") as f:
        json.dump(corpus, f, indent=2)
        
    print(f"Saved {len(corpus)} items to {output_file}!")

if __name__ == "__main__":
    main()
