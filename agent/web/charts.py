"""Small server-rendered SVG charts (no JavaScript, no external assets)."""

from __future__ import annotations

from markupsafe import Markup, escape

from .fmt import num

W, H, PAD = 320, 70, 4


def sparkline(points: list[dict], highlight_url: str | None = None) -> Markup:
    """Values as a line, the band each run was checked against as a shaded area.

    Each point is a decision document: value, lower_boundary, upper_boundary, result.
    FAIL runs are red dots; the run being viewed gets a ring.
    """
    pts = [p for p in points if isinstance(p.get("value"), (int, float))]
    if len(pts) < 2:
        return Markup('<span class="muted">not enough history</span>')
    ys = [p["value"] for p in pts]
    ys += [p[k] for p in pts for k in ("lower_boundary", "upper_boundary") if isinstance(p.get(k), (int, float))]
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or abs(hi) or 1.0
    lo, hi = lo - 0.05 * span, hi + 0.05 * span

    def x(i):
        return PAD + i * (W - 2 * PAD) / (len(pts) - 1)

    def y(v):
        return H - PAD - (v - lo) * (H - 2 * PAD) / (hi - lo)

    band_top, band_bot = [], []
    for i, p in enumerate(pts):
        if isinstance(p.get("upper_boundary"), (int, float)) and isinstance(p.get("lower_boundary"), (int, float)):
            band_top.append(f"{x(i):.1f},{y(p['upper_boundary']):.1f}")
            band_bot.append(f"{x(i):.1f},{y(p['lower_boundary']):.1f}")
    parts = [f'<svg class="spark" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">']
    if band_top:
        parts.append(f'<polygon class="band" points="{" ".join(band_top + band_bot[::-1])}"/>')
    line = " ".join(f"{x(i):.1f},{y(p['value']):.1f}" for i, p in enumerate(pts))
    parts.append(f'<polyline class="line" points="{line}"/>')
    for i, p in enumerate(pts):
        cls = "fail" if p.get("result") == "FAIL" else "pass"
        if highlight_url and p.get("build_url") == highlight_url:
            cls += " current"
        title = escape(f"{(p.get('uploaded') or '')[:16]}  value {num(p['value'])}  "
                       f"band {num(p.get('lower_boundary'))} – {num(p.get('upper_boundary'))}  {p.get('result')}")
        parts.append(f'<circle class="{cls}" cx="{x(i):.1f}" cy="{y(p["value"]):.1f}" r="2.5"><title>{title}</title></circle>')
    parts.append("</svg>")
    return Markup("".join(parts))
