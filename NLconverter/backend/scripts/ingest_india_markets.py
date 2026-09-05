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

    india_market_terms = [
        {
            "id": "ind_nifty50",
            "type": "market_structure",
            "canonical_name": "Nifty 50",
            "aliases": ["nifty", "nifty50", "nse nifty"],
            "maps_to_field": "asset",
            "embedding_text": "Nifty 50: The benchmark index of the National Stock Exchange (NSE) representing the weighted average of 50 of the largest Indian companies. Maps to asset='NIFTY'.",
            "metadata": {"category": "index", "market": "NSE"}
        },
        {
            "id": "ind_banknifty",
            "type": "market_structure",
            "canonical_name": "Bank Nifty",
            "aliases": ["banknifty", "nifty bank", "bank index"],
            "maps_to_field": "asset",
            "embedding_text": "Bank Nifty: A highly volatile sector index representing the 12 most liquid Indian banking stocks. The most heavily traded index in the Indian F&O segment. Maps to asset='BANKNIFTY'.",
            "metadata": {"category": "index", "market": "NSE"}
        },
        {
            "id": "ind_finnifty",
            "type": "market_structure",
            "canonical_name": "FinNifty",
            "aliases": ["finnifty", "nifty financial services"],
            "maps_to_field": "asset",
            "embedding_text": "FinNifty: Nifty Financial Services index tracking banks, NBFCs, and insurance companies. Maps to asset='FINNIFTY'.",
            "metadata": {"category": "index", "market": "NSE"}
        },
        {
            "id": "ind_sensex",
            "type": "market_structure",
            "canonical_name": "Sensex",
            "aliases": ["bse sensex"],
            "maps_to_field": "asset",
            "embedding_text": "Sensex: The benchmark index of the Bombay Stock Exchange (BSE), comprising 30 established Indian companies.",
            "metadata": {"category": "index", "market": "BSE"}
        },
        {
            "id": "ind_spot_price",
            "type": "market_structure",
            "canonical_name": "Spot Price",
            "aliases": ["spot", "cash price", "underlying price"],
            "maps_to_field": "conditions",
            "embedding_text": "Spot Price: The actual underlying cash market price of an asset (e.g., the Nifty 50 index value) as opposed to the future contract price.",
            "metadata": {"category": "pricing", "market": "NSE"}
        },
        {
            "id": "ind_india_vix",
            "type": "market_structure",
            "canonical_name": "India VIX",
            "aliases": ["vix", "india volatility index"],
            "maps_to_field": "conditions",
            "embedding_text": "India VIX: The Volatility Index based on the NIFTY Index Option prices. A higher VIX implies higher expected volatility and inflated option premiums over the next 30 days.",
            "metadata": {"category": "index", "market": "NSE"}
        },
        {
            "id": "ind_cash_market",
            "type": "execution_term",
            "canonical_name": "Cash Market",
            "aliases": ["equity delivery", "cash segment", "delivery"],
            "maps_to_field": "segment",
            "embedding_text": "Cash Market (Equity Delivery): Buying stocks with the intent to hold them for more than a day. Requires 100% capital upfront. Maps to segment='CASH' or 'CASH_DELIVERY'.",
            "metadata": {"category": "segment", "type": "CASH"}
        },
        {
            "id": "ind_cnc",
            "type": "execution_term",
            "canonical_name": "CNC (Cash N Carry)",
            "aliases": ["cnc", "cash and carry"],
            "maps_to_field": "segment",
            "embedding_text": "CNC (Cash N Carry): The standard Indian broker order designation for delivery-based equity investing where shares are delivered to the Demat account. Maps to segment='CNC'.",
            "metadata": {"category": "order_product", "type": "CNC"}
        },
        {
            "id": "ind_mis",
            "type": "execution_term",
            "canonical_name": "MIS (Margin Intraday Square-off)",
            "aliases": ["mis", "intraday product"],
            "maps_to_field": "segment",
            "embedding_text": "Intraday (MIS): Margin Intraday Square-off. Highly leveraged trades that must be squared off manually or automatically by the broker before market close (usually 3:15 PM - 3:20 PM IST). Maps to segment='MIS'.",
            "metadata": {"category": "order_product", "type": "MIS"}
        },
        {
            "id": "ind_fno",
            "type": "execution_term",
            "canonical_name": "F&O",
            "aliases": ["futures and options", "derivatives segment", "fno"],
            "maps_to_field": "segment",
            "embedding_text": "F&O (Futures & Options): The derivatives market segment in India. Maps to segment='F&O'.",
            "metadata": {"category": "segment", "type": "F_AND_O"}
        },
        {
            "id": "ind_amo",
            "type": "execution_term",
            "canonical_name": "AMO (After Market Order)",
            "aliases": ["amo", "after market order"],
            "maps_to_field": "time_in_force",
            "embedding_text": "AMO (After Market Order): Orders placed after the normal trading session ends (post 3:30 PM IST) to be executed on the next trading day.",
            "metadata": {"category": "order_type", "type": "AMO"}
        },
        {
            "id": "ind_lot_size",
            "type": "market_structure",
            "canonical_name": "Lot Size",
            "aliases": ["lot", "contract size"],
            "maps_to_field": "position_sizing",
            "embedding_text": "Lot Size: The strictly defined minimum number of units that can be traded in a single Indian F&O contract. Trades must be multiples of the lot size.",
            "metadata": {"category": "derivatives", "market": "NSE"}
        },
        {
            "id": "ind_weekly_expiry",
            "type": "market_structure",
            "canonical_name": "Weekly Expiry",
            "aliases": ["weekly options", "weekly expiry"],
            "maps_to_field": "expiry",
            "embedding_text": "Weekly Expiry: F&O contracts (predominantly Index options) that expire every week. Expiry days vary by index (e.g., Nifty on Thursday, Bank Nifty on Wednesday, FinNifty on Tuesday).",
            "metadata": {"category": "derivatives", "type": "EXPIRY"}
        },
        {
            "id": "ind_monthly_expiry",
            "type": "market_structure",
            "canonical_name": "Monthly Expiry",
            "aliases": ["monthly options", "monthly expiry", "month end expiry"],
            "maps_to_field": "expiry",
            "embedding_text": "Monthly Expiry: Derivative contracts expiring on the last Thursday of every month. Applies to both Index and Stock derivatives in India.",
            "metadata": {"category": "derivatives", "type": "EXPIRY"}
        },
        {
            "id": "ind_ce",
            "type": "market_structure",
            "canonical_name": "CE (Call European)",
            "aliases": ["ce", "call option", "calls"],
            "maps_to_field": "instrument_type",
            "embedding_text": "CE (Call European): The standard designation for Call options in India (e.g., NIFTY 22000 CE).",
            "metadata": {"category": "derivatives", "type": "CALL"}
        },
        {
            "id": "ind_pe",
            "type": "market_structure",
            "canonical_name": "PE (Put European)",
            "aliases": ["pe", "put option", "puts"],
            "maps_to_field": "instrument_type",
            "embedding_text": "PE (Put European): The standard designation for Put options in India (e.g., BANKNIFTY 48000 PE).",
            "metadata": {"category": "derivatives", "type": "PUT"}
        },
        {
            "id": "ind_option_premium",
            "type": "market_structure",
            "canonical_name": "Option Premium",
            "aliases": ["premium"],
            "maps_to_field": "conditions",
            "embedding_text": "Option Premium: The price paid by the buyer to the seller to acquire the CE or PE contract.",
            "metadata": {"category": "derivatives", "market": "NSE"}
        },
        {
            "id": "ind_otm_itm_atm",
            "type": "market_structure",
            "canonical_name": "Moneyness (OTM/ITM/ATM)",
            "aliases": ["otm", "itm", "atm", "out of the money", "in the money", "at the money"],
            "maps_to_field": "strike_selection",
            "embedding_text": "OTM / ITM / ATM: Out-of-the-Money, In-the-Money, and At-the-Money option strikes relative to the current spot price.",
            "metadata": {"category": "derivatives", "market": "NSE"}
        },
        {
            "id": "ind_circuit_limits",
            "type": "market_structure",
            "canonical_name": "Circuit Limits",
            "aliases": ["upper circuit", "lower circuit", "circuit breaker", "uc", "lc"],
            "maps_to_field": "conditions",
            "embedding_text": "Circuit Limits (Upper/Lower Circuit): Daily price bands (e.g., 5%, 10%, 20%) set by the exchange to curb extreme volatility. Trading halts if a stock hits a circuit. Note: Stocks in the F&O segment do not have hard daily circuits.",
            "metadata": {"category": "market_mechanics", "market": "NSE"}
        },
        {
            "id": "ind_pre_open",
            "type": "market_structure",
            "canonical_name": "Pre-Open Session",
            "aliases": ["pre open", "pre market"],
            "maps_to_field": "conditions",
            "embedding_text": "Pre-Open Session: A 15-minute window from 9:00 AM to 9:15 AM IST used for price discovery to absorb overnight news volatility before normal trading begins on NSE/BSE.",
            "metadata": {"category": "market_mechanics", "market": "NSE"}
        },
        {
            "id": "ind_post_closing",
            "type": "market_structure",
            "canonical_name": "Post-Closing Session",
            "aliases": ["post close", "after market close"],
            "maps_to_field": "conditions",
            "embedding_text": "Post-Closing Session: A 20-minute window from 3:40 PM to 4:00 PM IST where trades can be placed at the calculated closing price on NSE/BSE.",
            "metadata": {"category": "market_mechanics", "market": "NSE"}
        },
        {
            "id": "ind_freak_trade",
            "type": "market_structure",
            "canonical_name": "Freak Trade",
            "aliases": ["freak trades", "fat finger"],
            "maps_to_field": "conditions",
            "embedding_text": "Freak Trade: An abnormal, instantaneous, and extreme price spike or crash (often by hundreds of points in options) usually caused by low liquidity or fat-finger errors, reversing within seconds in the Indian market.",
            "metadata": {"category": "market_mechanics", "market": "NSE"}
        },
        {
            "id": "ind_short_covering",
            "type": "market_structure",
            "canonical_name": "Short Covering",
            "aliases": ["short cover", "covering"],
            "maps_to_field": "conditions",
            "embedding_text": "Short Covering: Buying back borrowed securities to close an open short position, often causing rapid upward price spikes in the Indian markets.",
            "metadata": {"category": "market_mechanics", "market": "NSE"}
        },
        {
            "id": "ind_long_unwinding",
            "type": "market_structure",
            "canonical_name": "Long Unwinding",
            "aliases": ["unwinding"],
            "maps_to_field": "conditions",
            "embedding_text": "Long Unwinding: Selling of long positions by traders looking to exit, often triggering rapid downward momentum in the Indian markets.",
            "metadata": {"category": "market_mechanics", "market": "NSE"}
        }
    ]

    # Add only if not already present
    existing_ids = {doc["id"] for doc in corpus}
    added_count = 0

    for term in india_market_terms:
        if term["id"] not in existing_ids:
            corpus.append(term)
            added_count += 1
            print(f"Added term: {term['canonical_name']}")
        else:
            print(f"Term {term['canonical_name']} already exists. Skipping.")

    print(f"\nAdded {added_count} new India market terms.")
    print(f"Total documents in corpus: {len(corpus)}")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)

if __name__ == "__main__":
    main()
