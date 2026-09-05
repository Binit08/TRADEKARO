"""Unit test for trade log Excel export."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from app.execution.trade import Trade
from app.reports.trade_log import export_trades_to_excel


def test_export_trades_to_excel(tmp_path):
    trades = [
        Trade(symbol="RELIANCE", side="BUY", entry_price=100.0, qty=10, entry_time=datetime(2024, 1, 1, 9, 15)),
        Trade(
            symbol="RELIANCE",
            side="SELL",
            entry_price=100.0,
            qty=10,
            entry_time=datetime(2024, 1, 1, 9, 15),
            exit_price=105.0,
            exit_time=datetime(2024, 1, 1, 10, 0),
            status="CLOSED",
        ),
    ]

    out_file = tmp_path / "trades.xlsx"
    written = export_trades_to_excel(trades, out_file)

    p = Path(written)
    assert p.exists()

    df = pd.read_excel(p)
    assert len(df) == 2

    expected_cols = {"symbol", "side", "entry_price", "qty", "entry_time", "exit_price", "exit_time", "status", "pnl"}
    assert expected_cols.issubset(set(df.columns))

    closed_row = df[df["status"] == "CLOSED"].iloc[0]
    assert round(float(closed_row["pnl"]), 6) == round((105.0 - 100.0) * 10, 6)
