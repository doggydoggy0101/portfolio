"""Open-orders view: rich.Table built from `data/order.csv`, filtered by action.

Each tab shows one decision metric:
- Sell tab: "Gain" — % return if executed at the limit price vs current avg cost basis.
- Buy tab: "vs ATH" — % the limit price is below all-time high (negative number).
"""

import pandas as pd
from rich import box
from rich.table import Table


def _extra_cell(
    row: pd.Series,
    action: str,
    positions: pd.DataFrame | None,
    ath: dict[str, float] | None,
) -> str:
    """% gain (sell, green) vs avg cost OR % vs ATH (buy, red)."""
    if action == "sell" and positions is not None and row["ticker"] in positions.index:
        avg = positions.loc[row["ticker"], "avg_cost"]
        pct = (row["price"] - avg) / avg * 100
        sign = "+" if pct >= 0 else ""
        return f"[green]{sign}{pct:.2f}%[/green]"
    if action == "buy" and ath and row["ticker"] in ath:
        ath_price = ath[row["ticker"]]
        pct = (row["price"] - ath_price) / ath_price * 100
        sign = "+" if pct >= 0 else ""
        return f"[red]{sign}{pct:.2f}%[/red]"
    return "-"


def build_orders_table(
    orders: pd.DataFrame,
    action: str,
    *,
    positions: pd.DataFrame | None = None,
    ath: dict[str, float] | None = None,
) -> Table:
    """Filter to one action ('buy' or 'sell') and render as a compact table.

    Column order: ticker, Price, Qty, Expires, Gain/vs ATH (rightmost).
    """
    filtered = orders[orders["action"] == action] if not orders.empty else orders
    extra_label = "Gain" if action == "sell" else "vs ATH"

    table = Table(box=box.ROUNDED)
    table.add_column("", justify="left")  # ticker, no color
    table.add_column("Price", justify="right")
    table.add_column("Qty", justify="right")
    table.add_column("Expires", justify="right")
    table.add_column(extra_label, justify="right")

    if filtered.empty:
        table.add_row(f"[dim]No open {action} orders[/]", "", "", "", "")
        return table

    for _, r in filtered.iterrows():
        table.add_row(
            r["ticker"],
            f"${r['price']:,.2f}",
            str(r["quantity"]),
            r["expires"].strftime("%Y-%m-%d"),
            _extra_cell(r, action, positions, ath),
        )

    return table
