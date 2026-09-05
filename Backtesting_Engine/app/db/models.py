from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, JSON, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import relationship
from app.db.database import Base

class PaperSession(Base):
    __tablename__ = "paper_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    symbols = Column(JSON, nullable=False)
    strategy_config = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="CREATED")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("PaperOrder", back_populates="session")
    fills = relationship("PaperFill", back_populates="session")
    positions = relationship("PaperPosition", back_populates="session")
    equity_snapshots = relationship("PaperEquitySnapshot", back_populates="session")


class PaperOrder(Base):
    __tablename__ = "paper_orders"
    
    order_intent_id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("paper_sessions.session_id"), nullable=False, index=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    qty = Column(Numeric, nullable=False)
    order_type = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    limit_price = Column(Numeric, nullable=True)
    stop_price = Column(Numeric, nullable=True)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    session = relationship("PaperSession", back_populates="orders")
    fill = relationship("PaperFill", back_populates="order", uselist=False)


class PaperFill(Base):
    __tablename__ = "paper_fills"
    
    fill_id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("paper_sessions.session_id"), nullable=False, index=True)
    order_intent_id = Column(String, ForeignKey("paper_orders.order_intent_id"), nullable=False, unique=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    filled_qty = Column(Numeric, nullable=False)
    filled_price = Column(Numeric, nullable=False)
    fees = Column(Numeric, nullable=False, default=0.0)
    slippage = Column(Numeric, nullable=False, default=0.0)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    session = relationship("PaperSession", back_populates="fills")
    order = relationship("PaperOrder", back_populates="fill")


class PaperPosition(Base):
    __tablename__ = "paper_positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("paper_sessions.session_id"), nullable=False, index=True)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    qty = Column(Numeric, nullable=False)
    avg_entry_price = Column(Numeric, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    session = relationship("PaperSession", back_populates="positions")
    
    __table_args__ = (
        UniqueConstraint('session_id', 'symbol', name='uq_paper_position_session_symbol'),
    )


class PaperEquitySnapshot(Base):
    __tablename__ = "paper_equity_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("paper_sessions.session_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    cash = Column(Numeric, nullable=False)
    unrealized_pnl = Column(Numeric, nullable=False)
    realized_pnl = Column(Numeric, nullable=False)
    total_equity = Column(Numeric, nullable=False)
    
    session = relationship("PaperSession", back_populates="equity_snapshots")


class PaperSessionCheckpoint(Base):
    __tablename__ = "paper_session_checkpoints"
    
    session_id = Column(String, ForeignKey("paper_sessions.session_id"), primary_key=True)
    instrument_token = Column(Integer, primary_key=True)
    timeframe = Column(String, nullable=False)
    last_processed_timestamp = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
