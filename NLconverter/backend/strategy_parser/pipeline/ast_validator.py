from typing import Tuple, List

from backend.strategy_parser.ast import ASTNode
from backend.strategy_parser.ast import ASTValidator as CoreASTValidator


class ASTValidatorStep:
    """
    Validates node types, operator correctness, parameter integrity.
    """

    def validate(self, ast: ASTNode) -> Tuple[bool, List[str]]:
        """
        Returns (is_valid, list_of_errors)
        """
        return CoreASTValidator.validate(ast)
