"""Fetch current + previous close + ATH prices via yfinance.

Fetches run in parallel (ThreadPoolExecutor). yfinance is thread-safe per
Ticker instance, and Yahoo handles ~8-way concurrency comfortably.
No on-disk caching yet — every call hits the network.
"""

from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import yfinance as yf

_MAX_WORKERS = 8


def fetch_ath(tickers: list[str]) -> dict[str, float]:
    """Return {ticker: all-time high} (max daily high since IPO), in parallel.

    Yahoo doesn't expose ATH as a single field, so we still have to download
    history and take the max. Cache to disk later — ATH barely changes.
    """

    def _one(t: str) -> tuple[str, float | None]:
        hist = yf.Ticker(t).history(period="max", auto_adjust=False)
        return (t, float(hist["High"].max())) if not hist.empty else (t, None)

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as ex:
        results = list(ex.map(_one, tickers))
    return {t: ath for t, ath in results if ath is not None}


def fetch_latest_bar_time(ticker: str) -> pd.Timestamp:
    """Timestamp of the most recent 1-minute bar — the freshness of our data.

    For liquid US equities, yfinance tends to land within ~1 min of real time
    (waits for the minute to complete before publishing the bar).
    """
    hist = yf.Ticker(ticker).history(period="5d", interval="1m")
    return hist.index[-1] if not hist.empty else pd.NaT


def fetch_prices(tickers: list[str]) -> pd.DataFrame:
    """Return DataFrame indexed by ticker with columns price/prev_close/ts. Parallel.

    Uses `fast_info` (Yahoo's live quote cache) rather than the daily `history()`
    bar: history()'s current-day row is often NaN until the bar is finalized,
    which silently fell back to the prior day's close — up to a full day stale.
    fast_info.lastPrice / regularMarketPreviousClose track the actual latest quote.
    """

    def _one(t: str) -> dict:
        fi = yf.Ticker(t).fast_info
        price = fi.get("lastPrice", float("nan"))
        prev = fi.get("regularMarketPreviousClose", float("nan"))
        return {
            "ticker": t,
            "price": float(price) if price is not None else float("nan"),
            "prev_close": float(prev) if prev is not None else float("nan"),
            "price_ts": pd.Timestamp.now(),
            "prev_ts": pd.NaT,
        }

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as ex:
        rows = list(ex.map(_one, tickers))
    return pd.DataFrame(rows).set_index("ticker")
