"""CLI: list, analyze, and visualize stablecoin supply from DeFiLlama."""

from __future__ import annotations

import argparse
import os

from . import analysis, charts, render
from .client import StablecoinsClient


def _fmt(n: float) -> str:
    for unit in ("", "K", "M", "B", "T"):
        if abs(n) < 1000:
            return f"{n:,.2f}{unit}"
        n /= 1000
    return f"{n:,.2f}P"


def _pct(x: float | None) -> str:
    if x is None:
        return "   n/a"
    return f"{x*100:+6.2f}%"


def cmd_list(args) -> int:
    coins = StablecoinsClient().get_stablecoins()
    coins.sort(key=lambda c: c.total_supply, reverse=True)
    if not args.all:
        coins = coins[: args.top]

    total = 0.0
    print(f"{'#':>3}  {'SYMBOL':<10} {'NAME':<24} {'MECHANISM':<14} {'TOTAL SUPPLY':>16}")
    print("-" * 72)
    for i, c in enumerate(coins, 1):
        total += c.total_supply
        print(
            f"{i:>3}  {c.symbol:<10} {c.name[:24]:<24} "
            f"{c.peg_mechanism:<14} {_fmt(c.total_supply):>16}"
        )
    print("-" * 72)
    print(f"Shown total: {_fmt(total)}")
    return 0


def cmd_analyze(args) -> int:
    coins = StablecoinsClient().get_stablecoins()
    rows = analysis.analyze(coins)
    grand_total = analysis.total_supply(coins)

    print(f"Total stablecoin supply: {_fmt(grand_total)}  across {len(coins)} assets")
    print(
        f"Top-3 concentration: {analysis.concentration(rows, 3)*100:.1f}%   "
        f"Top-10: {analysis.concentration(rows, 10)*100:.1f}%\n"
    )

    top = rows[: args.top]
    hdr = f"{'#':>3}  {'SYMBOL':<8} {'SHARE':>7} {'SUPPLY':>13}   {'Δ DAY':>7} {'Δ WEEK':>7} {'Δ MONTH':>8}"
    print(hdr)
    print("-" * len(hdr))
    for i, r in enumerate(top, 1):
        print(
            f"{i:>3}  {r.coin.symbol:<8} {r.market_share*100:6.2f}% {_fmt(r.coin.total_supply):>13}"
            f"   {_pct(r.growth_day)} {_pct(r.growth_week)} {_pct(r.growth_month)}"
        )

    print("\nBy peg mechanism:")
    for name, val in analysis.mechanism_breakdown(coins).items():
        print(f"  {name:<16} {_fmt(val):>14}  ({val/grand_total*100:5.1f}%)")

    print("\nBy peg type:")
    for name, val in analysis.peg_breakdown(coins).items():
        print(f"  {name:<16} {_fmt(val):>14}  ({val/grand_total*100:5.1f}%)")

    if args.charts or args.png:
        os.makedirs(args.out, exist_ok=True)
        svgs = {
            "supply_bar": charts.bar_chart(rows, top_n=args.top),
            "mechanism_donut": charts.donut_chart(
                analysis.mechanism_breakdown(coins), "Supply by peg mechanism"
            ),
            "pegtype_donut": charts.donut_chart(
                analysis.peg_breakdown(coins), "Supply by peg type"
            ),
        }
        # Always write the SVG (source of truth); PNG is derived from it.
        print(f"\nCharts written to {args.out}/:")
        for name, svg in svgs.items():
            svg_path = os.path.join(args.out, f"{name}.svg")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"  {svg_path}")

        if args.png:
            if render.available_backend() is None:
                print(
                    "\n[!] Cannot make PNGs: no converter found. "
                    "Install librsvg (`brew install librsvg`) or `pip install cairosvg`."
                )
                return 1
            print(f"\nPNGs (scale {args.scale}x) via {render.available_backend()}:")
            for name, svg in svgs.items():
                png_path = os.path.join(args.out, f"{name}.png")
                render.svg_to_png(svg, png_path, scale=args.scale)
                print(f"  {png_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stablecoins and their total supply from DeFiLlama."
    )
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="List stablecoins by total supply.")
    p_list.add_argument("-n", "--top", type=int, default=25)
    p_list.add_argument("--all", action="store_true")
    p_list.set_defaults(func=cmd_list)

    p_an = sub.add_parser("analyze", help="Analyze + visualize supply.")
    p_an.add_argument("-n", "--top", type=int, default=12)
    p_an.add_argument("--charts", action="store_true", help="Write SVG charts.")
    p_an.add_argument("--png", action="store_true", help="Also write PNGs (for Word/Docs).")
    p_an.add_argument("--scale", type=float, default=2.0, help="PNG scale factor (default 2x).")
    p_an.add_argument("--out", default="charts", help="Chart output dir.")
    p_an.set_defaults(func=cmd_analyze)

    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        # default: list top 25
        args.top, args.all = 25, False
        return cmd_list(args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
