"""Performance rendering: portfolio time-weighted return (TWR) vs S&P 500.

TWR is the standard brokerage performance metric — what most brokerage apps display.
Uses real deposit dates from the account's `data/<account>/deposit.csv`.
"""

from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import yfinance as yf

from loader import load_deposits, load_transactions

_MAX_WORKERS = 8

BENCHMARKS = [
    ("SPY", "S&P 500", "orange"),
]
PORTFOLIO_COLOR = "blue"


def _range_start(range_: str, today: pd.Timestamp) -> pd.Timestamp | None:
    if range_ == "max":
        return None
    if range_ == "ytd":
        return pd.Timestamp(today.year, 1, 1)
    months = {"1mo": 1, "3mo": 3, "6mo": 6}
    years = {"1y": 1, "2y": 2, "5y": 5}
    if range_ in months:
        return today - pd.DateOffset(months=months[range_])
    if range_ in years:
        return today - pd.DateOffset(years=years[range_])
    return None


def _shares_on_date(tk_trades: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.Series:
    signed = tk_trades["quantity"] * tk_trades["action"].map({"buy": 1, "sell": -1})
    cum = signed.groupby(tk_trades["date"]).sum().sort_index().cumsum()
    return cum.reindex(dates, method="ffill").fillna(0)


def _cash_on_date(
    trades: pd.DataFrame,
    cashflows: pd.DataFrame,
    dates: pd.DatetimeIndex,
) -> pd.Series:
    dep_cum = cashflows.groupby("date")["amount"].sum().sort_index().cumsum()
    dep_cum = dep_cum.reindex(dates, method="ffill").fillna(0)
    trade_cum = trades.groupby("date")["amount"].sum().sort_index().cumsum()
    trade_cum = trade_cum.reindex(dates, method="ffill").fillna(0)
    return dep_cum + trade_cum


def _portfolio_value(
    trades: pd.DataFrame,
    cashflows: pd.DataFrame,
    dates: pd.DatetimeIndex,
    prices: dict[str, pd.Series],
) -> pd.Series:
    value = pd.Series(0.0, index=dates)
    for tk in trades["ticker"].unique():
        if tk not in prices:
            continue
        shares = _shares_on_date(trades[trades["ticker"] == tk], dates)
        px = prices[tk].reindex(dates, method="ffill")
        value = value.add((shares * px).fillna(0), fill_value=0)
    return value + _cash_on_date(trades, cashflows, dates)


def _daily_deposits(cashflows: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.Series:
    daily = cashflows.groupby("date")["amount"].sum()
    return daily.reindex(dates).fillna(0)


def _fetch_history(
    tickers: list[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, pd.Series]:
    """Fetch daily-close history per ticker in parallel."""
    start_str = start.strftime("%Y-%m-%d")
    end_str = (end + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    def _one(tk: str) -> tuple[str, pd.Series | None]:
        hist = yf.Ticker(tk).history(start=start_str, end=end_str, auto_adjust=False)
        if hist.empty:
            return tk, None
        closes = hist["Close"].dropna()
        if closes.index.tz:
            closes.index = closes.index.tz_localize(None)
        return tk, closes

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as ex:
        results = list(ex.map(_one, tickers))
    return {tk: c for tk, c in results if c is not None}


def _twr_pct(value: pd.Series, deposits: pd.Series) -> list[float]:
    """Cumulative time-weighted return as % series.

    Daily return r_t = (V_t - V_{t-1} - deposit_t) / V_{t-1}.
    Convention: deposit treated as end-of-day (does not earn intraday).
    """
    prev = value.shift(1)
    r = (value - prev - deposits) / prev
    r = r.fillna(0).replace([float("inf"), -float("inf")], 0)
    cum = (1 + r).cumprod() - 1
    return (cum * 100).tolist()


def _to_pct(series: pd.Series) -> list[float]:
    return ((series / series.iloc[0] - 1) * 100).tolist()


def render_performance(
    plt_ctx, range_: str = "max", theme: dict | None = None, account: str = "ira"
) -> bool:
    """Render perf chart into the given plotext-like context. Returns False on no data.

    `theme` (all keys optional):
        portfolio: line color (default named "blue")
        benchmarks: {ticker: color} override (default uses BENCHMARKS table)
        plotext_theme: name passed to plt_ctx.theme(...) — default "pro"
        canvas_color / axes_color / ticks_color: explicit overrides
    `account`: which account's trades/deposits to chart (default "ira").
    """
    theme = theme or {}
    portfolio_color = theme.get("portfolio", PORTFOLIO_COLOR)
    bench_override = theme.get("benchmarks", {})
    plotext_theme = theme.get("plotext_theme", "pro")

    trades = load_transactions(account)
    deposits = load_deposits(account)
    if trades.empty:
        return False

    today = pd.Timestamp.now().normalize()
    start_candidates = [trades["date"].min()]
    if not deposits.empty:
        start_candidates.append(deposits["date"].min())
    start = min(start_candidates)
    held_tickers = trades["ticker"].unique().tolist()

    prices = _fetch_history(held_tickers, start, today)
    if not prices:
        return False

    dates = pd.DatetimeIndex(sorted(set().union(*[p.index for p in prices.values()])))
    portfolio = _portfolio_value(trades, deposits, dates, prices)
    daily_deps = _daily_deposits(deposits, dates)
    bench_prices = _fetch_history([b[0] for b in BENCHMARKS], start, today)

    range_start = _range_start(range_, today)
    if range_start is not None:
        mask = portfolio.index >= range_start
        if mask.any():
            portfolio = portfolio[mask]
            daily_deps = daily_deps[mask]

    portfolio_twr = _twr_pct(portfolio, daily_deps)
    date_strs = [d.strftime("%Y/%m/%d") for d in portfolio.index]

    plt_ctx.clear_figure()
    plt_ctx.date_form("Y/m/d")
    plt_ctx.theme(plotext_theme)
    if "canvas_color" in theme:
        plt_ctx.canvas_color(theme["canvas_color"])
    if "axes_color" in theme:
        plt_ctx.axes_color(theme["axes_color"])
    if "ticks_color" in theme:
        plt_ctx.ticks_color(theme["ticks_color"])

    # Plot benchmarks first so portfolio line renders on top where they overlap.
    for ticker, label, default_color in BENCHMARKS:
        if ticker not in bench_prices:
            continue
        aligned = bench_prices[ticker].reindex(portfolio.index, method="ffill")
        bench_pct = _to_pct(aligned)
        plt_ctx.plot(
            date_strs,
            bench_pct,
            label=f"{label} ({bench_pct[-1]:+.2f}%)",
            color=bench_override.get(ticker, default_color),
        )
    plt_ctx.plot(
        date_strs,
        portfolio_twr,
        label=f"Portfolio ({portfolio_twr[-1]:+.2f}%)",
        color=portfolio_color,
    )

    plt_ctx.yticks([])  # legend shows current % — gridline labels are redundant
    return True
