"""Trade log reporting.

Provides helpers to convert an in-memory list of `Trade` objects into a
Pandas `DataFrame` and export it to an Excel file (.xlsx).

Example:
	from app.portfolio.portfolio import Portfolio
	from app.reports.trade_log import export_trades_to_excel

	# given a running `portfolio` instance
	export_trades_to_excel(portfolio, "out/trade_history.xlsx")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Union

logger = logging.getLogger(__name__)

import pandas as pd

from app.execution.trade import Trade
from app.portfolio.portfolio import Portfolio


def trades_to_dataframe(trades: List[Trade]) -> pd.DataFrame:
	"""Convert list of `Trade` objects into a DataFrame.

	Columns: symbol, side, entry_price, qty, entry_time, exit_price, exit_time,
	status, pnl
	"""
	rows = []
	for t in trades:
		pnl = getattr(t, "pnl", None)
		if pnl is None and t.exit_price is not None:
			try:
				if str(getattr(t, "position_side", "") or "").upper() == "SHORT":
					gross = (float(t.entry_price) - float(t.exit_price)) * float(t.qty)
				else:
					gross = (float(t.exit_price) - float(t.entry_price)) * float(t.qty)
				pnl = gross - float(getattr(t, "fees", 0.0) or 0.0)
			except Exception:
				pnl = None

		rows.append(
			{
				"symbol": t.symbol,
				"side": t.side,
				"entry_price": t.entry_price,
				"qty": t.qty,
				"entry_time": t.entry_time,
				"exit_price": t.exit_price,
				"exit_time": t.exit_time,
				"status": t.status,
				"fees": getattr(t, "fees", 0.0),
				"entry_fee": getattr(t, "entry_fee", None),
				"exit_fee": getattr(t, "exit_fee", None),
				"slippage": getattr(t, "slippage", 0.0),
				"order_type": getattr(t, "order_type", "MARKET"),
				"exit_order_type": getattr(t, "exit_order_type", None),
				"position_side": getattr(t, "position_side", None),
				"entry_reason": getattr(t, "entry_reason", None),
				"exit_reason": getattr(t, "exit_reason", None),
				"stop_loss": getattr(t, "stop_loss", None),
				"take_profit": getattr(t, "take_profit", None),
				"gross_pnl": getattr(t, "gross_pnl", None),
				"pnl": pnl,
				"avg_entry_price": getattr(t, "entry_price", None),
				"original_entry_price": getattr(t, "original_entry_price", getattr(t, "lifecycle_first_entry_price", t.entry_price)),
			}
		)

	df = pd.DataFrame(rows)
	if not df.empty:
		# normalize datetimes so Excel shows them correctly
		if "entry_time" in df.columns:
			df["entry_time"] = pd.to_datetime(df["entry_time"])
		if "exit_time" in df.columns:
			df["exit_time"] = pd.to_datetime(df["exit_time"])

	return df


def export_trades_to_excel(trades_or_portfolio: Union[List[Trade], Portfolio], path: Union[str, Path] = "trade_history.xlsx", index: bool = False) -> str:
	"""Export trades to an Excel file and return the written file path.

	Accepts either a list of `Trade` objects or a `Portfolio` instance.
	"""
	if isinstance(trades_or_portfolio, Portfolio):
		trades = trades_or_portfolio.trade_history
	else:
		trades = trades_or_portfolio

	df = trades_to_dataframe(list(trades))
	if not df.empty:
		# Write timestamps as text so Excel previews render human-readable values
		# instead of serial date numbers.
		for column in ("entry_time", "exit_time"):
			if column in df.columns:
				df[column] = pd.to_datetime(df[column], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
				df[column] = df[column].fillna("")

	out_path = Path(path)
	if out_path.parent and not out_path.parent.exists():
		out_path.parent.mkdir(parents=True, exist_ok=True)

	# Pandas will choose an appropriate engine (openpyxl) for .xlsx files.
	df.to_excel(out_path, index=index)
	return str(out_path.resolve())


def _trades_from_dicts(dicts: List[dict]) -> List[Trade]:
	out: List[Trade] = []
	for d in dicts:
		out.append(
			Trade(
				symbol=d.get("symbol"),
				side=d.get("side"),
				entry_price=d.get("entry_price"),
				qty=d.get("qty"),
				entry_time=d.get("entry_time"),
				exit_price=d.get("exit_price"),
				exit_time=d.get("exit_time"),
				status=d.get("status", "OPEN"),
				fees=d.get("fees", 0.0),
				entry_fee=d.get("entry_fee"),
				exit_fee=d.get("exit_fee"),
				slippage=d.get("slippage", 0.0),
				pnl=d.get("pnl"),
				order_type=d.get("order_type", "MARKET"),
				exit_order_type=d.get("exit_order_type"),
				position_side=d.get("position_side"),
				entry_reason=d.get("entry_reason"),
				exit_reason=d.get("exit_reason"),
				stop_loss=d.get("stop_loss"),
				take_profit=d.get("take_profit"),
			)
		)
	return out


if __name__ == "__main__":
	import argparse
	import json
	logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

	parser = argparse.ArgumentParser(description="Export trades to Excel (.xlsx)")
	parser.add_argument("--in", dest="infile", help="Input JSON file with list of trades (optional)")
	parser.add_argument("--out", dest="outfile", default="trade_history.xlsx", help="Output .xlsx file path")
	args = parser.parse_args()

	if args.infile:
		p = Path(args.infile)
		if not p.exists():
			raise SystemExit(f"Input file not found: {p}")
		with p.open("r", encoding="utf8") as fh:
			data = json.load(fh)
		# expect a list of dicts
		trades = _trades_from_dicts(data)
	else:
		# demo trades for quick testing
		from datetime import datetime

		trades = [
			Trade(symbol="DEMO", side="BUY", entry_price=100.0, qty=1, entry_time=datetime.now()),
			Trade(symbol="DEMO", side="SELL", entry_price=110.0, qty=1, entry_time=datetime.now(), exit_price=110.0, exit_time=datetime.now(), status="CLOSED"),
		]

	out = export_trades_to_excel(trades, args.outfile)
	logger.info(out)
