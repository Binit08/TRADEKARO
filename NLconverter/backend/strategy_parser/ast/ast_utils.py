"""AST utilities for validation, debugging, and structural analysis."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .ast_nodes import (
    ASTNode,
    ArithmeticNode,
    CrossNode,
    EntryNode,
    ExitNode,
    FilterNode,
    IndicatorNode,
    MarketReferenceNode,
    PatternNode,
    RiskNode,
    StrategyRootNode,
    OperationNode,
    NotNode,
    ComparisonNode,
)


@dataclass
class ASTMetrics:
    """Metrics about AST structure."""

    total_nodes: int
    max_depth: int
    avg_children_per_node: float
    node_type_distribution: Dict[str, int]
    node_memory_bytes: int  # Size of root node only, not the full tree


def iter_structural_children(node: Optional[ASTNode]) -> Iterable[ASTNode]:
    """Yield children across root-specific fields and generic children."""
    if node is None:
        return
    if isinstance(node, StrategyRootNode):
        if node.operation_nodes:
            for child in (node.risk_node,):
                if child is not None:
                    yield child
        else:
            for child in (node.entry_node, node.exit_node, node.risk_node):
                if child is not None:
                    yield child
        for filter_node in node.filter_nodes:
            yield filter_node
        for op_node in node.operation_nodes:
            yield op_node
        return
    if isinstance(node, OperationNode):
        for child in node.entry_nodes:
            yield child
        for child in node.exit_nodes:
            yield child
        return
    for child in node.children:
        yield child


class ASTValidator:
    """Validate AST structural invariants only."""

    @staticmethod
    def validate(ast_root: StrategyRootNode) -> Tuple[bool, List[str]]:
        """Validate an AST. Returns (is_valid, errors)."""
        errors: List[str] = []

        if not isinstance(ast_root, StrategyRootNode):
            return False, ["AST root must be a StrategyRootNode"]

        if not ast_root.entry_node and not ast_root.exit_node and not ast_root.operation_nodes:
            errors.append("Strategy must have at least entry OR exit condition")

        errors.extend(ASTValidator._validate_node(ast_root))
        return len(errors) == 0, errors

    @staticmethod
    def _validate_node(node: Optional[ASTNode]) -> List[str]:
        if node is None:
            return []

        errors: List[str] = []
        child_count = len(list(iter_structural_children(node)))

        if isinstance(node, (EntryNode, ExitNode, FilterNode)):
            if len(node.children) != 1:
                errors.append(
                    f"{node.node_type} node {node.node_id} must have exactly 1 child, got {len(node.children)}"
                )
        elif isinstance(node, RiskNode):
            if len(node.children) < 1:
                errors.append(f"RISK node {node.node_id} must have at least 1 child")
        elif isinstance(node, NotNode):
            if len(node.children) != 1:
                errors.append(
                    f"NOT node {node.node_id} must have exactly 1 child, got {len(node.children)}"
                )
        elif isinstance(node, ComparisonNode):
            if len(node.children) != 2:
                errors.append(
                    f"Comparison node {node.node_id} must have exactly 2 children, got {len(node.children)}"
                )
        elif isinstance(node, CrossNode):
            if len(node.children) != 2:
                errors.append(
                    f"Cross node {node.node_id} must have exactly 2 children, got {len(node.children)}"
                )
        elif isinstance(node, ArithmeticNode):
            if node.operator == "ABS" and len(node.children) != 1:
                errors.append(f"ABS node {node.node_id} must have exactly 1 child")
            elif node.operator != "ABS" and len(node.children) < 1:
                errors.append(f"Arithmetic node {node.node_id} must have at least 1 child")
        elif isinstance(node, IndicatorNode):
            if node.indicator_config is None:
                errors.append(f"Indicator node {node.node_id} requires indicator_config")
        elif isinstance(node, MarketReferenceNode):
            if not node.data_type:
                errors.append(f"Market reference node {node.node_id} requires data_type")
        elif isinstance(node, PatternNode):
            if node.pattern_config is None:
                errors.append(f"Pattern node {node.node_id} requires pattern_config")

        if isinstance(node, StrategyRootNode) and child_count == 0:
            errors.append(f"Strategy root {node.node_id} has no structural children")

        for child in iter_structural_children(node):
            errors.extend(ASTValidator._validate_node(child))

        return errors


class ASTDebugger:
    """Debug and visualize AST structure."""

    @staticmethod
    def print_tree(node: Optional[ASTNode], indent: int = 0, max_depth: int = 20) -> None:
        """Print AST as a tree structure."""
        if not node or indent > max_depth:
            return

        prefix = "  " * indent
        print(f"{prefix}├─ {ASTDebugger._node_label(node)}")

        for child in iter_structural_children(node):
            ASTDebugger.print_tree(child, indent + 1, max_depth)

    @staticmethod
    def to_mermaid(node: Optional[ASTNode], title: str = "Strategy AST") -> str:
        """Generate a Mermaid diagram of AST structure."""
        if not node:
            return ""

        lines = [f"graph TD", f"    ROOT[\"{title}\"]"]
        counter = {"id": 0}

        def traverse(current: ASTNode, parent_id: str) -> None:
            counter["id"] += 1
            current_id = f"N{counter['id']}"
            label = ASTDebugger._node_label(current).replace('"', "'")
            lines.append(f"    {current_id}[\"{label}\"]")
            lines.append(f"    {parent_id} --> {current_id}")
            for child_node in iter_structural_children(current):
                traverse(child_node, current_id)

        traverse(node, "ROOT")
        return "\n".join(lines)

    @staticmethod
    def node_count(node: Optional[ASTNode]) -> Dict[str, int]:
        """Count node types in an AST."""
        counts: Dict[str, int] = {}

        def traverse(current: Optional[ASTNode]) -> None:
            if current is None:
                return
            counts[current.node_type] = counts.get(current.node_type, 0) + 1
            for child_node in iter_structural_children(current):
                traverse(child_node)

        traverse(node)
        return counts

    @staticmethod
    def print_stats(node: Optional[ASTNode]) -> None:
        """Print AST node statistics."""
        if not node:
            return

        counts = ASTDebugger.node_count(node)
        total = sum(counts.values())

        print("\n=== AST Statistics ===")
        print(f"Total nodes: {total}")
        print("\nNode distribution:")
        for node_type in sorted(counts.keys()):
            count = counts[node_type]
            percent = (count / total * 100) if total > 0 else 0
            print(f"  {node_type:20s}: {count:3d} ({percent:5.1f}%)")

    @staticmethod
    def _node_label(node: ASTNode) -> str:
        if node.node_type == "MULTIPLE":
            return f"MULTIPLE [{getattr(node, 'value')}]"
        if node.node_type == "REFERENCE_INDICATOR":
            return f"REFERENCE_INDICATOR [{getattr(node, 'indicator_ref')}]"

        label = f"{node.node_type} ({node.node_id})"
        if hasattr(node, "value"):
            label += f" = {getattr(node, 'value')}"
        elif hasattr(node, "operator") and getattr(node, "operator"):
            label += f" [{getattr(node, 'operator')}]"
        elif isinstance(node, IndicatorNode) and node.indicator_config:
            params = []
            if node.indicator_config.parameters:
                params = [f"{v}" for k, v in node.indicator_config.parameters.items()]
            param_str = f"({', '.join(params)})" if params else ""
            label += f" [{node.indicator_config.indicator_type}{param_str}]"
        return label


class ASTAnalyzer:
    """Analyze AST structure and metrics."""

    @staticmethod
    def analyze(node: Optional[ASTNode]) -> ASTMetrics:
        """Analyze AST metrics."""
        if not node:
            return ASTMetrics(0, 0, 0, {}, 0)

        counts: Dict[str, int] = {}
        depths: List[int] = []
        total_nodes = [0]
        total_children = [0]

        def traverse(current: Optional[ASTNode], depth: int) -> None:
            if current is None:
                return

            children = list(iter_structural_children(current))
            total_nodes[0] += 1
            depths.append(depth)
            counts[current.node_type] = counts.get(current.node_type, 0) + 1
            total_children[0] += len(children)

            for child_node in children:
                traverse(child_node, depth + 1)

        traverse(node, 0)

        avg_children = (
            total_children[0] / total_nodes[0]
            if total_nodes[0] > 0
            else 0
        )

        return ASTMetrics(
            total_nodes=total_nodes[0],
            max_depth=max(depths) if depths else 0,
            avg_children_per_node=avg_children,
            node_type_distribution=counts,
            node_memory_bytes=sys.getsizeof(node),
        )

    @staticmethod
    def print_metrics(node: Optional[ASTNode]) -> None:
        """Print AST metrics."""
        if not node:
            print("No AST to analyze")
            return

        metrics = ASTAnalyzer.analyze(node)

        print("\n=== AST Metrics ===")
        print(f"Total nodes:           {metrics.total_nodes}")
        print(f"Max depth:             {metrics.max_depth}")
        print(f"Avg children/node:     {metrics.avg_children_per_node:.2f}")
        print(f"Root node memory:      {metrics.node_memory_bytes:,} bytes")
        print("\nNode type distribution:")
        for node_type in sorted(metrics.node_type_distribution.keys()):
            count = metrics.node_type_distribution[node_type]
            percent = (
                count / metrics.total_nodes * 100
                if metrics.total_nodes > 0
                else 0
            )
            print(f"  {node_type:20s}: {count:3d} ({percent:5.1f}%)")
