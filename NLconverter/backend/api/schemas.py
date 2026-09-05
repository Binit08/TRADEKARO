from typing import List, Optional
from enum import Enum
from datetime import date
from pathlib import Path
from pydantic import BaseModel, field_validator, model_validator

MAX_PROMPT_LENGTH = 10_000
ALLOWED_TIMEFRAMES = {"1m", "2m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"}
ALLOWED_SIZING_MODES = {"fixed_qty", "percent_equity"}

class Resolution(BaseModel):
    source: str
    resolution: str

class Universe(BaseModel):
    index: str
    exchange: str
    asset_class: str

class CapitalPerTrade(BaseModel):
    amount: float
    currency: str

class MarketType(str, Enum):
    EQUITY = "equity"
    FUTURES = "futures"

# Schema Config
SCHEMA_CONFIG = {
    MarketType.EQUITY: {
        "execution_context": Path(__file__).parent.parent / "strategy_parser" / "schemas" / "EQUITY_EXECUTION_CONTEXT_SCHEMA.json",
        "strategy": Path(__file__).parent.parent / "strategy_parser" / "schemas" / "EQUITY_SCHEMA.json",
    },
    MarketType.FUTURES: {
        "execution_context": Path(__file__).parent.parent / "strategy_parser" / "schemas" / "FUTURES_EXECUTION_CONTEXT_SCHEMA.json",
        "strategy": Path(__file__).parent.parent / "strategy_parser" / "schemas" / "FUTURES_SCHEMA.json",
    },
}

class StrategyRequest(BaseModel):
    name: Optional[str] = None
    tag: Optional[str] = None
    description: Optional[str] = None
    prompt: str
    semantic_resolutions: Optional[List[Resolution]] = None
    market_type: MarketType = MarketType.EQUITY
    execution_context: Optional[dict] = None

    @field_validator("prompt")
    @classmethod
    def validate_prompt_length(cls, v: str) -> str:
        if len(v) > MAX_PROMPT_LENGTH:
            raise ValueError(
                f"Prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters "
                f"(received {len(v)})"
            )
        return v

class ProxyBacktestRequest(BaseModel):
    strategy_id: Optional[int] = None
    broker_name: Optional[str] = "kite"
    symbol: Optional[str] = None
    symbols: Optional[List[str]] = None
    exchange: Optional[str] = "NSE"
    start: str
    end: str
    timeframe: str
    strategy_ast: dict
    initial_cash: float
    position_size_type: str = "fixed_qty"
    position_size: float = 1.0
    commission_rate: float = 0.0001
    slippage_bps: float = 2.0
    allow_short: bool = False
    position_side: Optional[str] = None
    close_on_opposite_signal: bool = True
    market_type: str = "equity"
    multiplier: Optional[float] = None
    margin: Optional[float] = None
    expiry: Optional[str] = None

    @field_validator("start", "end")
    @classmethod
    def validate_dates(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date format: '{v}'. Expected YYYY-MM-DD.")
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if date.fromisoformat(self.start) >= date.fromisoformat(self.end):
            raise ValueError("start date must be before end date")
        return self

    @field_validator("initial_cash")
    @classmethod
    def validate_initial_cash(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("initial_cash must be positive")
        return v

    @field_validator("position_size")
    @classmethod
    def validate_position_size(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("position_size must be positive")
        return v

    @field_validator("commission_rate")
    @classmethod
    def validate_commission_rate(cls, v: float) -> float:
        if v < 0:
            raise ValueError("commission_rate must be non-negative")
        return v

    @field_validator("slippage_bps")
    @classmethod
    def validate_slippage_bps(cls, v: float) -> float:
        if v < 0:
            raise ValueError("slippage_bps must be non-negative")
        return v

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        if v.lower() not in ALLOWED_TIMEFRAMES:
            raise ValueError(
                f"timeframe must be one of {sorted(ALLOWED_TIMEFRAMES)}"
            )
        return v

    @field_validator("position_size_type")
    @classmethod
    def validate_sizing_mode(cls, v: str) -> str:
        if v not in ALLOWED_SIZING_MODES:
            raise ValueError(
                f"position_size_type must be one of {sorted(ALLOWED_SIZING_MODES)}"
            )
        return v
