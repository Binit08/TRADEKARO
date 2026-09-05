import pytest
import asyncio
from datetime import datetime, timezone
import uuid

from app.api.routes import session_manager
from app.session.paper_trade_session import PaperTradeSession
from app.core.paper_engine import PaperTradingEngine
from app.market_data.live_feed import LiveKiteFeed
from app.execution.paper_simulator import PaperExecutionSimulator
from app.domain.orders import OrderFill, OrderIntent
from app.db.database import AsyncSessionLocal
from app.persistence.repository import PaperTradingRepository
from app.db.models import Base
from sqlalchemy.ext.asyncio import create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
def mock_feed():
    class MockFeed(LiveKiteFeed):
        def __init__(self):
            pass
        def stream(self):
            yield []
        def run(self):
            pass
    return MockFeed()

@pytest.mark.asyncio
async def test_paper_trading_crash_recovery(mock_feed):
    # Setup test DB
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_id = str(uuid.uuid4())
    
    # Pre-seed the database with some historical fills to simulate a previous run
    async with AsyncSessionLocal() as db_session:
        # Patch the database URL to use memory for this test inside the repo
        # Actually since PaperTradeSession uses AsyncSessionLocal internally without injection,
        # we have to mock it or just rely on the test DB if we overwrite the global url.
        pass
        
    # Since patching AsyncSessionLocal globally is complex, we will just test the `recover` method directly on the session.
    
    # 1. Create a session wrapper manually
    class MockEngine:
        def __init__(self, feed):
            self.feed = feed

    session = PaperTradeSession(
        session_id=session_id,
        engine=MockEngine(mock_feed),
        symbols=["AAPL"],
        strategy_ast={"ast": {"node_type": "STRATEGY_ROOT", "operation_nodes": []}},
        strategy_settings={},
        on_update_callback=None,
        loop=asyncio.get_running_loop()
    )
    
    # 2. Start without feed
    session.start(start_feed=False)
    
    # 3. Simulate Recovery
    historical_fills = [
        OrderFill(
            fill_id=str(uuid.uuid4()),
            session_id=session_id,
            order_intent_id=str(uuid.uuid4()),
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            side="BUY",
            filled_quantity=10.0,
            filled_price=150.0,
            fees=1.5,
            slippage=0.0
        )
    ]
    
    session.recover(historical_fills)
    
    # 4. Verify portfolio state was rebuilt!
    position = session.portfolio.positions.get("AAPL")
    assert position is not None
    assert position.qty == 10.0
    assert position.entry_price == 150.0
    assert session.portfolio.cash == 100000.0 - (10.0 * 150.0) - 1.5
    
    session.stop()
