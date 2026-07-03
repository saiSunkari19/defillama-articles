"""Client for the DeFiLlama stablecoins API.

Docs: https://api-docs.defillama.com/#tag/stablecoins
Base:  https://stablecoins.llama.fi
"""

from __future__ import annotations

import urllib.request
import urllib.error
import json

from .models import Stablecoin

BASE_URL = "https://stablecoins.llama.fi"


class StablecoinsClient:
    """Minimal, dependency-free client for DeFiLlama stablecoins."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:  # pragma: no cover - network
            raise RuntimeError(f"HTTP {e.code} fetching {url}: {e.reason}") from e
        except urllib.error.URLError as e:  # pragma: no cover - network
            raise RuntimeError(f"Network error fetching {url}: {e.reason}") from e

    def get_stablecoins(self, include_prices: bool = True) -> list[Stablecoin]:
        """Return all stablecoins with their total (circulating) supply."""
        data = self._get(
            "/stablecoins",
            params={"includePrices": str(include_prices).lower()},
        )
        assets = data.get("peggedAssets", [])
        return [Stablecoin.from_api(a) for a in assets]


def total_supply_by_symbol(coins: list[Stablecoin]) -> dict[str, float]:
    """Convenience: map symbol -> total supply."""
    return {c.symbol: c.total_supply for c in coins}
