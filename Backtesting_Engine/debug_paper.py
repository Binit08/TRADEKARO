import asyncio
import traceback
from app.api.routes import run_paper_trade
from app.api.models import PaperTradeRequest, BrokerCredentials
from fastapi import Request

async def main():
    req = PaperTradeRequest(
        symbols=["AAPL"],
        timeframe="1m",
        strategy_ast={"ast": {"node_type": "STRATEGY_ROOT", "operation_nodes": []}},
        instrument_tokens=[12345],
        symbol_map={12345: "AAPL"},
        initial_cash=100000.0,
        position_size_type="percent_equity",
        position_size=1.0,
        execution_mode="next_candle_open",
        broker=BrokerCredentials(broker_name="kite", credentials={})
    )
    
    try:
        # Pass a mock request object if needed
        class MockRequest:
            pass
            
        res = await run_paper_trade(req, MockRequest())
        print(res)
    except Exception as e:
        print("CRASH TRACEBACK:")
        traceback.print_exc()

asyncio.run(main())
