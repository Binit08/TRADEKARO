"""
Script to append timeframe terminology to the knowledge corpus.
"""

import json
from pathlib import Path

def main():
    backend_dir = Path(__file__).resolve().parent.parent
    corpus_path = backend_dir / "data" / "knowledge_corpus.json"
    
    timeframes = [
        {
            "id": "tf_1m",
            "type": "timeframe",
            "canonical_name": "1 Minute Timeframe",
            "aliases": ["1m", "1 minute", "one minute", "M1"],
            "maps_to_field": "timeframe.1m",
            "embedding_text": "1 Minute resolution (1m). Used for ultra short-term scalping and high-frequency intraday trading.",
            "metadata": {"category": "resolution", "resolution": "1m"}
        },
        {
            "id": "tf_3m",
            "type": "timeframe",
            "canonical_name": "3 Minute Timeframe",
            "aliases": ["3m", "3 minute", "three minute", "M3"],
            "maps_to_field": "timeframe.3m",
            "embedding_text": "3 Minute resolution (3m). Used for fast-paced intraday trading.",
            "metadata": {"category": "resolution", "resolution": "3m"}
        },
        {
            "id": "tf_5m",
            "type": "timeframe",
            "canonical_name": "5 Minute Timeframe",
            "aliases": ["5m", "5 minute", "five minute", "M5"],
            "maps_to_field": "timeframe.5m",
            "embedding_text": "5 Minute resolution (5m). A very popular lower timeframe for intraday entries and day trading.",
            "metadata": {"category": "resolution", "resolution": "5m"}
        },
        {
            "id": "tf_15m",
            "type": "timeframe",
            "canonical_name": "15 Minute Timeframe",
            "aliases": ["15m", "15 minute", "fifteen minute", "M15"],
            "maps_to_field": "timeframe.15m",
            "embedding_text": "15 Minute resolution (15m). A standard lower timeframe for intraday trading structure and session analysis.",
            "metadata": {"category": "resolution", "resolution": "15m"}
        },
        {
            "id": "tf_30m",
            "type": "timeframe",
            "canonical_name": "30 Minute Timeframe",
            "aliases": ["30m", "30 minute", "thirty minute", "M30"],
            "maps_to_field": "timeframe.30m",
            "embedding_text": "30 Minute resolution (30m). A bridging timeframe between short-term intraday and hourly macro structures.",
            "metadata": {"category": "resolution", "resolution": "30m"}
        },
        {
            "id": "tf_1h",
            "type": "timeframe",
            "canonical_name": "1 Hour Timeframe",
            "aliases": ["1h", "1 hour", "hourly", "60m", "H1"],
            "maps_to_field": "timeframe.1h",
            "embedding_text": "1 Hour resolution (1h or 60m). A widely used timeframe for intraday trend identification and swing trade entries.",
            "metadata": {"category": "resolution", "resolution": "1h"}
        },
        {
            "id": "tf_2h",
            "type": "timeframe",
            "canonical_name": "2 Hour Timeframe",
            "aliases": ["2h", "2 hour", "120m", "H2"],
            "maps_to_field": "timeframe.2h",
            "embedding_text": "2 Hour resolution (2h or 120m). Used as a slightly higher timeframe filter for intraday trends.",
            "metadata": {"category": "resolution", "resolution": "2h"}
        },
        {
            "id": "tf_4h",
            "type": "timeframe",
            "canonical_name": "4 Hour Timeframe",
            "aliases": ["4h", "4 hour", "240m", "H4"],
            "maps_to_field": "timeframe.4h",
            "embedding_text": "4 Hour resolution (4h or 240m). A highly popular macro timeframe used to dictate overall trend direction for swing trading.",
            "metadata": {"category": "resolution", "resolution": "4h"}
        },
        {
            "id": "tf_1d",
            "type": "timeframe",
            "canonical_name": "Daily Timeframe",
            "aliases": ["1d", "1 day", "daily", "D", "D1", "end of day", "eod"],
            "maps_to_field": "timeframe.1d",
            "embedding_text": "Daily resolution (1D). The most important macro timeframe for determining broad market structure and long-term trend.",
            "metadata": {"category": "resolution", "resolution": "1d"}
        },
        {
            "id": "tf_1w",
            "type": "timeframe",
            "canonical_name": "Weekly Timeframe",
            "aliases": ["1w", "1 week", "weekly", "W", "W1"],
            "maps_to_field": "timeframe.1w",
            "embedding_text": "Weekly resolution (1W). A massive macro timeframe used for long-term investments and identifying major historical support/resistance levels.",
            "metadata": {"category": "resolution", "resolution": "1w"}
        },
        {
            "id": "tf_1M",
            "type": "timeframe",
            "canonical_name": "Monthly Timeframe",
            "aliases": ["1M", "1 month", "monthly", "MN"],
            "maps_to_field": "timeframe.1M",
            "embedding_text": "Monthly resolution (1M). Used almost exclusively for multi-year long-term macro analysis.",
            "metadata": {"category": "resolution", "resolution": "1M"}
        },
        {
            "id": "tf_1y",
            "type": "timeframe",
            "canonical_name": "Yearly Timeframe",
            "aliases": ["1y", "1 year", "yearly", "Y", "YTD"],
            "maps_to_field": "timeframe.1y",
            "embedding_text": "Yearly resolution (1Y). Represents the highest-level macroeconomic view.",
            "metadata": {"category": "resolution", "resolution": "1y"}
        },
        {
            "id": "term_htf",
            "type": "term",
            "canonical_name": "Higher Timeframe",
            "aliases": ["htf", "higher timeframe", "macro timeframe", "higher tf"],
            "maps_to_field": None,
            "embedding_text": "Higher Timeframe (HTF): Refers to a macro chart resolution larger than the current execution timeframe, typically used for filtering trend direction.",
            "metadata": {"category": "timeframe_concept"}
        },
        {
            "id": "term_ltf",
            "type": "term",
            "canonical_name": "Lower Timeframe",
            "aliases": ["ltf", "lower timeframe", "micro timeframe", "lower tf"],
            "maps_to_field": None,
            "embedding_text": "Lower Timeframe (LTF): Refers to a micro chart resolution smaller than the current execution timeframe, typically used for fine-tuning entries.",
            "metadata": {"category": "timeframe_concept"}
        },
        {
            "id": "term_mtf",
            "type": "term",
            "canonical_name": "Multiple Timeframe Analysis",
            "aliases": ["mtf", "multiple timeframe analysis", "multi timeframe"],
            "maps_to_field": None,
            "embedding_text": "Multiple Timeframe Analysis (MTF): The practice of referencing data from a higher timeframe while executing logic on a lower timeframe.",
            "metadata": {"category": "timeframe_concept"}
        },
        {
            "id": "term_intraday",
            "type": "term",
            "canonical_name": "Intraday",
            "aliases": ["intraday", "day trading", "intra-day", "within the day"],
            "maps_to_field": None,
            "embedding_text": "Intraday: Refers broadly to trading activity or timeframes contained within a single trading day (e.g., 1m to 4h).",
            "metadata": {"category": "timeframe_concept"}
        },
        {
            "id": "term_swing",
            "type": "term",
            "canonical_name": "Swing Trading",
            "aliases": ["swing", "swing trading", "swing trader", "multi-day"],
            "maps_to_field": None,
            "embedding_text": "Swing Trading: Refers broadly to trading activity or timeframes spanning multiple days or weeks, typically executing on 1H to 1D charts.",
            "metadata": {"category": "timeframe_concept"}
        },
        {
            "id": "term_scalp",
            "type": "term",
            "canonical_name": "Scalping",
            "aliases": ["scalp", "scalping", "scalper", "ultra short term"],
            "maps_to_field": None,
            "embedding_text": "Scalping: Refers broadly to ultra-short-term trading activity seeking minor price changes, heavily utilizing the 1m to 5m timeframes.",
            "metadata": {"category": "timeframe_concept"}
        }
    ]
    
    with open(corpus_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Append non-duplicates
    seen = {d["id"] for d in data}
    added_count = 0
    for tf in timeframes:
        if tf["id"] not in seen:
            data.append(tf)
            seen.add(tf["id"])
            added_count += 1
            
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"Successfully added {added_count} timeframe concepts to {corpus_path}!")

if __name__ == "__main__":
    main()
