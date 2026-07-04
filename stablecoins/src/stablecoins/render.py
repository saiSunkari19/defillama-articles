"""Rasterize SVG charts to PNG for embedding in Word / Google Docs.

Uses whichever external converter is available, preferring the one that
gives the crispest output. No Python dependencies required.

Preference order:
  1. rsvg-convert (librosvg)  -- fast, exact, high quality
  2. inkscape                 -- high quality
  3. cairosvg (python module) -- if installed
  4. qlmanage (macOS Quick Look) -- last resort, approximate sizing
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import os


class RenderError(RuntimeError):
    """No SVG->PNG converter available, or conversion failed."""


def available_backend() -> str | None:
    """Return the name of the first usable backend, or None."""
    if shutil.which("rsvg-convert"):
        return "rsvg-convert"
    if shutil.which("inkscape"):
        return "inkscape"
    try:
        import cairosvg  # noqa: F401

        return "cairosvg"
    except Exception:
        pass
    if shutil.which("qlmanage"):
        return "qlmanage"
    return None


def svg_to_png(svg: str, png_path: str, scale: float = 2.0) -> str:
    """Rasterize an SVG string to a PNG file at ``scale`` device pixels.

    scale=2.0 roughly matches "retina"/print quality for a Word document.
    Returns the png_path on success; raises RenderError otherwise.
    """
    backend = available_backend()
    if backend is None:
        raise RenderError(
            "No SVG->PNG converter found. Install one of: "
            "librsvg (brew install librsvg), inkscape, or "
            "`pip install cairosvg`."
        )

    os.makedirs(os.path.dirname(os.path.abspath(png_path)) or ".", exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w", suffix=".svg", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(svg)
        svg_path = tmp.name

    try:
        if backend == "rsvg-convert":
            _run(["rsvg-convert", "-z", str(scale), "-o", png_path, svg_path])
        elif backend == "inkscape":
            _run([
                "inkscape", svg_path,
                "--export-type=png",
                f"--export-filename={png_path}",
                f"--export-dpi={int(96 * scale)}",
            ])
        elif backend == "cairosvg":
            import cairosvg

            cairosvg.svg2png(
                bytestring=svg.encode("utf-8"),
                write_to=png_path,
                scale=scale,
            )
        elif backend == "qlmanage":
            _qlmanage(svg_path, png_path, scale)
    finally:
        try:
            os.unlink(svg_path)
        except OSError:
            pass

    if not os.path.exists(png_path):
        raise RenderError(f"{backend} did not produce {png_path}")
    return png_path


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RenderError(
            f"{cmd[0]} failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        )


def _qlmanage(svg_path: str, png_path: str, scale: float) -> None:
    # qlmanage writes <name>.png into an output dir; sizing is approximate.
    out_dir = tempfile.mkdtemp()
    size = int(900 * scale)
    _run(["qlmanage", "-t", "-s", str(size), "-o", out_dir, svg_path])
    produced = os.path.join(out_dir, os.path.basename(svg_path) + ".png")
    if not os.path.exists(produced):
        raise RenderError("qlmanage produced no output")
    shutil.move(produced, png_path)
    shutil.rmtree(out_dir, ignore_errors=True)
