import urllib.request
import json
import sys

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
          },
          {
            "children": [
              {
                "children": [
                  {
                    "metadata": {
                      "type": "literal",
                      "value": 1
                    },
                    "node_id": "literal_4",
                    "node_type": "LITERAL",
                    "value": 1
                  }
                ],
                "metadata": {
                  "type": "STOP_LOSS"
                },
                "node_id": "stop_loss_1",
                "node_type": "STOP_LOSS",
                "value": 1
              }
            ],
            "metadata": {},
            "node_id": "exit_node_3",
            "node_type": "EXIT"
          }
        ],
        "metadata": {},
        "node_id": "operation_0",
        "node_type": "OPERATION",
        "position_sizing": {
          "metadata": {},
          "node_id": "position_sizing_1",
          "node_type": "POSITION_SIZING",
          "value": 100
        }
      }
    ]
  },
  "execution_context": {
    "capital": 100000,
    "position_side": "LONG",
    "position_size": 100,
    "position_size_type": "percentage",
    "pyramiding": 0,
    "timeframe": "1d",
    "trade_type": "EQUITY"
  }
}

req_data = {
    "strategy_ast": ast,
    "symbol": "ADANIENT",
    "start": "2024-01-01T00:00:00Z",
    "end": "2025-01-01T00:00:00Z",
    "timeframe": "1d",
    "initial_cash": 100000.0,
    "position_size_type": "percentage",
    "position_size": 100.0,
    "commission_rate": 0.0001,
    "slippage_bps": 2.0,
    "allow_short": False,
    "close_on_opposite_signal": True,
    "execution_mode": "next_candle_open",
    "market_type": "EQUITY",
    "multiplier": 1.0,
    "margin": 1.0,
    "expiry": None,
}

url = 'http://127.0.0.1:8002/api/backtests'
req = urllib.request.Request(url, data=json.dumps(req_data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode('utf-8'))
    
    # Print the trades
    trades = data.get("trades", [])
    print(f"Total trades: {len(trades)}")
    
    # Show first 10 trades
    for i, t in enumerate(trades[:10]):
        print(f"Trade {i+1}: Entry at {t.get('entry_time')} Price {t.get('entry_price')} | Exit at {t.get('exit_time')} Price {t.get('exit_price')}")
        
except Exception as e:
    print('Error:', e)
    if hasattr(e, 'read'):
        print('Response:', e.read().decode('utf-8'))
