"""Market event models.

Provides a lightweight `MarketEvent` dataclass used by the
historical replay feed. The dataclass is intentionally small and
frozen so that events are immutable once created (production-friendly).
"""
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class MarketEvent:
	"""Represents a single OHLCV market data point.

	Attributes:
		symbol: Ticker symbol (single-asset system expects one symbol).
		timestamp: UTC tz-aware datetime for the candle.
		open: Opening price for the period.
		high: High price for the period.
		low: Low price for the period.
		close: Closing price for the period.
		volume: Traded volume for the period.
	"""

	symbol: str
	timestamp: datetime
	open: float
	high: float
	low: float
	close: float
	volume: float
	oi: float = 0.0

	def __post_init__(self) -> None:
		if self.timestamp.tzinfo is None:
			import warnings
			from datetime import timezone
			warnings.warn(
				"Naive datetime encountered in MarketEvent. Wrapping to UTC.",
				UserWarning,
				stacklevel=2
			)
			object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=timezone.utc))
