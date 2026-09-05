"""
AST serialization and versioning.

The serializer preserves structure only. It does not attach runtime state or
evaluation results from the backtesting engine.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from .ast_nodes import (
    ASTNode,
    ASTNodeMetadata,
    ASTNodeRegistry,
    ArithmeticNode,
    CapitalAllocationNode,
    ComparisonNode,
    ConstantNode,
    CrossNode,
    DateNode,
    DayOfWeekNode,
    IndicatorConfig,
    IndicatorNode,
    MarketReferenceNode,
    MaxDailyLossNode,
    MaxDrawdownNode,
    MaxOpenTradesNode,
    PatternConfig,
    PatternNode,
    PositionSizeConfig,
    PositionSizeNode,
    RiskRewardNode,
    SessionNode,
    StopLossConfig,
    StopLossNode,
    StrategyRootNode,
    OperationNode,
    TakeProfitConfig,
    TakeProfitNode,
    TimeNode,
    TrailingStopNode,
    MultipleNode,
    ReferenceIndicatorNode,
    SequenceNode,
    VariableAssignmentNode,
    VariableReferenceNode,
)


class ASTSerializer:
    """Serialize and deserialize AST nodes to and from dictionaries/JSON."""

    @staticmethod
    def to_dict(node: Optional[ASTNode]) -> Optional[Dict[str, Any]]:
        """Convert an AST node to a serializable dictionary."""
        if node is None:
            return None

        result: Dict[str, Any] = {
            "node_type": node.node_type,
            "node_id": node.node_id,
        }

        if isinstance(node, StrategyRootNode):
            result["strategy_id"] = node.strategy_id
            if node.entry_node:
                result["entry_node"] = ASTSerializer.to_dict(node.entry_node)
            if node.exit_node:
                result["exit_node"] = ASTSerializer.to_dict(node.exit_node)
            if node.risk_node:
                result["risk_node"] = ASTSerializer.to_dict(node.risk_node)
            result["filter_nodes"] = [
                ASTSerializer.to_dict(filter_node)
                for filter_node in node.filter_nodes
            ]
            result["variable_nodes"] = [
                ASTSerializer.to_dict(var_node)
                for var_node in node.variable_nodes
            ]
            result["operation_nodes"] = [
                ASTSerializer.to_dict(op_node)
                for op_node in node.operation_nodes
            ]
        else:
            ASTSerializer._add_node_fields(node, result)
            if node.children and not isinstance(node, SequenceNode):
                result["children"] = [
                    ASTSerializer.to_dict(child)
                    for child in node.children
                ]

        if node.metadata:
            result["metadata"] = ASTSerializer._metadata_to_dict(node.metadata)

        return result

    @staticmethod
    def to_versioned_dict(node: ASTNode) -> Dict[str, Any]:
        """Return a version envelope containing the serialized AST."""
        ast_dict = ASTSerializer.to_dict(node)
        return {
            "_version_info": {
                "ast_schema_version": ASTVersionManager.CURRENT_AST_VERSION,
            },
            "ast": ast_dict,
        }

    @staticmethod
    def to_json(node: ASTNode, include_version: bool = False) -> str:
        """Serialize an AST node to a stable JSON string."""
        data = ASTSerializer.to_versioned_dict(node) if include_version else ASTSerializer.to_dict(node)
        return json.dumps(data, indent=2, sort_keys=True, default=str)

    @staticmethod
    def to_file(node: ASTNode, filepath: str, include_version: bool = True) -> None:
        """Save an AST node to a JSON file."""
        Path(filepath).write_text(ASTSerializer.to_json(node, include_version=include_version))

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Optional[ASTNode]:
        """Reconstruct an AST node from a dictionary."""
        if not data:
            return None

        if "ast" in data and "_version_info" in data:
            ast_data = data["ast"]
            if not isinstance(ast_data, dict):
                return None
            data = ast_data

        node_type = ASTNodeRegistry.normalize(data.get("node_type", ""))
        node_id = data.get("node_id")
        if not node_type:
            raise ValueError("Serialized AST node is missing 'node_type'")
        if not node_id:
            raise ValueError(f"Serialized AST node {node_type} is missing 'node_id'")

        metadata = ASTSerializer._metadata_from_dict(data.get("metadata"))

        if node_type == "STRATEGY_ROOT":
            node = StrategyRootNode(
                node_id=node_id,
                metadata=metadata,
                strategy_id=str(data.get("strategy_id", "")),
                entry_node=ASTSerializer.from_dict(data.get("entry_node") if isinstance(data.get("entry_node"), dict) else None),  # type: ignore[arg-type]
                exit_node=ASTSerializer.from_dict(data.get("exit_node") if isinstance(data.get("exit_node"), dict) else None),  # type: ignore[arg-type]
                risk_node=ASTSerializer.from_dict(data.get("risk_node") if isinstance(data.get("risk_node"), dict) else None),  # type: ignore[arg-type]
                filter_nodes=[
                    filter_node
                    for filter_node in (
                        ASTSerializer.from_dict(item) if isinstance(item, dict) else None
                        for item in data.get("filter_nodes", [])
                    )
                    if filter_node is not None
                ],
                # pyrefly: ignore [unexpected-keyword]
                variable_nodes=[
                    var_node
                    for var_node in (
                        ASTSerializer.from_dict(item) if isinstance(item, dict) else None
                        for item in data.get("variable_nodes", [])
                    )
                    if var_node is not None
                ],
                operation_nodes=[
                    op_node
                    for op_node in (
                        ASTSerializer.from_dict(item) if isinstance(item, dict) else None
                        for item in data.get("operation_nodes", [])
                    )
                    if op_node is not None
                ],
            )
            return node  # type: ignore[return-value]

        node = ASTSerializer._instantiate_node(node_type, node_id, metadata, data)  # type: ignore[assignment]
        node.children = [
            child
            for child in (
                ASTSerializer.from_dict(item) if isinstance(item, dict) else None
                for item in data.get("children", [])
            )
            if child is not None
        ]
        return node

    @staticmethod
    def from_json(json_str: str) -> ASTNode:
        """Deserialize an AST from JSON."""
        node = ASTSerializer.from_dict(json.loads(json_str))
        if node is None:
            raise ValueError("Serialized AST is empty")
        return node

    @staticmethod
    def from_file(filepath: str) -> ASTNode:
        """Load an AST from a JSON file."""
        return ASTSerializer.from_json(Path(filepath).read_text())

    @staticmethod
    def _add_node_fields(node: ASTNode, result: Dict[str, Any]) -> None:
        if isinstance(node, OperationNode):
            result["entry_nodes"] = [
                ASTSerializer.to_dict(entry_node)
                for entry_node in node.entry_nodes
            ]
            result["exit_nodes"] = [
                ASTSerializer.to_dict(exit_node)
                for exit_node in node.exit_nodes
            ]
        elif isinstance(node, IndicatorNode):
            result["indicator_config"] = (
                asdict(node.indicator_config)
                if node.indicator_config
                else None
            )
        elif isinstance(node, ConstantNode):
            result["value"] = node.value
        elif isinstance(node, MarketReferenceNode):
            result["data_type"] = node.data_type
            result["lookback_periods"] = node.lookback_periods
            result["timeframe"] = node.timeframe
        elif isinstance(node, PatternNode):
            result["pattern_config"] = (
                asdict(node.pattern_config)
                if node.pattern_config
                else None
            )
        elif isinstance(node, ComparisonNode):
            result["operator"] = node.operator
            result["lookback_periods"] = node.lookback_periods
        elif isinstance(node, ArithmeticNode):
            result["operator"] = node.operator
        elif isinstance(node, SequenceNode):
            result["count"] = node.count
            result["direction"] = node.direction
            if node.children:
                result["condition"] = ASTSerializer.to_dict(node.children[0])
        elif isinstance(node, CrossNode):
            result["cross_type"] = node.cross_type
            result["lookback_periods"] = node.lookback_periods
        elif isinstance(node, StopLossNode):
            result["config"] = asdict(node.config) if node.config else None
        elif isinstance(node, TakeProfitNode):
            result["config"] = asdict(node.config) if node.config else None
        elif isinstance(node, PositionSizeNode):
            result["config"] = asdict(node.config) if node.config else None
        elif isinstance(node, TrailingStopNode):
            result["trail_amount"] = node.trail_amount
            result["trail_type"] = node.trail_type
            result["reference"] = node.reference
            result["indicator_ref"] = node.indicator_ref
        elif isinstance(node, MultipleNode):
            result["value"] = node.value
        elif isinstance(node, ReferenceIndicatorNode):
            result["indicator_ref"] = node.indicator_ref
        elif isinstance(node, RiskRewardNode):
            result["ratio"] = node.ratio
        elif isinstance(node, TimeNode):
            result["start_time"] = node.start_time
            result["end_time"] = node.end_time
            result["timezone"] = node.timezone
        elif isinstance(node, DateNode):
            result["start_date"] = node.start_date
            result["end_date"] = node.end_date
        elif isinstance(node, SessionNode):
            result["sessions"] = node.sessions
        elif isinstance(node, DayOfWeekNode):
            result["days"] = node.days
        elif isinstance(node, MaxDrawdownNode):
            result["max_drawdown_percent"] = node.max_drawdown_percent
        elif isinstance(node, MaxDailyLossNode):
            result["max_loss_amount"] = node.max_loss_amount
        elif isinstance(node, MaxOpenTradesNode):
            result["max_trades"] = node.max_trades
        elif isinstance(node, CapitalAllocationNode):
            result["allocation_percent"] = node.allocation_percent
        elif isinstance(node, VariableAssignmentNode):
            result["variable_name"] = node.variable_name
        elif isinstance(node, VariableReferenceNode):
            result["variable_name"] = node.variable_name

    @staticmethod
    def _instantiate_node(
        node_type: str,
        node_id: str,
        metadata: ASTNodeMetadata,
        data: Dict[str, Any],
    ) -> ASTNode:
        if node_type == "OPERATION":
            return OperationNode(
                node_id=node_id,
                metadata=metadata,
                entry_nodes=[
                    entry_node
                    for entry_node in (
                        ASTSerializer.from_dict(item) if isinstance(item, dict) else None
                        for item in data.get("entry_nodes", [])
                    )
                    if entry_node is not None
                ],
                exit_nodes=[
                    exit_node
                    for exit_node in (
                        ASTSerializer.from_dict(item) if isinstance(item, dict) else None
                        for item in data.get("exit_nodes", [])
                    )
                    if exit_node is not None
                ],
            )
        if node_type == "INDICATOR":
            config_data = data.get("indicator_config") or {}
            config = IndicatorConfig(**config_data) if config_data else None
            return IndicatorNode(node_id=node_id, metadata=metadata, indicator_config=config)
        if node_type == "CONSTANT":
            return ConstantNode(node_id=node_id, metadata=metadata, value=data.get("value"))
        if node_type == "MARKET_REFERENCE":
            return MarketReferenceNode(
                node_id=node_id,
                metadata=metadata,
                data_type=data.get("data_type", ""),
                lookback_periods=data.get("lookback_periods", 0),
                timeframe=data.get("timeframe", "1d"),
            )
        if node_type == "PATTERN":
            config_data = data.get("pattern_config") or {}
            pattern_config = PatternConfig(**config_data) if config_data else None
            return PatternNode(node_id=node_id, metadata=metadata, pattern_config=pattern_config)
        if node_type == "COMPARISON":
            return ComparisonNode(
                node_id=node_id,
                metadata=metadata,
                operator=data.get("operator", ""),
                lookback_periods=data.get("lookback_periods", 0),
            )
        if node_type == "SEQUENCE":
            return SequenceNode(
                node_id=node_id,
                metadata=metadata,
                count=data.get("count", 1),
                direction=data.get("direction", "BACKWARD"),
            )
        if node_type == "CROSS":
            return CrossNode(
                node_id=node_id,
                metadata=metadata,
                cross_type=data.get("cross_type", ""),
                lookback_periods=data.get("lookback_periods", 1),
            )
        if node_type == "ARITHMETIC":
            return ArithmeticNode(
                node_id=node_id,
                metadata=metadata,
                operator=data.get("operator", ""),
            )
        if node_type == "STOP_LOSS":
            config_data = data.get("config") or {}
            sl_config = StopLossConfig(**config_data) if config_data else None
            return StopLossNode(node_id=node_id, metadata=metadata, config=sl_config)
        if node_type == "TAKE_PROFIT":
            config_data = data.get("config") or {}
            tp_config = TakeProfitConfig(**config_data) if config_data else None
            return TakeProfitNode(node_id=node_id, metadata=metadata, config=tp_config)
        if node_type == "POSITION_SIZE":
            config_data = data.get("config") or {}
            ps_config = PositionSizeConfig(**config_data) if config_data else None
            return PositionSizeNode(node_id=node_id, metadata=metadata, config=ps_config)
        if node_type == "TRAILING_STOP":
            return TrailingStopNode(
                node_id=node_id,
                metadata=metadata,
                trail_amount=data.get("trail_amount"),
                trail_type=data.get("trail_type", "PERCENTAGE"),
                reference=data.get("reference", "highest_price"),
                indicator_ref=data.get("indicator_ref"),
            )
        if node_type == "MULTIPLE":
            return MultipleNode(
                node_id=node_id,
                metadata=metadata,
                value=data.get("value", 1.0),
            )
        if node_type == "REFERENCE_INDICATOR":
            return ReferenceIndicatorNode(
                node_id=node_id,
                metadata=metadata,
                indicator_ref=data.get("indicator_ref", ""),
            )
        if node_type == "RISK_REWARD":
            return RiskRewardNode(node_id=node_id, metadata=metadata, ratio=data.get("ratio", 2.0))
        if node_type == "TIME":
            return TimeNode(
                node_id=node_id,
                metadata=metadata,
                start_time=data.get("start_time", ""),
                end_time=data.get("end_time", ""),
                timezone=data.get("timezone"),
            )
        if node_type == "DATE":
            return DateNode(
                node_id=node_id,
                metadata=metadata,
                start_date=data.get("start_date", ""),
                end_date=data.get("end_date", ""),
            )
        if node_type == "SESSION":
            return SessionNode(node_id=node_id, metadata=metadata, sessions=data.get("sessions", []))
        if node_type == "DAY_OF_WEEK":
            return DayOfWeekNode(node_id=node_id, metadata=metadata, days=data.get("days", []))
        if node_type == "MAX_DRAWDOWN":
            return MaxDrawdownNode(
                node_id=node_id,
                metadata=metadata,
                max_drawdown_percent=data.get("max_drawdown_percent"),
            )
        if node_type == "VARIABLE_ASSIGNMENT":
            return VariableAssignmentNode(
                node_id=node_id,
                metadata=metadata,
                variable_name=data.get("variable_name", ""),
            )
        if node_type == "VARIABLE_REFERENCE":
            return VariableReferenceNode(
                node_id=node_id,
                metadata=metadata,
                variable_name=data.get("variable_name", ""),
            )
        if node_type == "MAX_DAILY_LOSS":
            return MaxDailyLossNode(
                node_id=node_id,
                metadata=metadata,
                max_loss_amount=data.get("max_loss_amount"),
            )
        if node_type == "MAX_OPEN_TRADES":
            return MaxOpenTradesNode(
                node_id=node_id,
                metadata=metadata,
                max_trades=data.get("max_trades"),
            )
        if node_type == "CAPITAL_ALLOCATION":
            return CapitalAllocationNode(
                node_id=node_id,
                metadata=metadata,
                allocation_percent=data.get("allocation_percent"),
            )

        # Fallback for generic/unknown node types via registry
        node_class = ASTNodeRegistry.require(node_type)
        return node_class(node_id=node_id, metadata=metadata)

    @staticmethod
    def _metadata_to_dict(metadata: ASTNodeMetadata) -> Dict[str, Any]:
        return {
            "version": metadata.version,
            "created_at": metadata.created_at,
            "source_path": metadata.source_path,
            "tags": dict(metadata.tags),
        }

    @staticmethod
    def _metadata_from_dict(data: Optional[Dict[str, Any]]) -> ASTNodeMetadata:
        if not data:
            return ASTNodeMetadata()
        return ASTNodeMetadata(
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", ""),
            source_path=data.get("source_path", ""),
            tags=dict(data.get("tags", {})),
        )


class ASTVersionManager:
    """Manage AST schema version metadata and migrations."""

    CURRENT_AST_VERSION = "1.0.0"

    @staticmethod
    def add_version_info(ast_node: ASTNode) -> Dict[str, Any]:
        """Create a versioned serialized representation."""
        return ASTSerializer.to_versioned_dict(ast_node)

    @staticmethod
    def migrate(ast_dict: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Migrate serialized AST data between schema versions."""
        if from_version == to_version:
            return ast_dict
        raise NotImplementedError(
            f"No AST migration registered from {from_version} to {to_version}"
        )
