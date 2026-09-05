import pytest
from app.signal.signal_engine import SignalEngine
from app.signal.models import SignalType
from app.config.settings import StrategySettings

def _make_market_data(close=100.0, high=105.0, low=95.0, open_=100.0, volume=1000.0):
    return {"CLOSE": close, "HIGH": high, "LOW": low, "OPEN": open_, "VOLUME": volume}

def _run_sequence(ast, indicators_list, market_data_list, position_side_list=None):
    engine = SignalEngine(warmup_bars=0)
    if position_side_list is None:
        position_side_list = [None] * len(indicators_list)
    results = []
    for inds, mkt, pos in zip(indicators_list, market_data_list, position_side_list):
        res = engine.evaluate(ast, inds, market_data=mkt, current_position_side=pos)
        results.append(res.signal)
    return results

# 1. Complex MA Crossover + RSI + Trend Filter (Multi-Condition AND)
def test_complex_ma_rsi_trend():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "AND",
                        "children": [
                            {
                                "node_type": "CROSS_ABOVE",
                                "children": [
                                    {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "EMA", "parameters": {"timeperiod": 50}, "output_property": "value"}},
                                    {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "EMA", "parameters": {"timeperiod": 200}, "output_property": "value"}}
                                ]
                            },
                            {
                                "node_type": "GREATER_THAN",
                                "children": [
                                    {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "RSI", "parameters": {"timeperiod": 14}, "output_property": "value"}},
                                    {"node_type": "CONSTANT", "value": 50}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    inds1 = {"EMA_TIMEPERIOD=50": 90, "EMA_TIMEPERIOD=200": 100, "RSI_TIMEPERIOD=14": 55}
    inds2 = {"EMA_TIMEPERIOD=50": 105, "EMA_TIMEPERIOD=200": 100, "RSI_TIMEPERIOD=14": 55}
    
    res = _run_sequence(ast, [inds1, inds2], [_make_market_data()]*2)
    assert res == [SignalType.HOLD, SignalType.BUY]

# 2. Volatility Breakout (Arithmetic expressions: CLOSE > EMA + ATR*1.5)
def test_volatility_breakout():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "GREATER_THAN",
                        "children": [
                            {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE"},
                            {
                                "node_type": "ADD",
                                "children": [
                                    {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "EMA", "parameters": {"timeperiod": 20}}},
                                    {
                                        "node_type": "MULTIPLY",
                                        "children": [
                                            {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "ATR", "parameters": {"timeperiod": 14}}},
                                            {"node_type": "CONSTANT", "value": 1.5}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }
    inds = {"EMA_TIMEPERIOD=20": 100, "ATR_TIMEPERIOD=14": 10}
    res = _run_sequence(ast, [inds, inds], [_make_market_data(close=110), _make_market_data(close=116)])
    assert res == [SignalType.HOLD, SignalType.BUY]

# 3. Sequential Logic (RSI < 30 followed by cross above 30 within 3 bars)
def test_sequential_logic_rsi_reversal():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "FOLLOWED_BY",
                        "max_bars_between": 3,
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
    
    inds_list = [{"RSI_TIMEPERIOD=14": v} for v in [40, 25, 28, 35]]
    mkt = [_make_market_data()]*4
    res = _run_sequence(ast, inds_list, mkt)
    assert res == [SignalType.HOLD, SignalType.HOLD, SignalType.HOLD, SignalType.BUY]

# 4. Price Action Lookback (CLOSE > CLOSE[1])
def test_price_action_lookback():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "GREATER_THAN",
                        "children": [
                            {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE", "lookback_periods": 0},
                            {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE", "lookback_periods": 1}
                        ]
                    }
                ]
            }
        }
    }
    
    res = _run_sequence(ast, [{}, {}, {}], [_make_market_data(close=100), _make_market_data(close=105), _make_market_data(close=90)])
    assert res == [SignalType.HOLD, SignalType.BUY, SignalType.HOLD]

# 5. Position-Aware Exits (If LONG and CLOSE < EMA20)
def test_position_aware_exit():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "exit_node": {
                "node_type": "EXIT",
                "children": [
                    {
                        "node_type": "AND",
                        "children": [
                            {
                                "node_type": "EQUAL",
                                "children": [
                                    {"node_type": "MARKET_REFERENCE", "data_type": "POSITION_SIDE"},
                                    {"node_type": "CONSTANT", "value": "LONG"}
                                ]
                            },
                            {
                                "node_type": "LESS_THAN",
                                "children": [
                                    {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE"},
                                    {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "EMA", "parameters": {"timeperiod": 20}}}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    inds = {"EMA_TIMEPERIOD=20": 100}
    res = _run_sequence(ast, [inds]*3, [_make_market_data(close=90), _make_market_data(close=110), _make_market_data(close=90)], [None, "LONG", "LONG"])
    assert res == [SignalType.HOLD, SignalType.HOLD, SignalType.SELL]

# 6. Mean Reversion (Cross Below lower BBAND AND RSI < 20)
def test_mean_reversion_bbands():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "AND",
                        "children": [
                            {
                                "node_type": "CROSS_BELOW",
                                "children": [
                                    {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE"},
                                    {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "BBANDS", "parameters": {"timeperiod": 20}, "output_property": "lowerband"}}
                                ]
                            },
                            {
                                "node_type": "LESS_THAN",
                                "children": [
                                    {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "RSI", "parameters": {"timeperiod": 14}}},
                                    {"node_type": "CONSTANT", "value": 20}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    inds1 = {"BBANDS_TIMEPERIOD=20": {"lowerband": 100}, "RSI_TIMEPERIOD=14": 30}
    inds2 = {"BBANDS_TIMEPERIOD=20": {"lowerband": 100}, "RSI_TIMEPERIOD=14": 15}
    
    res = _run_sequence(ast, [inds1, inds2], [_make_market_data(close=105), _make_market_data(close=95)])
    assert res == [SignalType.HOLD, SignalType.BUY]

# 7. Volume Confirmation (Breakout AND Volume > Volume[1]*2)
def test_volume_confirmation():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "GREATER_THAN",
                        "children": [
                            {"node_type": "MARKET_REFERENCE", "data_type": "VOLUME", "lookback_periods": 0},
                            {
                                "node_type": "MULTIPLY",
                                "children": [
                                    {"node_type": "MARKET_REFERENCE", "data_type": "VOLUME", "lookback_periods": 1},
                                    {"node_type": "CONSTANT", "value": 2}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    res = _run_sequence(ast, [{}, {}, {}], [
        _make_market_data(volume=1000), 
        _make_market_data(volume=1500), 
        _make_market_data(volume=3500)
    ])
    assert res == [SignalType.HOLD, SignalType.HOLD, SignalType.BUY]

# 8. Variable Assignment and Ref
def test_variable_assignment_and_reference():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "variable_nodes": [
                {
                    "node_type": "VARIABLE_ASSIGNMENT",
                    "variable_name": "MY_THRESH",
                    "children": [
                        {"node_type": "CONSTANT", "value": 1},
                        {
                            "node_type": "ADD",
                            "children": [
                                {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "EMA", "parameters": {"timeperiod": 20}}},
                                {"node_type": "CONSTANT", "value": 10}
                            ]
                        }
                    ]
                }
            ],
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "GREATER_THAN",
                        "children": [
                            {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE"},
                            {"node_type": "VARIABLE_REFERENCE", "variable_name": "MY_THRESH"}
                        ]
                    }
                ]
            }
        }
    }
    
    inds = {"EMA_TIMEPERIOD=20": 100}
    res = _run_sequence(ast, [inds, inds], [_make_market_data(close=105), _make_market_data(close=115)])
    assert res == [SignalType.HOLD, SignalType.BUY]

# 9. Gap and Go ((OPEN - CLOSE[1])/CLOSE[1] > 0.02 AND CLOSE > OPEN)
def test_gap_and_go():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "entry_node": {
                "node_type": "ENTRY",
                "children": [
                    {
                        "node_type": "AND",
                        "children": [
                            {
                                "node_type": "GREATER_THAN",
                                "children": [
                                    {
                                        "node_type": "DIVIDE",
                                        "children": [
                                            {
                                                "node_type": "SUBTRACT",
                                                "children": [
                                                    {"node_type": "MARKET_REFERENCE", "data_type": "OPEN"},
                                                    {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE", "lookback_periods": 1}
                                                ]
                                            },
                                            {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE", "lookback_periods": 1}
                                        ]
                                    },
                                    {"node_type": "CONSTANT", "value": 0.02}
                                ]
                            },
                            {
                                "node_type": "GREATER_THAN",
                                "children": [
                                    {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE"},
                                    {"node_type": "MARKET_REFERENCE", "data_type": "OPEN"}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    res = _run_sequence(ast, [{}, {}], [
        _make_market_data(open_=100, close=100),
        _make_market_data(open_=103, close=105)
    ])
    assert res == [SignalType.HOLD, SignalType.BUY]

# 10. Multi-Condition OR Exits
def test_multi_condition_or_exits():
    ast = {
        "ast": {
            "node_type": "STRATEGY_ROOT",
            "exit_node": {
                "node_type": "EXIT",
                "children": [
                    {
                        "node_type": "OR",
                        "children": [
                            {
                                "node_type": "CROSS_BELOW",
                                "children": [
                                    {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE"},
                                    {"node_type": "INDICATOR", "indicator_config": {"indicator_type": "EMA", "parameters": {"timeperiod": 20}}}
                                ]
                            },
                            {
                                "node_type": "LESS_THAN",
                                "children": [
                                    {"node_type": "MARKET_REFERENCE", "data_type": "CLOSE"},
                                    {"node_type": "CONSTANT", "value": 90}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    inds = {"EMA_TIMEPERIOD=20": 100}
    res = _run_sequence(ast, [inds, inds, inds], [
        _make_market_data(close=105),
        _make_market_data(close=102),
        _make_market_data(close=85)
    ])
    assert res == [SignalType.HOLD, SignalType.HOLD, SignalType.SELL]

