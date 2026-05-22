"""Orders pane tables: open orders (filtered by action) + transaction history.

Each open-orders tab shows one decision metric:
- Sell tab: "Gain" — % return if executed at the limit price vs current avg cost basis.
- Buy tab: "vs ATH" — % the limit price is below all-time high (negative number).

History tab shows past fills from `data/transactions.csv`, newest first.
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

    for _, r in filtered.sort_values("expires", ascending=False).iterrows():
        table.add_row(
            r["ticker"],
            f"${r['price']:,.2f}",
            str(r["quantity"]),
            r["expires"].strftime("%Y-%m-%d"),
            _extra_cell(r, action, positions, ath),
        )

    return table


def build_history_table(trades: pd.DataFrame) -> Table:
    """Past fills from `data/transactions.csv`, newest first.

    Columns: Date, Ticker, Action (Buy red / Sell green — matches the Open Orders
    Buy/Sell color convention), Qty, Price.
    """
    table = Table(box=box.ROUNDED)
    table.add_column("", justify="left")  # ticker
    table.add_column("Price", justify="right")
    table.add_column("Qty", justify="right")
    table.add_column("Date", justify="right")
    table.add_column("Action", justify="left")

    if trades.empty:
        table.add_row("[dim]No transactions[/]", "", "", "", "")
        return table

    for _, r in trades.sort_values("date", ascending=False).iterrows():
        color = "red" if r["action"] == "buy" else "green"
        label = r["action"].capitalize()
        # Quantity may be fractional from the broker export — strip trailing zeros.
        qty = r["quantity"]
        qty_str = f"{qty:g}"
        table.add_row(
            r["ticker"],
            f"${r['price']:,.2f}",
            qty_str,
            r["date"].strftime("%Y-%m-%d"),
            f"[{color}]{label}[/{color}]",
        )

    return table
