"""
AST Builder - deterministic Canonical JSON to AST transformation.

This module contains no LLM calls and no strategy evaluation logic. It maps a
validated canonical JSON document into a stable data-only AST.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from .ast_nodes import (
    ASTNode,
    ASTNodeMetadata,
    ASTNodeRegistry,
    EntryNode,
    ExitNode,
    FilterNode,
    OperationNode,
    StrategyRootNode,
)


class ASTBuildError(ValueError):
    """Raised when canonical JSON cannot be converted to an AST."""

    def __init__(
        self,
        message: str,
        source_path: str = "",
        node_type: Optional[str] = None,
    ) -> None:
        self.source_path = source_path
        self.node_type = node_type
        details = message
        if node_type:
            details = f"{details} (node_type={node_type})"
        if source_path:
            details = f"{details} at {source_path}"
        super().__init__(details)


ConditionBuilder = Callable[[Dict[str, Any], str], ASTNode]
OperandBuilder = Callable[[Dict[str, Any], str], ASTNode]
RiskBuilder = Callable[[Dict[str, Any], str], ASTNode]

from .builders.condition_builder import ConditionBuilderMixin
from .builders.operand_builder import OperandBuilderMixin
from .builders.risk_builder import RiskBuilderMixin


class ASTBuilder(ConditionBuilderMixin, OperandBuilderMixin, RiskBuilderMixin):
    """
    Converts Canonical JSON to an AST.

    The builder is deterministic:
    - no LLM calls
    - no timestamps
    - stable node IDs from traversal order
    - stable content hashes from sorted JSON
    """

    def __init__(self) -> None:
        self.node_counter: Dict[str, int] = {}
        self.signal_registry: Dict[str, Dict[str, Any]] = {}
        self.deterministic_schema: Dict[str, Any] = {}
        self.deterministic_indicator_registry: Dict[str, Dict[str, Any]] = {}

        self.condition_builders: Dict[str, ConditionBuilder] = {}
        self.operand_builders: Dict[str, OperandBuilder] = {}
        self.risk_builders: Dict[str, RiskBuilder] = {}

        self._register_builtin_builders()

    def register_condition_builder(
        self,
        node_type: str,
        builder: ConditionBuilder,
    ) -> None:
        """Register an extension condition builder."""
        self.condition_builders[ASTNodeRegistry.normalize(node_type)] = builder

    def register_operand_builder(self, node_type: str, builder: OperandBuilder) -> None:
        """Register an extension operand builder."""
        self.operand_builders[ASTNodeRegistry.normalize(node_type)] = builder

    def register_risk_builder(self, node_type: str, builder: RiskBuilder) -> None:
        """Register an extension risk builder."""
        self.risk_builders[ASTNodeRegistry.normalize(node_type)] = builder

    def build(
        self,
        canonical_json: Dict[str, Any],
        strategy_id: Optional[str] = "default",
        deterministic_schema: Optional[Dict[str, Any]] = None,
        settings_json: Optional[Dict[str, Any]] = None,
    ) -> StrategyRootNode:
        """
        Convert canonical JSON into a StrategyRootNode.

        Args:
            canonical_json: Validated canonical strategy JSON.
            strategy_id: Optional externally supplied strategy identifier.
            deterministic_schema: Deterministic schema JSON with timeframe, market_type, etc.
            settings_json: Deprecated alias for deterministic_schema (backward compat).
        """
        if not isinstance(canonical_json, dict):
            raise ASTBuildError("Canonical JSON must be an object")

        resolved_det_schema = deterministic_schema or settings_json

        self.node_counter = {}
        self.signal_registry = self._build_signal_registry(canonical_json)
        self.deterministic_schema = self._build_deterministic_context(resolved_det_schema)
        self.deterministic_indicator_registry = self._build_deterministic_indicator_registry(self.deterministic_schema)

        resolved_strategy_id = self._resolve_strategy_id(canonical_json, strategy_id)
        root = StrategyRootNode(
            node_id=f"strategy_{self._slug(resolved_strategy_id)}",
            strategy_id=resolved_strategy_id,
            metadata=self._metadata("", canonical_json),
        )

        # Check operation (new schema format)
        operation_list = canonical_json.get("operation")
        if isinstance(operation_list, list) and len(operation_list) > 0:
            for op_idx, operation in enumerate(operation_list):
                if not isinstance(operation, dict):
                    continue

                op_node = OperationNode(
                    node_id=self._generate_node_id("OPERATION"),
                    metadata=self._metadata(f"operation[{op_idx}]", operation),
                )

                # entry is a list of condition nodes in the new schema
                entry_list = operation.get("entry") or []
                if isinstance(entry_list, dict):
                    entry_list = [entry_list]
                for entry_idx, entry_data in enumerate(entry_list):
                    if self._has_buildable_condition(entry_data) and isinstance(entry_data, dict):
                        built_entry = self._build_core_wrapper(
                            EntryNode,
                            entry_data,
                            f"operation[{op_idx}].entry[{entry_idx}]",
                            "ENTRY",
                        )
                        op_node.entry_nodes.append(built_entry)

                # exit is a list of condition nodes in the new schema
                exit_list = operation.get("exit") or []
                if isinstance(exit_list, dict):
                    exit_list = [exit_list]
                for exit_idx, exit_data in enumerate(exit_list):
                    if self._has_buildable_condition(exit_data) and isinstance(exit_data, dict):
                        built_exit = self._build_core_wrapper(
                            ExitNode,
                            exit_data,
                            f"operation[{op_idx}].exit[{exit_idx}]",
                            "EXIT",
                        )
                        op_node.exit_nodes.append(built_exit)

                root.operation_nodes.append(op_node)

            # Assign single references for backward compatibility only if not compiling operation nodes
            # (Keeping them None to avoid duplicate entry/exit declarations floating in StrategyRootNode)
            pass
        else:
            # Fallback to conditions (old format)
            conditions = canonical_json.get("conditions") or {}
            if not isinstance(conditions, dict):
                raise ASTBuildError("'conditions' must be an object", "conditions")

            entry_data = conditions.get("entry")
            if self._has_buildable_condition(entry_data) and isinstance(entry_data, dict):
                root.entry_node = self._build_core_wrapper(
                    EntryNode,
                    entry_data,
                    "conditions.entry",
                    "ENTRY",
                )

            exit_data = conditions.get("exit")
            if self._has_buildable_condition(exit_data) and isinstance(exit_data, dict):
                root.exit_node = self._build_core_wrapper(
                    ExitNode,
                    exit_data,
                    "conditions.exit",
                    "EXIT",
                )

        risk_data = canonical_json.get("risk") or {}
        if risk_data:
            root.risk_node = self._build_risk_tree(risk_data, "risk")

        filters_data = canonical_json.get("filters") or []
        if isinstance(filters_data, dict):
            filters_data = [filters_data]
        if not isinstance(filters_data, list):
            raise ASTBuildError("'filters' must be a list or object", "filters")

        for index, filter_data in enumerate(filters_data):
            if self._has_buildable_condition(filter_data):
                root.filter_nodes.append(
                    self._build_core_wrapper(
                        FilterNode,
                        filter_data,
                        f"filters[{index}]",
                        "FILTER",
                    )
                )

        variables_data = canonical_json.get("variables") or []
        if isinstance(variables_data, dict):
            variables_data = [variables_data]
        if not isinstance(variables_data, list):
            raise ASTBuildError("'variables' must be a list or object", "variables")

        for index, var_data in enumerate(variables_data):
            if isinstance(var_data, dict) and var_data.get("type", "").upper() == "VARIABLE_ASSIGNMENT":
                root.variable_nodes.append(
                    self._build_variable_assignment_node(
                        var_data,
                        f"variables[{index}]"
                    )
                )

        return root

    def _register_builtin_builders(self) -> None:
        for node_type in ("AND", "OR", "NOT"):
            self.register_condition_builder(node_type, self._build_logical_node)

        for node_type in (
            "GREATER_THAN",
            "LESS_THAN",
            "GREATER_THAN_EQUAL",
            "LESS_THAN_EQUAL",
            "EQUAL",
            "NOT_EQUAL",
            "GT",
            "LT",
            "GTE",
            "LTE",
            "EQ",
            "NEQ",
        ):
            self.register_condition_builder(node_type, self._build_comparison_node)

        for node_type in ("CROSS_ABOVE", "CROSS_BELOW"):
            self.register_condition_builder(node_type, self._build_cross_node)

        self.register_condition_builder("SEQUENCE", self._build_sequence_node)
        self.register_condition_builder("FOLLOWED_BY", self._build_followed_by_node)

        for node_type in ("TIME", "DATE", "SESSION", "DAY_OF_WEEK"):
            self.register_condition_builder(node_type, self._build_time_node)

        for node_type in (
            "INDICATOR",
            "CONSTANT",
            "MARKET_REFERENCE",
            "MARKET_DATA",
            "PATTERN",
            "ARITHMETIC",
            "ADD",
            "SUBTRACT",
            "MULTIPLY",
            "DIVIDE",
            "MIN",
            "MAX",
            "ABS",
            "SUB",
            "MUL",
            "DIV",
            "VARIABLE_REFERENCE",
        ):
            self.register_operand_builder(node_type, self._build_operand_by_type)

        for node_type in (
            "STOP_LOSS",
            "TAKE_PROFIT",
            "TRAILING_STOP",
            "POSITION_SIZE",
            "RISK_REWARD",
            "MAX_DRAWDOWN",
            "MAX_DAILY_LOSS",
            "MAX_OPEN_TRADES",
            "CAPITAL_ALLOCATION",
        ):
            self.register_risk_builder(node_type, self._build_risk_node_by_type)

    def _build_core_wrapper(
        self,
        wrapper_class: type,
        node_data: Dict[str, Any],
        source_path: str,
        id_type: str,
    ) -> ASTNode:
        wrapper = wrapper_class(
            node_id=self._generate_node_id(id_type),
            metadata=self._metadata(source_path, node_data),
        )
        wrapper.children.append(self._build_condition_tree(node_data, source_path))
        return wrapper

    def _build_condition_tree(self, node_data: Dict[str, Any], source_path: str) -> ASTNode:
        """Recursively build a condition tree."""
        if not isinstance(node_data, dict):
            raise ASTBuildError("Condition node must be an object", source_path)

        raw_type = node_data.get("type")
        if not raw_type:
            raise ASTBuildError("Missing required field 'type'", source_path)

        node_type = ASTNodeRegistry.normalize(raw_type)
        builder = self.condition_builders.get(node_type)
        if not builder:
            if node_type in self.operand_builders:
                return self._build_operand(node_data, source_path)
            raise ASTBuildError("Unknown condition type", source_path, node_type)

        return builder(node_data, source_path)

    def _binary_operands(
        self,
        node_data: Dict[str, Any],
        source_path: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        left = (
            node_data.get("operand_1")
            or node_data.get("left")
            or node_data.get("lhs")
        )
        right = (
            node_data.get("operand_2")
            or node_data.get("right")
            or node_data.get("rhs")
        )

        operands = node_data.get("operands")
        if (left is None or right is None) and isinstance(operands, list):
            if len(operands) != 2:
                raise ASTBuildError("Binary node requires exactly two operands", source_path)
            left, right = operands

        if left is None:
            raise ASTBuildError("Missing left operand", f"{source_path}.operand_1")
        if right is None:
            raise ASTBuildError("Missing right operand", f"{source_path}.operand_2")
        return left, right

    def _build_signal_registry(self, canonical_json: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        signals = canonical_json.get("signals") or {}
        indicators = signals.get("indicators", []) if isinstance(signals, dict) else []
        registry: Dict[str, Dict[str, Any]] = {}
        if not isinstance(indicators, list):
            return registry
        for index, indicator in enumerate(indicators):
            if not isinstance(indicator, dict):
                continue
            indicator_id = indicator.get("id") or indicator.get("indicator_id") or f"indicator_{index}"
            registry[str(indicator_id)] = dict(indicator)
        return registry

    def _build_deterministic_context(
        self,
        deterministic_schema: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if deterministic_schema is None:
            return {}
        if not isinstance(deterministic_schema, dict):
            raise ASTBuildError("Deterministic schema must be an object")
        return dict(deterministic_schema)

    def _build_deterministic_indicator_registry(
        self,
        deterministic_schema: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        signals = deterministic_schema.get("signals") or {}
        indicators: List[Dict[str, Any]] = []
        if isinstance(signals, dict):
            indicators = signals.get("indicators") or []
        if not isinstance(indicators, list):
            indicators = []
        registry: Dict[str, Dict[str, Any]] = {}
        if not isinstance(indicators, list):
            return registry
        for index, indicator in enumerate(indicators):
            if not isinstance(indicator, dict):
                continue
            indicator_id = indicator.get("id") or indicator.get("indicator_id") or f"indicator_{index}"
            registry[str(indicator_id)] = dict(indicator)
        return registry

    def _lookup_indicator_signal(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        signal_ref = (
            indicator_data.get("indicator_ref")
            or indicator_data.get("indicator_id")
            or indicator_data.get("ref")
        )
        if signal_ref is None:
            return {}

        signal = self.signal_registry.get(str(signal_ref))
        if signal:
            return signal
        return self.deterministic_indicator_registry.get(str(signal_ref), {})

    def _get_execution_context(self, key: str) -> Optional[Any]:
        """Safely read a value from deterministic_schema.execution_context."""
        ec = self.deterministic_schema.get("execution_context")
        if isinstance(ec, dict):
            return ec.get(key)
        return None

    def _lookup_deterministic_timeframe(self, indicator_data: Dict[str, Any]) -> Optional[str]:
        """Look up timeframe from deterministic schema indicator registry."""
        signal_ref = (
            indicator_data.get("indicator_ref")
            or indicator_data.get("indicator_id")
            or indicator_data.get("ref")
        )
        if signal_ref:
            det_indicator = self.deterministic_indicator_registry.get(str(signal_ref), {})
            tf = det_indicator.get("timeframe")
            if tf:
                return str(tf)
        return None

    def _resolve_strategy_id(
        self,
        canonical_json: Dict[str, Any],
        strategy_id: Optional[str],
    ) -> str:
        if strategy_id and strategy_id != "default":
            return str(strategy_id)
        metadata = canonical_json.get("metadata") or {}
        return str(
            canonical_json.get("strategy_id")
            or canonical_json.get("id")
            or metadata.get("strategy_id")
            or metadata.get("id")
            or strategy_id
            or "default"
        )

    def _has_buildable_condition(self, node_data: Any) -> bool:
        if not isinstance(node_data, dict):
            return False
        if not node_data.get("type"):
            return False
        parse_status = node_data.get("parse_status") or {}
        if parse_status.get("state") == "NOT_APPLICABLE":
            return False
        return True

    def _has_buildable_risk_value(self, value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        raw_type = value.get("type")
        if raw_type is None:
            return False
        return str(raw_type).strip() != ""

    def _normalize_operand_type(self, node_type: str) -> str:
        raw = str(node_type).upper()
        lower_aliases = {
            "INDICATOR": "INDICATOR",
            "MARKET_DATA": "MARKET_REFERENCE",
            "MARKET_REFERENCE": "MARKET_REFERENCE",
            "CONSTANT": "CONSTANT",
            "PATTERN": "PATTERN",
            "ARITHMETIC": "ARITHMETIC",
        }
        return lower_aliases.get(raw, ASTNodeRegistry.normalize(raw))

    def _metadata(self, source_path: str, node_data: Optional[Dict[str, Any]] = None) -> ASTNodeMetadata:
        nd = node_data or {}
        metadata = ASTNodeMetadata(source_path=source_path)
        existing_meta = nd.get("metadata")
        if isinstance(existing_meta, dict):
            metadata.created_at = str(existing_meta.get("created_at", ""))
            metadata.version = str(existing_meta.get("version", "1.0.0"))
            metadata.tags = dict(existing_meta.get("tags", {}))
        return metadata

    def _generate_node_id(self, node_type: str) -> str:
        """Generate a stable node ID from normalized type and traversal order."""
        normalized = ASTNodeRegistry.normalize(node_type)
        counter = self.node_counter.get(normalized, 0)
        self.node_counter[normalized] = counter + 1
        return f"{self._slug(normalized)}_{counter}"

    def _slug(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_") or "node"
