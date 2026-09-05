import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.db.models import Base, PaperSession, PaperOrder, PaperFill, PaperPosition, PaperEquitySnapshot
from app.persistence.repository import PaperTradingRepository
from app.domain.orders import OrderIntent, OrderFill
from app.domain.events import PortfolioUpdateEvent

# Use an in-memory SQLite for testing to avoid hitting Supabase in unit tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
def repo(session):
    return PaperTradingRepository(session)

@pytest.mark.asyncio
async def test_create_session(repo, session):
    session_id = "test-session-1"
    await repo.create_session(session_id, ["AAPL", "TSLA"], {"name": "TestStrat"})
    
    # Verify it exists
    result = await session.execute(text(f"SELECT session_id, status FROM paper_sessions WHERE session_id='{session_id}'"))
    row = result.fetchone()
    assert row is not None
    assert row[0] == session_id
    assert row[1] == "CREATED"

@pytest.mark.asyncio
async def test_save_order_intent_and_idempotency(repo, session):
    session_id = "test-session-2"
    await repo.create_session(session_id, ["AAPL"], {})
    
    intent_id = str(uuid.uuid4())
    intent = OrderIntent(
        order_intent_id=intent_id,
        session_id=session_id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        order_type="MARKET",
        reason="SIGNAL",
        limit_price=None,
        stop_price=None,
        timestamp=datetime.now(timezone.utc)
    )
    
    # Save first time
    await repo.save_order_intent(intent)
    
    # Save second time (should ignore gracefully)
    await repo.save_order_intent(intent)
    
    # Verify exactly one row
    result = await session.execute(text(f"SELECT COUNT(*) FROM paper_orders WHERE order_intent_id='{intent_id}'"))
    count = result.scalar()
    assert count == 1

@pytest.mark.asyncio
async def test_commit_fill_transaction_and_idempotency(repo, session):
    session_id = "test-session-3"
    await repo.create_session(session_id, ["AAPL"], {})
    
    intent_id = str(uuid.uuid4())
    intent = OrderIntent(
        order_intent_id=intent_id,
        session_id=session_id,
        symbol="AAPL",
        side="BUY",
        quantity=10,
        order_type="MARKET",
        reason="SIGNAL",
        limit_price=None,
        stop_price=None,
        timestamp=datetime.now(timezone.utc)
    )
    await repo.save_order_intent(intent)
    
    fill_id = str(uuid.uuid4())
    fill = OrderFill(
        fill_id=fill_id,
        session_id=session_id,
        order_intent_id=intent_id,
        symbol="AAPL",
        timestamp=datetime.now(timezone.utc),
        side="BUY",
        filled_quantity=10,
        filled_price=150.0,
        fees=1.5,
        slippage=0.0
    )
    
    success = await repo.commit_fill_transaction(fill, position_qty=10, position_avg_price=150.0)
    assert success is True
    
    # Check Fill exists
    result = await session.execute(text(f"SELECT filled_qty FROM paper_fills WHERE fill_id='{fill_id}'"))
    assert result.scalar() == 10
    
    # Check Order Status is FILLED
    result = await session.execute(text(f"SELECT status FROM paper_orders WHERE order_intent_id='{intent_id}'"))
    assert result.scalar() == "FILLED"
    
    # Check Position UPSERT
    result = await session.execute(text(f"SELECT qty, avg_entry_price FROM paper_positions WHERE session_id='{session_id}' AND symbol='AAPL'"))
    row = result.fetchone()
    assert row[0] == 10
    assert float(row[1]) == 150.0
    
    # Test duplicate fill attempt
    success_dup = await repo.commit_fill_transaction(fill, position_qty=20, position_avg_price=155.0)
    assert success_dup is False
    
    # Verify position did NOT update on duplicate
    result = await session.execute(text(f"SELECT qty FROM paper_positions WHERE session_id='{session_id}' AND symbol='AAPL'"))
    assert result.scalar() == 10

@pytest.mark.asyncio
async def test_save_equity_snapshot(repo, session):
    session_id = "test-session-4"
    await repo.create_session(session_id, ["AAPL"], {})
    
    snapshot = PortfolioUpdateEvent(
        event_id=str(uuid.uuid4()),
        session_id=session_id,
        timestamp=datetime.now(timezone.utc),
        cash=100000.0,
        unrealized_pnl=500.0,
        realized_pnl=100.0,
        total_equity=100600.0
    )
    
    await repo.save_equity_snapshot(snapshot)
    
    result = await session.execute(text(f"SELECT total_equity FROM paper_equity_snapshots WHERE session_id='{session_id}'"))
    assert result.scalar() == 100600.0
