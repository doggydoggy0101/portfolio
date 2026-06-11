"""Terminal UI — see CLAUDE.md for the full layout diagram."""

import pandas as pd
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.theme import Theme
from textual.widgets import Footer, Header, Static, Tab, TabbedContent, TabPane, Tabs
from textual_plotext import PlotextPlot

import chart
import performance
from loader import load_deposits, load_dividends, load_orders, load_transactions, load_watchlist
from order import build_history_table, build_orders_table
from portfolio import compute_positions
from position import build_position_view, build_positions_table
from price import fetch_ath, fetch_prices

# Tokyo Night Storm palette as RGB tuples — plotext doesn't honor hex strings.
TN_STORM = {
    "panel_bg": (31, 35, 53),  # #1f2335
    "fg": (192, 202, 245),  # #c0caf5
    "blue": (122, 162, 247),  # #7aa2f7
    "orange": (255, 158, 100),  # #ff9e64
    "red": (247, 118, 142),  # #f7768e
    "green": (158, 206, 106),  # #9ece6a
}

PERF_THEME = {
    "portfolio": TN_STORM["blue"],
    "benchmarks": {"SPY": TN_STORM["orange"]},
    "plotext_theme": "clear",
    "canvas_color": TN_STORM["panel_bg"],
    "axes_color": TN_STORM["panel_bg"],
    "ticks_color": TN_STORM["fg"],
}

TOKYO_NIGHT_STORM = Theme(
    name="tokyo-night-storm",
    primary="#7aa2f7",
    secondary="#bb9af7",
    accent="#7aa2f7",
    foreground="#c0caf5",
    background="#24283b",
    surface="#1f2335",
    panel="#1d202f",
    success="#9ece6a",
    warning="#e0af68",
    error="#f7768e",
    dark=True,
)

CHART_THEME = {
    "up_color": TN_STORM["green"],
    "down_color": TN_STORM["red"],
    "plotext_theme": "clear",
    "canvas_color": TN_STORM["panel_bg"],
    "axes_color": TN_STORM["panel_bg"],
    "ticks_color": TN_STORM["fg"],
}


class PerformancePane(PlotextPlot):
    """Top-left: portfolio TWR vs S&P 500 since inception."""

    def on_mount(self) -> None:
        self.theme = "clear"
        performance.render_performance(self.plt, "max", theme=PERF_THEME)


class StockChartItem(PlotextPlot):
    """One per-stock chart inside the Holdings/Watchlist tab. Range set at construction."""

    def __init__(
        self,
        ticker: str,
        range_: str = "1d",
        ath: float | None = None,
        price: float | None = None,
        hist: pd.DataFrame | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.ticker = ticker
        self._range = range_
        self._ath = ath
        self._price = price
        self._hist = hist  # if provided, skips per-widget network fetch

    def on_mount(self) -> None:
        self.theme = "clear"
        parts = [self.ticker]
        if self._price is not None and not pd.isna(self._price):
            parts.append(f"${self._price:,.2f}")
        if self._ath is not None and not pd.isna(self._ath):
            parts.append(f"(${self._ath:,.2f})")
        self.border_title = "  ".join(parts)
        chart.render_chart(self.plt, self.ticker, self._range, theme=CHART_THEME, hist=self._hist)


class OrdersView(Vertical):
    """Bottom-left: pending orders (Buy / Sell) + past fills (History). Sell active by default."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._positions: pd.DataFrame | None = None
        self._ath: dict[str, float] = {}

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="tab-sell", id="orders-tabs"):
            with TabPane("Order Buy", id="tab-buy"):
                yield VerticalScroll(id="buy-scroll", classes="scroll-pane")
            with TabPane("Order Sell", id="tab-sell"):
                yield VerticalScroll(id="sell-scroll", classes="scroll-pane")
            with TabPane("Order History", id="tab-history"):
                yield VerticalScroll(id="history-scroll", classes="scroll-pane")

    def populate(
        self, positions: pd.DataFrame, ath: dict[str, float], trades: pd.DataFrame
    ) -> None:
        """Wire data in. Called from `StockTUI.on_mount` after ATH is fetched.
        Idempotent — clears existing tables before mounting fresh ones, so it
        can also be called from a reload action."""
        self._positions = positions
        self._ath = ath
        orders = load_orders()
        buy = self.query_one("#buy-scroll", VerticalScroll)
        sell = self.query_one("#sell-scroll", VerticalScroll)
        history = self.query_one("#history-scroll", VerticalScroll)
        buy.remove_children()
        sell.remove_children()
        history.remove_children()
        buy.mount(Static(build_orders_table(orders, "buy", positions=positions, ath=ath)))
        sell.mount(Static(build_orders_table(orders, "sell", positions=positions, ath=ath)))
        history.mount(Static(build_history_table(trades)))


class HoldingsView(Vertical):
    """Holdings tab content: range-selector tabs + scrollable chart list."""

    RANGES = ["1d", "5d", "15d", "1m", "3m", "6m", "1y", "max"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_range = "1d"
        self._ath: dict[str, float] = {}
        self._prices: dict[str, float] = {}
        # {ticker: pre-fetched history DataFrame} for the current range.
        self._chart_data: dict[str, pd.DataFrame] = {}

    def compose(self) -> ComposeResult:
        yield Tabs(*(Tab(r, id=f"range-{r}") for r in self.RANGES), id="range-tabs")
        yield VerticalScroll(id="charts-scroll", classes="scroll-pane")

    def set_ath(self, ath: dict[str, float]) -> None:
        """Set the ATH lookup used for chart titles. Call before add_chart."""
        self._ath = ath

    def set_prices(self, prices: dict[str, float]) -> None:
        """Set the current-price lookup used for chart titles. Call before add_chart."""
        self._prices = prices

    def set_chart_data(self, data: dict[str, pd.DataFrame]) -> None:
        """Set pre-fetched chart history. Each add_chart will use it instead of fetching."""
        self._chart_data = data

    def add_chart(self, ticker: str) -> None:
        self.query_one("#charts-scroll", VerticalScroll).mount(
            StockChartItem(
                ticker,
                range_=self._current_range,
                ath=self._ath.get(ticker),
                price=self._prices.get(ticker),
                hist=self._chart_data.get(ticker),
            )
        )

    async def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab.id is None:
            return
        new_range = event.tab.id.removeprefix("range-")
        if new_range == self._current_range:
            return
        self._current_range = new_range
        scroll = self.query_one("#charts-scroll", VerticalScroll)
        tickers = [c.ticker for c in scroll.children if isinstance(c, StockChartItem)]
        # Bulk-fetch the new range's data in parallel BEFORE remounting widgets.
        # In-place plt mutation triggers textual-plotext render-state bugs, so we
        # still swap fresh widgets — but the network calls now run concurrently.
        self._chart_data = chart.bulk_fetch_history(tickers, new_range)
        await self.query(StockChartItem).remove()
        for t in tickers:
            scroll.mount(
                StockChartItem(
                    t,
                    range_=new_range,
                    ath=self._ath.get(t),
                    price=self._prices.get(t),
                    hist=self._chart_data.get(t),
                )
            )


class StockTUI(App):
    """Personal investing copilot — terminal UI. Styles live in `tui.tcss`."""

    CSS_PATH = "tui.tcss"

    # Disable Textual's default Ctrl+P command palette — we don't use it and
    # it gets in the way.
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("escape", "quit", "Quit"),
        # Re-read data/*.csv and re-render the dynamic panes (Position table,
        # Open Orders). Useful after a Claude Code chat session updates
        # data/order.csv or data/transactions.csv. Charts are kept as-is
        # (re-fetching all chart history is expensive — restart the TUI if
        # you need a full refresh).
        ("ctrl+r", "reload", "Reload"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with Vertical(id="left"):
                yield PerformancePane(id="performance")
                yield OrdersView(id="orders")
            with TabbedContent(id="right-tabs"):
                with TabPane("Position", id="tab-cols"):
                    yield VerticalScroll(id="cols-scroll", classes="scroll-pane")
                with TabPane("Holdings", id="tab-charts"):
                    yield HoldingsView(id="holdings-view")
                with TabPane("Watchlist", id="tab-watchlist"):
                    yield HoldingsView(id="watchlist-view")
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(TOKYO_NIGHT_STORM)
        self.theme = "tokyo-night-storm"
        self._populate_dynamic_panes()

    def action_reload(self) -> None:
        """Re-read data/*.csv and refresh the Position table + Open Orders pane.
        Charts (Holdings/Watchlist) are untouched — restart the TUI for those."""
        # Clear the Position-tab content; OrdersView.populate is already idempotent.
        self.query_one("#cols-scroll", VerticalScroll).remove_children()
        self._populate_dynamic_panes(refresh_charts=False)
        self.notify("Reloaded data from disk.", timeout=2)

    def _populate_dynamic_panes(self, *, refresh_charts: bool = True) -> None:
        """Load data from disk and mount the Position table + Open Orders pane
        (and optionally the Holdings/Watchlist charts on first mount).

        Called from `on_mount` (refresh_charts=True) and from `action_reload`
        (refresh_charts=False — chart history is expensive to re-fetch and
        the Holdings/Watchlist tabs already have their own range-switch reload).
        """
        trades = load_transactions()
        deposits = load_deposits()
        dividends = load_dividends()
        orders = load_orders()
        df = build_position_view(trades)
        positions = compute_positions(trades)  # has avg_cost — used for sell-order Gain%
        cash = deposits["amount"].sum() + trades["amount"].sum() + dividends["amount"].sum()

        # Fetch ATH once for every ticker we'll need across all panes.
        held = set(df.index)
        watchlist_tickers = [t for t in load_watchlist() if t not in held]
        buy_order_tickers = (
            set(orders[orders["action"] == "buy"]["ticker"]) if not orders.empty else set()
        )
        ath_tickers = list(held | set(watchlist_tickers) | buy_order_tickers)
        ath = fetch_ath(ath_tickers)

        # Current prices: held already have them in df["price"]; fetch for watchlist.
        prices: dict[str, float] = (
            {t: float(p) for t, p in df["price"].items()} if not df.empty else {}
        )
        if watchlist_tickers:
            wl_prices = fetch_prices(watchlist_tickers)["price"]
            prices.update({t: float(p) for t, p in wl_prices.items()})

        # Position tab (always refreshed)
        cols_scroll = self.query_one("#cols-scroll", VerticalScroll)
        cols_scroll.mount(
            Static(
                build_positions_table(df, cash, ath=ath, deposits_total=deposits["amount"].sum())
            )
        )

        # Open Orders pane (always refreshed; populate is idempotent)
        self.query_one("#orders", OrdersView).populate(positions, ath, trades)

        if refresh_charts:
            # Bulk-fetch 1d intraday data once for every chart we'll render.
            held_list = list(df.index)
            holdings_chart_data = chart.bulk_fetch_history(held_list, "1d") if held_list else {}
            watchlist_chart_data = (
                chart.bulk_fetch_history(watchlist_tickers, "1d") if watchlist_tickers else {}
            )

            # Holdings tab
            holdings = self.query_one("#holdings-view", HoldingsView)
            holdings.set_ath(ath)
            holdings.set_prices(prices)
            holdings.set_chart_data(holdings_chart_data)
            for ticker in held_list:
                holdings.add_chart(ticker)

            # Watchlist tab
            watchlist = self.query_one("#watchlist-view", HoldingsView)
            watchlist.set_ath(ath)
            watchlist.set_prices(prices)
            watchlist.set_chart_data(watchlist_chart_data)
            for ticker in watchlist_tickers:
                watchlist.add_chart(ticker)


def add_parser(subparsers) -> None:
    p = subparsers.add_parser("tui", help="launch the terminal UI")
    p.set_defaults(func=cmd_tui)
