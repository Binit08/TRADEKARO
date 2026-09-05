import pytest
from datetime import datetime, timezone
from app.execution.paper_simulator import PaperExecutionSimulator
from app.domain.events import TickEvent
from app.domain.orders import OrderIntent

def test_paper_execution_simulator_market_order():
    fills = []
    def on_fill(f):
        fills.append(f)
        
    sim = PaperExecutionSimulator(on_fill, slippage_bps=10.0, fee_rate=0.001)
    
    # Send a MARKET BUY order intent
    intent = OrderIntent(
        order_intent_id="i1",
        session_id="test",
        symbol="RELIANCE",
        timestamp=datetime.now(timezone.utc),
        side="BUY",
        quantity=10,
        order_type="MARKET",
        reason="STRATEGY_ENTRY"
    )
    
    sim.on_order_intent(intent)
    assert len(sim.pending_intents) == 1
    assert len(fills) == 0
    
    # Emulate a tick
    tick = TickEvent(
        event_id="t1",
        session_id="test",
        instrument_token=1,
        symbol="RELIANCE",
        timestamp=datetime.now(timezone.utc),
        last_price=100.0,
        volume=100
    )
    
    sim.on_tick(tick)
    
    assert len(sim.pending_intents) == 0
    assert len(fills) == 1
    
    fill = fills[0]
    assert fill.symbol == "RELIANCE"
    assert fill.side == "BUY"
    assert fill.filled_quantity == 10
    
    # check slippage: 10 bps on 100.0 price for BUY -> 100.1
    assert fill.filled_price == 100.1
    # check fees: 0.001 on (100.1 * 10) = 1001 * 0.001 = 1.001
    assert abs(fill.fees - 1.001) < 1e-6

def test_paper_execution_simulator_limit_order():
    fills = []
    def on_fill(f):
        fills.append(f)
        
    sim = PaperExecutionSimulator(on_fill, slippage_bps=0.0, fee_rate=0.0)
    
    intent = OrderIntent(
        order_intent_id="i2",
        session_id="test",
        symbol="RELIANCE",
        timestamp=datetime.now(timezone.utc),
        side="BUY",
        quantity=10,
        order_type="LIMIT",
        limit_price=95.0,
        reason="STRATEGY_ENTRY"
    )
    
    sim.on_order_intent(intent)
    
    # Tick above limit
    tick_high = TickEvent("t1", "test", 1, "RELIANCE", datetime.now(timezone.utc), 96.0)
    sim.on_tick(tick_high)
    assert len(fills) == 0  # Should not fill
    assert len(sim.pending_intents) == 1
    
    # Tick below limit
    tick_low = TickEvent("t2", "test", 1, "RELIANCE", datetime.now(timezone.utc), 94.0)
    sim.on_tick(tick_low)
    assert len(fills) == 1  # Should fill
    assert len(sim.pending_intents) == 0
    assert fills[0].filled_price == 94.0 # Execution price is the LTP
