"""AST validation logic.

Validates strategy ASTs before the backtest engine processes them.
Accepts both schemas:

1. **NLconverter AST** — must have ``ast.node_type == "STRATEGY_ROOT"``
   and ``ast.operation_nodes`` list.
2. **Legacy flat AST** — any dict that does not have a top-level ``"ast"``
   key is treated as a legacy flat-format AST and passes validation
   (structure correctness is enforced lazily by the evaluator).
"""
from __future__ import annotations

from typing import Any, Dict

KNOWN_NODE_TYPES = {
    "STRATEGY_ROOT",
    "OPERATION",
    "ENTRY",
    "EXIT",
    "AND",
    "OR",
    "NOT",
    "ADD",
    "SUBTRACT",
    "MULTIPLY",
    "DIVIDE",
    "MIN",
    "MAX",
    "ABS",
    "ARITHMETIC",
    "GREATER_THAN",
    "LESS_THAN",
    "EQUAL",
    "NOT_EQUAL",
    "GREATER_EQUAL",
    "LESS_EQUAL",
    "GREATER_THAN_EQUAL",
    "LESS_THAN_EQUAL",
    "CROSS_ABOVE",
    "CROSS_BELOW",
    "SEQUENCE",
    "INDICATOR",
    "MARKET_REFERENCE",
    "PATTERN",
    "CONSTANT",
    "STOP_LOSS",
    "TAKE_PROFIT",
    "VARIABLE_ASSIGNMENT",
    "VARIABLE_REFERENCE",
}


def _validate_node(node: Any, path: str) -> None:
    """Recursively validates a single AST node and its children."""
    if not isinstance(node, dict):
        raise ValueError(f"Node at '{path}' must be a dictionary, got {type(node).__name__}")

    node_type = node.get("node_type")
    if not isinstance(node_type, str):
        raise ValueError(f"Node at '{path}' must have a string 'node_type'")

    node_type_upper = node_type.upper()
    if node_type_upper not in KNOWN_NODE_TYPES:
        raise ValueError(f"Unsupported node_type: {node_type} at '{path}'")

    # Recurse based on node_type structure
    if node_type_upper == "STRATEGY_ROOT":
        # operation_nodes
        op_nodes = node.get("operation_nodes", [])
        if not isinstance(op_nodes, list):
            raise ValueError(f"'operation_nodes' must be a list at '{path}'")
        for i, child in enumerate(op_nodes):
            _validate_node(child, f"{path}.operation_nodes[{i}]")

        # variable_nodes
        var_nodes = node.get("variable_nodes", [])
        if not isinstance(var_nodes, list):
            raise ValueError(f"'variable_nodes' must be a list at '{path}'")
        for i, child in enumerate(var_nodes):
            _validate_node(child, f"{path}.variable_nodes[{i}]")

        # legacy entry_node / exit_node
        if "entry_node" in node:
            _validate_node(node["entry_node"], f"{path}.entry_node")
        if "exit_node" in node:
            _validate_node(node["exit_node"], f"{path}.exit_node")

    elif node_type_upper == "OPERATION":
        # entry_nodes
        entry_nodes = node.get("entry_nodes", [])
        if not isinstance(entry_nodes, list):
            raise ValueError(f"'entry_nodes' must be a list at '{path}'")
        for i, child in enumerate(entry_nodes):
            _validate_node(child, f"{path}.entry_nodes[{i}]")

        # exit_nodes
        exit_nodes = node.get("exit_nodes", [])
        if not isinstance(exit_nodes, list):
            raise ValueError(f"'exit_nodes' must be a list at '{path}'")
        for i, child in enumerate(exit_nodes):
            _validate_node(child, f"{path}.exit_nodes[{i}]")

    elif node_type_upper == "SEQUENCE":
        condition = node.get("condition")
        if condition is not None:
            _validate_node(condition, f"{path}.condition")
        else:
            raise ValueError(f"SEQUENCE node missing 'condition' at '{path}'")

    else:
        # All other nodes can contain `children` list
        if "children" in node:
            children = node.get("children", [])
            if not isinstance(children, list):
                raise ValueError(f"'children' must be a list at '{path}'")
            for i, child in enumerate(children):
                _validate_node(child, f"{path}.children[{i}]")


def validate(ast: Dict[str, Any]) -> None:
    """Validate a strategy AST for required structural fields.

    Accepts both the NLconverter hierarchical schema and the legacy flat format.

    Raises:
        ValueError: when the AST is malformed (e.g. not a dict, or is a
            NLconverter AST missing required structural keys).
    """
    if not isinstance(ast, dict):
        raise ValueError("AST must be a dictionary")

    # If no top-level "ast" key is present, treat as legacy flat format — always valid here.
    if "ast" not in ast:
        return

    # ── NLconverter schema validation ─────────────────────────────────────
    core = ast["ast"]

    if not isinstance(core, dict):
        raise ValueError("'ast' field must be a dictionary")

    # Perform recursive node validation starting from root
    _validate_node(core, "ast")
