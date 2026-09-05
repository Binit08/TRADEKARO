"""AST Loader.

Converts the raw JSON dicts matching the NLconverter schema into typed in-memory
AST dataclasses. Validates structure during loading.
"""

import json
from typing import Any, Dict

from app.ast.nodes import (
    ASTNode, BaseNode, ComparisonNode, ConstantNode, CrossNode,
    EntryNode, ExitNode, ArithmeticNode,
    IndicatorConfig, IndicatorNode, LogicNode,
    MarketReferenceNode, OperationNode, StrategyRootNode,
    PatternNode, PatternConfig, SequenceNode, FollowedByNode,
    VariableAssignmentNode,
    FilterNode, VariableReferenceNode
)
from app.ast.bundle import ExecutionContext, StrategyBundle


class ASTLoadError(Exception):
    """Raised when the JSON cannot be mapped to the typed AST."""


class StrategyLoader:
    def load_from_json(self, raw_data: Dict[str, Any]) -> StrategyBundle:
        """Parses the root JSON into a typed StrategyBundle."""
        try:
            # Auto-wrap modern JSON payloads that don't have the explicit 'ast' and 'execution_context' wrappers
            is_unwrapped = (
                "ast" not in raw_data and 
                (
                    "operation" in raw_data or 
                    raw_data.get("node_type") == "STRATEGY_ROOT" or 
                    raw_data.get("type") == "STRATEGY_ROOT"
                )
            )
            
            if is_unwrapped:
                raw_data = {
                    "ast": raw_data,
                    "execution_context": raw_data.get("execution_context", {})
                }
                
            if "ast" not in raw_data:
                raise ValueError("Missing 'ast' root block.")
            if "execution_context" not in raw_data:
                # Provide an empty execution context if totally missing
                raw_data["execution_context"] = {}
                
            schema_version = raw_data.get("schema_version", "1.0.0")
            ctx_data = raw_data["execution_context"]
            execution_context = self._parse_execution_context(ctx_data)

            # 3. Parse AST root
            ast_data = raw_data["ast"]
            ast_root = self._parse_node(ast_data, depth=0, node_count=None)
            
            if not isinstance(ast_root, StrategyRootNode):
                raise ValueError(f"Root node must be STRATEGY_ROOT, got {type(ast_root).__name__}")

            return StrategyBundle(
                schema_version=schema_version,
                ast=ast_root,
                execution_context=execution_context
            )
        except Exception as e:
            raise ASTLoadError(f"Failed to load strategy: {e}") from e

    def _parse_execution_context(self, ctx: Dict[str, Any]) -> ExecutionContext:
        """Parses the ExecutionContext."""
        capital_data = ctx.get("capital_per_trade", {})
        capital = float(capital_data.get("amount", 100000.0)) if isinstance(capital_data, dict) else float(capital_data)

        return ExecutionContext(
            symbol=ctx.get("symbol", "UNKNOWN"),
            timeframe=ctx.get("timeframe", "1D"),
            start_date=ctx.get("start_date", "2020-01-01"),
            end_date=ctx.get("end_date", "2025-01-01"),
            capital=capital,
            position_side=ctx.get("position_side", "LONG").upper(),
            order_type=ctx.get("order_type", "MARKET").upper(),
            max_concurrent_positions=int(ctx.get("max_concurrent_positions", 1))
        )

    def _parse_node(self, node: Dict[str, Any], depth: int = 0, node_count: list[int] = None) -> BaseNode:
        """Recursively parses individual AST nodes."""
        if node_count is None:
            node_count = [0]
            
        node_count[0] += 1
        if node_count[0] > 10000:
            raise ValueError("AST has too many nodes")
            
        if depth > 64:
            raise ValueError("AST too deep")

        node_type = node.get("node_type", node.get("type", "")).upper()
        
        # If the payload is a Canonical JSON (has 'operation' key), treat it as a STRATEGY_ROOT
        if not node_type and "operation" in node:
            node_type = "STRATEGY_ROOT"
            # Canonical JSON uses "operation" instead of "operation_nodes"
            node["operation_nodes"] = node.get("operation", [])

        if node_type == "STRATEGY_ROOT":
            op_nodes = [self._parse_node(n, depth + 1, node_count) for n in node.get("operation_nodes", [])]
            valid_op_nodes = [n for n in op_nodes if isinstance(n, OperationNode)]
            
            # Backwards compatibility: if operation_nodes is empty but entry_node/exit_node exist
            if not valid_op_nodes:
                legacy_entry = node.get("entry_node")
                legacy_exit = node.get("exit_node")
                
                if legacy_entry or legacy_exit:
                    parsed_entry = self._parse_node(legacy_entry, depth + 1, node_count) if legacy_entry else None
                    parsed_exit = self._parse_node(legacy_exit, depth + 1, node_count) if legacy_exit else None
                    
                    entries = [parsed_entry] if isinstance(parsed_entry, EntryNode) else []
                    exits = [parsed_exit] if isinstance(parsed_exit, ExitNode) else []
                    
                    if entries or exits:
                        valid_op_nodes = [OperationNode(entry_nodes=entries, exit_nodes=exits)]

            variable_nodes = []
            for n in node.get("variable_nodes", []):
                try:
                    parsed_var = self._parse_node(n, depth + 1, node_count)
                    if isinstance(parsed_var, VariableAssignmentNode):
                        variable_nodes.append(parsed_var)
                except Exception as e:
                    pass

            filter_nodes = []
            for n in node.get("filter_nodes", []):
                try:
                    parsed_filter = self._parse_node(n, depth + 1, node_count)
                    if isinstance(parsed_filter, FilterNode):
                        filter_nodes.append(parsed_filter)
                except Exception as e:
                    pass

            return StrategyRootNode(
                strategy_id=node.get("strategy_id", "unknown_strategy"),
                operation_nodes=valid_op_nodes,
                variable_nodes=variable_nodes,
                filter_nodes=filter_nodes
            )

        if not node_type and ("entry" in node or "exit" in node):
            node_type = "OPERATION"
            
        if node_type == "OPERATION":
            entry_list = node.get("entry_nodes", node.get("entry", []))
            exit_list = node.get("exit_nodes", node.get("exit", []))
            
            entries = []
            for n in entry_list:
                parsed = self._parse_node(n, depth + 1, node_count)
                if not isinstance(parsed, EntryNode):
                    parsed = EntryNode(condition=parsed)
                entries.append(parsed)
                
            exits = []
            for n in exit_list:
                parsed = self._parse_node(n, depth + 1, node_count)
                if not isinstance(parsed, ExitNode):
                    parsed = ExitNode(condition=parsed)
                exits.append(parsed)
                
            return OperationNode(
                entry_nodes=entries,
                exit_nodes=exits
            )

        if node_type == "FILTER":
            children = node.get("children", [])
            if not children:
                raise ValueError("Filter node must have children")
            return FilterNode(
                condition=self._parse_node(children[0], depth + 1, node_count)
            )

        if node_type == "ENTRY":
            children = node.get("children", [])
            if not children:
                raise ValueError("ENTRY node missing children.")
            return EntryNode(condition=self._parse_node(children[0], depth + 1, node_count))

        if node_type == "EXIT":
            children = node.get("children", [])
            if not children:
                raise ValueError("EXIT node missing children.")
            return ExitNode(condition=self._parse_node(children[0], depth + 1, node_count))

        if node_type in ("AND", "OR", "NOT"):
            children = [self._parse_node(n, depth + 1, node_count) for n in node.get("children", [])]
            return LogicNode(operator=node_type, children=children)

        if node_type in ("ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "MIN", "MAX", "ABS", "ARITHMETIC"):
            operator = node.get("operator", node_type).upper()
            if operator == "ARITHMETIC":
                operator = node_type.upper()
            children = [self._parse_node(n, depth + 1, node_count) for n in node.get("children", [])]
            return ArithmeticNode(operator=operator, children=children)

        if node_type in ("GREATER_THAN", "LESS_THAN", "EQUAL", "NOT_EQUAL", "GREATER_EQUAL", "LESS_EQUAL", "GREATER_THAN_EQUAL", "LESS_THAN_EQUAL"):
            children = node.get("children", [])
            # Map canonical JSON operand_1 and operand_2 to children
            if not children and "operand_1" in node and "operand_2" in node:
                children = [node["operand_1"], node["operand_2"]]
                
            if len(children) < 2:
                raise ValueError(f"{node_type} node requires 2 children or operands.")
            op = node_type
            if op == "LESS_THAN_EQUAL":
                op = "LESS_EQUAL"
            elif op == "GREATER_THAN_EQUAL":
                op = "GREATER_EQUAL"
            left_node = self._parse_node(children[0], depth + 1, node_count)
            right_node = self._parse_node(children[1], depth + 1, node_count)
            lookback = int(node.get("lookback_periods", 0))

            # Semantic normalization: If the NL converter places lookback on the comparison,
            # but we are comparing a raw MarketReference to an Indicator, shift the lookback 
            # to the Indicator. `Close[1] > MAX[1]` is usually false, they mean `Close[0] > MAX[1]`.
            if lookback > 0 and isinstance(left_node, MarketReferenceNode) and getattr(left_node, "lookback_periods", 0) == 0:
                if isinstance(right_node, IndicatorNode) and getattr(right_node, "lookback_periods", 0) == 0:
                    right_node = IndicatorNode(config=right_node.config, lookback_periods=lookback)
                    lookback = 0
                # Same for exit conditions comparing Close to Entry Price math
                elif isinstance(right_node, ArithmeticNode):
                    lookback = 0

            return ComparisonNode(
                operator=op,
                left=left_node,
                right=right_node,
                lookback_periods=lookback
            )

        if node_type in ("CROSS_ABOVE", "CROSS_BELOW"):
            children = node.get("children", [])
            # Map canonical JSON operand_1 and operand_2 to children
            if not children and "operand_1" in node and "operand_2" in node:
                children = [node["operand_1"], node["operand_2"]]
                
            if len(children) < 2:
                raise ValueError(f"{node_type} node requires 2 children or operands.")
            cross_type = "ABOVE" if node_type == "CROSS_ABOVE" else "BELOW"
            # Some schemas use explicit cross_type, some just encode it in node_type
            if "cross_type" in node:
                cross_type = node["cross_type"]
            return CrossNode(
                cross_type=cross_type,
                left=self._parse_node(children[0], depth + 1, node_count),
                right=self._parse_node(children[1], depth + 1, node_count),
                lookback_periods=node.get("lookback_periods", 1)
            )

        if node_type == "FOLLOWED_BY":
            return FollowedByNode(
                max_bars_between=node.get("max_bars_between"),
                setup_condition=self._parse_node(node.get("setup_condition", {}), depth + 1, node_count),
                trigger_condition=self._parse_node(node.get("trigger_condition", {}), depth + 1, node_count)
            )

        if node_type == "SEQUENCE":
            condition = node.get("condition")
            if not condition:
                raise ValueError("SEQUENCE node requires a condition.")
            count = int(node.get("count", 1))
            if count < 1:
                raise ValueError("SEQUENCE node count must be >= 1.")
            return SequenceNode(
                condition=self._parse_node(condition, depth + 1, node_count),
                count=count,
                direction=node.get("direction", "BACKWARD"),
                aggregate=node.get("aggregate")
            )

        if node_type == "INDICATOR":
            cfg = node.get("indicator_config", {})
            params = cfg.get("parameters", {})
            period = params.get("period") or params.get("timeperiod")
            config = IndicatorConfig(
                indicator_type=cfg.get("indicator_type", node.get("indicator_id", "UNKNOWN")),
                period=int(period) if period is not None else None,
                output_property=cfg.get("output_property", node.get("property", "value")),
                timeframe=cfg.get("timeframe", "1D"),
                parameters=params,
                input_node=self._parse_node(node.get("input_node"), depth + 1, node_count) if node.get("input_node") else None
            )
            return IndicatorNode(
                config=config,
                lookback_periods=int(node.get("lookback_periods", 0))
            )

        if node_type in ("MARKET_REFERENCE", "MARKET_DATA"):
            return MarketReferenceNode(
                data_type=node.get("data_type", "CLOSE").upper(),
                lookback_periods=int(node.get("lookback_periods", node.get("lookback", 0))),
                timeframe=node.get("timeframe", "1D")
            )
            
        if node_type == "PATTERN":
            cfg = node.get("pattern_config", {})
            return PatternNode(
                config=PatternConfig(
                    pattern_type=cfg.get("pattern_type", "UNKNOWN"),
                    lookback_periods=int(cfg.get("lookback_periods", 0)),
                    parameters=cfg.get("parameters", {})
                )
            )

        if node_type == "CONSTANT":
            val = node.get("value", 0.0)
            if isinstance(val, str):
                try:
                    val = float(val)
                except ValueError:
                    pass
            return ConstantNode(value=val)
            
        # Safely ignore STOP_LOSS and TAKE_PROFIT as signal nodes (they belong in risk_management)
        if node_type in ("STOP_LOSS", "TAKE_PROFIT"):
            return ConstantNode(value=0.0)

        if node_type == "VARIABLE_ASSIGNMENT":
            children = node.get("children", [])
            if len(children) < 2:
                raise ValueError("VARIABLE_ASSIGNMENT node requires 2 children (condition and value).")
            return VariableAssignmentNode(
                variable_name=node.get("variable_name", ""),
                condition=self._parse_node(children[0], depth + 1, node_count),
                value_node=self._parse_node(children[1], depth + 1, node_count)
            )

        if node_type == "VARIABLE_REFERENCE":
            return VariableReferenceNode(
                variable_name=node.get("variable_name", "")
            )

        # Ignore unhandled nodes like MULTIPLE, RISK_REWARD for MVP signal logic
        raise ValueError(f"Unsupported node_type: {node_type}")
