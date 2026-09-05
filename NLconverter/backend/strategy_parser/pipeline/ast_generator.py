from typing import Dict, Any, Optional

from backend.strategy_parser.ast import ASTBuilder, ASTNode


class ASTGenerator:
    """
    Generate AST only from validated Canonical JSON.
    Never generate AST directly from natural language.
    """

    def __init__(self, builder: ASTBuilder):
        self.builder = builder

    def generate(self, canonical_json: Dict[str, Any], strategy_id: str, deterministic_schema: Optional[Dict[str, Any]] = None) -> ASTNode:
        return self.builder.build(
            canonical_json,
            strategy_id=strategy_id,
            deterministic_schema=deterministic_schema
        )
