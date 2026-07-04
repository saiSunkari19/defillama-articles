# stablecoins

Fetch stablecoins and their total (circulating) supply from the
[DefiLlama stablecoins API](https://api-docs.defillama.com/#tag/stablecoins).

No third-party dependencies — uses the Python standard library only.

## Usage

```bash
# List: top 25 stablecoins by total supply
python -m stablecoins.cli list

# List top 10 / everything
python -m stablecoins.cli list --top 10
python -m stablecoins.cli list --all

# Analyze: market share, day/week/month growth, mechanism & peg-type breakdown
python -m stablecoins.cli analyze --top 12

# Analyze + write SVG charts (bar + donuts) to ./charts/
python -m stablecoins.cli analyze --top 12 --charts --out charts

# Also write high-res PNGs (for Word / Google Docs)
python -m stablecoins.cli analyze --top 12 --png --scale 2.5 --out charts
```

The charts are self-contained SVG files (no dependencies) that open in any
browser or VSCode:

- `supply_bar.svg` — top-N stablecoins by supply with market share
- `mechanism_donut.svg` — fiat- vs crypto-backed vs algorithmic
- `pegtype_donut.svg` — peggedUSD vs EUR/RUB/etc.

### PNG export (for Word)

`--png` rasterizes each chart to PNG at `--scale` device pixels (default 2×;
2.5× gives ~2150px-wide crisp images). It uses whichever converter is
installed, preferring quality:

1. `rsvg-convert` — `brew install librsvg`
2. `inkscape`
3. `cairosvg` — `pip install cairosvg`
4. `qlmanage` (macOS Quick Look) — fallback

The `.svg` is always written as the source of truth; the `.png` is derived
from it. Drop the PNGs straight into a Word document.

Or from Python:

```python
from stablecoins import StablecoinsClient

client = StablecoinsClient()
coins = client.get_stablecoins()
for c in sorted(coins, key=lambda c: c.total_supply, reverse=True)[:5]:
    print(c.symbol, c.total_supply)
```

## Data source

`GET https://stablecoins.llama.fi/stablecoins?includePrices=true`

The **total supply** is DeFiLlama's `circulating` value, denominated in the
peg unit (e.g. `peggedUSD`).
