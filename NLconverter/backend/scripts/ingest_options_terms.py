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

    options_terms = [
        # Fundamentals
        {
            "id": "opt_call",
            "type": "derivatives_term",
            "canonical_name": "Call Option",
            "aliases": ["call", "calls", "call option"],
            "maps_to_field": "instrument_type",
            "embedding_text": "Call Option (Call): A derivative contract giving the buyer the right, but not the obligation, to buy the underlying asset at a specified strike price. Maps to instrument_type='CALL'.",
            "metadata": {"category": "derivatives", "type": "CALL"}
        },
        {
            "id": "opt_put",
            "type": "derivatives_term",
            "canonical_name": "Put Option",
            "aliases": ["put", "puts", "put option"],
            "maps_to_field": "instrument_type",
            "embedding_text": "Put Option (Put): A derivative contract giving the buyer the right, but not the obligation, to sell the underlying asset at a specified strike price. Maps to instrument_type='PUT'.",
            "metadata": {"category": "derivatives", "type": "PUT"}
        },
        {
            "id": "opt_strike_price",
            "type": "derivatives_term",
            "canonical_name": "Strike Price",
            "aliases": ["strike", "strikes"],
            "maps_to_field": "strike_selection",
            "embedding_text": "Strike Price: The pre-determined price at which the underlying asset can be bought (call) or sold (put) when exercising the contract.",
            "metadata": {"category": "derivatives", "type": "STRIKE"}
        },
        {
            "id": "opt_expiration",
            "type": "derivatives_term",
            "canonical_name": "Expiration Date",
            "aliases": ["expiry", "expiration"],
            "maps_to_field": "expiry",
            "embedding_text": "Expiration Date: The exact date and time when an option contract becomes void and ceases to exist.",
            "metadata": {"category": "derivatives", "type": "EXPIRATION"}
        },
        {
            "id": "opt_premium",
            "type": "derivatives_term",
            "canonical_name": "Option Premium",
            "aliases": ["premium", "option price"],
            "maps_to_field": "conditions",
            "embedding_text": "Option Premium: The current market price of an option contract paid by the buyer to the seller.",
            "metadata": {"category": "derivatives", "type": "PREMIUM"}
        },
        {
            "id": "opt_underlying",
            "type": "derivatives_term",
            "canonical_name": "Underlying Asset",
            "aliases": ["underlying", "spot asset"],
            "maps_to_field": "asset",
            "embedding_text": "Underlying Asset: The financial instrument (stock, index, commodity) on which the derivative's value is derived.",
            "metadata": {"category": "derivatives", "type": "UNDERLYING"}
        },
        
        # Moneyness
        {
            "id": "opt_itm",
            "type": "derivatives_term",
            "canonical_name": "In-The-Money",
            "aliases": ["itm", "in the money"],
            "maps_to_field": "strike_selection",
            "embedding_text": "In-The-Money (ITM): An option that possesses intrinsic value (e.g., a Call where the strike is below the current market price).",
            "metadata": {"category": "moneyness", "type": "ITM"}
        },
        {
            "id": "opt_otm",
            "type": "derivatives_term",
            "canonical_name": "Out-Of-The-Money",
            "aliases": ["otm", "out of the money"],
            "maps_to_field": "strike_selection",
            "embedding_text": "Out-Of-The-Money (OTM): An option that consists purely of extrinsic (time) value and no intrinsic value.",
            "metadata": {"category": "moneyness", "type": "OTM"}
        },
        {
            "id": "opt_atm",
            "type": "derivatives_term",
            "canonical_name": "At-The-Money",
            "aliases": ["atm", "at the money"],
            "maps_to_field": "strike_selection",
            "embedding_text": "At-The-Money (ATM): An option where the strike price is exactly identical to the current spot price of the underlying asset.",
            "metadata": {"category": "moneyness", "type": "ATM"}
        },

        # Volatility & Metrics
        {
            "id": "opt_oi",
            "type": "derivatives_term",
            "canonical_name": "Open Interest",
            "aliases": ["oi", "open interest"],
            "maps_to_field": "conditions",
            "embedding_text": "Open Interest (OI): The total number of outstanding derivative contracts that have not yet been settled or closed out by traders.",
            "metadata": {"category": "market_data", "type": "OI"}
        },
        {
            "id": "opt_pcr",
            "type": "derivatives_term",
            "canonical_name": "Put-Call Ratio",
            "aliases": ["pcr", "put call ratio"],
            "maps_to_field": "conditions",
            "embedding_text": "Put-Call Ratio (PCR): A sentiment indicator calculated by dividing put volume (or OI) by call volume (or OI). A high PCR indicates bearish sentiment.",
            "metadata": {"category": "market_data", "type": "PCR"}
        },
        {
            "id": "opt_iv",
            "type": "derivatives_term",
            "canonical_name": "Implied Volatility",
            "aliases": ["iv", "implied volatility"],
            "maps_to_field": "conditions",
            "embedding_text": "Implied Volatility (IV): A forward-looking metric estimating the market's expectation of future price fluctuations, heavily influencing option premiums.",
            "metadata": {"category": "market_data", "type": "IV"}
        },
        {
            "id": "opt_hv",
            "type": "derivatives_term",
            "canonical_name": "Historical Volatility",
            "aliases": ["hv", "historical volatility", "realized volatility"],
            "maps_to_field": "conditions",
            "embedding_text": "Historical Volatility (HV): A backward-looking statistical measure of the actual dispersion of returns over a specific past timeframe.",
            "metadata": {"category": "market_data", "type": "HV"}
        },
        {
            "id": "opt_max_pain",
            "type": "derivatives_term",
            "canonical_name": "Max Pain",
            "aliases": ["max pain", "option pain"],
            "maps_to_field": "conditions",
            "embedding_text": "Max Pain: The specific strike price at which the highest number of open options contracts (both calls and puts) would expire worthless, maximizing losses for option buyers.",
            "metadata": {"category": "market_data", "type": "MAX_PAIN"}
        },

        # The Greeks
        {
            "id": "opt_delta",
            "type": "derivatives_term",
            "canonical_name": "Delta",
            "aliases": ["delta", "option delta"],
            "maps_to_field": "conditions",
            "embedding_text": "Delta (Option Greek): Measures the expected change in an option's premium for every $1 movement in the underlying asset's price. Also acts as a proxy for the probability of expiring ITM.",
            "metadata": {"category": "greeks", "type": "DELTA"}
        },
        {
            "id": "opt_gamma",
            "type": "derivatives_term",
            "canonical_name": "Gamma",
            "aliases": ["gamma", "option gamma"],
            "maps_to_field": "conditions",
            "embedding_text": "Gamma (Option Greek): The rate of change of an option's Delta for a $1 move in the underlying asset. Highest for ATM options.",
            "metadata": {"category": "greeks", "type": "GAMMA"}
        },
        {
            "id": "opt_theta",
            "type": "derivatives_term",
            "canonical_name": "Theta",
            "aliases": ["theta", "time decay"],
            "maps_to_field": "conditions",
            "embedding_text": "Theta (Time Decay): Measures the rate at which an option's premium loses value as time passes (value lost per day).",
            "metadata": {"category": "greeks", "type": "THETA"}
        },
        {
            "id": "opt_vega",
            "type": "derivatives_term",
            "canonical_name": "Vega",
            "aliases": ["vega", "option vega"],
            "maps_to_field": "conditions",
            "embedding_text": "Vega (Option Greek): Measures the sensitivity of an option's premium to a 1% absolute change in Implied Volatility (IV).",
            "metadata": {"category": "greeks", "type": "VEGA"}
        },
        {
            "id": "opt_rho",
            "type": "derivatives_term",
            "canonical_name": "Rho",
            "aliases": ["rho", "option rho"],
            "maps_to_field": "conditions",
            "embedding_text": "Rho (Option Greek): Measures the expected change in an option's premium for a 1% change in the risk-free interest rate.",
            "metadata": {"category": "greeks", "type": "RHO"}
        },

        # Multi-Leg Strategies
        {
            "id": "opt_strat_long_straddle",
            "type": "options_strategy",
            "canonical_name": "Long Straddle",
            "aliases": ["long straddle", "straddle", "buy straddle"],
            "maps_to_field": "strategy_type",
            "embedding_text": "Long Straddle: A volatility options strategy involving buying a Call and a Put at the exact same ATM strike and expiration, profiting from explosive directional movement.",
            "metadata": {"category": "multi_leg_strategy", "type": "STRADDLE"}
        },
        {
            "id": "opt_strat_short_straddle",
            "type": "options_strategy",
            "canonical_name": "Short Straddle",
            "aliases": ["short straddle", "sell straddle"],
            "maps_to_field": "strategy_type",
            "embedding_text": "Short Straddle: A neutral options strategy involving selling a Call and a Put at the same ATM strike, profiting from tight consolidation and time decay (Theta).",
            "metadata": {"category": "multi_leg_strategy", "type": "STRADDLE_SHORT"}
        },
        {
            "id": "opt_strat_strangle",
            "type": "options_strategy",
            "canonical_name": "Strangle",
            "aliases": ["strangle", "long strangle", "short strangle"],
            "maps_to_field": "strategy_type",
            "embedding_text": "Strangle: An options strategy similar to a Straddle, but utilizes OTM Call and Put strikes, requiring a larger price movement but costing less capital.",
            "metadata": {"category": "multi_leg_strategy", "type": "STRANGLE"}
        },
        {
            "id": "opt_strat_iron_condor",
            "type": "options_strategy",
            "canonical_name": "Iron Condor",
            "aliases": ["iron condor", "condor"],
            "maps_to_field": "strategy_type",
            "embedding_text": "Iron Condor: A four-leg, limited-risk, non-directional options strategy involving two sold OTM options (a call and a put) protected by two further-OTM bought options, profiting from low volatility.",
            "metadata": {"category": "multi_leg_strategy", "type": "IRON_CONDOR"}
        },
        {
            "id": "opt_strat_bull_call_spread",
            "type": "options_strategy",
            "canonical_name": "Bull Call Spread",
            "aliases": ["bull call spread", "call debit spread"],
            "maps_to_field": "strategy_type",
            "embedding_text": "Bull Call Spread (Debit Spread): A bullish options strategy involving buying a Call and simultaneously selling a higher-strike Call to offset the cost.",
            "metadata": {"category": "multi_leg_strategy", "type": "BULL_CALL_SPREAD"}
        },
        {
            "id": "opt_strat_bear_put_spread",
            "type": "options_strategy",
            "canonical_name": "Bear Put Spread",
            "aliases": ["bear put spread", "put debit spread"],
            "maps_to_field": "strategy_type",
            "embedding_text": "Bear Put Spread (Debit Spread): A bearish options strategy involving buying a Put and simultaneously selling a lower-strike Put.",
            "metadata": {"category": "multi_leg_strategy", "type": "BEAR_PUT_SPREAD"}
        },
        {
            "id": "opt_strat_butterfly",
            "type": "options_strategy",
            "canonical_name": "Butterfly Spread",
            "aliases": ["butterfly", "butterfly spread"],
            "maps_to_field": "strategy_type",
            "embedding_text": "Butterfly Spread: A limited-risk, multi-leg options strategy combining bull and bear spreads, utilizing three different strike prices to profit from a highly specific price target.",
            "metadata": {"category": "multi_leg_strategy", "type": "BUTTERFLY"}
        },
        {
            "id": "opt_strat_covered_call",
            "type": "options_strategy",
            "canonical_name": "Covered Call",
            "aliases": ["covered call", "cc"],
            "maps_to_field": "strategy_type",
            "embedding_text": "Covered Call: An income-generating strategy involving holding a long position in the underlying asset while simultaneously selling OTM Call options against it.",
            "metadata": {"category": "multi_leg_strategy", "type": "COVERED_CALL"}
        }
    ]

    # Add only if not already present
    existing_ids = {doc["id"] for doc in corpus}
    added_count = 0

    for term in options_terms:
        if term["id"] not in existing_ids:
            corpus.append(term)
            added_count += 1
            print(f"Added term: {term['canonical_name']}")
        else:
            print(f"Term {term['canonical_name']} already exists. Skipping.")

    print(f"\nAdded {added_count} new options terms.")
    print(f"Total documents in corpus: {len(corpus)}")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)

if __name__ == "__main__":
    main()
