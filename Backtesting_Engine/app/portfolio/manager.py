"""Portfolio Manager."""
import uuid
import logging
from typing import Callable, Dict, Any

from app.domain.events import TickEvent, PortfolioUpdateEvent, PositionUpdateEvent
from app.domain.orders import OrderFill
from app.portfolio.portfolio import Portfolio
from app.execution.trade import Trade
from app.data.market_event import MarketEvent

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Event-driven wrapper around the legacy Portfolio engine (Phase 8).
    
    Consumes OrderFills and TickEvents, mutating the underlying Portfolio,
    and dispatching Domain Events for the EventBus.
    """
    
    def __init__(
        self,
        session_id: str,
        portfolio: Portfolio,
        on_portfolio_update: Callable[[PortfolioUpdateEvent], None],
        on_position_update: Callable[[PositionUpdateEvent], None]
    ):
        self.session_id = session_id
        self.portfolio = portfolio
        self.on_portfolio_update = on_portfolio_update
        self.on_position_update = on_position_update
        
    def on_tick(self, tick: TickEvent) -> None:
        """Update MTM (Mark-To-Market) Unrealized PnL."""
        # The legacy Portfolio needs a MarketEvent to update MTM.
        # We construct a synthetic one from the tick.
        synthetic_candle = MarketEvent(
            symbol=tick.symbol,
            timestamp=tick.timestamp,
            open=tick.last_price,
            high=tick.last_price,
            low=tick.last_price,
            close=tick.last_price,
            volume=float(tick.volume or 0.0)
        )
        self.portfolio.mark_to_market(synthetic_candle)
        self._emit_updates(tick.symbol, tick.timestamp)

    def on_order_fill(self, fill: OrderFill) -> None:
        """Process a fill and update cash/positions."""
        symbol = fill.symbol
        position = self.portfolio.positions.get(symbol)
        
        trade = Trade(
            symbol=symbol,
            side=fill.side,
            entry_price=fill.filled_price,
            qty=fill.filled_quantity,
            entry_time=fill.timestamp,
            fees=fill.fees,
            slippage=fill.slippage
        )
        
        # Determine if it's an entry or exit based on existing position
        is_exit = False
        if position is not None:
            if (position.side == "LONG" and fill.side == "SELL") or \
               (position.side == "SHORT" and fill.side == "BUY"):
                is_exit = True
                
        if is_exit:
            try:
                self.portfolio.close_position(
                    symbol=symbol,
                    exit_price=fill.filled_price,
                    exit_time=fill.timestamp,
                    exit_fee=fill.fees,
                    exit_reason="FILL_EXIT",
                    exit_order_type="MARKET",
                    slippage=fill.slippage
                )
            except Exception as e:
                logger.error(f"Failed to close position on fill: {e}")
        else:
            try:
                self.portfolio.open_position(trade)
            except Exception as e:
                logger.error(f"Failed to open position on fill: {e}")
                
        self._emit_updates(symbol, fill.timestamp)
        
    def _emit_updates(self, symbol: str, timestamp: Any) -> None:
        state = self.portfolio.state()
        
        # Emit Portfolio Update
        port_event = PortfolioUpdateEvent(
            event_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=timestamp,
            cash=state.cash,
            unrealized_pnl=state.unrealized_pnl,
            realized_pnl=state.realized_pnl,
            total_equity=state.equity
        )
        self.on_portfolio_update(port_event)
        
        # Emit Position Update if it exists
        pos = self.portfolio.positions.get(symbol)
        if pos:
            pos_event = PositionUpdateEvent(
                event_id=str(uuid.uuid4()),
                session_id=self.session_id,
                symbol=symbol,
                timestamp=timestamp,
                quantity=pos.qty,
                average_entry_price=pos.entry_price,
                current_price=pos.current_price,
                unrealized_pnl=pos.unrealized_pnl,
                realized_pnl=0.0 # Legacy Position object doesn't track realized PnL directly on the position itself while open
            )
            self.on_position_update(pos_event)
