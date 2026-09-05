from typing import Any, Dict
from ..ast_nodes import (
    ASTNode,
    AndNode,
    OrNode,
    NotNode,
    GreaterThanNode,
    LessThanNode,
    GreaterEqualNode,
    LessEqualNode,
    EqualNode,
    NotEqualNode,
    CrossAboveNode,
    CrossBelowNode,
    SequenceNode,
    TimeNode,
    DateNode,
    SessionNode,
    DayOfWeekNode,
    ASTNodeRegistry,
)

class ConditionBuilderMixin:
    def _build_logical_node(self, node_data: Dict[str, Any], source_path: str) -> ASTNode:
        node_type = ASTNodeRegistry.normalize(node_data["type"])
        node_class = {"AND": AndNode, "OR": OrNode, "NOT": NotNode}[node_type]
        node = node_class(
            node_id=self._generate_node_id(node_type),
            metadata=self._metadata(source_path, node_data),
        )

        if node_type == "NOT":
            child_data = node_data.get("child")
            children_data = node_data.get("children")
            if child_data is None and isinstance(children_data, list):
                from ..ast_builder import ASTBuildError
                if len(children_data) != 1:
                    raise ASTBuildError(
                        "NOT node requires exactly one child",
                        source_path,
                        node_type,
                    )
                child_data = children_data[0]
            if child_data is None:
                from ..ast_builder import ASTBuildError
                raise ASTBuildError("NOT node requires 'child'", source_path, node_type)
            node.children.append(self._build_condition_tree(child_data, f"{source_path}.child"))
            return node

        children = node_data.get("children")
        if not isinstance(children, list) or not children:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError(
                f"{node_type} node requires a non-empty 'children' list",
                source_path,
                node_type,
            )

        for index, child_data in enumerate(children):
            node.children.append(
                self._build_condition_tree(child_data, f"{source_path}.children[{index}]")
            )
        return node

    def _build_comparison_node(self, node_data: Dict[str, Any], source_path: str) -> ASTNode:
        node_type = ASTNodeRegistry.normalize(node_data["type"])
        left_data, right_data = self._binary_operands(node_data, source_path)
        node_class = {
            "GREATER_THAN": GreaterThanNode,
            "LESS_THAN": LessThanNode,
            "GREATER_THAN_EQUAL": GreaterEqualNode,
            "LESS_THAN_EQUAL": LessEqualNode,
            "EQUAL": EqualNode,
            "NOT_EQUAL": NotEqualNode,
        }[node_type]
        node = node_class(
            node_id=self._generate_node_id(node_type),
            metadata=self._metadata(source_path, node_data),
            lookback_periods=int(node_data.get("lookback_periods") or 0)
        )
        node.children = [
            self._build_operand(left_data, f"{source_path}.operand_1"),
            self._build_operand(right_data, f"{source_path}.operand_2"),
        ]
        
        # Defense in depth: prevent double counting lookbacks
        if getattr(node, "lookback_periods", 0) > 0:
            for child in node.children:
                if hasattr(child, "lookback_periods"):
                    child.lookback_periods = 0
                    
        return node

    def _build_cross_node(self, node_data: Dict[str, Any], source_path: str) -> ASTNode:
        node_type = ASTNodeRegistry.normalize(node_data["type"])
        left_data, right_data = self._binary_operands(node_data, source_path)
        node_class = CrossAboveNode if node_type == "CROSS_ABOVE" else CrossBelowNode
        node = node_class(
            node_id=self._generate_node_id(node_type),
            metadata=self._metadata(source_path, node_data),
            lookback_periods=int(node_data.get("lookback_periods") or 1),
        )
        node.children = [
            self._build_operand(left_data, f"{source_path}.operand_1"),
            self._build_operand(right_data, f"{source_path}.operand_2"),
        ]
        return node

    def _build_sequence_node(self, node_data: Dict[str, Any], source_path: str) -> ASTNode:
        metadata = self._metadata(source_path, node_data)
        count = int(node_data.get("count") or 1)
        direction = node_data.get("direction") or "BACKWARD"
        
        node = SequenceNode(
            node_id=self._generate_node_id("SEQUENCE"),
            metadata=metadata,
            count=count,
            direction=str(direction).upper()
        )
        
        condition_data = node_data.get("condition")
        if not condition_data:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("SEQUENCE node requires 'condition'", source_path)
            
        node.children.append(self._build_condition_tree(condition_data, f"{source_path}.condition"))
        return node

    def _build_followed_by_node(self, node_data: Dict[str, Any], source_path: str) -> ASTNode:
        from ..ast_nodes import FollowedByNode
        metadata = self._metadata(source_path, node_data)
        
        node = FollowedByNode(
            node_id=self._generate_node_id("FOLLOWED_BY"),
            metadata=metadata,
            max_bars_between=node_data.get("max_bars_between")
        )
        
        setup_data = node_data.get("setup_condition")
        trigger_data = node_data.get("trigger_condition")
        
        if not setup_data or not trigger_data:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("FOLLOWED_BY node requires 'setup_condition' and 'trigger_condition'", source_path)
            
        node.children.append(self._build_condition_tree(setup_data, f"{source_path}.setup_condition"))
        node.children.append(self._build_condition_tree(trigger_data, f"{source_path}.trigger_condition"))
        return node

    def _build_time_node(self, node_data: Dict[str, Any], source_path: str) -> ASTNode:
        node_type = ASTNodeRegistry.normalize(node_data["type"])
        metadata = self._metadata(source_path, node_data)
        if node_type == "TIME":
            return TimeNode(
                node_id=self._generate_node_id("TIME"),
                metadata=metadata,
                start_time=node_data.get("start_time", ""),
                end_time=node_data.get("end_time", ""),
                timezone=node_data.get("timezone"),
            )
        if node_type == "DATE":
            return DateNode(
                node_id=self._generate_node_id("DATE"),
                metadata=metadata,
                start_date=node_data.get("start_date", ""),
                end_date=node_data.get("end_date", ""),
            )
        if node_type == "SESSION":
            return SessionNode(
                node_id=self._generate_node_id("SESSION"),
                metadata=metadata,
                sessions=list(node_data.get("sessions", [])),
            )
        return DayOfWeekNode(
            node_id=self._generate_node_id("DAY_OF_WEEK"),
            metadata=metadata,
            days=list(node_data.get("days", [])),
        )
