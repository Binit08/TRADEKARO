from typing import Dict, Any, List
from dataclasses import is_dataclass, asdict
from app.portfolio.portfolio import Portfolio
from app.execution.trade import Trade

class ReportBuilder:
    @staticmethod
    def build_trade_report(port: Portfolio) -> List[Dict[str, Any]]:
        report = []
        for trade in port.trade_history:
            rec = ReportBuilder._record_from_trade(trade)
            rec["avg_entry_price"] = trade.entry_price
            rec["original_entry_price"] = getattr(trade, "original_entry_price", getattr(trade, "lifecycle_first_entry_price", trade.entry_price))
            if trade.status == "OPEN":
                pos = port.positions.get(trade.symbol)
                if pos:
                    rec["current_price"] = pos.current_price
                    if trade.side.upper() in ("BUY", "LONG"):
                        rec["unrealized_pnl"] = (pos.current_price - trade.entry_price) * trade.qty - (trade.fees or 0.0)
                    else:
                        rec["unrealized_pnl"] = (trade.entry_price - pos.current_price) * trade.qty - (trade.fees or 0.0)
                    rec["avg_entry_price"] = trade.entry_price
                    rec["original_entry_price"] = pos.lifecycle_first_entry_price
            report.append(rec)
        return report

    @staticmethod
    def _record_from_trade(trade: Trade) -> Dict[str, Any]:
        if is_dataclass(trade):
            return asdict(trade)
        return dict(trade)
