"""Unit tests for PositionSizer input validation, fractional percentages, and lot sizing."""
import pytest
import math
from app.risk.position import PositionSizer

def test_position_sizer_valid_defaults():
    sizer = PositionSizer()
    assert sizer.mode == "fixed_qty"
    assert sizer.value is None
    assert sizer.commission_rate == 0.0
    assert sizer.lot_size == 1.0

def test_position_sizer_nan_and_inf_price():
    sizer = PositionSizer()
    for bad_price in [float('nan'), float('inf'), float('-inf'), 0.0, -10.5]:
        with pytest.raises(ValueError, match="Price must be strictly positive and finite"):
            sizer.size(
                default_qty=10.0,
                cash=1000.0,
                equity=1000.0,
                price=bad_price
            )
        with pytest.raises(ValueError, match="Price must be strictly positive and finite"):
            sizer.rebalance_to_target(
                default_qty=10.0,
                cash=1000.0,
                equity=1000.0,
                price=bad_price
            )

def test_position_sizer_nan_and_inf_cash_equity():
    sizer = PositionSizer()
    for bad_val in [float('nan'), float('inf'), float('-inf')]:
        # Test cash
        with pytest.raises(ValueError, match="Cash must be a finite number"):
            sizer.size(default_qty=10.0, cash=bad_val, equity=1000.0, price=100.0)
        with pytest.raises(ValueError, match="Cash must be a finite number"):
            sizer.rebalance_to_target(default_qty=10.0, cash=bad_val, equity=1000.0, price=100.0)

        # Test equity
        with pytest.raises(ValueError, match="Equity must be a finite number"):
            sizer.size(default_qty=10.0, cash=1000.0, equity=bad_val, price=100.0)
        with pytest.raises(ValueError, match="Equity must be a finite number"):
            sizer.rebalance_to_target(default_qty=10.0, cash=1000.0, equity=bad_val, price=100.0)

def test_position_sizer_invalid_lot_size():
    for bad_lot in [float('nan'), float('inf'), float('-inf'), 0.0, -1.0]:
        sizer = PositionSizer(lot_size=bad_lot)
        with pytest.raises(ValueError, match="Lot size must be strictly positive and finite"):
            sizer.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0)
        with pytest.raises(ValueError, match="Lot size must be strictly positive and finite"):
            sizer.rebalance_to_target(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0)

def test_position_sizer_invalid_commission():
    for bad_comm in [float('nan'), float('inf'), float('-inf'), -0.01]:
        sizer = PositionSizer(commission_rate=bad_comm)
        with pytest.raises(ValueError, match="Commission rate must be non-negative and finite"):
            sizer.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0)
        with pytest.raises(ValueError, match="Commission rate must be non-negative and finite"):
            sizer.rebalance_to_target(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0)

def test_position_sizer_invalid_value():
    for bad_val in [float('nan'), float('inf'), float('-inf'), 0.0, -5.0]:
        sizer = PositionSizer(value=bad_val)
        with pytest.raises(ValueError, match="Sizer value must be strictly positive and finite"):
            sizer.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0)
        with pytest.raises(ValueError, match="Sizer value must be strictly positive and finite"):
            sizer.rebalance_to_target(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0)

def test_position_sizer_invalid_existing_qty_notional():
    sizer = PositionSizer()
    for bad_val in [float('nan'), float('inf'), float('-inf'), -1.0]:
        with pytest.raises(ValueError, match="Existing quantity must be non-negative and finite"):
            sizer.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0, existing_qty=bad_val)
        with pytest.raises(ValueError, match="Existing quantity must be non-negative and finite"):
            sizer.rebalance_to_target(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0, existing_qty=bad_val)

        with pytest.raises(ValueError, match="Existing notional must be non-negative and finite"):
            sizer.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0, existing_notional=bad_val)
        with pytest.raises(ValueError, match="Existing notional must be non-negative and finite"):
            sizer.rebalance_to_target(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0, existing_notional=bad_val)

def test_position_sizer_percent_range_validation():
    # Test values out of [0.0, 1.0] range
    for out_of_range in [-0.01, 1.01, 10.0]:
        sizer = PositionSizer(mode="percent_equity", value=out_of_range)
        with pytest.raises(ValueError) as excinfo:
            sizer.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0)
        assert ("Sizer value must be strictly positive" in str(excinfo.value) or
                "Percent size must be in range" in str(excinfo.value))

        with pytest.raises(ValueError) as excinfo:
            sizer.rebalance_to_target(default_qty=10.0, cash=1000.0, equity=1000.0, price=100.0)
        assert ("Sizer value must be strictly positive" in str(excinfo.value) or
                "Percent size must be in range" in str(excinfo.value))

    # Valid bounds (0.0, 1.0]
    for in_range in [0.5, 1.0]:
        sizer = PositionSizer(mode="percent_equity", value=in_range)
        qty = sizer.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=10.0)
        assert qty >= 0.0

def test_position_sizer_lot_size_rounding_down():
    # Test rounding down with lot_size = 1.0
    sizer = PositionSizer(mode="fixed_qty", value=10.5, lot_size=1.0)
    qty = sizer.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=10.0)
    assert qty == 10.0  # Rounds 10.5 down to 10.0

    # Test rounding down with lot_size = 10.0
    sizer_10 = PositionSizer(mode="fixed_qty", value=25.0, lot_size=10.0)
    qty_10 = sizer_10.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=10.0)
    assert qty_10 == 20.0  # Rounds 25.0 down to 20.0

    # Test rounding down with lot_size = 0.1
    sizer_pt1 = PositionSizer(mode="fixed_qty", value=1.23, lot_size=0.1)
    qty_pt1 = sizer_pt1.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=10.0)
    assert pytest.approx(qty_pt1) == 1.2  # Rounds 1.23 down to 1.2

def test_position_sizer_modes_rounding():
    # Cash mode rounding: notional = 100, price = 3.0, expected raw = 33.33 -> round down to lot_size 1.0 -> 33
    sizer_cash = PositionSizer(mode="cash", value=100.0, lot_size=1.0)
    qty_cash = sizer_cash.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=3.0)
    assert qty_cash == 33.0

    # Cash mode with lot_size 5.0: 33.33 -> round down to 30.0
    sizer_cash_5 = PositionSizer(mode="cash", value=100.0, lot_size=5.0)
    qty_cash_5 = sizer_cash_5.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=3.0)
    assert qty_cash_5 == 30.0

    # Percent equity mode rounding: equity = 1000, pct = 0.15, notional = 150, price = 4.0, raw = 37.5 -> round to lot_size 1.0 -> 37
    sizer_pct = PositionSizer(mode="percent_equity", value=0.15, lot_size=1.0)
    qty_pct = sizer_pct.size(default_qty=10.0, cash=1000.0, equity=1000.0, price=4.0)
    assert qty_pct == 37.0

def test_rebalance_to_target_rounding():
    # Cash mode rebalance: target_notional = 500, price = 10.0, existing_notional = 150 -> desired_notional = 350 -> raw_qty = 35 -> round to lot_size 10 -> 30
    sizer = PositionSizer(mode="cash", value=500.0, lot_size=10.0)
    qty = sizer.rebalance_to_target(
        default_qty=10.0,
        cash=1000.0,
        equity=1000.0,
        price=10.0,
        existing_qty=15.0,
        existing_notional=150.0
    )
    assert qty == 30.0
