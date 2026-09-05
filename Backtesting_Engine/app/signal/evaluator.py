"""Signal Evaluator.

Walks the typed AST to evaluate trading logic against market and indicator data.
"""

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.ast.nodes import (
    ASTNode, BaseNode, ComparisonNode, ConstantNode, CrossNode,
    EntryNode, ExitNode, ArithmeticNode,
    IndicatorConfig, IndicatorNode, LogicNode,
    MarketReferenceNode, OperationNode, StrategyRootNode,
    PatternNode, PatternConfig, SequenceNode, FollowedByNode,
    VariableAssignmentNode, VariableReferenceNode
)
from app.signal.models import SignalType, SignalResult


from typing import Union

ComparisonValue = Union[str, float, int, Dict[str, Any]]


@dataclass
class EvaluatorState:
    previous: Dict[str, float]


def _normalize_indicator_key(indicator_type: str, parameters: Dict[str, Any]) -> str:
    base = indicator_type.strip().upper()
    normalized: Dict[str, Any] = {}
    for k, v in parameters.items():
        if k == "period" or k == "timeperiod":
            normalized["timeperiod"] = v
        else:
            normalized[k.lower()] = v
    if not normalized:
        return base
    parts = [f"{k.upper()}={normalized[k]}" for k in sorted(normalized)]
    return f"{base}_{'_'.join(parts)}"


def _indicator_spec_to_key(spec: Dict[str, Any]) -> Optional[str]:
    if not isinstance(spec, dict):
        return None

    name = spec.get("indicator") or spec.get("name")
    if not isinstance(name, str):
        return None

    name = name.strip().upper()
    params: Dict[str, Any] = {}
    for k, v in spec.items():
        k_lower = k.lower()
        if k_lower not in {"indicator", "name", "alias", "output", "component"}:
            if k_lower == "period" or k_lower == "timeperiod":
                params["timeperiod"] = v
            else:
                params[k_lower] = v

    if not params:
        return name

    parts = [f"{k.upper()}={params[k]}" for k in sorted(params)]
    return f"{name}_{'_'.join(parts)}"


def _resolve_operand(operand: ComparisonValue, indicators: Dict[str, Any]) -> Optional[float]:
    """Resolve an operand which may be a numeric literal, string name, or indicator spec."""
    if isinstance(operand, (int, float)):
        return float(operand)

    if isinstance(operand, dict):
        alias = operand.get("alias")
        value = None
        if isinstance(alias, str):
            value = indicators.get(alias)
            if value is None:
                value = indicators.get(alias.upper())
        if value is None:
            key = _indicator_spec_to_key(operand)
            if key is not None:
                value = indicators.get(key)
        if value is None:
            base_key = operand.get("indicator")
            if isinstance(base_key, str):
                value = indicators.get(base_key.upper())
        if value is None:
            return None

        if isinstance(value, dict):
            output_prop = operand.get("output") or operand.get("component") or "value"
            return float(value.get(output_prop, 0.0))

        try:
            return float(value)
        except Exception:
            return None

    if isinstance(operand, str):
        value = indicators.get(operand)
        if value is None:
            value = indicators.get(operand.upper())
        if value is None:
            return None
        try:
            return float(value)
        except Exception:
            return None

    return None


def _operand_key(operand: ComparisonValue) -> Optional[str]:
    if isinstance(operand, dict):
        return _indicator_spec_to_key(operand)
    if isinstance(operand, str):
        return operand.upper()
    return None


def _resolve_previous(operand: ComparisonValue, state: EvaluatorState) -> Optional[float]:
    key = _operand_key(operand)
    val = None
    if key is not None:
        val = state.previous.get(key)
    if val is None and isinstance(operand, dict):
        alias = operand.get("alias")
        if isinstance(alias, str):
            val = state.previous.get(alias)
            if val is None:
                val = state.previous.get(alias.upper())
    if val is None:
        return None
    if isinstance(operand, dict) and isinstance(val, dict):
        output_prop = operand.get("output") or operand.get("component") or "value"
        return float(val.get(output_prop, 0.0))
    return float(val)


def _eval_comparison(left: ComparisonValue, operator: str, right: ComparisonValue, indicators: Dict[str, Any], state: EvaluatorState) -> bool:
    """Evaluate a single comparison node.

    Supports standard comparisons and CROSS_ABOVE/CROSS_BELOW which rely
    on `state.previous` for prior values.
    """
    left_now = _resolve_operand(left, indicators)
    right_now = _resolve_operand(right, indicators)

    if operator in {"CROSS_ABOVE", "CROSS_BELOW"}:
        left_prev = _resolve_previous(left, state)
        right_prev = _resolve_previous(right, state)

        if left_prev is None or (isinstance(right, (str, dict)) and right_prev is None):
            return False

        if isinstance(right, (int, float)):
            rprev = float(right)
            rnow = right_now
        else:
            rprev = right_prev
            rnow = right_now

        if left_prev is None or rprev is None or left_now is None or rnow is None:
            return False

        if operator == "CROSS_ABOVE":
            return (left_prev <= rprev) and (left_now > rnow)
        return (left_prev >= rprev) and (left_now < rnow)

    if left_now is None or right_now is None:
        return False

    if operator == "<":
        return left_now < right_now
    if operator == ">":
        return left_now > right_now
    if operator == "<=":
        return left_now <= right_now
    if operator == ">=":
        return left_now >= right_now
    if operator == "==":
        return math.isclose(left_now, right_now, rel_tol=1e-5, abs_tol=1e-8)
    if operator == "!=":
        return not math.isclose(left_now, right_now, rel_tol=1e-5, abs_tol=1e-8)

    raise ValueError(f"Unknown comparison operator: {operator}")


def evaluate_node(node: Dict[str, Any], indicators: Dict[str, Any], state: EvaluatorState) -> bool:
    """Recursively evaluate an AST node."""
    if not isinstance(node, dict):
        raise ValueError("AST node must be a dictionary")

    node_type = node.get("type")
    if node_type == "logic":
        operator = node.get("operator")
        conditions = node.get("conditions", [])
        if operator == "AND":
            return all(evaluate_node(c, indicators, state) for c in conditions)
        if operator == "OR":
            return any(evaluate_node(c, indicators, state) for c in conditions)
        if operator == "NOT":
            return not any(evaluate_node(c, indicators, state) for c in conditions)
        raise ValueError(f"Unknown logical operator: {operator}")

    if node_type == "comparison":
        left = node.get("left")
        operator = node.get("operator")
        right = node.get("right")
        if left is None or operator is None or right is None:
            raise ValueError("Invalid comparison node: missing left/operator/right")
        return _eval_comparison(left, operator, right, indicators, state)

    # Backwards-compatible AST format without explicit type
    op = node.get("operator")
    if op in {"AND", "OR", "NOT"}:
        conditions = node.get("conditions", [])
        if op == "AND":
            return all(evaluate_node(c, indicators, state) for c in conditions)
        if op == "OR":
            return any(evaluate_node(c, indicators, state) for c in conditions)
        if op == "NOT":
            return not any(evaluate_node(c, indicators, state) for c in conditions)

    left = node.get("left")
    operator = node.get("operator")
    right = node.get("right")
    if left is None or operator is None or right is None:
        raise ValueError("Invalid condition node: missing left/operator/right")

    return _eval_comparison(left, operator, right, indicators, state)


def _resolve_ast_value(
    node: Any,
    indicators: Dict[str, Any],
    state: EvaluatorState,
    market_data: Optional[Dict[str, float]]
) -> Optional[float]:
    if isinstance(node, (int, float)):
        return float(node)
    if not isinstance(node, dict):
        return None
        
    node_type = node.get("node_type", "").upper()
    if node_type == "CONSTANT":
        return float(node.get("value", 0.0))
        
    if node_type == "MARKET_REFERENCE":
        lookback = int(node.get("lookback_periods", 0))
        data_type = node.get("data_type", "CLOSE").upper()
        if lookback == 0:
            if market_data is None:
                return None
            return market_data.get(data_type)
        else:
            key = f"MARKET_{data_type}"
            return state.previous.get(key)
            
    if node_type == "INDICATOR":
        cfg = node.get("indicator_config", {})
        ind_type = cfg.get("indicator_type", "UNKNOWN")
        params = cfg.get("parameters", {})
        period = params.get("period") or params.get("timeperiod")
        
        merged_params = dict(params)
        if period is not None:
            merged_params["timeperiod"] = period
        elif "period" in cfg:
            merged_params["timeperiod"] = cfg["period"]
            
        key = _normalize_indicator_key(ind_type, merged_params)
            
        val = indicators.get(key)
        if val is None:
            val = indicators.get(cfg.get("alias", ""))
        if val is None:
            return None
            
        if isinstance(val, dict):
            return float(val.get(node.get("indicator_config", {}).get("output_property", "value"), 0.0))
        return float(val)

    if node_type in ("ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "MIN", "MAX", "ABS", "ARITHMETIC"):
        operator = node.get("operator", node_type).upper()
        if operator == "ARITHMETIC":
            operator = node_type.upper()
            
        children = node.get("children", [])
        vals = [_resolve_ast_value(c, indicators, state, market_data) for c in children]
        
        if operator != "ABS" and len(vals) < 2:
            return None
        if any(v is None for v in vals):
            return None
            
        try:
            if operator == "ADD": return vals[0] + vals[1]
            if operator == "SUBTRACT": return vals[0] - vals[1]
            if operator == "MULTIPLY": return vals[0] * vals[1]
            if operator == "DIVIDE": return vals[0] / vals[1] if vals[1] != 0 else None
            if operator == "MIN": return min(vals)
            if operator == "MAX": return max(vals)
            if operator == "ABS": return abs(vals[0])
        except Exception:
            return None
        
    return None


def _resolve_ast_value_prev(
    node: Any,
    indicators: Dict[str, Any],
    state: EvaluatorState,
    market_data: Optional[Dict[str, float]],
    lookback: int
) -> Optional[float]:
    if isinstance(node, (int, float)):
        return float(node)
    if not isinstance(node, dict):
        return None
        
    node_type = node.get("node_type", "").upper()
    if node_type == "CONSTANT":
        return float(node.get("value", 0.0))
        
    if node_type == "MARKET_REFERENCE":
        data_type = node.get("data_type", "CLOSE").upper()
        key = f"MARKET_{data_type}"
        return state.previous.get(key)
        
    if node_type == "INDICATOR":
        cfg = node.get("indicator_config", {})
        ind_type = cfg.get("indicator_type", "UNKNOWN")
        params = cfg.get("parameters", {})
        period = params.get("period") or params.get("timeperiod")
        
        merged_params = dict(params)
        if period is not None:
            merged_params["timeperiod"] = period
        elif "period" in cfg:
            merged_params["timeperiod"] = cfg["period"]
            
        key = _normalize_indicator_key(ind_type, merged_params)
            
        val = state.previous.get(key)
        if val is None:
            val = state.previous.get(cfg.get("alias", ""))
        if val is None:
            return None
            
        if isinstance(val, dict):
            out_prop = cfg.get("output_property", "value")
            return float(val.get(out_prop, 0.0))
        return float(val)
        
    return None


def evaluate_ast_node(node: Dict[str, Any], indicators: Dict[str, Any], state: EvaluatorState, market_data: Optional[Dict[str, float]]) -> bool:
    """Recursively evaluate an AST node in the NLconverter format."""
    if not isinstance(node, dict):
        return False
        
    node_type = node.get("node_type", "").upper()
    
    if node_type == "AND":
        children = node.get("children", [])
        return all(evaluate_ast_node(c, indicators, state, market_data) for c in children)
    if node_type == "OR":
        children = node.get("children", [])
        return any(evaluate_ast_node(c, indicators, state, market_data) for c in children)
    if node_type == "NOT":
        children = node.get("children", [])
        return not any(evaluate_ast_node(c, indicators, state, market_data) for c in children)
        
    if node_type in ("GREATER_THAN", "LESS_THAN", "EQUAL", "NOT_EQUAL", "GREATER_EQUAL", "LESS_EQUAL", "GREATER_THAN_EQUAL", "LESS_THAN_EQUAL"):
        children = node.get("children", [])
        if len(children) < 2:
            return False
            
        left_val = _resolve_ast_value(children[0], indicators, state, market_data)
        right_val = _resolve_ast_value(children[1], indicators, state, market_data)
        
        if left_val is None or right_val is None:
            return False
            
        if node_type == "GREATER_THAN":
            return left_val > right_val
        if node_type == "LESS_THAN":
            return left_val < right_val
        if node_type in ("GREATER_EQUAL", "GREATER_THAN_EQUAL"):
            return left_val >= right_val
        if node_type in ("LESS_EQUAL", "LESS_THAN_EQUAL"):
            return left_val <= right_val
        if node_type == "EQUAL":
            return math.isclose(left_val, right_val, rel_tol=1e-5, abs_tol=1e-8)
        if node_type == "NOT_EQUAL":
            return not math.isclose(left_val, right_val, rel_tol=1e-5, abs_tol=1e-8)
            
    if node_type in ("CROSS_ABOVE", "CROSS_BELOW"):
        children = node.get("children", [])
        if len(children) < 2:
            return False
            
        lookback = int(node.get("lookback_periods", 1))
        
        left_now = _resolve_ast_value(children[0], indicators, state, market_data)
        right_now = _resolve_ast_value(children[1], indicators, state, market_data)
        
        left_prev = _resolve_ast_value_prev(children[0], indicators, state, market_data, lookback)
        right_prev = _resolve_ast_value_prev(children[1], indicators, state, market_data, lookback)
        
        if None in (left_now, right_now, left_prev, right_prev):
            return False
            
        if node_type == "CROSS_ABOVE":
            return left_prev <= right_prev and left_now > right_now
        if node_type == "CROSS_BELOW":
            return left_prev >= right_prev and left_now < right_now

    return False

_LOG = logging.getLogger(__name__)


import collections

def get_max_lookback(node: Any, current_lookback: int = 0) -> int:
    """Recursively traverse the AST to find the maximum possible lookback requirement."""
    if node is None:
        return current_lookback

    if isinstance(node, StrategyRootNode):
        val = current_lookback
        if hasattr(node, "operation_nodes") and node.operation_nodes:
            val = max(val, *(get_max_lookback(op, 0) for op in node.operation_nodes))
        if hasattr(node, "variable_nodes") and node.variable_nodes:
            val = max(val, *(get_max_lookback(var, 0) for var in node.variable_nodes))
        return val

    if isinstance(node, OperationNode):
        val = current_lookback
        if hasattr(node, "entry_nodes") and node.entry_nodes:
            val = max(val, *(get_max_lookback(entry, 0) for entry in node.entry_nodes))
        if hasattr(node, "exit_nodes") and node.exit_nodes:
            val = max(val, *(get_max_lookback(ex, 0) for ex in node.exit_nodes))
        return val

    if isinstance(node, (EntryNode, ExitNode)):
        return get_max_lookback(getattr(node, "condition", None), 0)

    if isinstance(node, LogicNode):
        children = getattr(node, "children", []) or []
        if not children:
            return current_lookback
        return max(get_max_lookback(child, current_lookback) for child in children)

    if isinstance(node, ComparisonNode):
        lb = getattr(node, "lookback_periods", 0)
        return max(
            get_max_lookback(node.left, current_lookback + lb),
            get_max_lookback(node.right, current_lookback + lb)
        )

    if isinstance(node, CrossNode):
        lb = getattr(node, "lookback_periods", 1)
        return max(
            get_max_lookback(node.left, current_lookback + lb),
            get_max_lookback(node.right, current_lookback + lb)
        )

    if isinstance(node, SequenceNode):
        count = getattr(node, "count", 0)
        return get_max_lookback(node.condition, current_lookback + count)

    if isinstance(node, ArithmeticNode):
        children = getattr(node, "children", []) or []
        if not children:
            return current_lookback
        return max(get_max_lookback(child, current_lookback) for child in children)

    if isinstance(node, VariableAssignmentNode):
        return max(
            get_max_lookback(node.condition, current_lookback),
            get_max_lookback(node.value_node, current_lookback)
        )

    if isinstance(node, MarketReferenceNode):
        lb = getattr(node, "lookback_periods", 0)
        return current_lookback + abs(lb)

    if isinstance(node, PatternNode):
        cfg = getattr(node, "config", None)
        lb = getattr(cfg, "lookback_periods", 0) if cfg else 0
        return current_lookback + abs(lb)

    if isinstance(node, IndicatorNode):
        lb = getattr(node, "lookback_periods", 0)
        return current_lookback + abs(lb)

    return current_lookback


class SignalEvaluator:
    def __init__(self, maxlen: int = 256):
        self.variables: Dict[str, float] = {}
        self.history: collections.deque = collections.deque(maxlen=maxlen)

    @property
    def previous_state(self) -> Dict[str, float]:
        """Derive previous_state from history[-1] (the last evaluated candle snapshot)."""
        if not self.history:
            return {}
        
        indicators, market_data = self.history[-1]
        prev_state: Dict[str, float] = {}
        
        for k, v in indicators.items():
            if isinstance(v, dict):
                for out_name, out_val in v.items():
                    try:
                        prev_state[f"{k}.{out_name}"] = float(out_val)
                    except Exception:
                        pass
            else:
                try:
                    prev_state[k] = float(v)
                except Exception:
                    pass

        for field, value in market_data.items():
            try:
                prev_state[f"MARKET_{field.upper()}"] = float(value)
            except Exception:
                pass
                
        return prev_state

    @previous_state.setter
    def previous_state(self, val: Dict[str, float]) -> None:
        """Seed history with a mock snapshot based on a flat dictionary.

        WARNING: This setter is for test seeding only. Do not call this from
        inside the evaluate() loop, as calling it inside the loop will corrupt
        subsequent lookback indexing.
        """
        indicators: Dict[str, Any] = {}
        market_data: Dict[str, float] = {}
        
        for k, v in val.items():
            if k.startswith("MARKET_"):
                field = k[len("MARKET_"):]
                market_data[field] = v
            else:
                if "." in k:
                    ind_name, out_name = k.split(".", 1)
                    if ind_name not in indicators:
                        indicators[ind_name] = {}
                    indicators[ind_name][out_name] = v
                else:
                    indicators[k] = v
                    
        # Replace history[-1] if history is not empty, otherwise append
        if self.history:
            self.history[-1] = (indicators, market_data)
        else:
            self.history.append((indicators, market_data))

    def reset(self) -> None:
        """Clear state for a new backtest run."""
        self.variables.clear()
        self.history.clear()

    def configure_history(self, strategy: Any) -> None:
        """Verify the strategy's lookback requirement does not exceed maxlen."""
        max_lookback = get_max_lookback(strategy)
        if max_lookback > (self.history.maxlen or 256):
            raise ValueError(
                f"Strategy lookback requirement of {max_lookback} exceeds history buffer capacity "
                f"of {self.history.maxlen}."
            )

    def evaluate(
        self,
        strategy: Any,
        indicators: Dict[str, Any],
        market_data: Dict[str, float],
        position_side: str = "LONG",
        current_position_side: Optional[str] = None,
    ) -> SignalResult:
        """Evaluate a StrategyRootNode and return the resulting signal."""
        # Verify the strategy's lookback requirement does not exceed maxlen
        self.configure_history(strategy)

        # Append current snapshot to history
        self.history.append((indicators, market_data))

        # Backward compatibility for direct OperationNode arguments in unit tests
        if not hasattr(strategy, "variable_nodes"):
            operation = strategy
        else:
            # Evaluate variable assignments before any signal logic
            for var_node in strategy.variable_nodes:
                try:
                    if self._eval_node(var_node.condition, 0):
                        val = self._resolve_value(var_node.value_node, 0, 0)
                        if val is not None:
                            self.variables[var_node.variable_name] = val
                except Exception as exc:
                    _LOG.warning(f"Error evaluating variable assignment: {exc}")

            if not strategy.operation_nodes:
                return SignalResult(signal=SignalType.HOLD, reason={"intent": "NONE"})

            operation = strategy.operation_nodes[0]

        is_holding_position = current_position_side == position_side
        
        def _check_exit():
            for exit_node in operation.exit_nodes:
                try:
                    if self._eval_node(exit_node.condition, 0):
                        sig = SignalType.SELL if position_side == "LONG" else SignalType.BUY
                        return SignalResult(signal=sig, reason={"intent": "EXIT"})
                except Exception as exc:
                    _LOG.warning(f"Error evaluating exit condition: {exc}")
            return None
            
        def _check_entry():
            for entry in operation.entry_nodes:
                try:
                    if self._eval_node(entry.condition, 0):
                        sig = SignalType.BUY if position_side == "LONG" else SignalType.SELL
                        return SignalResult(signal=sig, reason={"intent": "ENTRY"})
                except Exception as exc:
                    _LOG.warning(f"Error evaluating entry condition: {exc}")
            return None
            
        if is_holding_position:
            res = _check_exit()
            if res: return res
            res = _check_entry()
            if res: return res
        else:
            res = _check_entry()
            if res: return res
            res = _check_exit()
            if res: return res

        return SignalResult(signal=SignalType.HOLD, reason={"intent": "NONE"})

    def _eval_node(self, node: ASTNode, current_offset: int) -> bool:
        """Recursively evaluate boolean nodes."""
        if isinstance(node, ConstantNode):
            return bool(node.value)
            
        if isinstance(node, LogicNode):
            if node.operator == "AND":
                return all(self._eval_node(c, current_offset) for c in node.children)
            if node.operator == "OR":
                return any(self._eval_node(c, current_offset) for c in node.children)
            if node.operator == "NOT":
                return not any(self._eval_node(c, current_offset) for c in node.children)
            return False

        if isinstance(node, FollowedByNode):
            if not self._eval_node(node.trigger_condition, current_offset):
                return False
            max_bars = node.max_bars_between or 50
            for offset in range(1, max_bars + 1):
                idx = current_offset + offset
                if idx >= len(self.history):
                    break
                if self._eval_node(node.setup_condition, idx):
                    return True
            return False

        if isinstance(node, ComparisonNode):
            left_val = self._resolve_value(node.left, current_offset, lookback=node.lookback_periods)
            right_val = self._resolve_value(node.right, current_offset, lookback=node.lookback_periods)
            
            if left_val is None or right_val is None:
                return False

            if node.operator == "GREATER_THAN":
                return left_val > right_val
            if node.operator == "LESS_THAN":
                return left_val < right_val
            if node.operator == "GREATER_EQUAL":
                return left_val >= right_val
            if node.operator == "LESS_EQUAL":
                return left_val <= right_val
            if node.operator == "EQUAL":
                if isinstance(left_val, str) or isinstance(right_val, str):
                    return left_val == right_val
                return math.isclose(left_val, right_val, rel_tol=1e-5, abs_tol=1e-8)
            if node.operator == "NOT_EQUAL":
                if isinstance(left_val, str) or isinstance(right_val, str):
                    return left_val != right_val
                return not math.isclose(left_val, right_val, rel_tol=1e-5, abs_tol=1e-8)

        if isinstance(node, CrossNode):
            left_now = self._resolve_value(node.left, current_offset, lookback=0)
            right_now = self._resolve_value(node.right, current_offset, lookback=0)
            
            # For lookback, we fetch the previous state (t-1)
            left_prev = self._resolve_value(node.left, current_offset, lookback=node.lookback_periods)
            right_prev = self._resolve_value(node.right, current_offset, lookback=node.lookback_periods)

            if None in (left_now, right_now, left_prev, right_prev):
                return False

            if node.cross_type == "ABOVE":
                return left_prev <= right_prev and left_now > right_now
            if node.cross_type == "BELOW":
                return left_prev >= right_prev and left_now < right_now

        if isinstance(node, SequenceNode):
            for offset in range(node.count):
                idx = current_offset + offset
                if idx >= len(self.history):
                    return False
                if not self._eval_node(node.condition, idx):
                    return False
            return True

        return False

    def _resolve_value(self, node: ASTNode, current_offset: int, lookback: int) -> Optional[Union[float, str]]:
        """Resolve a leaf node to a numeric value."""
        total_lookback = current_offset + lookback

        if total_lookback > (self.history.maxlen or 256):
            raise ValueError(
                f"Requested lookback of {total_lookback} exceeds history buffer capacity "
                f"of {self.history.maxlen}."
            )

        if isinstance(node, ConstantNode):
            return node.value

        if isinstance(node, MarketReferenceNode):
            # Effective lookback is requested lookback + node's intrinsic lookback + current_offset
            total_lookback += abs(node.lookback_periods)
            if total_lookback > (self.history.maxlen or 256):
                raise ValueError(
                    f"Requested lookback of {total_lookback} exceeds history buffer capacity "
                    f"of {self.history.maxlen}."
                )
            if total_lookback >= len(self.history):
                return None
            _, past_market_data = self.history[-(total_lookback + 1)]
            val = past_market_data.get(node.data_type.upper())
            if val is None:
                return None
            if isinstance(val, str):
                return val
            try:
                return float(val)
            except (ValueError, TypeError):
                return val

        if isinstance(node, IndicatorNode):
            key = node.config.key
            total_lookback += abs(getattr(node, "lookback_periods", 0))
            if total_lookback > (self.history.maxlen or 256):
                raise ValueError(
                    f"Requested lookback of {total_lookback} exceeds history buffer capacity "
                    f"of {self.history.maxlen}."
                )
            if total_lookback >= len(self.history):
                return None
            
            past_indicators, _ = self.history[-(total_lookback + 1)]
            val = past_indicators.get(key)

            if val is None:
                return None
                
            # Handle multi-output indicators (e.g. MACD)
            if isinstance(val, dict):
                return float(val.get(node.config.output_property, 0.0))
            return float(val)

        if isinstance(node, PatternNode):
            return 0.0

        if isinstance(node, ArithmeticNode):
            vals = [self._resolve_value(c, current_offset, lookback) for c in node.children]
            if node.operator != "ABS" and len(vals) < 2:
                return None
            if any(v is None for v in vals):
                return None
                
            try:
                if node.operator == "ADD": return vals[0] + vals[1]
                if node.operator == "SUBTRACT": return vals[0] - vals[1]
                if node.operator == "MULTIPLY": return vals[0] * vals[1]
                if node.operator == "DIVIDE": return vals[0] / vals[1] if vals[1] != 0 else None
                if node.operator == "MIN": return min(vals)
                if node.operator == "MAX": return max(vals)
                if node.operator == "ABS": return abs(vals[0])
            except Exception:
                return None

        if isinstance(node, VariableReferenceNode):
            return self.variables.get(node.variable_name)

        return None
