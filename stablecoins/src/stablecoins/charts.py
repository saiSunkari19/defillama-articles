"""Self-contained SVG chart generation (no dependencies).

Produces standalone .svg files that render in any browser or VSCode.
Palette is a colorblind-safe categorical set on a neutral surface.
"""

from __future__ import annotations

import html

from .analysis import Row

# Colorblind-safe categorical palette (Okabe-Ito derived).
PALETTE = [
    "#0072B2", "#E69F00", "#009E73", "#D55E00",
    "#CC79A7", "#56B4E9", "#F0E442", "#999999",
]
BG = "#ffffff"
INK = "#1a1a2e"
MUTED = "#6b7280"
GRID = "#e5e7eb"
FONT = "font-family='ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif'"


def _fmt(n: float) -> str:
    for unit in ("", "K", "M", "B", "T"):
        if abs(n) < 1000:
            return f"{n:,.1f}{unit}"
        n /= 1000
    return f"{n:,.1f}P"


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def bar_chart(rows: list[Row], top_n: int = 12, title: str = "Stablecoins by total supply") -> str:
    """Horizontal bar chart of the top-N stablecoins by supply."""
    rows = rows[:top_n]
    if not rows:
        return _empty(title)

    W, pad_l, pad_r, pad_t, pad_b = 860, 210, 120, 64, 30
    row_h, gap = 30, 10
    H = pad_t + pad_b + len(rows) * (row_h + gap)
    max_val = max(r.coin.total_supply for r in rows) or 1.0
    plot_w = W - pad_l - pad_r

    parts = [_header(W, H, title)]
    for i, r in enumerate(rows):
        y = pad_t + i * (row_h + gap)
        w = plot_w * (r.coin.total_supply / max_val)
        color = PALETTE[i % len(PALETTE)]
        label = f"{r.coin.symbol}  ·  {r.coin.name[:18]}"
        parts.append(
            f"<text x='{pad_l - 12}' y='{y + row_h/2 + 4}' text-anchor='end' "
            f"font-size='13' fill='{INK}' {FONT}>{_esc(label)}</text>"
        )
        parts.append(
            f"<rect x='{pad_l}' y='{y}' width='{w:.1f}' height='{row_h}' "
            f"rx='4' fill='{color}'><title>{_esc(r.coin.name)}: {_fmt(r.coin.total_supply)}</title></rect>"
        )
        parts.append(
            f"<text x='{pad_l + w + 8}' y='{y + row_h/2 + 4}' font-size='12' "
            f"fill='{MUTED}' {FONT}>{_fmt(r.coin.total_supply)} "
            f"({r.market_share*100:.1f}%)</text>"
        )
    parts.append("</svg>")
    return "\n".join(parts)


def donut_chart(breakdown: dict[str, float], title: str = "Supply by peg mechanism") -> str:
    """Donut chart of a category -> value breakdown."""
    items = [(k, v) for k, v in breakdown.items() if v > 0]
    if not items:
        return _empty(title)

    W, H = 860, 420
    cx, cy, r_out, r_in = 250, 230, 150, 88
    total = sum(v for _, v in items) or 1.0

    parts = [_header(W, H, title)]
    angle = -90.0  # start at top
    legend_y = 90
    for i, (name, val) in enumerate(items):
        frac = val / total
        sweep = frac * 360.0
        color = PALETTE[i % len(PALETTE)]
        parts.append(_arc(cx, cy, r_out, r_in, angle, angle + sweep, color,
                          f"{name}: {_fmt(val)} ({frac*100:.1f}%)"))
        angle += sweep
        # legend
        ly = legend_y + i * 30
        parts.append(f"<rect x='560' y='{ly}' width='16' height='16' rx='3' fill='{color}'/>")
        parts.append(
            f"<text x='584' y='{ly + 13}' font-size='13' fill='{INK}' {FONT}>"
            f"{_esc(name)} — {_fmt(val)} ({frac*100:.1f}%)</text>"
        )
    parts.append(
        f"<text x='{cx}' y='{cy - 4}' text-anchor='middle' font-size='14' "
        f"fill='{MUTED}' {FONT}>Total</text>"
    )
    parts.append(
        f"<text x='{cx}' y='{cy + 20}' text-anchor='middle' font-size='20' "
        f"font-weight='700' fill='{INK}' {FONT}>{_fmt(total)}</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _arc(cx, cy, r_out, r_in, a0, a1, color, tooltip):
    import math

    def pt(r, a):
        rad = math.radians(a)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    large = 1 if (a1 - a0) > 180 else 0
    x0o, y0o = pt(r_out, a0)
    x1o, y1o = pt(r_out, a1)
    x0i, y0i = pt(r_in, a1)
    x1i, y1i = pt(r_in, a0)
    d = (
        f"M {x0o:.2f} {y0o:.2f} "
        f"A {r_out} {r_out} 0 {large} 1 {x1o:.2f} {y1o:.2f} "
        f"L {x0i:.2f} {y0i:.2f} "
        f"A {r_in} {r_in} 0 {large} 0 {x1i:.2f} {y1i:.2f} Z"
    )
    return f"<path d='{d}' fill='{color}'><title>{_esc(tooltip)}</title></path>"


def _header(w: int, h: int, title: str) -> str:
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
        f"viewBox='0 0 {w} {h}'>"
        f"<rect width='{w}' height='{h}' fill='{BG}'/>"
        f"<text x='32' y='36' font-size='18' font-weight='700' fill='{INK}' {FONT}>"
        f"{_esc(title)}</text>"
    )


def _empty(title: str) -> str:
    return (
        f"{_header(600, 120, title)}"
        f"<text x='32' y='80' font-size='14' fill='{MUTED}' {FONT}>No data.</text></svg>"
    )
