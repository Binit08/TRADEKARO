import sys
sys.path.append('/Users/binit/NLconverter/backend')
import asyncio
from strategy_parser.parser.llm_parser import LLMStrategyParser

async def main():
    parser = LLMStrategyParser()
    strategy_text = "Buy when the previous candle is green. Exit at 1% take profit or 1% stop loss."
    result = await parser.parse(strategy_text)
    print(result.json(indent=2))

asyncio.run(main())
