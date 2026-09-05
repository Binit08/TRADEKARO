import json
from pathlib import Path

def main():
    backend_dir = Path(__file__).resolve().parent.parent
    corpus_path = backend_dir / "data" / "knowledge_corpus.json"

    # Load existing corpus
    if corpus_path.exists():
        with open(corpus_path, "r", encoding="utf-8") as f:
            corpus = json.load(f)
    else:
        corpus = []
        
    print(f"Loaded {len(corpus)} existing documents.")

    price_action_terms = [
        # Core Levels
        {
            "id": "pa_support",
            "type": "price_action",
            "canonical_name": "Support",
            "aliases": ["support", "support level", "floor"],
            "maps_to_field": "conditions",
            "embedding_text": "Support: A historical price level where a downtrend tends to pause or reverse due to a heavy concentration of demand (buying interest).",
            "metadata": {"category": "structure", "type": "SUPPORT"}
        },
        {
            "id": "pa_resistance",
            "type": "price_action",
            "canonical_name": "Resistance",
            "aliases": ["resistance", "resistance level", "ceiling"],
            "maps_to_field": "conditions",
            "embedding_text": "Resistance: A historical price level where an uptrend tends to pause or reverse due to a heavy concentration of supply (selling pressure).",
            "metadata": {"category": "structure", "type": "RESISTANCE"}
        },
        {
            "id": "pa_supply_zone",
            "type": "price_action",
            "canonical_name": "Supply Zone",
            "aliases": ["supply zone", "supply area", "distribution zone"],
            "maps_to_field": "conditions",
            "embedding_text": "Supply Zone: A broader structural area on the chart where selling pressure previously overwhelmed buying pressure, often associated with institutional selling.",
            "metadata": {"category": "structure", "type": "SUPPLY"}
        },
        {
            "id": "pa_demand_zone",
            "type": "price_action",
            "canonical_name": "Demand Zone",
            "aliases": ["demand zone", "demand area", "accumulation zone"],
            "maps_to_field": "conditions",
            "embedding_text": "Demand Zone: A broader structural area on the chart where buying pressure previously overwhelmed selling pressure, often associated with institutional accumulation.",
            "metadata": {"category": "structure", "type": "DEMAND"}
        },
        {
            "id": "pa_pivot_point",
            "type": "price_action",
            "canonical_name": "Pivot Point",
            "aliases": ["pivot point", "pivots", "pivot"],
            "maps_to_field": "conditions",
            "embedding_text": "Pivot Point: Key price levels mathematically derived from the previous period's high, low, and close prices, used to project intraday support and resistance.",
            "metadata": {"category": "structure", "type": "PIVOT"}
        },

        # Trend Structure
        {
            "id": "pa_higher_high_low",
            "type": "price_action",
            "canonical_name": "Higher High / Higher Low",
            "aliases": ["higher high", "higher low", "hh", "hl", "uptrend structure"],
            "maps_to_field": "trend_identification",
            "embedding_text": "Higher High (HH) & Higher Low (HL): The fundamental structural definition of an active Uptrend, where each successive price peak is higher than the last, and each trough is higher than the last.",
            "metadata": {"category": "trend", "type": "UPTREND_STRUCTURE"}
        },
        {
            "id": "pa_lower_high_low",
            "type": "price_action",
            "canonical_name": "Lower High / Lower Low",
            "aliases": ["lower high", "lower low", "lh", "ll", "downtrend structure"],
            "maps_to_field": "trend_identification",
            "embedding_text": "Lower High (LH) & Lower Low (LL): The fundamental structural definition of an active Downtrend, where each successive price peak and trough is lower than the previous one.",
            "metadata": {"category": "trend", "type": "DOWNTREND_STRUCTURE"}
        },
        {
            "id": "pa_trendline",
            "type": "price_action",
            "canonical_name": "Trendline",
            "aliases": ["trend line", "trendline"],
            "maps_to_field": "conditions",
            "embedding_text": "Trendline: A diagonal line connecting successive pivot highs or pivot lows, visually representing the prevailing momentum and dynamic support/resistance of an asset.",
            "metadata": {"category": "trend", "type": "TRENDLINE"}
        },
        {
            "id": "pa_consolidation",
            "type": "price_action",
            "canonical_name": "Consolidation",
            "aliases": ["consolidation", "range bound", "sideways", "choppy"],
            "maps_to_field": "trend_identification",
            "embedding_text": "Consolidation (Range-bound): A market phase where price oscillates sideways between defined support and resistance boundaries with no clear directional trend.",
            "metadata": {"category": "trend", "type": "CONSOLIDATION"}
        },
        {
            "id": "pa_choppy",
            "type": "price_action",
            "canonical_name": "Choppy Market",
            "aliases": ["choppy market", "whipsaw", "erratic market"],
            "maps_to_field": "trend_identification",
            "embedding_text": "Choppy Market (Whipsaw): A highly volatile, erratic market environment lacking clear directional momentum, notorious for triggering false signals and stop-losses.",
            "metadata": {"category": "trend", "type": "CHOPPY"}
        },

        # Breakouts & Mechanics
        {
            "id": "pa_breakout",
            "type": "price_action",
            "canonical_name": "Breakout",
            "aliases": ["breakout", "breaking out"],
            "maps_to_field": "conditions",
            "embedding_text": "Breakout: When price decisively moves above a resistance level or out of a consolidation pattern, typically on increased volume, signaling the start of upward momentum.",
            "metadata": {"category": "momentum", "type": "BREAKOUT"}
        },
        {
            "id": "pa_breakdown",
            "type": "price_action",
            "canonical_name": "Breakdown",
            "aliases": ["breakdown", "breaking down"],
            "maps_to_field": "conditions",
            "embedding_text": "Breakdown: When price decisively moves below a support level, signaling the start or continuation of downward momentum.",
            "metadata": {"category": "momentum", "type": "BREAKDOWN"}
        },
        {
            "id": "pa_pullback",
            "type": "price_action",
            "canonical_name": "Pullback",
            "aliases": ["pullback", "retracement", "dip", "pull back"],
            "maps_to_field": "conditions",
            "embedding_text": "Pullback (Retracement / Dip): A temporary, counter-trend price reversal occurring within the context of a larger prevailing trend, often used as an entry opportunity.",
            "metadata": {"category": "momentum", "type": "PULLBACK"}
        },
        {
            "id": "pa_throwback",
            "type": "price_action",
            "canonical_name": "Throwback",
            "aliases": ["throwback", "retest support"],
            "maps_to_field": "conditions",
            "embedding_text": "Throwback (Retest): Occurs immediately after a breakout when the price temporarily drops back down to 'retest' the prior resistance level (which now acts as new support) before continuing upward.",
            "metadata": {"category": "momentum", "type": "THROWBACK"}
        },
        {
            "id": "pa_pullup",
            "type": "price_action",
            "canonical_name": "Pullup",
            "aliases": ["pullup", "retest resistance"],
            "maps_to_field": "conditions",
            "embedding_text": "Pullup (Retest): Occurs immediately after a breakdown when the price temporarily rallies up to 'retest' the prior support level (which now acts as new resistance) before continuing downward.",
            "metadata": {"category": "momentum", "type": "PULLUP"}
        },
        {
            "id": "pa_gap_up",
            "type": "price_action",
            "canonical_name": "Gap Up",
            "aliases": ["gap up", "gapping up"],
            "maps_to_field": "conditions",
            "embedding_text": "Gap Up: When an asset opens at a price significantly higher than its previous session's close, leaving a void on the chart with no trading activity in between.",
            "metadata": {"category": "mechanics", "type": "GAP_UP"}
        },
        {
            "id": "pa_gap_down",
            "type": "price_action",
            "canonical_name": "Gap Down",
            "aliases": ["gap down", "gapping down"],
            "maps_to_field": "conditions",
            "embedding_text": "Gap Down: When an asset opens at a price significantly lower than its previous session's close.",
            "metadata": {"category": "mechanics", "type": "GAP_DOWN"}
        }
    ]

    # Add only if not already present
    existing_ids = {doc["id"] for doc in corpus}
    added_count = 0

    for term in price_action_terms:
        if term["id"] not in existing_ids:
            corpus.append(term)
            added_count += 1
            print(f"Added term: {term['canonical_name']}")
        else:
            print(f"Term {term['canonical_name']} already exists. Skipping.")

    print(f"\nAdded {added_count} new price action terms.")
    print(f"Total documents in corpus: {len(corpus)}")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)

if __name__ == "__main__":
    main()
