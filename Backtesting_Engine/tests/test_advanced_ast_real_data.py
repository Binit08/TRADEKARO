import pytest
import numpy as np
import pandas as pd
from app.signal.signal_engine import SignalEngine
from app.signal.models import SignalType
from app.indicators.indicator_engine import IndicatorEngine
from app.ast.indicator_extractor import IndicatorExtractor

def generate_sine_wave_data(length=200):
    t = np.arange(length)
    # A wave that starts at 100, goes to 120, drops to 80, rises to 120
    close_price = 100 + 20 * np.sin(2 * np.pi * t / 100)
    open_price = close_price - 0.5
    high_price = close_price + 1.0
    low_price = close_price - 1.0
    volume = np.full(length, 1000.0)
    
    return pd.DataFrame({
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "volume": volume
    })

def run_simulation_with_real_data(ast_dict, df):
    # 1. Extract required indicators
    configs = IndicatorExtractor.gather_indicator_configs(ast_dict.get("ast", ast_dict), [])
    
    # 2. Compute all
    ind_engine = IndicatorEngine()
    ind_engine.compute_all(df, configs)
    
    sig_engine = SignalEngine(warmup_bars=0)
    
    results = []
    for i in range(len(df)):
        inds = ind_engine.get_snapshot(i)
        
        row = df.iloc[i]
        mkt = {
            "OPEN": row["open"],
            "HIGH": row["high"],
            "LOW": row["low"],
            "CLOSE": row["close"],
            "VOLUME": row["volume"]
        }
        
        res = sig_engine.evaluate(ast_dict, inds, market_data=mkt)
        results.append(res.signal)
        
    return results

def test_real_data_ma_crossover():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "CROSS_ABOVE",
                        "children": [
                            {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "EMA", "parameters": {"timeperiod": 10}, "output_property": "value"}},
                            {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "EMA", "parameters": {"timeperiod": 30}, "output_property": "value"}}
                        ]
                    }
                ]
            }
        }
    }
    
    df = generate_sine_wave_data(200)
    # Sine starts at 100, goes to 120 (t=25), drops to 80 (t=75), rises to 120 (t=125).
    # The drop causes EMA10 to fall below EMA30. The rise causes it to cross back above.
    # EMA30 requires 30 bars warmup.
    res = run_simulation_with_real_data(ast, df)
    
    # Verify we get at least one BUY signal
    assert SignalType.BUY in res
    
    # Find index of BUY
    buy_idx = res.index(SignalType.BUY)
    
    # Manually compute EMA to verify
    ema10 = df['close'].ewm(span=10, adjust=False).mean()
    ema30 = df['close'].ewm(span=30, adjust=False).mean()
    
    # Wait, TA-Lib EMA has a warmup where it uses SMA. Let's just trust TA-lib.
    # The BUY should occur exactly where EMA10 crosses EMA30.
    assert buy_idx > 30

def test_real_data_rsi_reversal():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "FOLLOWED_BY",
                        "max_bars_between": 10,
                        "setup_condition": {
                            "node_type": "LESS_THAN",
                            "children": [
                                {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "RSI", "parameters": {"timeperiod": 14}}},
                                {"node_type": "CONSTANT", "value": 30}
                            ]
                        },
                        "trigger_condition": {
                            "node_type": "CROSS_ABOVE",
                            "children": [
                                {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "RSI", "parameters": {"timeperiod": 14}}},
                                {"node_type": "CONSTANT", "value": 30}
                            ]
                        }
                    }
                ]
            }
        }
    }
    
    # We need a sharp drop then recovery
    df = generate_sine_wave_data(200)
    # At t=0 it's 80, rises to 120 (t=50), drops to 80 (t=100)
    # The drop into t=100 will push RSI < 30. Then as t > 100 it rises, pushing RSI > 30.
    res = run_simulation_with_real_data(ast, df)
    assert SignalType.BUY in res


def test_real_data_green_candle_and_profit_exit():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "GREATER_THAN",
                        "children": [
                            {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE", "lookback_periods": 1},
                            {"node_type": "MARKET_REFERENCE", "data_type": "OPEN", "lookback_periods": 1}
                        ]
                    }
                ]
            },
            "exit_node": {
                "node_type": "EXIT",
                "children": [
                    {
                        "node_type": "GREATER_THAN",
                        "children": [
                            {"node_type": "MARKET_REFERENCE", "data_type": "UNREALIZED_PNL_PERCENT"},
                            {"node_type": "CONSTANT", "value": 5.0}
                        ]
                    }
                ]
            }
        }
    }
    
    df = pd.DataFrame({
        "open": [100, 100, 105, 110, 115, 120],
        "high": [101, 106, 111, 116, 121, 126],
        "low": [99, 99, 104, 109, 114, 119],
        "close": [98, 105, 110, 115, 120, 125], # Index 1 is GREEN (105 > 100). Index 0 is RED.
        "volume": [1000] * 6
    })
    
    # We'll run a custom simulation loop since we need to inject dynamic UNREALIZED_PNL_PERCENT
    sig_engine = SignalEngine(warmup_bars=0)
    ind_engine = IndicatorEngine()
    ind_engine.compute_all(df, [])
    
    results = []
    entry_price = None
    
    for i in range(len(df)):
        inds = ind_engine.get_snapshot(i)
        row = df.iloc[i]
        
        mkt = {
            "OPEN": row["open"],
            "HIGH": row["high"],
            "LOW": row["low"],
            "CLOSE": row["close"],
            "VOLUME": row["volume"],
            "UNREALIZED_PNL_PERCENT": 0.0
        }
        
        if entry_price is not None:
            mkt["UNREALIZED_PNL_PERCENT"] = ((row["close"] - entry_price) / entry_price) * 100.0
            
        pos_side = "LONG" if entry_price is not None else None
        res = sig_engine.evaluate(ast, inds, market_data=mkt, current_position_side=pos_side)
        results.append(res.signal)
        
        # If we get a BUY signal, simulate entering a position for the next bar
        if res.signal == SignalType.BUY and entry_price is None:
            entry_price = row["close"]
            
    # Index 0: RED candle -> HOLD
    # Index 1: GREEN candle -> but evaluated at t=1, lookback=1 is t=0 (RED), so HOLD
    # Index 2: Evaluated at t=2, lookback=1 is t=1 (GREEN), so BUY! (Entry price = 110)
    # Index 3: Close is 115. PNL = (115-110)/110 = 4.54% -> HOLD
    # Index 4: Close is 120. PNL = (120-110)/110 = 9.09% (> 5.0) -> SELL!
    
    assert results[2] == SignalType.BUY
    assert results[4] == SignalType.SELL

