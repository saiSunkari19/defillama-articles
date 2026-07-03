"""Data models for DeFiLlama stablecoins."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stablecoin:
    """A single stablecoin and its circulating supply.

    Total supply on DeFiLlama is represented by the "circulating" amount,
    denominated in the peg unit (e.g. peggedUSD).
    """

    id: str
    name: str
    symbol: str
    peg_type: str
    peg_mechanism: str
    price: float | None
    circulating: float
    circulating_prev_day: float
    circulating_prev_week: float
    circulating_prev_month: float

    @property
    def total_supply(self) -> float:
        """Current circulating (total) supply in peg units."""
        return self.circulating

    @classmethod
    def from_api(cls, data: dict) -> "Stablecoin":
        def peg(field: str) -> float:
            value = data.get(field) or {}
            if isinstance(value, dict):
                # e.g. {"peggedUSD": 1234.5}
                return float(next(iter(value.values()), 0.0) or 0.0)
            return float(value or 0.0)

        price = data.get("price")
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            symbol=data.get("symbol", ""),
            peg_type=data.get("pegType", ""),
            peg_mechanism=data.get("pegMechanism", ""),
            price=float(price) if price is not None else None,
            circulating=peg("circulating"),
            circulating_prev_day=peg("circulatingPrevDay"),
            circulating_prev_week=peg("circulatingPrevWeek"),
            circulating_prev_month=peg("circulatingPrevMonth"),
        )
