import sys
sys.path.append("/Users/binit/Backtesting_Engine")
import pandas as pd
from app.signal.evaluator import SignalEvaluator, EvaluatorState
from app.ast.ast_nodes import StrategyRootNode, EntryNode, ComparisonNode, MarketReferenceNode, OperationNode

# Manually construct AST: Close[0] > Open[0] (what was originally there)
root = StrategyRootNode(node_id="test", strategy_id="test", metadata=None)
op = OperationNode(node_id="op", metadata=None)
entry = EntryNode(node_id="entry", metadata=None)

left = MarketReferenceNode(node_id="m1", metadata=None, data_type="CLOSE", lookback_periods=0, timeframe="1d")
right = MarketReferenceNode(node_id="m2", metadata=None, data_type="OPEN", lookback_periods=0, timeframe="1d")

comp = ComparisonNode(node_id="comp", metadata=None, operator="GREATER_THAN", lookback_periods=0)
comp.left = left
comp.right = right
comp.children = [left, right]

entry.condition = comp
entry.children = [comp]

op.entry_nodes = [entry]
root.operation_nodes = [op]

evaluator = SignalEvaluator(maxlen=10)

# Feed Jan 16
indicators = {}
market_data_16 = {"OPEN": 3095.0, "CLOSE": 3056.5}
evaluator.history.append((indicators, market_data_16))
res = evaluator.evaluate(root, indicators, market_data_16)
print(f"Jan 16 evaluation: {res.signal}")

# Feed Jan 17
market_data_17 = {"OPEN": 3033.0, "CLOSE": 2971.05}
evaluator.history.append((indicators, market_data_17))
res = evaluator.evaluate(root, indicators, market_data_17)
print(f"Jan 17 evaluation: {res.signal}")

# Feed Jan 18
market_data_18 = {"OPEN": 2975.55, "CLOSE": 2918.89}
evaluator.history.append((indicators, market_data_18))
res = evaluator.evaluate(root, indicators, market_data_18)
print(f"Jan 18 evaluation: {res.signal}")
