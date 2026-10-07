"""Structured writer for data/<account>/order.csv.

The note column is the 7th and last field. A literal comma inside a hand-typed
note silently adds a phantom 8th field and crashes `loader.load_orders` (plain
`pd.read_csv`), which breaks the TUI. This has happened repeatedly because
skills append rows by hand-editing the file as raw text.

Always append/remove order.csv rows through this module instead. Writing via
pandas quotes any field containing a comma automatically (same mechanism that
already protects transactions.csv's Description column), so a comma in a note
can no longer break the column count.

CLI:
    python -m src.order_writer append --account ira --ticker GOOG --action sell \
        --price 370 --quantity 1 --expires 2027-02-27 --note "default exit ladder tier 1"
    python -m src.order_writer remove --account ira --ticker GOOG --action sell --price 370
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from src.loader import DEFAULT_ACCOUNT, account_path

COLUMNS = ["date_added", "ticker", "action", "price", "quantity", "expires", "note"]


def _read(account: str) -> pd.DataFrame:
    path = account_path(account, "order.csv")
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(path, dtype=str)


def _write(account: str, df: pd.DataFrame) -> None:
    account_path(account, "order.csv").parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(account_path(account, "order.csv"), index=False)


def append_order(
    account: str,
    ticker: str,
    action: str,
    price: float,
    quantity: int,
    expires: str,
    note: str = "",
    date_added: str | None = None,
) -> None:
    """Append one row. Commas in `note` are safe — pandas quotes the field on write."""
    action = action.lower()
    if action not in ("buy", "sell"):
        raise ValueError(f"action must be 'buy' or 'sell', got {action!r}")
    row = {
        "date_added": date_added or date.today().isoformat(),
        "ticker": ticker.upper().strip(),
        "action": action,
        "price": str(float(price)),
        "quantity": str(int(quantity)),
        "expires": expires,
        "note": note,
    }
    df = _read(account)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write(account, df)


def remove_order(account: str, ticker: str, action: str, price: float) -> int:
    """Remove matching row(s) by ticker+action+price. Returns count removed."""
    df = _read(account)
    if df.empty:
        return 0
    mask = (
        (df["ticker"].str.upper() == ticker.upper())
        & (df["action"].str.lower() == action.lower())
        & (df["price"].astype(float) == float(price))
    )
    removed = int(mask.sum())
    if removed:
        _write(account, df[~mask])
    return removed


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Structured order.csv writer (append/remove).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("append")
    a.add_argument("--account", default=DEFAULT_ACCOUNT)
    a.add_argument("--ticker", required=True)
    a.add_argument("--action", required=True, choices=["buy", "sell"])
    a.add_argument("--price", required=True, type=float)
    a.add_argument("--quantity", required=True, type=int)
    a.add_argument("--expires", required=True)
    a.add_argument("--note", default="")
    a.add_argument("--date-added", default=None)

    r = sub.add_parser("remove")
    r.add_argument("--account", default=DEFAULT_ACCOUNT)
    r.add_argument("--ticker", required=True)
    r.add_argument("--action", required=True, choices=["buy", "sell"])
    r.add_argument("--price", required=True, type=float)

    args = ap.parse_args()
    if args.cmd == "append":
        append_order(
            args.account,
            args.ticker,
            args.action,
            args.price,
            args.quantity,
            args.expires,
            args.note,
            args.date_added,
        )
        print(
            f"appended {args.action} {args.ticker} @ {args.price} x{args.quantity} "
            f"to {args.account}/order.csv"
        )
    elif args.cmd == "remove":
        n = remove_order(args.account, args.ticker, args.action, args.price)
        print(
            f"removed {n} row(s) matching {args.ticker} {args.action} @ {args.price} "
            f"from {args.account}/order.csv"
        )
