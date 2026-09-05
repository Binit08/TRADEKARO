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

    execution_terms = [
        {
            "id": "exec_market_order",
            "type": "execution_term",
            "canonical_name": "Market Order",
            "aliases": ["market execution", "at market", "market price"],
            "maps_to_field": "order_type",
            "embedding_text": "Market Order: An order to buy or sell a security immediately at the best available current price. Prioritizes execution speed over price certainty. Typically maps to order_type='MARKET'.",
            "metadata": {"category": "order_type", "type": "MARKET"}
        },
        {
            "id": "exec_limit_order",
            "type": "execution_term",
            "canonical_name": "Limit Order",
            "aliases": ["limit execution", "at a limit", "target entry price"],
            "maps_to_field": "order_type",
            "embedding_text": "Limit Order: An order to buy or sell a security at a specific target price or better. Prioritizes price over execution speed. Typically maps to order_type='LIMIT'.",
            "metadata": {"category": "order_type", "type": "LIMIT"}
        },
        {
            "id": "exec_stop_loss",
            "type": "execution_term",
            "canonical_name": "Stop-Loss Order",
            "aliases": ["stop loss", "sl", "hard stop"],
            "maps_to_field": "exit_conditions.stop_loss",
            "embedding_text": "Stop-Loss Order: An order placed to exit a position once it reaches a certain price, strictly designed to cap a trader's loss on a position. Maps to exit_conditions.stop_loss.",
            "metadata": {"category": "exit_condition", "type": "STOP_LOSS"}
        },
        {
            "id": "exec_take_profit",
            "type": "execution_term",
            "canonical_name": "Take Profit",
            "aliases": ["target order", "profit target", "tp", "take-profit"],
            "maps_to_field": "exit_conditions.take_profit",
            "embedding_text": "Take Profit (Target Order): An order specifying the exact price at which to close out an open position to lock in a profit. Maps to exit_conditions.take_profit.",
            "metadata": {"category": "exit_condition", "type": "TAKE_PROFIT"}
        },
        {
            "id": "exec_stop_limit",
            "type": "execution_term",
            "canonical_name": "Stop-Limit Order",
            "aliases": ["stop limit"],
            "maps_to_field": "order_type",
            "embedding_text": "Stop-Limit Order: An order combining the features of a stop order and a limit order. Once a trigger price is reached, it becomes a limit order that executes only at the specified limit price or better.",
            "metadata": {"category": "order_type", "type": "STOP_LIMIT"}
        },
        {
            "id": "exec_trailing_stop",
            "type": "execution_term",
            "canonical_name": "Trailing Stop-Loss",
            "aliases": ["trailing stop", "tsl", "trail sl"],
            "maps_to_field": "exit_conditions.trailing_stop",
            "embedding_text": "Trailing Stop-Loss: A dynamic stop-loss order set at a percentage or absolute point distance below the market price that automatically adjusts upward as the price moves favorably.",
            "metadata": {"category": "exit_condition", "type": "TRAILING_STOP"}
        },
        {
            "id": "exec_gtc",
            "type": "execution_term",
            "canonical_name": "Good 'Til Canceled (GTC)",
            "aliases": ["gtc", "good till canceled"],
            "maps_to_field": "time_in_force",
            "embedding_text": "Good 'Til Canceled (GTC): A time-in-force designation indicating an order to buy or sell remains active indefinitely until it is filled or explicitly canceled by the trader.",
            "metadata": {"category": "time_in_force", "type": "GTC"}
        },
        {
            "id": "exec_gtt",
            "type": "execution_term",
            "canonical_name": "Good Till Triggered (GTT)",
            "aliases": ["gtt", "good 'til triggered"],
            "maps_to_field": "order_type",
            "embedding_text": "Good Till Triggered (GTT): A passive order kept dormant in the system until a trigger price is met, commonly used for long-term targets and stop-loss placements.",
            "metadata": {"category": "order_type", "type": "GTT"}
        },
        {
            "id": "exec_ioc",
            "type": "execution_term",
            "canonical_name": "Immediate Or Cancel (IOC)",
            "aliases": ["ioc"],
            "maps_to_field": "time_in_force",
            "embedding_text": "Immediate Or Cancel (IOC): A time-in-force order requiring that all or part of the order be executed immediately. Any unfilled portion is automatically canceled.",
            "metadata": {"category": "time_in_force", "type": "IOC"}
        },
        {
            "id": "exec_day_order",
            "type": "execution_term",
            "canonical_name": "Day Order",
            "aliases": ["day validity", "valid for day"],
            "maps_to_field": "time_in_force",
            "embedding_text": "Day Order: An order that is only valid for the current trading session and automatically expires if unexecuted by the market close.",
            "metadata": {"category": "time_in_force", "type": "DAY"}
        },
        {
            "id": "exec_fok",
            "type": "execution_term",
            "canonical_name": "Fill Or Kill (FOK)",
            "aliases": ["fok", "fill or kill"],
            "maps_to_field": "time_in_force",
            "embedding_text": "Fill Or Kill (FOK): A strict execution order mandating the transaction be executed immediately in its entirety, otherwise it is canceled completely.",
            "metadata": {"category": "time_in_force", "type": "FOK"}
        },
        {
            "id": "exec_bracket_order",
            "type": "execution_term",
            "canonical_name": "Bracket Order (BO)",
            "aliases": ["bracket order", "bo"],
            "maps_to_field": "order_type",
            "embedding_text": "Bracket Order (BO): An advanced order type where an entry order is placed simultaneously with an initial stop-loss and a target take-profit order (bracketing the price).",
            "metadata": {"category": "order_type", "type": "BRACKET"}
        },
        {
            "id": "exec_cover_order",
            "type": "execution_term",
            "canonical_name": "Cover Order (CO)",
            "aliases": ["cover order", "co"],
            "maps_to_field": "order_type",
            "embedding_text": "Cover Order (CO): A specialized intraday order type combining a market/limit entry with a mandatory stop-loss order to cap risk.",
            "metadata": {"category": "order_type", "type": "COVER"}
        },
        {
            "id": "exec_long",
            "type": "execution_term",
            "canonical_name": "Go Long",
            "aliases": ["long", "buy to open", "go long"],
            "maps_to_field": "position_type",
            "embedding_text": "Long (Go Long): Buying a security with the expectation that its price will rise to profit from upward momentum. Maps directly to position_type='LONG'.",
            "metadata": {"category": "position", "type": "LONG"}
        },
        {
            "id": "exec_short",
            "type": "execution_term",
            "canonical_name": "Go Short",
            "aliases": ["short", "sell to open", "go short", "short selling"],
            "maps_to_field": "position_type",
            "embedding_text": "Short (Go Short): Borrowing a security and selling it with the expectation that the price will fall, intending to buy it back cheaper. Maps directly to position_type='SHORT'.",
            "metadata": {"category": "position", "type": "SHORT"}
        },
        {
            "id": "exec_square_off",
            "type": "execution_term",
            "canonical_name": "Square-Off",
            "aliases": ["close position", "square off", "exit position"],
            "maps_to_field": "action",
            "embedding_text": "Square-Off (Close Position): The process of entirely settling a transaction by buying or selling the exact opposite of an open position, bringing the net exposure to zero.",
            "metadata": {"category": "action", "type": "CLOSE"}
        },
        {
            "id": "exec_hedge",
            "type": "execution_term",
            "canonical_name": "Hedge",
            "aliases": ["hedging"],
            "maps_to_field": "strategy_type",
            "embedding_text": "Hedge: A risk-management position intentionally taken to offset potential losses that may be incurred by a companion primary investment.",
            "metadata": {"category": "risk_management", "type": "HEDGE"}
        },
        {
            "id": "exec_leverage",
            "type": "execution_term",
            "canonical_name": "Leverage",
            "aliases": ["margin trading"],
            "maps_to_field": "position_sizing",
            "embedding_text": "Leverage: Using broker-borrowed capital to significantly increase the potential return (and risk) of a position.",
            "metadata": {"category": "capital", "type": "LEVERAGE"}
        },
        {
            "id": "exec_margin",
            "type": "execution_term",
            "canonical_name": "Margin",
            "aliases": ["margin requirement"],
            "maps_to_field": "capital",
            "embedding_text": "Margin: The required collateral that a trader must deposit with their broker to cover the credit risk of trading with leverage or holding short positions.",
            "metadata": {"category": "capital", "type": "MARGIN"}
        },
        {
            "id": "exec_pyramiding",
            "type": "execution_term",
            "canonical_name": "Pyramiding",
            "aliases": ["scaling in", "scale in", "add to position"],
            "maps_to_field": "position_sizing",
            "embedding_text": "Pyramiding (Scaling In): The strategic process of increasing the size of an active position by adding partial entries as the trade becomes increasingly profitable.",
            "metadata": {"category": "position_management", "type": "SCALE_IN"}
        },
        {
            "id": "exec_scaling_out",
            "type": "execution_term",
            "canonical_name": "Scaling Out",
            "aliases": ["scale out", "partial profit", "partial exit"],
            "maps_to_field": "position_sizing",
            "embedding_text": "Scaling Out: A risk-reduction strategy involving taking partial profits by closing fractional portions of an open position as the price moves favorably.",
            "metadata": {"category": "position_management", "type": "SCALE_OUT"}
        },
        {
            "id": "exec_slippage",
            "type": "execution_term",
            "canonical_name": "Slippage",
            "aliases": ["execution slippage"],
            "maps_to_field": "risk_management",
            "embedding_text": "Slippage: The difference between the expected price of a trade entry/exit and the actual price at which the trade is executed, commonly occurring in volatile or illiquid markets.",
            "metadata": {"category": "execution_risk", "type": "SLIPPAGE"}
        }
    ]

    # Add only if not already present
    existing_ids = {doc["id"] for doc in corpus}
    added_count = 0

    for term in execution_terms:
        if term["id"] not in existing_ids:
            corpus.append(term)
            added_count += 1
            print(f"Added term: {term['canonical_name']}")
        else:
            print(f"Term {term['canonical_name']} already exists. Skipping.")

    print(f"\nAdded {added_count} new execution terms.")
    print(f"Total documents in corpus: {len(corpus)}")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)

if __name__ == "__main__":
    main()
