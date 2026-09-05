"""Strategy Evaluation Engine."""
import uuid
import logging
import pandas as pd
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime, timezone

from app.domain.events import CandleEvent
from app.domain.orders import OrderIntent
from app.indicators.indicator_engine import IndicatorEngine
from app.signal.signal_engine import SignalEngine
from app.config.settings import StrategySettings
from app.ast.indicator_extractor import IndicatorExtractor

logger = logging.getLogger(__name__)


class StrategyEngine:
    """Evaluates trading logic against incoming CandleEvents."""
    
    def __init__(
        self,
        session_id: str,
        strategy_ast: Dict[str, Any],
        settings: StrategySettings,
        on_order_intent: Callable[[OrderIntent], None],
        get_current_position_side: Optional[Callable[[str], Optional[str]]] = None
    ):
        self.session_id = session_id
        self.strategy_ast = strategy_ast
        self.settings = settings
        self.on_order_intent = on_order_intent
        self.get_current_position_side = get_current_position_side
        
        self.signal_engine = SignalEngine()
        self.indicators: Dict[str, IndicatorEngine] = {}
        
        # We need historical data buffers to compute indicators dynamically
        self._history: Dict[str, List[CandleEvent]] = {}
        
        # Extract indicator configs early so we don't do it per-tick
        self._indicator_configs = IndicatorExtractor.gather_indicator_configs(
            self.strategy_ast, 
            {}
        )
        # Note: In a production setup, you would validate these against available TA-Lib ones here
        
    def on_candle(self, candle: CandleEvent) -> None:
        """Process a completed candle and potentially emit an OrderIntent."""
        sym = candle.symbol
        
        if sym not in self.indicators:
            self.indicators[sym] = IndicatorEngine()
            self._history[sym] = []
            
        history = self._history[sym]
        
        # We need to construct a dataframe for the indicator engine
        df_data_list = []
        for c in history:
            df_data_list.append({
                "timestamp": c.timestamp,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume)
            })
            
        # Temporarily append the live in-progress candle for this evaluation
        if not candle.is_completed:
            df_data_list.append({
                "timestamp": candle.timestamp,
                "open": float(candle.open),
                "high": float(candle.high),
                "low": float(candle.low),
                "close": float(candle.close),
                "volume": float(candle.volume)
            })
        else:
            history.append(candle)
            
            # Optimization: Cap history size to prevent memory leak.
            # Assuming maximum lookback is 200 bars for typical MAs.
            if len(history) > 200:
                self._history[sym] = history[-200:]
                
        df = pd.DataFrame(df_data_list)
        
        # Compute indicators for this symbol
        indicator_engine = self.indicators[sym]
        indicator_engine.compute_all(df, self._indicator_configs)
        
        # Get the latest snapshot
        current_idx = len(history) - 1
        indicators_snapshot = indicator_engine.get_snapshot(current_idx)
        
        # Prepare market data context
        market_data = {
            "OPEN": float(candle.open),
            "HIGH": float(candle.high),
            "LOW": float(candle.low),
            "CLOSE": float(candle.close),
            "VOLUME": float(candle.volume or 0.0),
        }

        if getattr(candle, "is_warmup", False):
            # Evaluate silently to populate SignalEngine's lookback history
            try:
                self.signal_engine.evaluate(
                    strategy_ast=self.strategy_ast,
                    indicators=indicators_snapshot,
                    default=self.settings.default_signal,
                    market_data=market_data,
                    current_position_side=None
                )
            except Exception:
                pass
            return
            
        # Evaluate AST
        try:
            # Fetch current position side if callback is provided
            current_pos = None
            if self.get_current_position_side:
                current_pos = self.get_current_position_side(sym)
                
            signal = self.signal_engine.evaluate(
                strategy_ast=self.strategy_ast,
                indicators=indicators_snapshot,
                default=self.settings.default_signal,
                market_data=market_data,
                current_position_side=current_pos
            )
        except Exception as e:
            logger.error(f"Strategy evaluation failed for {sym}: {e}")
            return
            
        sig_val = signal.signal.value
        
        # Determine if we should generate an intent (only one trade at a time)
        should_trade = False
        if sig_val == "BUY" and current_pos != "LONG":
            should_trade = True
        elif sig_val == "SELL" and current_pos != "SHORT":
            should_trade = True
            
        if should_trade:
            # Create OrderIntent
            intent = OrderIntent(
                order_intent_id=str(uuid.uuid4()),
                session_id=self.session_id,
                symbol=sym,
                timestamp=datetime.now(timezone.utc),
                side=sig_val,
                quantity=float(self.settings.position_size),
                order_type="MARKET",
                reason=signal.reason.get("intent", "STRATEGY_SIGNAL") if signal.reason else "STRATEGY_SIGNAL",
                limit_price=None,
                stop_price=None
            )
            
            self.on_order_intent(intent)
