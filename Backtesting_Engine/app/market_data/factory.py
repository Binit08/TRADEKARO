from typing import Dict, Any, List, Optional, Callable

from app.market_data.interfaces import HistoricalDataAdapter, LiveFeedAdapter
from app.market_data.adapters.kite import KiteHistoricalAdapter, KiteLiveFeedAdapter
from app.market_data.adapters.dhan import DhanHistoricalAdapter, DhanLiveFeedAdapter
from app.market_data.adapters.upstox import UpstoxHistoricalAdapter, UpstoxLiveFeedAdapter
from app.market_data.adapters.shoonya import ShoonyaHistoricalAdapter, ShoonyaLiveFeedAdapter

class BrokerAdapterFactory:
    """Factory for instantiating broker-specific data adapters."""
    
    @staticmethod
    def get_historical_adapter(broker: Dict[str, Any]) -> HistoricalDataAdapter:
        """Returns the appropriate historical data adapter based on the broker name."""
        broker_name = broker.get("broker_name", "").lower()
        credentials = broker.get("credentials", {})
        
        if broker_name == "kite":
            return KiteHistoricalAdapter(credentials)
        elif broker_name == "dhan":
            return DhanHistoricalAdapter(credentials)
        elif broker_name == "upstox":
            return UpstoxHistoricalAdapter(credentials)
        elif broker_name == "shoonya":
            return ShoonyaHistoricalAdapter(credentials)
        else:
            raise ValueError(f"Unsupported broker for historical data: {broker_name}")

    @staticmethod
    def get_live_feed_adapter(
        broker: Dict[str, Any], 
        symbols: List[str],
        timeframe_minutes: int = 1,
        session_id: str = "default_session",
        warmup_candles: int = 0,
        on_tick: Optional[Callable] = None,
        on_candle: Optional[Callable] = None
    ) -> LiveFeedAdapter:
        """Returns the appropriate live feed adapter based on the broker name."""
        broker_name = broker.get("broker_name", "").lower()
        credentials = broker.get("credentials", {})
        
        if broker_name == "kite":
            return KiteLiveFeedAdapter(credentials, symbols, timeframe_minutes, session_id, warmup_candles, on_tick, on_candle)
        elif broker_name == "dhan":
            return DhanLiveFeedAdapter(credentials, symbols, timeframe_minutes, session_id, warmup_candles, on_tick, on_candle)
        elif broker_name == "upstox":
            return UpstoxLiveFeedAdapter(credentials, symbols, timeframe_minutes, session_id, warmup_candles, on_tick, on_candle)
        elif broker_name == "shoonya":
            return ShoonyaLiveFeedAdapter(credentials, symbols, timeframe_minutes, session_id, warmup_candles, on_tick, on_candle)
        elif broker_name == "binance":
            from app.market_data.adapters.binance import BinanceLiveFeedAdapter
            return BinanceLiveFeedAdapter(credentials, symbols, timeframe_minutes, session_id, warmup_candles, on_tick, on_candle)
        else:
            raise ValueError(f"Unsupported broker for live feed: {broker_name}")
