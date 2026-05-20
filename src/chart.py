"""Chart rendering: single-ticker price history rendered into a plotext context."""

from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import yfinance as yf

# Map our short names to yfinance period strings (only where they differ).
YF_PERIOD = {"1m": "1mo", "3m": "3mo", "6m": "6mo"}

_MAX_WORKERS = 8


def _fetch_history(ticker: str, range_: str) -> pd.DataFrame:
    """Pick interval granularity to match the range."""
    if range_ == "1d":
        return yf.Ticker(ticker).history(period="1d", interval="1m")
    if range_ == "5d":
        return yf.Ticker(ticker).history(period="5d", interval="30m")
    if range_ == "15d":
        end = pd.Timestamp.now()
        start = end - pd.Timedelta(days=15)
        return yf.Ticker(ticker).history(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval="1h",
        )
    period = YF_PERIOD.get(range_, range_)
    return yf.Ticker(ticker).history(period=period, auto_adjust=False)


def bulk_fetch_history(tickers: list[str], range_: str = "1d") -> dict[str, pd.DataFrame]:
    """Fetch chart history for many tickers in parallel. Returns {ticker: DataFrame}."""
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as ex:
        results = list(ex.map(lambda t: (t, _fetch_history(t, range_)), tickers))
    return {t: df for t, df in results}


def render_chart(
    plt_ctx,
    ticker: str,
    range_: str = "1d",
    theme: dict | None = None,
    hide_xaxis: bool = False,
    *,
    hist: pd.DataFrame | None = None,
) -> bool:
    """Render a ticker's chart into the given plotext-like context. Returns False on no data.

    `theme` (all keys optional):
        up_color / down_color: line color when overall change is +/- (default named "green"/"red")
        plotext_theme: name passed to plt_ctx.theme(...) — default "pro"
        canvas_color / axes_color / ticks_color: explicit overrides

    `hide_xaxis`: skip x-axis tick labels (when a shared time-index lives elsewhere).
    `hist`: pre-fetched DataFrame. If provided, skip the network call. Used by the
    TUI which bulk-fetches in parallel and threads the result through.
    """
    if hist is None:
        hist = _fetch_history(ticker, range_)
    if hist.empty:
        return False

    closes = hist["Close"].dropna()
    if closes.index.tz:
        closes.index = closes.index.tz_localize(None)

    theme = theme or {}
    up_color = theme.get("up_color", "green")
    down_color = theme.get("down_color", "red")
    plotext_theme = theme.get("plotext_theme", "pro")
    color = up_color if closes.iloc[-1] >= closes.iloc[0] else down_color

    plt_ctx.clear_figure()
    plt_ctx.theme(plotext_theme)
    if "canvas_color" in theme:
        plt_ctx.canvas_color(theme["canvas_color"])
    if "axes_color" in theme:
        plt_ctx.axes_color(theme["axes_color"])
    if "ticks_color" in theme:
        plt_ctx.ticks_color(theme["ticks_color"])

    if range_ == "1d":
        # Fixed full trading day axis: 9:30 → 16:00 ET = 390 minutes.
        market_open = closes.index[0].replace(hour=9, minute=30, second=0, microsecond=0)
        xs = [(t - market_open).total_seconds() / 60 for t in closes.index]
        plt_ctx.plot(xs, closes.tolist(), color=color, marker="braille")
        plt_ctx.xlim(0, 390)
        if hide_xaxis:
            plt_ctx.xticks([], [])
        else:
            plt_ctx.xticks([0, 90, 180, 270, 390], ["09:30", "11:00", "12:30", "14:00", "16:00"])
    else:
        n = len(closes)
        xs = list(range(n))
        plt_ctx.plot(xs, closes.tolist(), color=color, marker="braille")
        if hide_xaxis:
            plt_ctx.xticks([], [])
        else:
            n_ticks = min(5, n)
            positions = [int(i * (n - 1) / (n_ticks - 1)) for i in range(n_ticks)]
            labels = [closes.index[i].strftime("%Y-%m-%d") for i in positions]
            plt_ctx.xticks(positions, labels)
    return True
