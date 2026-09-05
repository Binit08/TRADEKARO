"""Application and strategy settings.

Example:
    >>> from app.config.settings import StrategySettings
    >>> settings = StrategySettings(
    ...     stop_loss_pct=0.02,     # 2% stop-loss (using [0.0, 1.0] fraction convention)
    ...     take_profit_pct=0.05,   # 5% take-profit (using [0.0, 1.0] fraction convention)
    ...     allow_short=True,
    ... )
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from app.signal.models import SignalType


@dataclass(frozen=True)
class StrategySettings:
    """Runtime controls for the backtest engine.

    The strategy AST decides *when* to trade.  These settings decide *how* the
    engine executes, sizes, and manages those trades.

    Percent inputs such as ``stop_loss_pct``, ``take_profit_pct``, and
    ``short_margin_pct`` are expressed as fractional values in the range
    [0.0, 1.0].  For example, 2% is ``0.02``, not ``2``.
    """

    order_type: str = "MARKET"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

    position_size_type: str = "fixed_qty"
    position_size: Optional[float] = None

    commission_rate: Optional[float] = None
    fixed_commission: Optional[float] = None
    min_commission: Optional[float] = None
    slippage_bps: Optional[float] = None

    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None

    allow_short: bool = False
    pyramiding: int = 0
    close_on_opposite_signal: bool = True
    # When True, closing an opposite-side position on a signal will ALSO immediately
    # submit a new entry in the signal direction (close-and-reverse). Matches TradingView's
    # behavior when strategies are always-in-market. Requires close_on_opposite_signal=True.
    reverse_on_opposite_signal: bool = False
    # When True, after an EXIT order fills, the engine immediately re-evaluates the entry
    # condition on that same bar's indicators. If the entry fires, a new order is submitted
    # that fills at the NEXT bar's open. Matches TradingView's per-bar re-entry behavior.
    reentry_on_exit_bar: bool = False
    short_margin_pct: float = 0.5
    default_signal: SignalType = SignalType.HOLD
    assume_sl_wins: bool = True
    execution_mode: str = "next_candle_open"
    
    market_type: str = "equity"
    multiplier: Optional[float] = None
    margin: Optional[float] = None
    expiry: Optional[str] = None

    def __post_init__(self) -> None:
        self._validate()

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable settings snapshot."""
        return asdict(self)

    @classmethod
    def from_any(
        cls, raw: "StrategySettings | Dict[str, Any] | None"
    ) -> "StrategySettings":
        """Normalize dict/dataclass settings input."""
        if raw is None:
            return cls()
        if isinstance(raw, cls):
            return raw
        if not isinstance(raw, dict):
            raise TypeError(
                "strategy settings must be a StrategySettings instance or dict"
            )

        valid_keys = set(cls.__dataclass_fields__)
        filtered_keys = [k for k in raw.keys() if k not in valid_keys]
        if filtered_keys:
            import logging
            logger = logging.getLogger(__name__)
            for k in filtered_keys:
                logger.warning("Filtered out unsupported settings key: '%s'", k)
        candidate = cls(**{k: v for k, v in raw.items() if k in valid_keys})
        candidate._validate()
        return candidate

    @classmethod
    def from_execution_context(
        cls, ctx: Dict[str, Any], base: "StrategySettings | None" = None
    ) -> "StrategySettings":
        """Build (or overlay onto *base*) settings from a NLconverter execution_context block.

        Mapping:
            - ``order_type``            → ``settings.order_type``
            - ``capital_per_trade.amount`` → ``settings.position_size`` (notional cash mode)
            - ``position_side`` LONG    → ``allow_short = False``
            - ``position_side`` SHORT   → ``allow_short = True``
            - ``max_concurrent_positions`` → ``pyramiding`` (max positions − 1)

        Args:
            ctx: The ``execution_context`` dict from a NLconverter deterministic schema.
            base: Existing settings to overlay onto.  When ``None``, defaults are used.

        Returns:
            A new ``StrategySettings`` instance with fields derived from *ctx*
            merged over *base* (explicit ``ctx`` values take precedence).
        """
        base_dict: Dict[str, Any] = base.to_dict() if base is not None else {}

        # order_type
        order_type_raw = ctx.get("order_type")
        if order_type_raw is not None:
            base_dict["order_type"] = str(order_type_raw).upper()

        # capital_per_trade → position_size (cash / notional mode)
        capital = ctx.get("capital_per_trade")
        if isinstance(capital, dict):
            amount = capital.get("amount")
            if amount is not None:
                base_dict["position_size"] = float(amount)
                base_dict["position_size_type"] = "cash"
        elif isinstance(capital, (int, float)):
            base_dict["position_size"] = float(capital)
            base_dict["position_size_type"] = "cash"

        # position_side
        position_side = ctx.get("position_side")
        if position_side is not None:
            base_dict["allow_short"] = str(position_side).upper() == "SHORT"

        # max_concurrent_positions → pyramiding (0-based extra entries)
        max_pos = ctx.get("max_concurrent_positions")
        if max_pos is not None:
            pyramiding = max(0, int(max_pos) - 1)
            base_dict["pyramiding"] = pyramiding

        return cls.from_any(base_dict)

    @classmethod
    def from_ast_risk_node(
        cls, strategy_ast: Dict[str, Any], base: "StrategySettings | None" = None
    ) -> "StrategySettings":
        """Extract stop-loss and take-profit values directly from the NLP strategy AST."""
        base_dict: Dict[str, Any] = base.to_dict() if base is not None else {}
        
        # In NLconverter, AST is wrapped in an outer dict: {"ast": {"risk_node": ...}}
        root_node = strategy_ast.get("ast", strategy_ast)
        risk_node = root_node.get("risk_node")
        
        if isinstance(risk_node, dict):
            for child in risk_node.get("children", []):
                node_type = child.get("node_type")
                cfg = child.get("config", {})
                
                if node_type == "STOP_LOSS":
                    sl_type = str(cfg.get("stop_loss_type", "")).upper()
                    val = cfg.get("value")
                    if val is not None:
                        if sl_type == "PERCENTAGE":
                            base_dict["stop_loss_pct"] = float(val) / 100.0
                        elif sl_type in ("PRICE", "ABSOLUTE"):
                            base_dict["stop_loss_price"] = float(val)
                elif node_type == "TAKE_PROFIT":
                    tp_type = str(cfg.get("take_profit_type", "")).upper()
                    val = cfg.get("value")
                    if val is not None:
                        if tp_type == "PERCENTAGE":
                            base_dict["take_profit_pct"] = float(val) / 100.0
                        elif tp_type in ("PRICE", "ABSOLUTE"):
                            base_dict["take_profit_price"] = float(val)
                            
        return cls.from_any(base_dict)

    def _validate(self) -> None:
        for name in ("stop_loss_pct", "take_profit_pct", "short_margin_pct"):
            value = getattr(self, name)
            if value is None:
                continue
            if not isinstance(value, (float, int)):
                raise ValueError(
                    f"{name} must be a numeric fraction between 0 and 1"
                )
            if value < 0.0 or value > 1.0:
                raise ValueError(
                    f"{name} must be between 0.0 and 1.0, got {value}"
                )
