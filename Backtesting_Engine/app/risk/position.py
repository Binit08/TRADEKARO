"""Position sizing helpers."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PositionSizer:
    """Compute entry quantity from cash/equity based sizing settings."""

    mode: str = "fixed_qty"
    value: Optional[float] = None
    commission_rate: float = 0.0
    lot_size: float = 1.0

    def size(
        self,
        *,
        default_qty: float,
        cash: float,
        equity: float,
        price: float,
        existing_qty: float = 0.0,
        existing_notional: float = 0.0,
        pyramid_index: int = 0,
        total_layers: int = 1,
    ) -> float:
        """Return the quantity to submit for a new entry order, sizing each layer as a fresh fraction."""
        price = float(price)
        cash = float(cash)
        equity = float(equity)
        default_qty = float(default_qty)
        existing_qty = float(existing_qty)
        existing_notional = float(existing_notional)

        # Validation guards
        if math.isnan(price) or math.isinf(price) or price <= 0:
            raise ValueError(f"Price must be strictly positive and finite: {price}")
        if math.isnan(cash) or math.isinf(cash):
            raise ValueError(f"Cash must be a finite number: {cash}")
        if math.isnan(equity) or math.isinf(equity):
            raise ValueError(f"Equity must be a finite number: {equity}")
        if math.isnan(self.lot_size) or math.isinf(self.lot_size) or self.lot_size <= 0:
            raise ValueError(f"Lot size must be strictly positive and finite: {self.lot_size}")
        if math.isnan(self.commission_rate) or math.isinf(self.commission_rate) or self.commission_rate < 0:
            raise ValueError(f"Commission rate must be non-negative and finite: {self.commission_rate}")
        if self.value is not None:
            if math.isnan(self.value) or math.isinf(self.value) or self.value <= 0:
                raise ValueError(f"Sizer value must be strictly positive and finite: {self.value}")
        if math.isnan(existing_qty) or math.isinf(existing_qty) or existing_qty < 0:
            raise ValueError(f"Existing quantity must be non-negative and finite: {existing_qty}")
        if math.isnan(existing_notional) or math.isinf(existing_notional) or existing_notional < 0:
            raise ValueError(f"Existing notional must be non-negative and finite: {existing_notional}")

        mode = str(self.mode).lower()
        if mode in {"fixed", "fixed_qty", "qty", "quantity", "contracts"}:
            if self.value is None:
                if math.isnan(default_qty) or math.isinf(default_qty) or default_qty <= 0:
                    raise ValueError(f"Default quantity must be strictly positive and finite: {default_qty}")
            target_qty = float(default_qty) if self.value is None else float(self.value)
            raw_qty = target_qty / max(total_layers, 1)

        elif mode in {"cash", "notional"}:
            target_notional = float(cash if self.value is None else self.value)
            target_notional = target_notional / (1 + self.commission_rate)
            notional_per_layer = target_notional / max(total_layers, 1)
            raw_qty = notional_per_layer / price

        elif mode in {"percent_equity", "pct_equity", "equity_pct"}:
            pct = 1.0 if self.value is None else float(self.value)
            if pct < 0.0 or pct > 1.0:
                raise ValueError(f"Percent size must be in range [0.0, 1.0] under fractional convention, got: {pct}")
            notional = max(equity, 0.0) * pct
            notional = notional / (1 + self.commission_rate)
            notional_per_layer = notional / max(total_layers, 1)
            raw_qty = notional_per_layer / price

        else:
            raise ValueError(f"Unknown position size mode: {self.mode}")

        # Round down to lot_size
        qty = math.floor(raw_qty / self.lot_size) * self.lot_size
        return max(qty, 0.0)

    def rebalance_to_target(
        self,
        *,
        default_qty: float,
        cash: float,
        equity: float,
        price: float,
        existing_qty: float = 0.0,
        existing_notional: float = 0.0,
    ) -> float:
        """Return the quantity to submit to rebalance to a target value, subtracting existing holdings."""
        price = float(price)
        cash = float(cash)
        equity = float(equity)
        default_qty = float(default_qty)
        existing_qty = float(existing_qty)
        existing_notional = float(existing_notional)

        # Validation guards
        if math.isnan(price) or math.isinf(price) or price <= 0:
            raise ValueError(f"Price must be strictly positive and finite: {price}")
        if math.isnan(cash) or math.isinf(cash):
            raise ValueError(f"Cash must be a finite number: {cash}")
        if math.isnan(equity) or math.isinf(equity):
            raise ValueError(f"Equity must be a finite number: {equity}")
        if math.isnan(self.lot_size) or math.isinf(self.lot_size) or self.lot_size <= 0:
            raise ValueError(f"Lot size must be strictly positive and finite: {self.lot_size}")
        if math.isnan(self.commission_rate) or math.isinf(self.commission_rate) or self.commission_rate < 0:
            raise ValueError(f"Commission rate must be non-negative and finite: {self.commission_rate}")
        if self.value is not None:
            if math.isnan(self.value) or math.isinf(self.value) or self.value <= 0:
                raise ValueError(f"Sizer value must be strictly positive and finite: {self.value}")
        if math.isnan(existing_qty) or math.isinf(existing_qty) or existing_qty < 0:
            raise ValueError(f"Existing quantity must be non-negative and finite: {existing_qty}")
        if math.isnan(existing_notional) or math.isinf(existing_notional) or existing_notional < 0:
            raise ValueError(f"Existing notional must be non-negative and finite: {existing_notional}")

        mode = str(self.mode).lower()
        if mode in {"fixed", "fixed_qty", "qty", "quantity", "contracts"}:
            if self.value is None:
                if math.isnan(default_qty) or math.isinf(default_qty) or default_qty <= 0:
                    raise ValueError(f"Default quantity must be strictly positive and finite: {default_qty}")
                target_qty = float(default_qty)
            else:
                target_qty = float(self.value)
            raw_qty = max(target_qty - existing_qty, 0.0)

        elif mode in {"cash", "notional"}:
            target_notional = float(cash if self.value is None else self.value)
            target_notional = target_notional / (1 + self.commission_rate)
            desired_notional = max(target_notional - existing_notional, 0.0)
            raw_qty = desired_notional / price

        elif mode in {"percent_equity", "pct_equity", "equity_pct"}:
            pct = 1.0 if self.value is None else float(self.value)
            if pct < 0.0 or pct > 1.0:
                raise ValueError(f"Percent size must be in range [0.0, 1.0] under fractional convention, got: {pct}")
            notional = max(equity, 0.0) * pct
            notional = notional / (1 + self.commission_rate)
            desired_notional = max(notional - existing_notional, 0.0)
            raw_qty = desired_notional / price

        else:
            raise ValueError(f"Unknown position size mode: {self.mode}")

        # Round down to lot_size
        qty = math.floor(raw_qty / self.lot_size) * self.lot_size
        return max(qty, 0.0)
