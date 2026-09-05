import json
from pprint import pprint
from backend.services.strategy_service import StrategyGenerationService
from backend.api.schemas import StrategyRequest, Resolution
from backend.db.database import SessionLocal

def test_integration():
    db = SessionLocal()
    service = StrategyGenerationService(db, user_id=1)
    
    # Mock _save_record to avoid DB foreign key errors
    def mock_save_record(*args, **kwargs):
        class DummyRecord:
            id = 999
        return DummyRecord()
    service._save_record = mock_save_record

    # ---------------------------------------------------------
    # PASS 1: User sends raw strategy (No semantic_resolutions)
    # ---------------------------------------------------------
    print("\n--- PASS 1: Extracting & RAG Scoring ---")
    payload_pass1 = StrategyRequest(
        prompt="Buy 100 shares of RELIANCE when RSI crosses above 60 and price breaks resistance. Also check for choppy market. Exit when MACD crosses below signal line.",
        market_type="equity",
        execution_context={
            "timeframe": "1d",
            "position_side": "LONG",
            "universe": {"asset_class": "equity", "exchange": "NSE"},
            "stocks": ["RELIANCE", "TCS"]
        }
    )
    
    result_pass1 = service.process_strategy(payload_pass1)
    print("Status:", result_pass1["status"])
    print("Approval Items returned to UI:")
    for item in result_pass1.get("approval_items", []):
        print(f" - [{item['type'].upper()}] Source: '{item['source']}' -> Candidates: {item['candidates'][:1]} (Confidence: {item['confidence']:.2f})")

    # ---------------------------------------------------------
    # PASS 2: User confirms in UI and sends semantic_resolutions
    # ---------------------------------------------------------
    print("\n--- PASS 2: Compiling with RAG Context ---")
    # Simulate the UI sending back the exact names of the chosen candidates
    resolutions = []
    for item in result_pass1.get("approval_items", []):
        if item["candidates"]:
            # User picks the top candidate
            resolutions.append(Resolution(source=item["source"], resolution=item["candidates"][0]))
    
    payload_pass2 = StrategyRequest(
        prompt="Buy 100 shares of RELIANCE when RSI crosses above 60 and price breaks resistance. Also check for choppy market. Exit when MACD crosses below signal line.",
        market_type="equity",
        execution_context={
            "timeframe": "1d",
            "position_side": "LONG",
            "universe": {"asset_class": "equity", "exchange": "NSE"},
            "stocks": ["RELIANCE", "TCS"]
        },
        semantic_resolutions=resolutions
    )
    
    result_pass2 = service.process_strategy(payload_pass2)
    print("Status:", result_pass2["status"])
    if "canonical_json" in result_pass2:
        print("\nCanonical JSON successfully generated!\n")
        pprint(result_pass2["canonical_json"])
        
    db.close()

if __name__ == "__main__":
    test_integration()
