"""Compute current holdings and cost basis from a trades DataFrame."""

from collections import deque

import pandas as pd


def compute_book(trades: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Walk trades chronologically, FIFO. Returns (positions_df, realized_pnl).

    positions_df: indexed by ticker; columns shares, avg_cost, cost_basis.
                  Closed positions excluded.
    realized_pnl: total realized gain/loss from all sells.
    """
    lots: dict[str, deque] = {}  # ticker → deque of [qty, price] buy lots (oldest first)
    realized = 0.0

    for _, t in trades.sort_values("date").iterrows():
        q = lots.setdefault(t["ticker"], deque())
        if t["action"] == "buy":
            q.append([t["quantity"], t["price"]])
        else:  # sell: consume from front (oldest), realized uses actual proceeds
            cost_consumed = 0.0
            remaining = t["quantity"]
            while remaining > 1e-9 and q:
                lot_qty, lot_price = q[0]
                consumed = min(lot_qty, remaining)
                cost_consumed += consumed * lot_price
                if lot_qty <= remaining + 1e-9:
                    q.popleft()
                else:
                    q[0][0] = lot_qty - consumed
                remaining -= consumed
            realized += t["amount"] - cost_consumed  # actual cash received minus FIFO cost

    rows = []
    for ticker, q in lots.items():
        shares = sum(lot[0] for lot in q)
        if shares <= 1e-9:
            continue
        cost = sum(lot[0] * lot[1] for lot in q)
        rows.append(
            {
                "ticker": ticker,
                "shares": shares,
                "avg_cost": cost / shares,
                "cost_basis": cost,
            }
        )
    return pd.DataFrame(rows).set_index("ticker").sort_index(), realized


def compute_positions(trades: pd.DataFrame) -> pd.DataFrame:
    """Convenience: just the positions DataFrame from `compute_book`."""
    return compute_book(trades)[0]
