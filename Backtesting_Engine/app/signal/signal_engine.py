"""Signal engine implementation.

The ``SignalEngine`` evaluates strategy ASTs against a snapshot of indicator
values and returns a ``SignalType`` (BUY/SELL/HOLD).

Schema detection is automatic:
- If the AST contains a top-level ``"ast"`` key with ``node_type: STRATEGY_ROOT``
  it is treated as a **NLconverter AST** and evaluated via the hierarchical
  entry/exit node path.
- Any other dict is treated as the **legacy flat AST** and evaluated through
  the original comparison/logic path (fully backward-compatible).

If the AST (or a companion dict passed alongside it) contains a top-level
``"execution_context"`` key, the engine automatically derives and applies
``StrategySettings`` overrides from that block (Option A).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import logging

from app.signal.models import SignalType, SignalResult
from app.signal.evaluator import EvaluatorState, evaluate_node, evaluate_ast_node


_LOG = logging.getLogger(__name__)


class SignalEngine:
    """Engine that evaluates AST strategies into trading signals.

    The engine maintains a small in-memory buffer (``previous_indicators``)
    holding the last-seen value for every indicator and market field.  This
    enables CROSS_ABOVE / CROSS_BELOW operators and MARKET_REFERENCE nodes
    with non-zero ``lookback_periods``.
    """

    def __init__(self, maxlen: int = 256, max_failures: int = 50, warmup_bars: int = 0) -> None:
        """Initialize the SignalEngine.

        Rationale for max_failures:
        A default of 50 consecutive evaluation failures is chosen to allow for transient
        data gaps or warm-up periods where indicator values might be invalid/missing,
        while still providing a safeguard against persistent configuration issues or
        infinite error loops in large-scale automated backtest runs.
        """
        from app.signal.evaluator import SignalEvaluator
        from app.ast.loader import StrategyLoader
        from collections import deque
        self.evaluator = SignalEvaluator(maxlen=maxlen)
        self.loader = StrategyLoader()
        self.previous_indicators: Dict[str, float] = {}
        self.eval_outcomes = deque(maxlen=max_failures)
        self.warmup_bars = warmup_bars
        self.eval_count = 0
        self._ast_cache: Dict[int, Any] = {}
        self.warnings: list[str] = []

    def reset(self) -> None:
        """Reset the signal engine state between backtest runs."""
        self.evaluator.reset()
        self.previous_indicators.clear()
        self.eval_outcomes.clear()
        self.warnings.clear()
        self.eval_count = 0
        self._ast_cache.clear()

    # ── Public API ──────────────────────────────────────────────────────────

    def evaluate(
        self,
        strategy_ast: Dict[str, Any],
        indicators: Dict[str, Any],
        *,
        default: SignalType = SignalType.HOLD,
        market_data: Optional[Dict[str, float]] = None,
        current_position_side: Optional[str] = None,
    ) -> SignalResult:
        self.eval_count += 1
        state = EvaluatorState(previous=dict(self.previous_indicators))
        
        orig_ast_id = id(strategy_ast)

        # ── Schema detection ────────────────────────────────────────────────
        core = strategy_ast.get("ast") if isinstance(strategy_ast, dict) and "ast" in strategy_ast else strategy_ast
        is_nlconverter = (
            isinstance(core, dict) and (
                core.get("node_type") == "STRATEGY_ROOT" or 
                core.get("type") == "STRATEGY_ROOT" or 
                "operation" in core
            )
        )

        if is_nlconverter:
            signal = self._evaluate_nlconverter_ast(strategy_ast, indicators, state, market_data, orig_ast_id, current_position_side)
        else:
            signal = self._evaluate_legacy_ast(strategy_ast, indicators, state, default)

        # ── Persist current snapshot for next bar ──────────────────────────
        self._update_previous(indicators, market_data)

        return signal

    # ── NLconverter schema path ─────────────────────────────────────────────

    def _evaluate_nlconverter_ast(
        self,
        strategy_ast: Dict[str, Any],
        indicators: Dict[str, Any],
        state: EvaluatorState,
        market_data: Optional[Dict[str, float]],
        ast_id: Optional[int] = None,
        current_position_side: Optional[str] = None,
    ) -> SignalResult:
        if ast_id is None:
            ast_id = id(strategy_ast)

        if isinstance(strategy_ast, dict) and "execution_context" not in strategy_ast:
            strategy_ast = dict(strategy_ast)
            strategy_ast["execution_context"] = {}
            
        try:
            # Check cache using the stable ast_id
            if ast_id in self._ast_cache:
                bundle = self._ast_cache[ast_id]
            else:
                bundle = self.loader.load_from_json(strategy_ast)
                self._ast_cache[ast_id] = bundle

            if not bundle.ast.operation_nodes:
                raise ValueError("Strategy AST has no operation nodes")

            # Use the new Evaluator class
            position_side = "LONG"
            if hasattr(bundle, "execution_context") and bundle.execution_context:
                position_side = getattr(bundle.execution_context, "position_side", "LONG")
            elif isinstance(strategy_ast, dict):
                position_side = strategy_ast.get("execution_context", {}).get("position_side", "LONG")

            if current_position_side is not None:
                if not market_data:
                    market_data = {}
                elif not isinstance(market_data, dict):
                    market_data = dict(market_data)
                if "POSITION_SIDE" not in market_data:
                    market_data["POSITION_SIDE"] = current_position_side

            signal = self.evaluator.evaluate(bundle.ast, indicators, market_data or {}, position_side=position_side, current_position_side=current_position_side)
            
            self.eval_outcomes.append(True)
            return signal
        except (KeyError, ValueError, TypeError) as exc:
            if self.eval_count > self.warmup_bars:
                self.eval_outcomes.append(False)
            
            # Sanitize exception strings with generic codes to avoid leaking internals
            if isinstance(exc, KeyError):
                warning_code = "INDICATOR_NOT_FOUND"
            else:
                warning_code = "EVAL_ERROR"
            self.warnings.append(warning_code)

            if len(self.eval_outcomes) == self.eval_outcomes.maxlen and all(not outcome for outcome in self.eval_outcomes):
                raise RuntimeError(f"NLconverter evaluation failed consecutively {self.eval_outcomes.maxlen} times: {exc}") from exc
            _LOG.warning("Transient error evaluating NLconverter AST: %s", exc, exc_info=True)
            return SignalResult(signal=SignalType.HOLD, reason={"intent": "NONE"})

    # ── Legacy flat-AST path ────────────────────────────────────────────────

    def _evaluate_legacy_ast(
        self,
        strategy_ast: Dict[str, Any],
        indicators: Dict[str, Any],
        state: EvaluatorState,
        default: SignalType,
    ) -> SignalResult:
        """Evaluate a legacy flat-format AST (fully backward-compatible)."""
        try:
            triggered = evaluate_node(strategy_ast, indicators, state)
            self.eval_outcomes.append(True)
        except (KeyError, ValueError, TypeError) as exc:
            if self.eval_count > self.warmup_bars:
                self.eval_outcomes.append(False)
            
            # Sanitize exception strings with generic codes to avoid leaking internals
            if isinstance(exc, KeyError):
                warning_code = "INDICATOR_NOT_FOUND"
            else:
                warning_code = "EVAL_ERROR"
            self.warnings.append(warning_code)

            if len(self.eval_outcomes) == self.eval_outcomes.maxlen and all(not outcome for outcome in self.eval_outcomes):
                raise RuntimeError(f"Legacy evaluation failed consecutively {self.eval_outcomes.maxlen} times: {exc}") from exc
            _LOG.warning("Transient error evaluating strategy AST: %s", exc, exc_info=True)
            triggered = False

        if triggered:
            sig = strategy_ast.get("action_on_true") or strategy_ast.get("signal")
            if sig is not None:
                try:
                    return SignalResult(signal=SignalType(sig), reason={"intent": "LEGACY"})
                except ValueError:
                    return SignalResult(signal=default, reason={"intent": "LEGACY"})
            return SignalResult(signal=default, reason={"intent": "LEGACY"})

        sig = strategy_ast.get("else_action")
        if sig is not None:
            try:
                return SignalResult(signal=SignalType(sig), reason={"intent": "LEGACY"})
            except ValueError:
                return SignalResult(signal=SignalType.HOLD, reason={"intent": "LEGACY"})

        return SignalResult(signal=SignalType.HOLD, reason={"intent": "LEGACY"})

    # ── State management ────────────────────────────────────────────────────

    def _update_previous(
        self,
        indicators: Dict[str, Any],
        market_data: Optional[Dict[str, float]],
    ) -> None:
        """Persist current indicator and market values for the next bar."""
        for k, v in indicators.items():
            if isinstance(v, dict):
                for out_name, out_val in v.items():
                    try:
                        val = float(out_val)
                        key = f"{k}.{out_name}"
                        self.previous_indicators[key] = val
                        if key.upper() != key:
                            self.previous_indicators[key.upper()] = val
                    except (ValueError, TypeError):
                        continue
                continue
            try:
                val = float(v)
                self.previous_indicators[k] = val
                if k.upper() != k:
                    self.previous_indicators[k.upper()] = val
            except (ValueError, TypeError):
                continue

        # Store market data under "MARKET_<FIELD>" for MARKET_REFERENCE lookback
        if market_data:
            for field, value in market_data.items():
                try:
                    self.previous_indicators[f"MARKET_{field.upper()}"] = float(value)
                except (ValueError, TypeError):
                    continue
