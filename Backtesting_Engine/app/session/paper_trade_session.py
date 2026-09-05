"""Session wrapper for paper trading execution."""
import logging
import threading
from typing import Dict, Any, Optional

from app.domain.session import SessionStatus
from app.core.paper_engine import PaperTradingEngine
from app.core.event_bus import EventBus
from app.market_data.aggregator import CandleAggregator
from app.strategy.engine import StrategyEngine
from app.risk.risk_engine import RiskEngine
from app.execution.paper_simulator import PaperExecutionSimulator
from app.portfolio.manager import PortfolioManager
from app.portfolio.portfolio import Portfolio
from app.domain.events import TickEvent, CandleEvent, PortfolioUpdateEvent, PositionUpdateEvent
from app.domain.orders import OrderIntent, OrderFill
from app.store.redis_store import redis_store
from app.config.settings import StrategySettings

logger = logging.getLogger(__name__)

class PaperTradeSession:
    """Encapsulates a single paper trading session's lifecycle and dependencies."""
    
    def __init__(
        self, 
        session_id: str, 
        engine: PaperTradingEngine,
        symbols: list[str],
        strategy_ast: dict,
        strategy_settings: dict,
        on_update_callback: Any,
        loop: Optional[Any] = None
    ):
        self.session_id = session_id
        # We temporarily accept 'engine' from routes.py, but we only extract the feed from it
        self.feed = engine.feed
        self.symbols = symbols
        self.strategy_ast = strategy_ast
        
        # Convert dict to StrategySettings if needed
        if isinstance(strategy_settings, dict):
            self.strategy_settings = StrategySettings(**strategy_settings)
        else:
            self.strategy_settings = strategy_settings
            
        self.on_update_callback = on_update_callback
        self.loop = loop
        
        self.status = SessionStatus.CREATED
        self.cancel_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.event_bus = EventBus()
        self.is_recovering = False

    def start(self, start_feed: bool = True) -> None:
        """Start the paper trading event-driven architecture."""
        if self.status not in (SessionStatus.CREATED, SessionStatus.STOPPED, SessionStatus.FAILED):
            logger.warning(f"Session {self.session_id} cannot be started from status {self.status}")
            return
            
        self.status = SessionStatus.INITIALIZING
        self.cancel_event.clear()
        
        try:
            # 1. Instantiate EventBus (already done in init)
            self.event_bus.start()
            
            # 2. Instantiate Components
            self.portfolio = Portfolio(initial_cash=100000.0) # Assume default for now
            
            self.portfolio_manager = PortfolioManager(
                session_id=self.session_id,
                portfolio=self.portfolio,
                on_portfolio_update=lambda e: self.event_bus.publish(e),
                on_position_update=lambda e: self.event_bus.publish(e)
            )
            
            self.risk_engine = RiskEngine(
                session_id=self.session_id,
                portfolios={sym: self.portfolio for sym in self.symbols},
                on_approved_intent=self._on_approved_intent
            )
            
            self.execution_simulator = PaperExecutionSimulator(
                on_fill=self._on_simulated_fill,
                slippage_bps=0.0,
                fee_rate=0.0
            )
            
            self.strategy_engine = StrategyEngine(
                session_id=self.session_id,
                strategy_ast=self.strategy_ast,
                settings=self.strategy_settings,
                on_order_intent=lambda e: self.risk_engine.process_order_intent(e),
                get_current_position_side=lambda sym: (
                    self.portfolio.positions[sym].side 
                    if sym in self.portfolio.positions and getattr(self.portfolio.positions[sym], "qty", 0) > 0
                    else None
                )
            )
            
            # Using default 1-minute timeframe for aggregator
            self.aggregator = CandleAggregator(
                timeframe_minutes=1,
                on_candle=lambda e: self.event_bus.publish(e)
            )
            
            # 3. Wire Subscriptions
            self.event_bus.subscribe(CandleEvent, lambda e: self.strategy_engine.on_candle(e) if getattr(e, "is_completed", True) else None)
            
            # Start persistence consumer if loop is available
            self.persistence_consumer = None
            if self.loop:
                import asyncio
                from app.persistence.consumer import PersistenceConsumer
                self.persistence_consumer = PersistenceConsumer(self.event_bus, self.loop)
                asyncio.run_coroutine_threadsafe(self.persistence_consumer.start(), self.loop)
            
            # 4. Start Feed
            logger.info(f"Session {self.session_id} connecting to Kite Feed.")
            
            # TickEvents go to Risk (for SL/TP), ExecSimulator (for fills), PortfolioManager (for MTM), and Aggregator (for OHLC)
            self.event_bus.subscribe(TickEvent, self.risk_engine.on_tick)
            self.event_bus.subscribe(TickEvent, self.execution_simulator.on_tick)
            self.event_bus.subscribe(TickEvent, self.portfolio_manager.on_tick)
            self.event_bus.subscribe(TickEvent, self.aggregator.on_tick)
            
            self.event_bus.subscribe(OrderIntent, self.execution_simulator.on_order_intent)
            self.event_bus.subscribe(OrderFill, self.portfolio_manager.on_order_fill)
            
            # 4. Wire Redis Store to save state
            self.event_bus.subscribe(TickEvent, lambda e: redis_store.save_tick(e.session_id, e))
            self.event_bus.subscribe(CandleEvent, lambda e: redis_store.save_candle(e.session_id, e))
            self.event_bus.subscribe(OrderFill, lambda e: redis_store.save_order_fill(e.session_id, e))
            self.event_bus.subscribe(PortfolioUpdateEvent, lambda e: redis_store.save_portfolio_update(e.session_id, e))
            self.event_bus.subscribe(PositionUpdateEvent, lambda e: redis_store.save_position_update(e.session_id, e))
            
            # 5. Wire the LiveKiteFeed to the EventBus
            self.feed.on_tick = lambda t: self.event_bus.publish(t)
            self.feed.on_candle = lambda c: self.event_bus.publish(c)
            
            self.status = SessionStatus.RUNNING
            redis_store.set_session_status(self.session_id, "RUNNING")
            
            # 6. Start the feed blockingly in a background thread to keep session alive
            if start_feed:
                self.start_feed()

        except Exception as e:
            logger.error(f"Session {self.session_id} failed to initialize: {e}", exc_info=True)
            self.status = SessionStatus.FAILED
            redis_store.set_session_status(self.session_id, "FAILED")

    def start_feed(self) -> None:
        """Start the feed thread (called separately during recovery)."""
        if self.thread and self.thread.is_alive():
            return
            
        def run_target():
            try:
                if hasattr(self.feed, "stream"):
                    for _ in self.feed.stream():
                        if self.cancel_event.is_set():
                            break
                else:
                    if hasattr(self.feed, "start"):
                        self.feed.start()
                    while not self.cancel_event.is_set():
                        self.cancel_event.wait(1.0)
                    if hasattr(self.feed, "stop"):
                        self.feed.stop()
            except Exception as e:
                logger.error(f"Feed error in session {self.session_id}: {e}")
            finally:
                self.status = SessionStatus.STOPPED
                
        self.thread = threading.Thread(target=run_target, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Signal the background engine to stop gracefully."""
        self.status = SessionStatus.STOPPING
        redis_store.set_session_status(self.session_id, "STOPPING")
        self.cancel_event.set()
        
        if hasattr(self, 'persistence_consumer') and self.persistence_consumer and self.loop:
            import asyncio
            asyncio.run_coroutine_threadsafe(self.persistence_consumer.stop(), self.loop)
            
        self.event_bus.stop()
        self.status = SessionStatus.STOPPED
        redis_store.set_session_status(self.session_id, "STOPPED")

    def recover(self, historical_fills: list[OrderFill]) -> None:
        """Re-hydrate the session state from historical database records."""
        logger.info(f"Session {self.session_id} starting state re-hydration from {len(historical_fills)} fills.")
        self.is_recovering = True
        try:
            # Replay fills to rebuild portfolio state
            for fill in historical_fills:
                # Bypass execution simulator and DB sync, just feed PortfolioManager directly
                self.portfolio_manager.on_order_fill(fill)
            logger.info(f"Session {self.session_id} re-hydration complete.")
        finally:
            self.is_recovering = False

    def _on_approved_intent(self, intent: OrderIntent) -> None:
        """Handle risk-approved intent by synchronously saving it to DB, then forwarding."""
        if self.loop and not self.is_recovering:
            import asyncio
            from app.db.database import AsyncSessionLocal
            from app.persistence.repository import PaperTradingRepository
            
            async def save_intent():
                async with AsyncSessionLocal() as session:
                    repo = PaperTradingRepository(session)
                    await repo.save_order_intent(intent)
                    await session.commit()
                    
            try:
                future = asyncio.run_coroutine_threadsafe(save_intent(), self.loop)
                future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Failed to durably save OrderIntent: {e}")
                return # Abort if we can't save
        
        self.execution_simulator.on_order_intent(intent)

    def _on_simulated_fill(self, fill: OrderFill) -> None:
        """Intercept fill from simulator, calculate provisional position, save to DB, then publish."""
        position = self.portfolio.positions.get(fill.symbol)
        
        # Calculate new qty and price (simplified approach for DB)
        curr_qty = position.qty if position else 0.0
        curr_side = position.side if position else "FLAT"
        curr_price = position.entry_price if position else 0.0
        
        net_qty = curr_qty if curr_side == "LONG" else -curr_qty
        fill_qty = fill.filled_quantity if fill.side == "BUY" else -fill.filled_quantity
        
        new_net_qty = net_qty + fill_qty
        
        if new_net_qty == 0:
            new_avg_price = 0.0
        elif (net_qty >= 0 and fill_qty > 0) or (net_qty <= 0 and fill_qty < 0):
            new_avg_price = ((abs(net_qty) * curr_price) + (abs(fill_qty) * fill.filled_price)) / abs(new_net_qty)
        else:
            if abs(fill_qty) > abs(net_qty):
                new_avg_price = fill.filled_price
            else:
                new_avg_price = curr_price
                
        # 2. Durably commit to PostgreSQL
        success = True
        if self.loop and not self.is_recovering:
            import asyncio
            from app.db.database import AsyncSessionLocal
            from app.persistence.repository import PaperTradingRepository
            
            async def commit_tx():
                async with AsyncSessionLocal() as session:
                    repo = PaperTradingRepository(session)
                    return await repo.commit_fill_transaction(
                        fill=fill, 
                        position_qty=new_net_qty, 
                        position_avg_price=new_avg_price
                    )
            
            try:
                future = asyncio.run_coroutine_threadsafe(commit_tx(), self.loop)
                success = future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Failed to durably commit OrderFill: {e}")
                success = False
                
        # 3. If DB commit succeeds (or DB is disabled), push to EventBus to update Runtime memory
        if success:
            self.event_bus.publish(fill)

