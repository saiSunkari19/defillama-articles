"""Analysis over stablecoin supply data."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Stablecoin


@dataclass(frozen=True)
class Row:
    """One analyzed stablecoin with derived metrics."""

    coin: Stablecoin
    market_share: float          # fraction of total supply, 0..1
    growth_day: float | None     # fractional change vs prev day
    growth_week: float | None
    growth_month: float | None


def _growth(now: float, prev: float) -> float | None:
    if prev <= 0:
        return None
    return (now - prev) / prev


def total_supply(coins: list[Stablecoin]) -> float:
    return sum(c.total_supply for c in coins)


def analyze(coins: list[Stablecoin]) -> list[Row]:
    """Return rows sorted by total supply (desc) with derived metrics."""
    total = total_supply(coins) or 1.0
    rows = [
        Row(
            coin=c,
            market_share=c.total_supply / total,
            growth_day=_growth(c.circulating, c.circulating_prev_day),
            growth_week=_growth(c.circulating, c.circulating_prev_week),
            growth_month=_growth(c.circulating, c.circulating_prev_month),
        )
        for c in coins
    ]
    rows.sort(key=lambda r: r.coin.total_supply, reverse=True)
    return rows


def mechanism_breakdown(coins: list[Stablecoin]) -> dict[str, float]:
    """Total supply grouped by peg mechanism (fiat-backed, crypto-backed, ...)."""
    out: dict[str, float] = {}
    for c in coins:
        key = c.peg_mechanism or "unknown"
        out[key] = out.get(key, 0.0) + c.total_supply
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


def peg_breakdown(coins: list[Stablecoin]) -> dict[str, float]:
    """Total supply grouped by peg type (peggedUSD, peggedEUR, ...)."""
    out: dict[str, float] = {}
    for c in coins:
        key = c.peg_type or "unknown"
        out[key] = out.get(key, 0.0) + c.total_supply
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


def concentration(rows: list[Row], top_n: int = 3) -> float:
    """Combined market share of the top N stablecoins (0..1)."""
    return sum(r.market_share for r in rows[:top_n])
