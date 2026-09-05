import sys
sys.path.append("/Users/binit/Backtesting_Engine")
import pandas as pd
from app.core.backtest_engine import BacktestEngine
from app.data.loader import MarketDataLoader
from app.execution.simulator import ExecutionEngine
from app.indicators.engine import IndicatorEngine
from app.signal.signal_engine import SignalEngine
from app.reports.metrics import MetricsEngine
from app.reports.portfolio import Portfolio
from app.core.models import StrategySettings
from app.data.feed import HistoricalReplayFeed

ast = {
  "_version_info": {
    "ast_schema_version": "1.0.0"
  },
  "ast": {
    "filter_nodes": [],
    "metadata": {
      "created_at": "",
      "source_path": "",
      "tags": {},
      "version": "1.0.0"
    },
    "node_id": "strategy_frontend_strategy",
    "node_type": "STRATEGY_ROOT",
    "operation_nodes": [
      {
        "entry_nodes": [
          {
            "children": [
              {
                "children": [
                  {
                    "data_type": "CLOSE",
                    "lookback_periods": 0,
                    "metadata": {
                      "alias": "CLOSE_0",
                      "indicator": "CLOSE",
                      "original_type": "market_data",
                      "output": "value",
                      "timeframe": "1d"
                    },
                    "node_id": "market_reference_1",
                    "node_type": "MARKET_REFERENCE",
                    "timeframe": "1d"
                  },
                  {
                    "data_type": "OPEN",
                    "lookback_periods": 0,
                    "metadata": {
                      "alias": "OPEN_0",
                      "indicator": "OPEN",
                      "original_type": "market_data",
                      "output": "value",
                      "timeframe": "1d"
                    },
                    "node_id": "market_reference_2",
                    "node_type": "MARKET_REFERENCE",
                    "timeframe": "1d"
                  }
                ],
                "lookback_periods": 0,
                "metadata": {
                  "operator": "GREATER_THAN"
                },
                "node_id": "greater_than_0",
                "node_type": "GREATER_THAN",
                "operator": "GREATER_THAN"
              }
            ],
            "metadata": {},
            "node_id": "entry_node_1",
            "node_type": "ENTRY"
          }
        ],
        "exit_nodes": [
          {
            "children": [
              {
                "children": [
                  {
                    "metadata": {
                      "type": "literal",
                      "value": 1
                    },
                    "node_id": "literal_3",
                    "node_type": "LITERAL",
                    "value": 1
                  }
                ],
                "metadata": {
                  "type": "TAKE_PROFIT"
                },
                "node_id": "take_profit_0",
                "node_type": "TAKE_PROFIT",
                "value": 1
              }
            ],
            "metadata": {},
            "node_id": "exit_node_2",
            "node_type": "EXIT"
          }
        ],
        "metadata": {},
        "node_id": "operation_0",
        "node_type": "OPERATION"
      }
    ]
  }
}

loader = MarketDataLoader()
feed = HistoricalReplayFeed(loader)
indicator = IndicatorEngine()
signal = SignalEngine()
execution = ExecutionEngine(qty=1, comm_rate=0.0001, slippage=2.0)
portfolio = Portfolio(initial_cash=100000.0)
metrics = MetricsEngine()

settings = StrategySettings(
    position_size_type="percentage",
    position_size=100.0,
    commission_rate=0.0001,
    slippage_bps=2.0,
    allow_short=False,
    close_on_opposite_signal=True,
    execution_mode="next_candle_open",
)

engine = BacktestEngine(
    loader=loader,
    feed=feed,
    indicator=indicator,
    signal=signal,
    execution=execution,
    portfolio=portfolio,
    metrics=metrics,
    settings=settings
)

try:
    res = engine.run(
        symbols=["ADANIENT"],
        start="2024-01-01T00:00:00Z",
        end="2025-01-01T00:00:00Z",
        timeframe="1d",
        strategy_ast=ast
    )
    
    trades = res.get("trades", [])
    print(f"Total trades: {len(trades)}")
    
    import pandas as pd
    for i, t in enumerate(trades[:10]):
        entry_t = t.get("entry_time")
        exit_t = t.get("exit_time")
        print(f"Trade {i+1}: Entry at {entry_t} Price {t.get('entry_price')} | Exit at {exit_t} Price {t.get('exit_price')}")
except Exception as e:
    import traceback
    traceback.print_exc()
