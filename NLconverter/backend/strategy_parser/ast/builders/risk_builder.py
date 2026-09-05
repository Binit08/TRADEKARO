from typing import Any, Dict, Optional
from ..ast_nodes import (
    ASTNode,
    RiskNode,
    StopLossNode,
    StopLossConfig,
    TakeProfitNode,
    TakeProfitConfig,
    TrailingStopNode,
    PositionSizeNode,
    PositionSizeConfig,
    RiskRewardNode,
    MaxDrawdownNode,
    MaxDailyLossNode,
    MaxOpenTradesNode,
    CapitalAllocationNode,
    MultipleNode,
    ReferenceIndicatorNode,
    ASTNodeRegistry,
)

class RiskBuilderMixin:
    def _build_risk_tree(
        self,
        risk_data: Dict[str, Any],
        source_path: str,
    ) -> Optional[RiskNode]:
        """Build the risk declaration subtree."""
        if not isinstance(risk_data, dict):
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("'risk' must be an object", source_path)

        risk_root = RiskNode(
            node_id=self._generate_node_id("RISK"),
            metadata=self._metadata(source_path, risk_data),
        )

        explicit_items = risk_data.get("items") or []
        if isinstance(explicit_items, dict):
            explicit_items = [explicit_items]
        if not isinstance(explicit_items, list):
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("'risk.items' must be a list or object", f"{source_path}.items")

        for index, item in enumerate(explicit_items):
            risk_node = self._build_explicit_risk_item(item, f"{source_path}.items[{index}]")
            if risk_node:
                risk_root.children.append(risk_node)

        keyed_builds = (
            ("stop_loss", "STOP_LOSS"),
            ("take_profit", "TAKE_PROFIT"),
            ("trailing_stop", "TRAILING_STOP"),
            ("position_size", "POSITION_SIZE"),
            ("risk_reward", "RISK_REWARD"),
        )
        for key, node_type in keyed_builds:
            value = risk_data.get(key)
            if self._has_buildable_risk_value(value) and isinstance(value, dict):
                risk_kind = value.get("type")
                risk_root.children.append(
                    self._build_risk_node_by_type(
                        {**value, "kind": risk_kind, "type": node_type},
                        f"{source_path}.{key}",
                    )
                )

        constraints = risk_data.get("portfolio_constraints") or risk_data.get("constraints") or {}
        if constraints:
            if not isinstance(constraints, dict):
                from ..ast_builder import ASTBuildError
                raise ASTBuildError(
                    "'portfolio_constraints' must be an object",
                    f"{source_path}.portfolio_constraints",
                )
            self._append_portfolio_constraints(risk_root, constraints, source_path)

        if not risk_root.children:
            return None
        return risk_root

    def _build_explicit_risk_item(
        self,
        risk_item: Dict[str, Any],
        source_path: str,
    ) -> Optional[ASTNode]:
        if not isinstance(risk_item, dict):
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Risk item must be an object", source_path)
        raw_type = risk_item.get("type")
        if not raw_type:
            return None
        node_type = ASTNodeRegistry.normalize(raw_type)
        builder = self.risk_builders.get(node_type)
        if not builder:
            from ..ast_builder import ASTBuildError
            raise ASTBuildError("Unknown risk node type", source_path, node_type)
        return builder(risk_item, source_path)

    def _build_risk_node_by_type(self, risk_data: Dict[str, Any], source_path: str) -> ASTNode:
        node_type = ASTNodeRegistry.normalize(risk_data["type"])
        metadata = self._metadata(source_path, risk_data)

        if node_type == "STOP_LOSS":
            atr_mult = risk_data.get("atr_multiple")
            indicator_ref = risk_data.get("indicator_ref")
            config = StopLossConfig(
                stop_loss_type=str(risk_data.get("stop_loss_type") or risk_data.get("kind") or risk_data.get("type", "")),
                value=risk_data.get("value"),
                reference=risk_data.get("reference", "entry_price"),
                direction=risk_data.get("direction"),
                atr_multiple=atr_mult,
                price_level=risk_data.get("price_level"),
                indicator_ref=indicator_ref,
                trailing=bool(risk_data.get("trailing", False)),
            )
            node = StopLossNode(
                node_id=self._generate_node_id("STOP_LOSS"),
                metadata=metadata,
                config=config,
            )
            if atr_mult is not None:
                node.children.append(
                    MultipleNode(
                        node_id=self._generate_node_id("MULTIPLE"),
                        metadata=metadata,
                        value=float(atr_mult),
                    )
                )
            if indicator_ref:
                node.children.append(
                    ReferenceIndicatorNode(
                        node_id=self._generate_node_id("REFERENCE_INDICATOR"),
                        metadata=metadata,
                        indicator_ref=str(indicator_ref),
                    )
                )
            return node

        if node_type == "TAKE_PROFIT":
            tp_config = TakeProfitConfig(
                take_profit_type=str(risk_data.get("take_profit_type") or risk_data.get("kind") or risk_data.get("type", "")),
                value=risk_data.get("value"),
                target_indicator=risk_data.get("target_indicator"),
                price_level=risk_data.get("price_level"),
                risk_reward_ratio=risk_data.get("risk_reward_ratio"),
                indicator_ref=risk_data.get("indicator_ref"),
            )
            node = TakeProfitNode(
                node_id=self._generate_node_id("TAKE_PROFIT"),
                metadata=metadata,
                config=tp_config,
            )
            target_ind = risk_data.get("target_indicator") or risk_data.get("indicator_ref")
            if target_ind:
                indicator_node = self._build_indicator_node(
                    {"indicator_ref": target_ind},
                    f"{source_path}.target_indicator",
                )
                node.children.append(indicator_node)
            return node

        if node_type == "TRAILING_STOP":
            indicator_ref = risk_data.get("indicator_ref")
            node = TrailingStopNode(
                node_id=self._generate_node_id("TRAILING_STOP"),
                metadata=metadata,
                trail_amount=risk_data.get("trail_amount", risk_data.get("value")),
                trail_type=str(risk_data.get("trail_type") or risk_data.get("kind") or "PERCENTAGE"),
                reference=risk_data.get("reference", "highest_price"),
                indicator_ref=indicator_ref,
            )
            if indicator_ref:
                indicator_node = self._build_indicator_node(
                    {"indicator_ref": indicator_ref},
                    f"{source_path}.indicator_ref",
                )
                node.children.append(indicator_node)
            return node

        if node_type == "POSITION_SIZE":
            ps_config = PositionSizeConfig(
                size_type=str(risk_data.get("size_type") or risk_data.get("kind") or risk_data.get("type", "")),
                value=risk_data.get("value"),
                max_size=risk_data.get("max_size"),
                min_size=risk_data.get("min_size"),
            )
            return PositionSizeNode(
                node_id=self._generate_node_id("POSITION_SIZE"),
                metadata=metadata,
                config=ps_config,
            )

        if node_type == "RISK_REWARD":
            ratio = risk_data.get("ratio", risk_data.get("risk_reward_ratio", risk_data.get("value", 2.0)))
            return RiskRewardNode(
                node_id=self._generate_node_id("RISK_REWARD"),
                metadata=metadata,
                ratio=float(ratio),
            )

        if node_type == "MAX_DRAWDOWN":
            return MaxDrawdownNode(
                node_id=self._generate_node_id("MAX_DRAWDOWN"),
                metadata=metadata,
                max_drawdown_percent=risk_data.get("max_drawdown_percent", risk_data.get("value")),
            )

        if node_type == "MAX_DAILY_LOSS":
            return MaxDailyLossNode(
                node_id=self._generate_node_id("MAX_DAILY_LOSS"),
                metadata=metadata,
                max_loss_amount=risk_data.get("max_loss_amount", risk_data.get("value")),
            )

        if node_type == "MAX_OPEN_TRADES":
            return MaxOpenTradesNode(
                node_id=self._generate_node_id("MAX_OPEN_TRADES"),
                metadata=metadata,
                max_trades=risk_data.get("max_trades", risk_data.get("value")),
            )

        if node_type == "CAPITAL_ALLOCATION":
            return CapitalAllocationNode(
                node_id=self._generate_node_id("CAPITAL_ALLOCATION"),
                metadata=metadata,
                allocation_percent=risk_data.get("allocation_percent", risk_data.get("value")),
            )

        from ..ast_builder import ASTBuildError
        raise ASTBuildError("Unsupported risk node type", source_path, node_type)

    def _append_portfolio_constraints(
        self,
        risk_root: RiskNode,
        constraints: Dict[str, Any],
        source_path: str,
    ) -> None:
        mappings = {
            "max_drawdown": ("MAX_DRAWDOWN", "max_drawdown_percent"),
            "max_drawdown_percent": ("MAX_DRAWDOWN", "max_drawdown_percent"),
            "max_daily_loss": ("MAX_DAILY_LOSS", "max_loss_amount"),
            "max_loss_amount": ("MAX_DAILY_LOSS", "max_loss_amount"),
            "max_open_trades": ("MAX_OPEN_TRADES", "max_trades"),
            "max_trades": ("MAX_OPEN_TRADES", "max_trades"),
            "capital_allocation": ("CAPITAL_ALLOCATION", "allocation_percent"),
            "allocation_percent": ("CAPITAL_ALLOCATION", "allocation_percent"),
        }
        for key, value in constraints.items():
            if value is None or key not in mappings:
                continue
            node_type, value_key = mappings[key]
            risk_root.children.append(
                self._build_risk_node_by_type(
                    {"type": node_type, value_key: value, "value": value},
                    f"{source_path}.portfolio_constraints.{key}",
                )
            )
