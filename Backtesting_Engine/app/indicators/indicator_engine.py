"""Production-oriented dynamic indicator engine built on TA-Lib.

The engine consumes candle updates and computes any TA-Lib indicator
using dynamic routing from `talib.abstract.Function` metadata.

Main API:
- `update(candle)` appends OHLCV histories.
- `available()` returns all loaded TA-Lib indicators.
- `compute(indicator_name, **params)` returns the latest value only.
- `compute_many(configs)` computes multiple indicators in one call.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

import numpy as np


def indicator_config_key(name: str, params: Optional[Dict[str, Any]] = None) -> str:
    """Build a canonical indicator config key from name and params."""
    base = str(name).strip().upper()
    normalized: Dict[str, Any] = {}
    if params is not None:
        for key, value in params.items():
            if key == "period":
                normalized["timeperiod"] = value
            elif key == "timeperiod":
                normalized["timeperiod"] = value
            else:
                normalized[key.lower()] = value

    if not normalized:
        return base

    parts = [f"{k.upper()}={normalized[k]}" for k in sorted(normalized)]
    return f"{base}_{'_'.join(parts)}"

try:
    import talib
    from talib import abstract
except Exception:  # pragma: no cover - handled in tests
    talib = None
    abstract = None


def _sma(values: np.ndarray, timeperiod: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size < timeperiod:
        return np.full(values.shape, np.nan)

    out = np.full(values.shape, np.nan)
    cumsum = np.cumsum(values, dtype=float)
    out[timeperiod - 1 :] = (cumsum[timeperiod - 1 :] - np.concatenate(([0.0], cumsum[:-timeperiod]))) / float(timeperiod)
    return out


def _rsi(values: np.ndarray, timeperiod: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size < timeperiod + 1:
        return np.full(values.shape, np.nan)

    deltas = np.diff(values)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.full(values.shape, np.nan)
    avg_loss = np.full(values.shape, np.nan)

    avg_gain[timeperiod] = np.mean(gains[:timeperiod])
    avg_loss[timeperiod] = np.mean(losses[:timeperiod])

    for i in range(timeperiod + 1, values.size):
        avg_gain[i] = (avg_gain[i - 1] * (timeperiod - 1) + gains[i - 1]) / float(timeperiod)
        avg_loss[i] = (avg_loss[i - 1] * (timeperiod - 1) + losses[i - 1]) / float(timeperiod)

    rs = np.divide(avg_gain, avg_loss, out=np.full_like(avg_gain, np.nan), where=avg_loss != 0.0)
    return 100.0 - (100.0 / (1.0 + rs))


def _ema(values: np.ndarray, timeperiod: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size < timeperiod:
        return np.full(values.shape, np.nan)

    out = np.full(values.shape, np.nan)
    # The first EMA value is simple SMA
    sma_init = np.mean(values[:timeperiod])
    out[timeperiod - 1] = sma_init

    multiplier = 2.0 / (timeperiod + 1.0)
    for i in range(timeperiod, values.size):
        out[i] = (values[i] - out[i - 1]) * multiplier + out[i - 1]
    return out


def _continuous_upward_rally(
    open_p: np.ndarray,
    close_p: np.ndarray,
    lookback_days: int = 30,
    min_percent: float = 20.0,
    condition: str = "no_red_candles"
) -> Dict[str, np.ndarray]:
    size = close_p.size
    bottom_level = np.full(size, -np.inf)
    above_level = np.full(size, np.inf)
    
    if size >= lookback_days:
        for i in range(lookback_days - 1, size):
            start_price = close_p[i - lookback_days + 1]
            end_price = close_p[i]
            pct_change = ((end_price - start_price) / start_price) * 100.0 if start_price > 0 else 0.0
            
            no_red = True
            if condition == "no_red_candles":
                for j in range(i - lookback_days + 1, i + 1):
                    if close_p[j] < open_p[j]:
                        no_red = False
                        break
            
            if pct_change >= min_percent and no_red:
                bottom_level[i] = 99999999.0
                above_level[i] = -99999999.0
                
    return {"bottom_level": bottom_level, "above_level": above_level}


def _last_valid(arr: np.ndarray) -> Optional[float]:
    """Return the last non-NaN value from a numpy array, or None."""
    if arr is None:
        return None
    try:
        flat = np.asarray(arr).flatten()
    except Exception:
        return None
    for v in flat[::-1]:
        if not np.isnan(v):
            return float(v)
    return None


AVAILABLE_INDICATORS: List[str] = []
if talib is not None:
    try:
        AVAILABLE_INDICATORS = list(talib.get_functions())
    except Exception:
        AVAILABLE_INDICATORS = [n for n in dir(talib) if n.isupper() and callable(getattr(talib, n, None))]
else:
    AVAILABLE_INDICATORS = ["RSI", "SMA", "EMA"]

try:
    import pandas_ta as ta
    pandas_ta_indicators = [func.upper() for func in dir(ta) if not func.startswith('_') and callable(getattr(ta, func))]
    AVAILABLE_INDICATORS.extend(pandas_ta_indicators)
except ImportError:
    pass

AVAILABLE_INDICATORS = list(set(AVAILABLE_INDICATORS))

if "CONTINUOUS_UPWARD_RALLY" not in AVAILABLE_INDICATORS:
    AVAILABLE_INDICATORS.append("CONTINUOUS_UPWARD_RALLY")
if "CONTINUOUS_RALLY" not in AVAILABLE_INDICATORS:
    AVAILABLE_INDICATORS.append("CONTINUOUS_RALLY")


@dataclass
class IndicatorEngine:
    """Engine that pre-computes indicators over the full DataFrame for O(1) loop retrieval."""

    open_history: List[float] = field(default_factory=list)
    high_history: List[float] = field(default_factory=list)
    low_history: List[float] = field(default_factory=list)
    close_history: List[float] = field(default_factory=list)
    volume_history: List[float] = field(default_factory=list)

    _indicators_data: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def update(self, candle: Any) -> None:
        """Append a new candle-like object to histories."""
        self.open_history.append(float(candle.open))
        self.close_history.append(float(candle.close))
        self.high_history.append(float(candle.high))
        self.low_history.append(float(candle.low))
        vol = getattr(candle, "volume", None)
        self.volume_history.append(float(vol) if vol is not None else 0.0)

    def reset(self) -> None:
        """Reset the indicator history and computed data."""
        self.open_history.clear()
        self.high_history.clear()
        self.low_history.clear()
        self.close_history.clear()
        self.volume_history.clear()
        self._indicators_data.clear()

    def available(self) -> List[str]:
        """Return all loaded TA-Lib indicator names."""
        return list(AVAILABLE_INDICATORS)

    def compute_all(self, df: Any, requirements: List[Dict[str, Any]]) -> None:
        """Pre-compute all required indicators dynamically over the full DataFrame."""
        self._indicators_data.clear()
        if df is None or df.empty:
            return

        import pandas as pd
        df = pd.DataFrame(df)
        
        # Ensure column names are lowercase to match expectations
        df.columns = [str(c).lower() for c in df.columns]
        
        # Safe extraction with fallbacks (default to close if high/low/open are missing)
        close_s = df["close"] if "close" in df.columns else (df.iloc[:, 0] if not df.empty else pd.Series(dtype=float))
        
        inputs = {
            "close": close_s.to_numpy(dtype=float),
            "open": df["open"].to_numpy(dtype=float) if "open" in df.columns else close_s.to_numpy(dtype=float),
            "high": df["high"].to_numpy(dtype=float) if "high" in df.columns else close_s.to_numpy(dtype=float),
            "low": df["low"].to_numpy(dtype=float) if "low" in df.columns else close_s.to_numpy(dtype=float),
            "volume": df["volume"].to_numpy(dtype=float) if "volume" in df.columns else np.zeros(len(df), dtype=float),
        }

        for cfg in requirements:
            name = str(cfg.get("name", "")).strip().upper()
            if not name:
                continue
            params = {
                k: v
                for k, v in cfg.items()
                if k.lower() not in {"name", "alias", "output", "component"}
            }
            params_normalized = dict(params)
            if "period" in params_normalized and "timeperiod" not in params_normalized:
                params_normalized["timeperiod"] = params_normalized.pop("period")

            key = cfg.get("alias") or indicator_config_key(name, params)
            series = self._compute_series(name, inputs, params_normalized)
            self._indicators_data[key] = series
            
            if name not in self._indicators_data:
                self._indicators_data[name] = series

    def _compute_series(self, name: str, inputs: Dict[str, np.ndarray], params_normalized: Dict[str, Any]) -> Any:
        if name in ("CONTINUOUS_UPWARD_RALLY", "CONTINUOUS_RALLY") or name.startswith("SEQUENCE_UPWARD_"):
            lookback = int(params_normalized.get("lookback_days") or params_normalized.get("lookback_limit") or 30)
            min_pct = float(params_normalized.get("min_percent") or 20.0)
            cond = str(params_normalized.get("condition", "no_red_candles"))
            return _continuous_upward_rally(
                inputs["open"],
                inputs["close"],
                lookback_days=lookback,
                min_percent=min_pct,
                condition=cond
            )

        if talib is None:
            timeperiod = int(params_normalized.get("timeperiod", 14))
            if name == "SMA":
                return _sma(inputs["close"], timeperiod)
            elif name == "RSI":
                return _rsi(inputs["close"], timeperiod)
            elif name == "EMA":
                return _ema(inputs["close"], timeperiod)
            else:
                raise RuntimeError(f"Indicator '{name}' is not available without TA-Lib")
        else:
            try:
                func = abstract.Function(name)
                ordered_args: List[np.ndarray] = []
                for key, input_spec in func.input_names.items():
                    if isinstance(input_spec, str):
                        override = params_normalized.get("source") or params_normalized.get("price")
                        if key == "price" and override and override.lower() in inputs:
                            ordered_args.append(inputs[override.lower()])
                        else:
                            ordered_args.append(inputs[input_spec])
                    else:
                        for ik in input_spec:
                            ordered_args.append(inputs[ik])

                valid_params = {k: v for k, v in params_normalized.items() if k in func.parameters}
                result = getattr(talib, name)(*ordered_args, **valid_params)

                if isinstance(result, tuple):
                    output_names = [str(n) for n in func.output_names]
                    return {out_name: np.asarray(out_array) for out_name, out_array in zip(output_names, result)}
                else:
                    return np.asarray(result)
            except Exception:
                try:
                    import pandas as pd
                    import pandas_ta as ta
                    
                    df = pd.DataFrame(inputs)
                    
                    if "timeperiod" in params_normalized and "length" not in params_normalized:
                        params_normalized["length"] = params_normalized["timeperiod"]
                        
                    # Use pandas_ta Strategy or direct call
                    # df.ta(kind=...) is the easiest way to call it dynamically
                    result = df.ta(kind=name.lower(), append=False, **params_normalized)
                    
                    if result is None:
                        raise RuntimeError(f"Indicator '{name}' could not be computed by TA-Lib or pandas-ta.")
                        
                    if isinstance(result, pd.DataFrame):
                        return {col: result[col].to_numpy() for col in result.columns}
                    elif isinstance(result, pd.Series):
                        return result.to_numpy()
                    else:
                        return np.asarray(result)
                except ImportError:
                    raise RuntimeError(f"Indicator '{name}' not found in TA-Lib and pandas-ta is not installed.")
                except Exception as e:
                    raise RuntimeError(f"Failed to compute indicator '{name}' using pandas-ta: {e}")

    def get_snapshot(self, index: int) -> Dict[str, Any]:
        """Gets all indicator values for a specific row index."""
        snapshot = {}
        for key, data in self._indicators_data.items():
            if isinstance(data, dict):
                # Multi-output
                vals = {}
                for k, v in data.items():
                    if index < len(v):
                        val = v[index]
                        if not np.isnan(val):
                            vals[k] = float(val)
                if vals:
                    snapshot[key] = vals
            else:
                # Single-output
                if index < len(data):
                    val = data[index]
                    if not np.isnan(val):
                        snapshot[key] = float(val)
        return snapshot

    def compute_many(self, configs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Backward-compatible compute_many using histories.

        .. deprecated:: 1.0.0
           This method recomputes the entire history on every call, leading to O(N^2)
           complexity. Use `compute_all` and `get_snapshot` instead.
        """
        import warnings
        warnings.warn(
            "compute_many is deprecated because it recomputes the entire history on every call. "
            "Use compute_all and get_snapshot instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        if configs is None:
            return {}
        import pandas as pd
        df = pd.DataFrame({
            "open": self.open_history,
            "high": self.high_history,
            "low": self.low_history,
            "close": self.close_history,
            "volume": self.volume_history
        })
        self.compute_all(df, configs)
        return self.get_snapshot(len(df) - 1) if not df.empty else {}

    def compute(self, indicator_name: str, **params) -> Optional[Dict[str, Any]]:
        """Backward-compatible compute using histories.

        .. deprecated:: 1.0.0
           This method recomputes the entire history on every call, leading to O(N^2)
           complexity. Use `compute_all` and `get_snapshot` instead.
        """
        import warnings
        warnings.warn(
            "compute is deprecated because it recomputes the entire history on every call. "
            "Use compute_all and get_snapshot instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        import pandas as pd
        df = pd.DataFrame({
            "open": self.open_history,
            "high": self.high_history,
            "low": self.low_history,
            "close": self.close_history,
            "volume": self.volume_history
        })
        configs = [dict({"name": indicator_name}, **params)]
        self.compute_all(df, configs)
        snapshot = self.get_snapshot(len(df) - 1) if not df.empty else {}
        key = indicator_config_key(indicator_name.upper(), params)
        if key in snapshot:
            return {"name": indicator_name.upper(), "value": snapshot[key]}
        if indicator_name.upper() in snapshot:
            return {"name": indicator_name.upper(), "value": snapshot[indicator_name.upper()]}
        return None
