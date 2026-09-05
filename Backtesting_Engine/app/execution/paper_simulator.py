"""Paper Trading Execution Engine.

Simulates live execution by queuing orders and processing them against 
the incoming live tick stream, providing realistic real-time slippage.
"""
import logging
from typing import Optional, List

from app.data.market_event import MarketEvent
from app.execution.simulator import ExecutionEngine
from app.execution.trade import Trade
from app.execution.order import Order

logger = logging.getLogger(__name__)

class PaperExecutionEngine(ExecutionEngine):
    """Paper execution engine that simulates live trades."""

    def execute(self, next_candle: MarketEvent) -> Optional[Trade]:
        """Execute the oldest fillable pending order for this candle.
        
        In paper trading, `next_candle` is actually the most recent aggregated
        live candle or a pseudo-tick passed by the LiveKiteFeed.
        """
        if not self.pending_orders:
            return None

        # Similar logic to historical simulator, but we could add artificial delay
        # or more rigorous volume checking for paper trading realism here.
        for order in list(self.pending_orders):
            if order.symbol != next_candle.symbol:
                continue
                
            # Guard: ensure we don't execute instantly on the same candle that created it
            # if we are acting strictly on OHLC closes.
            if not (next_candle.timestamp > order.created_time):
                continue

            reference_price = self._reference_price(order, next_candle)
            if reference_price is None:
                continue

            self.pending_orders.remove(order)
            order.status = "FILLED"
            fill = self.create_fill(
                symbol=next_candle.symbol,
                side=order.signal,
                reference_price=reference_price,
                timestamp=next_candle.timestamp,
                qty=order.qty,
                volume=getattr(next_candle, "volume", None),
                order_type=order.order_type,
                intent=order.intent,
                reason=order.reason,
                stop_loss=order.stop_loss,
                take_profit=order.take_profit,
                order_created_time=order.created_time,
            )
            self.trade_history.append(fill)
            logger.info(f"PAPER TRADE EXECUTED: {fill.side} {fill.qty} {fill.symbol} @ {fill.entry_price}")
            return fill

        return None

import uuid
from datetime import datetime, timezone
from typing import Callable, List
from app.domain.events import TickEvent
from app.domain.orders import OrderIntent, OrderFill
from app.execution.slippage import apply_slippage

class PaperExecutionSimulator:
    """Event-driven Execution Engine Simulator (Phase 7).
    
    Consumes OrderIntents and TickEvents. 
    Simulates fills against live ticks without relying on candles.
    """
    
    def __init__(
        self, 
        on_fill: Callable[[OrderFill], None],
        slippage_bps: float = 1.0,
        fee_rate: float = 0.0001
    ):
        self.pending_intents: List[OrderIntent] = []
        self.on_fill = on_fill
        self.slippage_bps = slippage_bps
        self.fee_rate = fee_rate
        
    def on_order_intent(self, intent: OrderIntent) -> None:
        """Receive a validated OrderIntent from the Risk Engine."""
        self.pending_intents.append(intent)
        
    def on_tick(self, tick: TickEvent) -> None:
        """Evaluate pending intents against the latest tick."""
        if not self.pending_intents:
            return
            
        unfilled = []
        for intent in self.pending_intents:
            if intent.symbol != tick.symbol:
                unfilled.append(intent)
                continue
                
            ltp = tick.last_price
            can_fill = False
            
            if intent.order_type == "MARKET":
                can_fill = True
            elif intent.order_type == "LIMIT":
                if intent.side == "BUY" and ltp <= (intent.limit_price or ltp):
                    can_fill = True
                elif intent.side == "SELL" and ltp >= (intent.limit_price or ltp):
                    can_fill = True
            elif intent.order_type == "STOP":
                if intent.side == "BUY" and ltp >= (intent.stop_price or ltp):
                    can_fill = True
                elif intent.side == "SELL" and ltp <= (intent.stop_price or ltp):
                    can_fill = True
            else:
                can_fill = True # fallback
                
            if can_fill:
                fill_price = apply_slippage(
                    price=ltp,
                    side=intent.side,
                    bps=self.slippage_bps,
                    volume=tick.volume,
                    qty=intent.quantity
                )
                
                notional = fill_price * intent.quantity
                fees = notional * self.fee_rate
                
                fill = OrderFill(
                    fill_id=str(uuid.uuid4()),
                    session_id=intent.session_id,
                    order_intent_id=intent.order_intent_id,
                    symbol=intent.symbol,
                    timestamp=datetime.now(timezone.utc),
                    side=intent.side,
                    filled_quantity=intent.quantity,
                    filled_price=fill_price,
                    fees=fees,
                    slippage=abs(fill_price - ltp) * intent.quantity
                )
                
                self.on_fill(fill)
            else:
                unfilled.append(intent)
                
        self.pending_intents = unfilled

