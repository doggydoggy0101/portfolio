"""Deterministic price-range check for open orders.

For each row in data/order.csv:
  - If today > expires      → status: "expired"
  - Else fetch yfinance daily OHLC from date_added to today, and:
      - BUY  @ X: fills if any daily low  ≤ X → status: "likely_filled"
      - SELL @ X: fills if any daily high ≥ X → status: "likely_filled"
  - Else                    → status: "still_pending"
  - On fetch error / empty history / unknown ticker → status: "unknown"

This module writes nothing. It only reports findings; reconcile.md (Claude
skill) handles user confirmation and the actual file mutations.

CLI:
    python -m src.reconcile

prints a JSON array of findings to stdout.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Callable

import pandas as pd
import yfinance as yf

from src.loader import load_orders

_MAX_WORKERS = 8


@dataclass
class Finding:
    idx: int  # row index in order.csv (preserves original order)
    ticker: str
    action: str  # "buy" | "sell"
    price: float  # limit price
    quantity: int
    date_added: str  # ISO date
    expires: str  # ISO date
    status: str  # "still_pending" | "likely_filled" | "expired" | "unknown"
    evidence_date: str | None = None  # day the limit was first crossed
    evidence_price: float | None = None  # low (BUY) or high (SELL) on that day
    note: str = field(default="")  # short human-readable note


def fetch_history(ticker: str, start: date, end: date) -> pd.DataFrame:
    """Daily OHLC between start (inclusive) and end (inclusive). yfinance's end
    is exclusive, so we pass end+1."""
    start_str = start.strftime("%Y-%m-%d")
    end_inclusive = end + pd.Timedelta(days=1)
    end_str = end_inclusive.strftime("%Y-%m-%d")
    return yf.Ticker(ticker).history(start=start_str, end=end_str, auto_adjust=False)


def check_one(
    idx: int,
    row: pd.Series,
    today: date,
    history_fn: Callable[[str, date, date], pd.DataFrame] = fetch_history,
) -> Finding:
    """Pure logic; history_fn is injected so tests don't hit the network."""
    date_added = (
        row["date_added"].date() if hasattr(row["date_added"], "date") else row["date_added"]
    )
    expires = row["expires"].date() if hasattr(row["expires"], "date") else row["expires"]

    finding = Finding(
        idx=idx,
        ticker=str(row["ticker"]).upper(),
        action=str(row["action"]).lower(),
        price=float(row["price"]),
        quantity=int(row["quantity"]),
        date_added=date_added.isoformat(),
        expires=expires.isoformat(),
        status="still_pending",
    )

    if today > expires:
        finding.status = "expired"
        finding.note = f"expires was {expires.isoformat()}"
        return finding

    try:
        hist = history_fn(finding.ticker, date_added, today)
    except Exception as exc:
        finding.status = "unknown"
        finding.note = f"history fetch failed: {type(exc).__name__}"
        return finding

    if hist is None or hist.empty:
        finding.status = "unknown"
        finding.note = "history empty (ticker unknown or no trading days in range)"
        return finding

    limit = finding.price
    if finding.action == "buy":
        hits = hist[hist["Low"] <= limit]
        col = "Low"
    elif finding.action == "sell":
        hits = hist[hist["High"] >= limit]
        col = "High"
    else:
        finding.status = "unknown"
        finding.note = f"unsupported action: {finding.action!r}"
        return finding

    if not hits.empty:
        first_hit = hits.iloc[0]
        finding.status = "likely_filled"
        # first_hit.name is the row's DatetimeIndex value
        ts = first_hit.name
        finding.evidence_date = (ts.date() if hasattr(ts, "date") else ts).isoformat()
        finding.evidence_price = float(first_hit[col])
        finding.note = (
            f"{col.lower()} reached {finding.evidence_price:.2f} on {finding.evidence_date}"
        )

    return finding


def reconcile(
    orders: pd.DataFrame | None = None,
    today: date | None = None,
    history_fn: Callable[[str, date, date], pd.DataFrame] = fetch_history,
) -> list[Finding]:
    """Check every open order. Returns findings sorted by original row order.

    Caller passes `orders` and `today` to keep the function pure for testing;
    the CLI version uses real loader + date.today().
    """
    if orders is None:
        orders = load_orders()
    if today is None:
        today = date.today()
    if orders.empty:
        return []

    findings: list[Finding] = []
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as ex:
        futs = {
            ex.submit(check_one, idx, row, today, history_fn): idx for idx, row in orders.iterrows()
        }
        for fut in futs:
            findings.append(fut.result())
    findings.sort(key=lambda f: f.idx)
    return findings


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Reconcile open orders against price history.")
    ap.add_argument("--today", help="Override today (YYYY-MM-DD); useful for testing.")
    args = ap.parse_args()

    today_arg = date.fromisoformat(args.today) if args.today else None
    out = [asdict(f) for f in reconcile(today=today_arg)]
    print(json.dumps(out, indent=2))
