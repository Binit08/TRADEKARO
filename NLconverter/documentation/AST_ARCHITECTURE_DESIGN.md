# Trading Platform AST Architecture

Version: 1.0.0  
Scope: Canonical JSON -> AST Builder -> AST Structure  
Status: Implemented in `strategy_parser/ast`

This AST layer is a deterministic compiler stage. It does not call an LLM and
does not evaluate trading logic. Market data, indicator calculation, portfolio
state, position state, condition evaluation, and order execution all remain in
the backtesting engine.

## Pipeline Boundary

```text
User Prompt
  -> LLM
  -> Canonical JSON
  -> ASTBuilder
  -> StrategyRootNode
  -> Backtesting Engine
```

The AST is a data-only representation of strategy structure.

## Design Rules

1. Same Canonical JSON plus same strategy id produces the same AST.
2. AST generation is rule-based and uses no LLM.
3. Nodes are dataclasses with structural fields only.
4. Entry, exit, risk, and filters are explicit core wrapper nodes.
5. Strategy logic is represented recursively through `children`.
6. Indicators and patterns remain generic configuration references.
7. Short input aliases such as `GT`, `LT`, `SUB`, and `MUL` normalize to stable canonical AST node names.
8. Serialization includes schema versioning.

## Node Hierarchy

```text
ASTNode
├── Core
│   ├── StrategyRootNode
│   ├── EntryNode
│   ├── ExitNode
│   ├── RiskNode
│   └── FilterNode
├── Logical
│   ├── AndNode
│   ├── OrNode
│   └── NotNode
├── Comparison
│   ├── GreaterThanNode       (GREATER_THAN)
│   ├── LessThanNode          (LESS_THAN)
│   ├── GreaterEqualNode      (GREATER_EQUAL)
│   ├── LessEqualNode         (LESS_EQUAL)
│   ├── EqualNode             (EQUAL)
│   └── NotEqualNode          (NOT_EQUAL)
├── Cross
│   ├── CrossAboveNode
│   └── CrossBelowNode
├── Arithmetic
│   ├── AddNode
│   ├── SubtractNode
│   ├── MultiplyNode
│   ├── DivideNode
│   ├── MinNode
│   ├── MaxNode
│   └── AbsNode
├── References
│   ├── IndicatorNode
│   ├── ConstantNode
│   ├── MarketReferenceNode
│   └── PatternNode
├── Risk
│   ├── StopLossNode
│   ├── TakeProfitNode
│   ├── TrailingStopNode
│   ├── PositionSizeNode
│   └── RiskRewardNode
├── Time
│   ├── TimeNode
│   ├── DateNode
│   ├── SessionNode
│   └── DayOfWeekNode
└── Portfolio
    ├── MaxDrawdownNode
    ├── MaxDailyLossNode
    ├── MaxOpenTradesNode
    └── CapitalAllocationNode
```

## Core Shape

```text
StrategyRootNode
├── entry_node: EntryNode?
│   └── children[0]: condition tree
├── exit_node: ExitNode?
│   └── children[0]: condition tree
├── risk_node: RiskNode?
│   └── children[*]: risk/portfolio declarations
└── filter_nodes[*]: FilterNode
    └── children[0]: filter tree
```

The wrapper nodes make the top-level strategy contract stable even as condition
trees become more complex.

## Generic Reference Nodes

No indicator-specific AST classes are used.

```python
IndicatorNode(
    indicator_config=IndicatorConfig(
        indicator_type="RSI",
        parameters={"period": 14},
        output_property="value",
        timeframe="1d",
    )
)
```

The backtesting engine interprets `indicator_type`, `parameters`,
`output_property`, and `timeframe`. The AST only stores them.

## Registry

`ASTNodeRegistry` maps stable node type strings to dataclass implementations.

Canonical node types include:

```text
STRATEGY_ROOT, ENTRY, EXIT, RISK, FILTER
AND, OR, NOT
GREATER_THAN, LESS_THAN, GREATER_EQUAL, LESS_EQUAL, EQUAL, NOT_EQUAL
CROSS_ABOVE, CROSS_BELOW
ADD, SUBTRACT, MULTIPLY, DIVIDE, MIN, MAX, ABS
INDICATOR, CONSTANT, MARKET_REFERENCE, PATTERN
STOP_LOSS, TAKE_PROFIT, TRAILING_STOP, POSITION_SIZE, RISK_REWARD
TIME, DATE, SESSION, DAY_OF_WEEK
MAX_DRAWDOWN, MAX_DAILY_LOSS, MAX_OPEN_TRADES, CAPITAL_ALLOCATION
```

Aliases are accepted for backward compatibility:

```text
GT -> GREATER_THAN
LT -> LESS_THAN
GTE -> GREATER_EQUAL
LTE -> LESS_EQUAL
EQ -> EQUAL
NEQ -> NOT_EQUAL
SUB -> SUBTRACT
MUL -> MULTIPLY
DIV -> DIVIDE
MARKET_DATA -> MARKET_REFERENCE
```

Extensions can register new node classes and builders without editing the
built-in node set:

```python
ASTNodeRegistry.register("CUSTOM_NODE", CustomNode)
builder.register_condition_builder("CUSTOM_NODE", build_custom_condition)
```

## Builder

`ASTBuilder` performs a recursive factory mapping:

```text
Canonical condition type
  -> normalize node type
  -> find builder function
  -> instantiate dataclass node
  -> recursively build operands/children
  -> attach metadata with source_path
```

Supported input forms:

```json
{
  "type": "GREATER_THAN",
  "operand_1": {"type": "indicator", "indicator_type": "RSI"},
  "operand_2": {"type": "constant", "value": 30}
}
```

```json
{
  "type": "AND",
  "children": [
    {"type": "LT", "operand_1": {"type": "indicator", "indicator_type": "RSI"}, "operand_2": {"type": "constant", "value": 30}},
    {"type": "GT", "operand_1": {"type": "indicator", "indicator_type": "MACD", "property": "histogram"}, "operand_2": {"type": "constant", "value": 0}}
  ]
}
```

Errors raise `ASTBuildError` with the canonical JSON source path, for example:

```text
Indicator requires 'indicator_type' or signal reference at conditions.entry.operand_1
```

## Serialization

`ASTSerializer` supports:

```python
ast_dict = ASTSerializer.to_dict(ast)
json_text = ASTSerializer.to_json(ast)
versioned_json = ASTSerializer.to_json(ast, include_version=True)
ASTSerializer.to_file(ast, "strategy_ast.json")

loaded = ASTSerializer.from_json(versioned_json)
loaded_from_file = ASTSerializer.from_file("strategy_ast.json")
```

Versioned JSON uses an envelope:

```json
{
  "_version_info": {
    "ast_schema_version": "1.0.0"
  },
  "ast": {
    "node_type": "STRATEGY_ROOT"
  }
}
```

## Example AST Outputs

### RSI Below 30

```text
STRATEGY_ROOT (strategy_rsi)
└── ENTRY
    └── LESS_THAN
        ├── INDICATOR RSI(period=14).value
        └── CONSTANT 30
```

### MACD Histogram Greater Than 0

```text
STRATEGY_ROOT (strategy_macd)
└── ENTRY
    └── GREATER_THAN
        ├── INDICATOR MACD(fast=12, slow=26, signal=9).histogram
        └── CONSTANT 0
```

### EMA50 Crosses Above EMA200

```text
STRATEGY_ROOT (strategy_ema_cross)
└── ENTRY
    └── CROSS_ABOVE lookback_periods=1
        ├── INDICATOR EMA(period=50).value
        └── INDICATOR EMA(period=200).value
```

### Nested AND / OR / NOT

```text
STRATEGY_ROOT (strategy_nested)
└── ENTRY
    └── AND
        ├── OR
        │   ├── LESS_THAN
        │   │   ├── INDICATOR RSI(period=14).value
        │   │   └── CONSTANT 30
        │   └── GREATER_THAN
        │       ├── INDICATOR MACD(...).histogram
        │       └── CONSTANT 0
        └── NOT
            └── SESSION ["PRE_MARKET"]
```

### Stop Loss and Take Profit

```text
STRATEGY_ROOT (strategy_risk)
├── ENTRY
│   └── GREATER_THAN
│       ├── MARKET_REFERENCE CLOSE
│       └── INDICATOR SMA(period=20).value
└── RISK
    ├── STOP_LOSS {type=PERCENTAGE, value=2.0}
    └── TAKE_PROFIT {type=PERCENTAGE, value=5.0}
```

## Verification

AST coverage lives in `strategy_parser/tests/test_ast.py` and verifies:

- RSI comparison AST output
- MACD greater-than-zero AST output
- EMA50/EMA200 crossover AST output
- nested `AND` / `OR` / `NOT`
- stop-loss and take-profit risk structure
- deterministic generation
- versioned JSON and file round trips
- source-path error handling
