from datetime import date
from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, field_validator, model_validator, Field
from pydantic import StringConstraints

# Reusable constrained string type for ticker symbols
TickerSymbol = Annotated[str, StringConstraints(min_length=1, max_length=32, pattern=r"^[a-zA-Z0-9.\-=\^ ]+$")]

class BrokerCredentials(BaseModel):
    broker_name: str
    credentials: Dict[str, Any]

class BacktestRequest(BaseModel):
    symbol: Optional[TickerSymbol] = None
    """The ticker symbol to backtest. Deprecated, use `symbols`."""
    symbols: Optional[List[TickerSymbol]] = None
    """List of ticker symbols to backtest simultaneously for portfolio-level strategies."""
    start: date
    end: date
    timeframe: str = "1d"
    broker: Optional[BrokerCredentials] = None
    strategy_ast: Dict[str, Any]
    initial_cash: Annotated[float, Field(gt=0, le=1e10)] = 100000.0
    position_size_type: str = "percent_equity"
    position_size: Annotated[float, Field(gt=0)] = 1.0
    commission_rate: Annotated[float, Field(ge=0, le=1.0)] = 0.0005
    slippage_bps: Annotated[float, Field(ge=0, le=10000.0)] = 5.0
    allow_short: bool = False
    close_on_opposite_signal: bool = True
    execution_mode: str = "next_candle_open"
    allow_short: bool = False
    close_on_opposite_signal: bool = True
    market_type: str = "equity"
    multiplier: Optional[float] = None
    margin: Optional[float] = None
    expiry: Optional[str] = None

    @model_validator(mode="after")
    def validate_symbols(self) -> 'BacktestRequest':
        if not self.symbol and not self.symbols:
            raise ValueError("Either 'symbol' or 'symbols' must be provided.")
        return self

    @field_validator("strategy_ast")
    @classmethod
    def validate_strategy_ast(cls, v: Any) -> Any:
        import json
        import jsonschema
        
        if not isinstance(v, dict):
            raise ValueError("strategy_ast must be a dictionary")
            
        try:
            json_str = json.dumps(v)
        except Exception as e:
            raise ValueError(f"strategy_ast is not JSON serializable: {e}")
            
        if len(json_str.encode("utf-8")) > 256 * 1024:
            raise ValueError("strategy_ast exceeds maximum JSON size of 256 KB")
            
        AST_SCHEMA = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "oneOf": [
                # NLconverter format
                {
                    "properties": {
                        "ast": {
                            "type": "object",
                            "properties": {
                                "node_type": {"const": "STRATEGY_ROOT"},
                                "operation_nodes": {
                                    "type": "array",
                                    "items": {"type": "object"}
                                }
                            },
                            "required": ["node_type", "operation_nodes"]
                        },
                        "execution_context": {"type": "object"}
                    },
                    "required": ["ast"]
                },
                # Legacy flat formats
                {
                    "properties": {
                        "operator": {"type": "string"},
                        "conditions": {
                            "type": "array",
                            "items": {"type": "object"}
                        },
                        "signal": {"type": "string"}
                    },
                    "required": ["operator", "conditions"]
                },
                {
                    "properties": {
                        "left": {"type": ["object", "string", "number"]},
                        "operator": {"type": "string"},
                        "right": {"type": ["object", "string", "number"]},
                        "signal": {"type": "string"}
                    },
                    "required": ["left", "operator", "right"]
                }
            ]
        }
        
        try:
            jsonschema.validate(instance=v, schema=AST_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"strategy_ast validation failed against JSON schema: {e.message}")
            
        return v

class OHLCCandle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float

class BacktestResponse(BaseModel):
    metrics: Dict[str, Any] = Field(
        description="Performance metrics calculated for the backtest. Any float values that represent infinity or NaN are reported as null (None)."
    )
    """Performance metrics calculated for the backtest. Any float values that represent infinity or NaN are reported as null (None)."""
    trades: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]
    monthly_returns: List[Dict[str, Any]]
    ohlc_data: Dict[str, List[OHLCCandle]]
    warnings: List[str] = Field(
        default=[],
        description="List of non-critical warnings encountered during backtest execution. Raw exceptions are sanitized into generic codes (such as INDICATOR_NOT_FOUND or EVAL_ERROR) and warnings containing file paths, internal classes, or stack frames are filtered/removed to prevent leaking internal system details."
    )
    indicators_data: Dict[str, Dict[str, List[Dict[str, Any]]]] = Field(
        default_factory=dict,
        description="Indicator timeseries data per symbol. Format: {symbol: {indicator_name: [{time: str, value: float}]}}"
    )

class PaperTradeRequest(BaseModel):
    session_id: Optional[str] = None
    symbols: List[TickerSymbol]
    timeframe: str = "1m"
    strategy_ast: Dict[str, Any]
    broker: Optional[BrokerCredentials] = None
    instrument_tokens: List[int]
    symbol_map: Dict[int, str]
    initial_cash: Annotated[float, Field(gt=0, le=1e10)] = 100000.0
    position_size_type: str = "percent_equity"
    position_size: Annotated[float, Field(gt=0)] = 1.0
    execution_mode: str = "next_candle_open"
    allow_short: bool = False
    close_on_opposite_signal: bool = True
    margin: Optional[float] = None
    market_type: str = "equity"
    expiry: Optional[str] = None
    exchange: Optional[str] = None
