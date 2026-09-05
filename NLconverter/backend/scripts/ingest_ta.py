"""
Ingestion script to scrape the 'ta' library indicators and use Gemini to generate JSON corpus entries.
"""

import sys
from pathlib import Path
import json
import time

# Add the backend directory to sys.path so we can import from strategy_parser
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from strategy_parser.utils import load_dotenv
import ta
import google.generativeai as genai
import os

def generate_json_for_indicator(func_name, docstring):
    """Uses Gemini to convert a raw docstring into our exact JSON schema."""
    
    # We use a fast, cheap model for data extraction
    model = genai.GenerativeModel('gemini-3.1-flash-lite')
    
    prompt = f"""
    You are a financial data extractor. I will give you the docstring of a technical indicator from a python library.
    Convert it into a single JSON object matching this exact schema. Do not output anything other than the JSON object.
    
    Schema requirements:
    - id: A unique string starting with "ind_" (e.g., ind_rsi)
    - type: "indicator"
    - canonical_name: The official full name of the indicator.
    - aliases: An array of 3-5 strings including abbreviations, common typos, and slang (e.g., ["rsi", "relative strength", "rsi indicator"]).
    - maps_to_field: null
    - embedding_text: A dense 1-2 sentence description of what the indicator does based on the docstring.
    - metadata: A dictionary with a "category" field (e.g., "momentum", "trend", "volatility").
    
    Docstring for '{func_name}':
    {docstring[:1500]} # Truncate to save tokens
    """
    
    response = model.generate_content(prompt)
    
    # Clean up the response to just get the JSON
    text = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(text)

def scrape_library():
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

    corpus = []
    output_file = backend_dir / "data" / "ta_corpus.json"
    
    # The 'ta' library exposes submodules for categories: momentum, trend, volatility, volume, others
    categories = ['momentum', 'trend', 'volatility', 'volume', 'others']
    indicators = []
    
    for cat in categories:
        module = getattr(ta, cat)
        # Find all classes or functions that might be indicators (usually capitalized classes in this library)
        funcs = [f for f in dir(module) if not f.startswith('_') and (f.endswith('Indicator') or f[0].isupper())]
        indicators.extend([(cat, f, getattr(module, f)) for f in funcs])
        
    print(f"Found {len(indicators)} potential indicators.")
    
    for i, (cat, name, func) in enumerate(indicators):
        docstring = func.__doc__
        
        if docstring:
            print(f"[{i+1}/{len(indicators)}] Processing: {name} ({cat})...")
            try:
                # Ask Gemini to parse the docstring into our JSON format
                json_obj = generate_json_for_indicator(name, docstring)
                corpus.append(json_obj)
                
                # Sleep briefly to avoid rate limits
                time.sleep(1)
            except Exception as e:
                print(f"Failed to process {name}: {e}")
                
    # Save the result
    with open(output_file, "w") as f:
        json.dump(corpus, f, indent=2)
        
    print(f"Saved {len(corpus)} entries to {output_file}!")

if __name__ == "__main__":
    scrape_library()
