"""Risk management engine."""
import uuid
import logging
from typing import Dict, Callable
from datetime import datetime, timezone

from app.domain.events import TickEvent
from app.domain.orders import OrderIntent
from app.portfolio.portfolio import Portfolio

logger = logging.getLogger(__name__)


class RiskEngine:
    """Evaluates OrderIntents and open positions against risk constraints."""
    
    def __init__(
        self, 
        session_id: str,
        portfolios: Dict[str, Portfolio], 
        on_approved_intent: Callable[[OrderIntent], None]
    ):
        self.session_id = session_id
        self.portfolios = portfolios
        self.on_approved_intent = on_approved_intent
        
    def process_order_intent(self, intent: OrderIntent) -> None:
        """Validate an OrderIntent from the StrategyEngine.
        
        Checks margin and rejects if insufficient. Otherwise forwards to execution.
        """
        symbol = intent.symbol
        portfolio = self.portfolios.get(symbol)
        
        if not portfolio:
            logger.warning(f"Rejecting intent for {symbol}: No portfolio tracking found.")
            return
            
        # Simplified Margin Check
        # In a full implementation, we'd estimate the required margin based on ltp.
        # Here we just ensure we have *some* positive cash.
        if intent.reason == "STRATEGY_ENTRY" and portfolio.cash <= 0:
            logger.warning(f"Rejecting {intent.side} intent for {symbol}: Insufficient funds.")
            return
            
        logger.info(f"RiskEngine approved {intent.side} intent for {symbol}")
        self.on_approved_intent(intent)
        
    def on_tick(self, tick: TickEvent) -> None:
        """Evaluate open positions against the latest tick for Stop Loss / Take Profit."""
        symbol = tick.symbol
        portfolio = self.portfolios.get(symbol)
        
        if not portfolio:
            return
            
        position = portfolio.positions.get(symbol)
        if not position:
            return
            
        ltp = tick.last_price
        side = position.side
        
        intent_side = None
        reason = None
        
        # Check Stop Loss
        if position.stop_loss is not None:
            if side == "LONG" and ltp <= position.stop_loss:
                intent_side = "SELL"
                reason = "STOP_LOSS"
            elif side == "SHORT" and ltp >= position.stop_loss:
                intent_side = "BUY"
                reason = "STOP_LOSS"
                
        # Check Take Profit
        if not intent_side and position.take_profit is not None:
            if side == "LONG" and ltp >= position.take_profit:
                intent_side = "SELL"
                reason = "TAKE_PROFIT"
            elif side == "SHORT" and ltp <= position.take_profit:
                intent_side = "BUY"
                reason = "TAKE_PROFIT"
                
        if intent_side:
            logger.info(f"{reason} hit for {symbol} at {ltp}. Generating OrderIntent.")
            intent = OrderIntent(
                order_intent_id=str(uuid.uuid4()),
                session_id=self.session_id,
                symbol=symbol,
                timestamp=datetime.now(timezone.utc),
                side=intent_side,
                quantity=position.qty,
                order_type="MARKET",
                reason=reason,
                limit_price=None,
                stop_price=None
            )
            # Emit directly to execution since it's an internal risk override
            self.on_approved_intent(intent)
