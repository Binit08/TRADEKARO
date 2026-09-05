import pytest
from datetime import datetime, timezone
from app.portfolio.manager import PortfolioManager
from app.portfolio.portfolio import Portfolio
from app.domain.events import TickEvent, PortfolioUpdateEvent, PositionUpdateEvent
from app.domain.orders import OrderFill

def test_portfolio_manager_processes_fill_and_tick():
    port_events = []
    pos_events = []
    
    def on_port(e): port_events.append(e)
    def on_pos(e): pos_events.append(e)
        
    portfolio = Portfolio(initial_cash=10000.0)
    manager = PortfolioManager("test", portfolio, on_port, on_pos)
    
    # Process Entry Fill
    fill1 = OrderFill(
        fill_id="f1",
        session_id="test",
        order_intent_id="i1",
        symbol="RELIANCE",
        timestamp=datetime.now(timezone.utc),
        side="BUY",
        filled_quantity=10,
        filled_price=100.0,
        fees=1.0,
        slippage=0.0
    )
    
    manager.on_order_fill(fill1)
    
    assert portfolio.cash == 8999.0  # 10000 - (100 * 10) - 1.0
    assert "RELIANCE" in portfolio.positions
    
    assert len(port_events) == 1
    assert len(pos_events) == 1
    
    # Process Tick for MTM
    tick = TickEvent(
        event_id="t1",
        session_id="test",
        instrument_token=1,
        symbol="RELIANCE",
        timestamp=datetime.now(timezone.utc),
        last_price=110.0,
        volume=100
    )
    
    manager.on_tick(tick)
    
    # Unrealized PnL should be (110 - 100) * 10 = +100
    assert portfolio.state().unrealized_pnl == 100.0
    
    assert len(port_events) == 2
    assert len(pos_events) == 2
    
    # Process Exit Fill
    fill2 = OrderFill(
        fill_id="f2",
        session_id="test",
        order_intent_id="i2",
        symbol="RELIANCE",
        timestamp=datetime.now(timezone.utc),
        side="SELL", # Opposite side -> triggers exit
        filled_quantity=10,
        filled_price=110.0,
        fees=1.0,
        slippage=0.0
    )
    
    manager.on_order_fill(fill2)
    
    # Cash should be 8999.0 + 1100 - 1 = 10098.0
    assert portfolio.cash == 10098.0
    assert "RELIANCE" not in portfolio.positions
