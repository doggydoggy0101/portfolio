"""Position view: shared helpers for the rich.Table used by the TUI's Position tab."""

import pandas as pd
from rich import box
from rich.table import Table

from loader import load_transactions  # noqa: F401  (re-export convenience)
from portfolio import compute_positions
from prices import fetch_prices


def _price_ath(price: float, ath: float | None, *, bold: bool = False) -> str:
    """Two-line cell: $price on top, dim 'ATH $X' below (omitted if no ATH)."""
    if pd.isna(price):
        return "-"
    price_part = f"${price:,.2f}"
    if bold:
        price_part = f"[bold]{price_part}[/]"
    if ath is None or pd.isna(ath):
        return price_part
    return f"{price_part}\n[dim](${ath:,.2f})[/dim]"


def _money(x: float, *, signed: bool = False, bold: bool = False) -> str:
    if pd.isna(x):
        return "-"
    if signed:
        sign = "+" if x >= 0 else "-"
        s = f"{sign}${abs(x):,.2f}"
        color = "green" if x >= 0 else "red"
        style = f"bold {color}" if bold else color
        return f"[{style}]{s}[/]"
    s = f"${x:,.2f}"
    return f"[bold]{s}[/]" if bold else s


def _money_pct(money: float, pct: float, *, bold: bool = False) -> str:
    """Two-line cell: $amount on top, (%) below — only the % is colored."""
    if pd.isna(money) or pd.isna(pct):
        return "-"
    sign = "+" if money >= 0 else "-"
    pct_sign = "+" if pct >= 0 else ""
    color = "green" if pct >= 0 else "red"
    money_part = f"{sign}${abs(money):,.2f}"
    pct_part = f"({pct_sign}{pct:.2f}%)"
    if bold:
        money_part = f"[bold]{money_part}[/]"
        pct_part = f"[bold {color}]{pct_part}[/]"
    else:
        pct_part = f"[{color}]{pct_part}[/]"
    return f"{money_part}\n{pct_part}"


def _value_qty(value: float, shares: float, *, bold: bool = False) -> str:
    """Two-line cell: $value on top, (qty) below in dim style."""
    if pd.isna(value):
        return "-"
    qty_str = str(int(shares)) if shares == int(shares) else f"{shares:.4f}"
    value_part = f"${value:,.2f}"
    if bold:
        value_part = f"[bold]{value_part}[/]"
    return f"{value_part}\n[dim]({qty_str})[/dim]"


def build_position_view(trades: pd.DataFrame) -> pd.DataFrame:
    """Compute the per-position DataFrame for display.

    Returns DataFrame indexed by ticker with columns:
    shares, avg_cost, cost_basis, price, prev_close, price_ts, prev_ts,
    value, day_gl, day_gl_pct, total_gl, total_gl_pct.
    Sorted by value (largest first).
    """
    positions = compute_positions(trades)
    if positions.empty:
        return pd.DataFrame()
    prices = fetch_prices(positions.index.tolist())
    df = positions.join(prices)
    df["value"] = df["shares"] * df["price"]
    df["day_gl"] = df["shares"] * (df["price"] - df["prev_close"])
    df["day_gl_pct"] = (df["price"] - df["prev_close"]) / df["prev_close"] * 100
    df["total_gl"] = df["value"] - df["cost_basis"]
    df["total_gl_pct"] = df["total_gl"] / df["cost_basis"] * 100
    return df.sort_values("value", ascending=False)


def build_positions_table(
    df: pd.DataFrame, cash: float, ath: dict[str, float] | None = None
) -> Table:
    """Build the rich.Table shown in the TUI's Position tab.

    Each stock row spans two text rows: number on top, secondary value below in parens.
    `ath` (optional): {ticker: all-time high} — shown below price as "ATH $X".
    """
    ath = ath or {}
    table = Table(box=box.ROUNDED)
    cols = [
        ("", "left"),
        ("Price", "right"),
        ("Day", "right"),
        ("Total", "right"),
        ("Value", "right"),
    ]
    for name, justify in cols:
        table.add_column(name, justify=justify)

    for ticker, r in df.iterrows():
        table.add_row(
            ticker,
            _price_ath(r["price"], ath.get(ticker)),
            _money_pct(r["day_gl"], r["day_gl_pct"]),
            _money_pct(r["total_gl"], r["total_gl_pct"]),
            _value_qty(r["value"], r["shares"]),
        )

    table.add_row("CASH", "—", "—", "—", _money(cash))

    if not df.empty:
        stocks_value = df["value"].sum()
        stocks_cost = df["cost_basis"].sum()
        stocks_day_gl = df["day_gl"].sum()
        stocks_total_gl = df["total_gl"].sum()
        stocks_prev_value = (df["prev_close"] * df["shares"]).sum()
        day_gl_pct_total = stocks_day_gl / (stocks_prev_value + cash) * 100
        total_gl_pct = stocks_total_gl / stocks_cost * 100  # cash excluded from denominator

        table.add_section()
        total_value = stocks_value + cash
        table.add_row(
            "[bold]TOTAL[/]",
            "",
            _money_pct(stocks_day_gl, day_gl_pct_total, bold=True),
            _money_pct(stocks_total_gl, total_gl_pct, bold=True),
            _money(total_value, bold=True),
        )

    return table
