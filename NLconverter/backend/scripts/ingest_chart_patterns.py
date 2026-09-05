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

    chart_patterns = [
        {
            "id": "cp_head_and_shoulders",
            "type": "chart_pattern",
            "canonical_name": "Head and Shoulders",
            "aliases": ["h&s", "head & shoulders"],
            "maps_to_field": "conditions",
            "embedding_text": "Head and Shoulders: A bearish reversal chart pattern featuring a peak (shoulder), a higher peak (head), and a lower peak (shoulder) sharing a common neckline support.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bearish"}
        },
        {
            "id": "cp_inverse_head_and_shoulders",
            "type": "chart_pattern",
            "canonical_name": "Inverse Head and Shoulders",
            "aliases": ["inverse h&s", "inverted head and shoulders"],
            "maps_to_field": "conditions",
            "embedding_text": "Inverse Head and Shoulders: A bullish reversal chart pattern featuring three troughs, with the middle being the lowest, signaling a potential upside breakout above the neckline.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bullish"}
        },
        {
            "id": "cp_double_top",
            "type": "chart_pattern",
            "canonical_name": "Double Top",
            "aliases": ["double tops"],
            "maps_to_field": "conditions",
            "embedding_text": "Double Top: A bearish reversal chart pattern characterized by two peaks at approximately the same price level, indicating resistance and a potential trend reversal.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bearish"}
        },
        {
            "id": "cp_double_bottom",
            "type": "chart_pattern",
            "canonical_name": "Double Bottom",
            "aliases": ["double bottoms"],
            "maps_to_field": "conditions",
            "embedding_text": "Double Bottom: A bullish reversal chart pattern featuring two distinct lows at roughly the same level, signaling strong support and a potential upward reversal.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bullish"}
        },
        {
            "id": "cp_triple_top",
            "type": "chart_pattern",
            "canonical_name": "Triple Top",
            "aliases": ["triple tops"],
            "maps_to_field": "conditions",
            "embedding_text": "Triple Top: A bearish reversal chart pattern with three peaks at the same resistance level, indicating exhaustion of buying pressure.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bearish"}
        },
        {
            "id": "cp_triple_bottom",
            "type": "chart_pattern",
            "canonical_name": "Triple Bottom",
            "aliases": ["triple bottoms"],
            "maps_to_field": "conditions",
            "embedding_text": "Triple Bottom: A bullish reversal chart pattern with three lows at the same support level, showing strong buying interest preventing further decline.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bullish"}
        },
        {
            "id": "cp_rounding_bottom",
            "type": "chart_pattern",
            "canonical_name": "Rounding Bottom",
            "aliases": ["saucer bottom", "rounding saucer"],
            "maps_to_field": "conditions",
            "embedding_text": "Rounding Bottom: A bullish reversal chart pattern (saucer) that represents a gradual shift in market sentiment from bearish to bullish over a long period.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bullish"}
        },
        {
            "id": "cp_rounding_top",
            "type": "chart_pattern",
            "canonical_name": "Rounding Top",
            "aliases": ["saucer top"],
            "maps_to_field": "conditions",
            "embedding_text": "Rounding Top: A bearish reversal chart pattern indicating a gradual shift from bullish to bearish sentiment forming a rounded peak.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bearish"}
        },
        {
            "id": "cp_ascending_triangle",
            "type": "chart_pattern",
            "canonical_name": "Ascending Triangle",
            "aliases": ["ascending triangles"],
            "maps_to_field": "conditions",
            "embedding_text": "Ascending Triangle: A bullish continuation chart pattern defined by a flat upper resistance line and a rising lower support line.",
            "metadata": {"pattern_type": "continuation", "sentiment": "bullish"}
        },
        {
            "id": "cp_descending_triangle",
            "type": "chart_pattern",
            "canonical_name": "Descending Triangle",
            "aliases": ["descending triangles"],
            "maps_to_field": "conditions",
            "embedding_text": "Descending Triangle: A bearish continuation chart pattern defined by a flat lower support line and a falling upper resistance line.",
            "metadata": {"pattern_type": "continuation", "sentiment": "bearish"}
        },
        {
            "id": "cp_symmetrical_triangle",
            "type": "chart_pattern",
            "canonical_name": "Symmetrical Triangle",
            "aliases": ["symmetrical triangles"],
            "maps_to_field": "conditions",
            "embedding_text": "Symmetrical Triangle: A continuation chart pattern formed by converging trendlines, indicating consolidation before a breakout in the direction of the prior trend.",
            "metadata": {"pattern_type": "continuation", "sentiment": "neutral"}
        },
        {
            "id": "cp_bull_flag",
            "type": "chart_pattern",
            "canonical_name": "Bull Flag",
            "aliases": ["bull flags", "bullish flag"],
            "maps_to_field": "conditions",
            "embedding_text": "Bull Flag: A bullish continuation chart pattern consisting of a strong upward price movement (flagpole) followed by a slight downward consolidation in a parallel channel.",
            "metadata": {"pattern_type": "continuation", "sentiment": "bullish"}
        },
        {
            "id": "cp_bear_flag",
            "type": "chart_pattern",
            "canonical_name": "Bear Flag",
            "aliases": ["bear flags", "bearish flag"],
            "maps_to_field": "conditions",
            "embedding_text": "Bear Flag: A bearish continuation chart pattern featuring a sharp downward drop followed by a slight upward consolidation in a parallel channel.",
            "metadata": {"pattern_type": "continuation", "sentiment": "bearish"}
        },
        {
            "id": "cp_bull_pennant",
            "type": "chart_pattern",
            "canonical_name": "Bull Pennant",
            "aliases": ["bullish pennant"],
            "maps_to_field": "conditions",
            "embedding_text": "Bull Pennant: A bullish continuation chart pattern similar to a flag, but the consolidation phase forms a small symmetrical triangle rather than a channel.",
            "metadata": {"pattern_type": "continuation", "sentiment": "bullish"}
        },
        {
            "id": "cp_bear_pennant",
            "type": "chart_pattern",
            "canonical_name": "Bear Pennant",
            "aliases": ["bearish pennant"],
            "maps_to_field": "conditions",
            "embedding_text": "Bear Pennant: A bearish continuation chart pattern where a sharp drop is followed by a small symmetrical triangle consolidation before further downside.",
            "metadata": {"pattern_type": "continuation", "sentiment": "bearish"}
        },
        {
            "id": "cp_rising_wedge",
            "type": "chart_pattern",
            "canonical_name": "Rising Wedge",
            "aliases": ["ascending wedge"],
            "maps_to_field": "conditions",
            "embedding_text": "Rising Wedge: A bearish chart pattern (reversal or continuation) characterized by converging upward-sloping trendlines, indicating weakening upward momentum.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bearish"}
        },
        {
            "id": "cp_falling_wedge",
            "type": "chart_pattern",
            "canonical_name": "Falling Wedge",
            "aliases": ["descending wedge"],
            "maps_to_field": "conditions",
            "embedding_text": "Falling Wedge: A bullish chart pattern (reversal or continuation) defined by converging downward-sloping trendlines, signaling diminishing selling pressure.",
            "metadata": {"pattern_type": "reversal", "sentiment": "bullish"}
        },
        {
            "id": "cp_cup_and_handle",
            "type": "chart_pattern",
            "canonical_name": "Cup and Handle",
            "aliases": ["cup with handle"],
            "maps_to_field": "conditions",
            "embedding_text": "Cup and Handle: A bullish continuation chart pattern resembling a teacup, where a rounded bottom (cup) is followed by a slight downward consolidation (handle) before a breakout.",
            "metadata": {"pattern_type": "continuation", "sentiment": "bullish"}
        },
        {
            "id": "cp_rectangle_channel",
            "type": "chart_pattern",
            "canonical_name": "Rectangle Channel",
            "aliases": ["price channel", "horizontal channel"],
            "maps_to_field": "conditions",
            "embedding_text": "Rectangle Channel: A consolidation chart pattern where price bounces between parallel support and resistance lines before a breakout.",
            "metadata": {"pattern_type": "continuation", "sentiment": "neutral"}
        }
    ]

    # Add only if not already present
    existing_ids = {doc["id"] for doc in corpus}
    added_count = 0

    for pattern in chart_patterns:
        if pattern["id"] not in existing_ids:
            corpus.append(pattern)
            added_count += 1
            print(f"Added pattern: {pattern['canonical_name']}")
        else:
            print(f"Pattern {pattern['canonical_name']} already exists. Skipping.")

    print(f"\nAdded {added_count} new chart patterns.")
    print(f"Total documents in corpus: {len(corpus)}")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)

if __name__ == "__main__":
    main()
