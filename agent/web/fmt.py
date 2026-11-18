"""Number formatting for people: no scientific notation, thousands separators."""

from __future__ import annotations


def num(v) -> str:
    """614913.0 -> '614,913'; 382.74 -> '382.7'; 1.6285 -> '1.63'; 0.01234 -> '0.0123'."""
    if v is None:
        return "-"
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return str(v)
    a = abs(v)
    if a >= 1000:
        s = f"{v:,.0f}"
    elif a >= 10:
        s = f"{v:,.1f}"
    elif a >= 1:
        s = f"{v:.2f}"
    elif a == 0:
        return "0"
    else:
        # Three significant digits without exponent, e.g. 0.000123.
        decimals = 2
        while a < 10 ** -(decimals - 2) and decimals < 12:
            decimals += 1
        s = f"{v:.{decimals}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def pct(v) -> str:
    return "" if v is None else f"{v:+.1f}%"
