import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from backend.strategy_parser.parser.llm_client import LLMClient
from backend.strategy_parser.utils import strip_code_fences


@dataclass
class Blocker:
    reason: str
    question: str


@dataclass
class BlockerResult:
    status: str  # "CLEAR" or "BLOCKED"
    blockers: List[Blocker]


class BlockerDetector:
    """
    Determines whether deterministic compilation is possible.
    """

    SYSTEM_PROMPT = """
You are the Blocker Detector. Your job is to determine if a trading strategy can be deterministically compiled.

SUPPORTED EXECUTION CONTEXT FIELDS:
These fields are fully supported and should NEVER trigger a block:
- timeframe: 1D, 4H, 1H, 15M, 5M, 1M, etc.
- exchange: NSE, BSE, NYSE, NASDAQ, etc.
- asset_class: equity, futures, options, crypto, commodity, etc.
- index: NIFTY_50, SENSEX, S&P_500, etc.
- capital_per_trade: amount in any currency (INR, USD, EUR, etc.)
- currency: INR, USD, EUR, GBP, JPY, etc.
- position_side: LONG, SHORT, BOTH, etc.
- order_type: MARKET, LIMIT, STOP, etc.
- max_concurrent_positions: any integer value

A strategy is BLOCKED if it contains:
- Missing required information (not covered by execution context)
- Undefined references (undefined variables or entities)
- Contradictory instructions
- Unknown custom entities (beyond standard market terminology)
- Missing values that cannot be inferred

Examples of BLOCKERS:
- "Buy when RSI crosses above my custom level." (Custom level value unknown)
- "Use my proprietary indicator." (Indicator definition unavailable)
- "Enter at the value I mentioned earlier." (Referenced value unavailable)

Examples of NON-BLOCKERS (execution context):
- "On NSE exchange" (supported exchange field)
- "With 1D timeframe" (supported timeframe field)
- "Using 100,000 INR per trade" (supported capital_per_trade field)
- "Short position only" (supported position_side field)
- "Using LIMIT orders" (supported order_type field)

The following are NOT BLOCKERS and must NEVER trigger a block:

MARKET DIRECTION & TRENDS:
- bullish, bearish, uptrend, downtrend, trend reversal
- breakout, breakdown, fakeout, fake breakout
- pullback, retracement, correction, rally, bounce
- consolidation, ranging market, trading range
- accumulation, distribution

PRICE LEVELS & STRUCTURE:
- support, resistance, support test, resistance test
- swing high, swing low
- gap, gap fill
- new high, new low, all-time high, all-time low
- breakout to new levels

MOMENTUM & VOLUME:
- momentum, strong momentum, weak momentum
- high volume, low volume, volume surge, volume spike
- profit taking, liquidation

INDICATORS & TECHNICAL PATTERNS:
- RSI, MACD, Stochastic, Bollinger Bands, Moving Average
- crossover, cross above, cross below, cross under
- divergence, hidden divergence, momentum divergence
- overbought, oversold
- mean reversion

CANDLE PATTERNS & SETUPS:
- doji, engulfing, hammer, hanging man, shooting star
- double top, double bottom, head and shoulders
- inside bar, outside bar, pin bar

TRADE MANAGEMENT:
- take profit, stop loss, trailing stop
- position sizing, risk/reward, risk management

BASIC MARKET KEYWORDS:
- top gainers, top losers, most active, volume leaders
- 52-week high, 52-week low, daily high, daily low
- intra-day, intraday, day trade, swing trade, multi-day
- pre-market, after-hours, extended hours
- sector leaders, market breadth, market cap leaders

AMBIGUITY HANDLING:
If a strategy uses common market shorthand or keywords (see lists above) but lacks precise numeric parameters (for example: "top gainers" without a count, "high volume" without a threshold):
* Do NOT mark the strategy as BLOCKED solely for using these shorthand terms.
* Treat these terms as non-blocking market shorthand and return status "CLEAR" with an empty blockers list.
* Do NOT invent precise numeric thresholds or values. Leave precise parameter interpretation to downstream components.
* Only raise a BLOCKER when ambiguity affects deterministic compilation (e.g., missing numeric thresholds required for logic, undefined custom entities, or contradictory instructions).

Do NOT interpret or translate. Just check for blockers.
Respond ONLY with valid JSON in the following format:
{
  "status": "CLEAR" | "BLOCKED",
  "blockers": [
    {
      "reason": "Explain why it is blocked.",
      "question": "Ask the user to provide the missing information."
    }
  ]
}
If status is CLEAR, blockers should be an empty list.
"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def detect(self, strategy_text: str) -> BlockerResult:
        """
        Analyze the strategy text and return blockers.
        """
        prompt = f"Analyze the following strategy:\n\n{strategy_text}"
        response_text = self.llm_client.call(prompt, system_prompt=self.SYSTEM_PROMPT)

        # Handle potential markdown fencing
        response_text = strip_code_fences(response_text)

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response_text}")

        blockers = [Blocker(reason=b.get("reason", ""), question=b.get("question", "")) for b in data.get("blockers", [])]
        return BlockerResult(status=data.get("status", "BLOCKED"), blockers=blockers)


