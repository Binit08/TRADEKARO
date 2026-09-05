from typing import Any, Dict, List, Set, Optional

class IndicatorExtractor:
    @staticmethod
    def gather_indicator_configs(strategy_ast: Dict[str, Any], base_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        configs: List[Dict[str, Any]] = []
        seen: Set[str] = set()

        def _get_key(cfg: Dict[str, Any]) -> str:
            name = str(cfg.get("name", "")).strip().upper()
            normalized = {}
            for k, v in cfg.items():
                k_lower = k.lower()
                if k_lower in {"name", "alias", "output", "component"}:
                    continue
                if k_lower == "period" or k_lower == "timeperiod":
                    normalized["timeperiod"] = v
                else:
                    normalized[k_lower] = v
            parts = [f"{k.upper()}={normalized[k]}" for k in sorted(normalized)]
            return f"{name}_{'_'.join(parts)}" if parts else name

        for cfg in base_configs:
            name = str(cfg.get("name", "")).strip().upper()
            if not name:
                continue
            key = _get_key(cfg)
            if key not in seen:
                seen.add(key)
                configs.append(cfg)

        for cfg in IndicatorExtractor.extract_indicator_configs_from_ast(strategy_ast):
            key = _get_key(cfg)
            if key not in seen:
                seen.add(key)
                configs.append(cfg)

        return configs

    @staticmethod
    def get_max_lookback(configs: List[Dict[str, Any]]) -> int:
        max_lookback = 0
        for cfg in configs:
            for key in ["timeperiod", "period", "lookback_days", "lookback_limit", "fastperiod", "slowperiod", "signalperiod"]:
                val = cfg.get(key)
                if val is not None:
                    try:
                        val = int(val)
                        if val > max_lookback:
                            max_lookback = val
                    except (ValueError, TypeError):
                        pass
        # Add a buffer for smoothing indicators like EMA that require more history to settle
        return max(max_lookback * 2, 100)

    @staticmethod
    def validate_indicator_configs(configs: List[Dict[str, Any]], available: List[str]) -> None:
        available_set = {name.upper() for name in available}
        missing = []
        for cfg in configs:
            name = str(cfg.get("name", "")).strip().upper()
            if name and name not in available_set:
                if name.startswith("SEQUENCE_UPWARD_"):
                    continue
                missing.append(name)
        if missing:
            raise ValueError(f"Unknown indicator(s) referenced in strategy AST: {sorted(set(missing))}")

    @staticmethod
    def extract_indicator_configs_from_ast(node: Any, depth: int = 0, node_count: List[int] = None) -> List[Dict[str, Any]]:
        if node_count is None:
            node_count = [0]
            
        node_count[0] += 1
        if node_count[0] > 10000:
            raise ValueError("AST has too many nodes")
            
        if depth > 64:
            raise ValueError("AST too deep")
            
        configs: List[Dict[str, Any]] = []
        if isinstance(node, dict):
            cfg = IndicatorExtractor._normalize_indicator_spec(node)
            if cfg:
                configs.append(cfg)
            for key, value in node.items():
                if isinstance(value, dict):
                    configs.extend(IndicatorExtractor.extract_indicator_configs_from_ast(value, depth + 1, node_count))
                elif isinstance(value, list):
                    for item in value:
                        configs.extend(IndicatorExtractor.extract_indicator_configs_from_ast(item, depth + 1, node_count))
            return configs
        if isinstance(node, list):
            for item in node:
                configs.extend(IndicatorExtractor.extract_indicator_configs_from_ast(item, depth + 1, node_count))
        return configs

    @staticmethod
    def _normalize_indicator_spec(raw: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(raw, dict):
            return None
        if raw.get("node_type") == "INDICATOR" and "indicator_config" in raw:
            cfg = raw["indicator_config"]
            name = cfg.get("indicator_type")
            if not isinstance(name, str):
                return None
            if name.upper() in ("SEQUENCE", "ARITHMETIC", "PATTERN", "MARKET_REFERENCE", "CONSTANT"):
                return None
            config: Dict[str, Any] = {"name": name.strip().upper()}
            params = cfg.get("parameters", {})
            for k, v in params.items():
                if k == "period":
                    config["timeperiod"] = v
                else:
                    config[k] = v
            if "output_property" in cfg:
                config["output"] = cfg["output_property"]
            if "alias" in cfg:
                config["alias"] = cfg["alias"]
            return config
        name = raw.get("indicator")
        if not isinstance(name, str):
            return None
        if name.upper() in ("SEQUENCE", "ARITHMETIC", "PATTERN", "MARKET_REFERENCE", "CONSTANT"):
            return None
        config: Dict[str, Any] = {"name": name.strip().upper()}
        if "period" in raw:
            config["period"] = raw["period"]
        elif "timeperiod" in raw:
            config["timeperiod"] = raw["timeperiod"]
        if "output" in raw:
            config["output"] = raw["output"]
        elif "component" in raw:
            config["output"] = raw["component"]
        if "alias" in raw:
            config["alias"] = raw["alias"]
        return config
