from typing import Any, Dict
from ..ast_nodes import (
    ASTNode,
    IndicatorConfig,
    IndicatorNode,
    ConstantNode,
    MarketReferenceNode,
    PatternConfig,
    PatternNode,
    AddNode,
    SubtractNode,
    MultiplyNode,
    DivideNode,
    MinNode,
    MaxNode,
    AbsNode,
    VariableAssignmentNode,
    VariableReferenceNode,
    ASTNodeRegistry,
)

class OperandBuilderMixin:
    def _build_operand(self, operand_data: Dict[str, Any], source_path: str) -> ASTNode:
        """Build an operand node or operand subtree."""
        if not isinstance(operand_data, dict):
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Operand must be an object", source_path)

        raw_type = operand_data.get("type")
        if not raw_type:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Missing operand 'type'", source_path)

        node_type = self._normalize_operand_type(raw_type)
        builder = self.operand_builders.get(node_type)
        if not builder:
            if node_type in self.condition_builders:
                return self._build_condition_tree(operand_data, source_path)
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Unknown operand type", source_path, node_type)

        return builder(operand_data, source_path)

    def _build_operand_by_type(self, operand_data: Dict[str, Any], source_path: str) -> ASTNode:
        node_type = self._normalize_operand_type(operand_data["type"])

        if node_type == "INDICATOR":
            return self._build_indicator_node(operand_data, source_path)
        if node_type == "CONSTANT":
            return self._build_constant_node(operand_data, source_path)
        if node_type == "MARKET_REFERENCE":
            return self._build_market_reference_node(operand_data, source_path)
        if node_type == "PATTERN":
            return self._build_pattern_node(operand_data, source_path)
        if node_type in {
            "ARITHMETIC",
            "ADD",
            "SUBTRACT",
            "MULTIPLY",
            "DIVIDE",
            "MIN",
            "MAX",
            "ABS",
        }:
            return self._build_arithmetic_node(operand_data, source_path)
        if node_type == "VARIABLE_REFERENCE":
            return self._build_variable_reference_node(operand_data, source_path)

        from ..ast_builder import ASTBuildError
        raise ASTBuildError("Unsupported operand type", source_path, node_type)

    def _build_indicator_node(
        self,
        indicator_data: Dict[str, Any],
        source_path: str,
    ) -> IndicatorNode:
        signal_config = self._lookup_indicator_signal(indicator_data)
        indicator_type = (
            indicator_data.get("indicator_type")
            or indicator_data.get("name")
            or signal_config.get("indicator_type")
            or signal_config.get("name")
        )
        if not indicator_type:
            ref_val = indicator_data.get("indicator_ref") or indicator_data.get("indicator_id") or indicator_data.get("ref")
            from ..ast_builder import ASTBuildError
            if ref_val:
                raise ASTBuildError(f"Unknown indicator reference: '{ref_val}'", source_path)
            raise ASTBuildError("Indicator requires 'indicator_type' or signal reference", source_path)

        parameters = dict(signal_config.get("parameters") or signal_config.get("params") or {})
        parameters.update(indicator_data.get("parameters") or indicator_data.get("params") or {})

        output_property = (
            indicator_data.get("property")
            or indicator_data.get("output_property")
            or signal_config.get("output_property")
            or "value"
        )
        timeframe = (
            self._lookup_deterministic_timeframe(indicator_data)
            or self._get_execution_context("timeframe")
            or "1d"
        )

        config = IndicatorConfig(
            indicator_type=str(indicator_type).upper(),
            parameters=parameters,
            output_property=str(output_property),
            timeframe=str(timeframe),
        )
        
        input_node_data = indicator_data.get("input_node")
        if input_node_data:
            config.input_node = self._build_operand(input_node_data, f"{source_path}.input_node")

        return IndicatorNode(
            node_id=self._generate_node_id("INDICATOR"),
            metadata=self._metadata(source_path, indicator_data),
            indicator_config=config,
        )

    def _build_constant_node(
        self,
        constant_data: Dict[str, Any],
        source_path: str,
    ) -> ConstantNode:
        if "value" not in constant_data:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Constant requires 'value'", source_path)
        return ConstantNode(
            node_id=self._generate_node_id("CONSTANT"),
            metadata=self._metadata(source_path, constant_data),
            value=constant_data.get("value"),
        )

    def _build_market_reference_node(
        self,
        market_data: Dict[str, Any],
        source_path: str,
    ) -> MarketReferenceNode:
        data_type = market_data.get("data_type") or market_data.get("field")
        if not data_type:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Market reference requires 'data_type'", source_path)
        return MarketReferenceNode(
            node_id=self._generate_node_id("MARKET_REFERENCE"),
            metadata=self._metadata(source_path, market_data),
            data_type=str(data_type).upper(),
            lookback_periods=int(market_data.get("lookback_periods") or market_data.get("lookback") or 0),
            timeframe=self._get_execution_context("timeframe") or "1d",
        )

    def _build_pattern_node(
        self,
        pattern_data: Dict[str, Any],
        source_path: str,
    ) -> PatternNode:
        pattern_type = pattern_data.get("pattern_type") or pattern_data.get("name")
        if not pattern_type:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Pattern requires 'pattern_type'", source_path)
        config = PatternConfig(
            pattern_type=str(pattern_type).upper(),
            parameters=pattern_data.get("parameters") or pattern_data.get("params") or {},
            lookback_periods=int(pattern_data.get("lookback_periods") or 50),
        )
        return PatternNode(
            node_id=self._generate_node_id("PATTERN"),
            metadata=self._metadata(source_path, pattern_data),
            pattern_config=config,
        )

    def _build_arithmetic_node(
        self,
        arithmetic_data: Dict[str, Any],
        source_path: str,
    ) -> ASTNode:
        raw_operator = (
            arithmetic_data.get("operator")
            or arithmetic_data.get("operation")
            or arithmetic_data.get("type")
        )
        operator = ASTNodeRegistry.normalize(str(raw_operator))
        if operator == "ARITHMETIC":
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Arithmetic node requires 'operator'", source_path)

        node_classes = {
            "ADD": AddNode,
            "SUBTRACT": SubtractNode,
            "MULTIPLY": MultiplyNode,
            "DIVIDE": DivideNode,
            "MIN": MinNode,
            "MAX": MaxNode,
            "ABS": AbsNode,
        }
        node_class = node_classes.get(operator)
        if not node_class:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Unknown arithmetic operator", source_path, operator)

        operands = arithmetic_data.get("operands")
        if operands is None:
            operands = arithmetic_data.get("children")
        if operands is None:
            if "operand_1" in arithmetic_data and "operand_2" in arithmetic_data:
                operands = [arithmetic_data["operand_1"], arithmetic_data["operand_2"]]
            elif "operand" in arithmetic_data:
                operands = [arithmetic_data["operand"]]
            elif "child" in arithmetic_data:
                operands = [arithmetic_data["child"]]
        if isinstance(operands, dict):
            operands = [operands]
        if not isinstance(operands, list) or not operands:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Arithmetic node requires operands", source_path, operator)
        if operator == "ABS" and len(operands) != 1:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("ABS requires exactly one operand", source_path, operator)

        node = node_class(
            node_id=self._generate_node_id(operator),
            metadata=self._metadata(source_path, arithmetic_data),
        )
        node.children = [
            self._build_operand(operand, f"{source_path}.operands[{index}]")
            for index, operand in enumerate(operands)
        ]
        return node

    def _build_variable_assignment_node(self, var_data: Dict[str, Any], source_path: str) -> ASTNode:
        variable_name = var_data.get("variable_name") or var_data.get("name")
        if not variable_name:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Variable assignment requires 'variable_name'", source_path)

        node = VariableAssignmentNode(
            node_id=self._generate_node_id("VARIABLE_ASSIGNMENT"),
            metadata=self._metadata(source_path, var_data),
            variable_name=str(variable_name),
        )

        condition_data = var_data.get("condition")
        if not condition_data:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Variable assignment requires 'condition'", source_path)
        node.children.append(self._build_condition_tree(condition_data, f"{source_path}.condition"))

        value_data = var_data.get("value")
        if not value_data:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Variable assignment requires 'value'", source_path)
        node.children.append(self._build_operand(value_data, f"{source_path}.value"))

        return node

    def _build_variable_reference_node(self, var_data: Dict[str, Any], source_path: str) -> ASTNode:
        variable_name = var_data.get("variable_name") or var_data.get("name")
        if not variable_name:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Variable reference requires 'variable_name'", source_path)

        return VariableReferenceNode(
            node_id=self._generate_node_id("VARIABLE_REFERENCE"),
            metadata=self._metadata(source_path, var_data),
            variable_name=str(variable_name),
        )
