from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float, Boolean, ForeignKey
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True) # UUID from Supabase
    email = Column(String, unique=True, index=True, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
class StrategyRecord(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    tag = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # Nullable for legacy records
    prompt = Column(Text, nullable=False)
    canonical_json = Column(JSON, nullable=True)
    ast_json = Column(JSON, nullable=True)
    logs = Column(Text, nullable=True)
    execution_context = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="pending") # ok, error, blocked, semantic_approval
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class BacktestRecord(Base):
    """
    Fix 4: Single source of truth for backtests.
    Stores ALL reproducibility inputs and ALL outputs.
    """
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, nullable=True)  # Optional link to strategy
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # Nullable for legacy records

    # --- Reproducibility inputs ---
    symbol = Column(Text)
    timeframe = Column(String(10))
    start_date = Column(String(20))
    end_date = Column(String(20))
    exchange = Column(String(50), nullable=True, default="NSE")
    position_side = Column(String(20), nullable=True)
    initial_cash = Column(Float)
    position_size = Column(Float, nullable=True)
    position_size_type = Column(String(20), nullable=True)
    commission_rate = Column(Float, nullable=True)
    slippage_bps = Column(Float, nullable=True)
    allow_short = Column(Boolean, default=False)
    close_on_opposite_signal = Column(Boolean, default=True)
    market_type = Column(String(50), nullable=True)
    multiplier = Column(Float, nullable=True)
    margin = Column(Float, nullable=True)
    expiry = Column(String(50), nullable=True)
    strategy_ast = Column(JSON)

    # --- Outputs ---
    metrics = Column(JSON)
    equity_curve = Column(JSON, nullable=True)
    drawdown_curve = Column(JSON, nullable=True)
    trades = Column(JSON, nullable=True)
    ohlc_data = Column(JSON, nullable=True)

    status = Column(String(50), default="ok")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BrokerCredentials(Base):
    __tablename__ = "broker_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    broker_name = Column(String(50))
    credentials = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
