# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Personal investing copilot. Daily-loop system: ingest world + state + doctrine → discuss → log decisions. Advisory only, never auto-trades.

## Data files

All sensitive/personal financial data lives in `data/` (gitignored). Read the appropriate file when you need facts about the account — do not assume any specific amounts or counts.

- **Trade history:** `data/transactions.csv` — raw broker export. Do not hand-edit; future re-exports replace it wholesale.
- **Deposit history:** `data/deposit.csv` — one row per deposit/withdrawal.
- **Open orders:** `data/order.csv` — pending limit orders mirrored from the brokerage.
- **Watchlist:** `data/watchlist.txt` — one ticker per line, `#` comments allowed. Filtered against holdings in the TUI.

## Running

```
python main.py
```

Launches the Textual TUI. `Esc` to quit. No subcommands — the TUI is the only entry point.

Deps in `requirements.txt`. Install: `pip install -r requirements.txt`. Repo uses a `.venv/` for development.

## TUI structure

Layout (Tokyo Night Storm palette throughout, defined as a Textual theme):

```
┌────────────────────────┬──────────────────────────────────┐
│                        │ [Position] [Holdings] [Watchlist]│
│  Performance           ├──────────────────────────────────┤
│  (portfolio TWR        │                                  │
│   vs S&P 500)          │  Position: rich.Table            │
│                        │  Holdings: range tabs + charts   │
├────────────────────────┤  Watchlist: same shape, filtered │
│ [Order Buy] [Order Sell]│   against holdings              │
│                        │                                  │
│  Open Orders           │                                  │
│  (data/order.csv)      │                                  │
└────────────────────────┴──────────────────────────────────┘
```

- **Performance pane** (top-left): TWR % since first deposit, blue line for Portfolio, orange line for SPY benchmark.
- **Open Orders pane** (bottom-left): `TabbedContent` with Order Buy / Order Sell tabs. Each tab renders a small `rich.Table` filtered from `data/order.csv`. Columns: ticker, price, qty, expires, gain-or-vs-ATH (rightmost). Sell's "Gain" column is green, Buy's "vs ATH" column is red.
- **Position tab** (right): rich.Table — Price / Day / Total / Value columns. Each stock spans two text rows. Price cell shows current price on top and `(ATH)` below in dim. CASH and TOTAL rows below.
- **Holdings tab** (right): inner `Tabs` widget at top for time range (1d / 5d / 15d / 1m / 3m / 6m / 1y / max) + scrollable list of per-ticker charts. Border title is `TICKER  ($ATH)`. Switching range rebuilds the chart widgets (in-place mutation hits a textual-plotext render-state bug).
- **Watchlist tab** (right): same widget as Holdings, fed from `data/watchlist.txt`, filtered to exclude tickers in Holdings.
- Heights: left column is Performance:Orders ≈ 5:8 (Fibonacci ~golden ratio). Right column has `max-width: 64` so it doesn't bloat on wide terminals — the left side expands instead.

## Source files

- `main.py` — single-line launcher: imports `tui.StockTUI` and runs it.
- `src/tui.py` — Textual `StockTUI` app. Defines layout, `PerformancePane`, `OrdersView`, `StockChartItem`, `HoldingsView`. Styles in `src/tui.tcss`.
- `src/loader.py` — `load_transactions()`, `load_deposits()`, `load_orders()`, `load_watchlist()`. Each reads its respective file in `data/`.
- `src/portfolio.py` — `compute_book(trades)` walks trades chronologically (FIFO) and returns `(positions_df, realized_pnl)`. `compute_positions(trades)` is a thin wrapper.
- `src/prices.py` — `fetch_prices(tickers)` (current + previous close), `fetch_ath(tickers)` (all-time high), `fetch_latest_bar_time(ticker)`. All fetches run in parallel via `ThreadPoolExecutor`.
- `src/positions.py` — `build_position_view(trades)` computes the per-position DataFrame; `build_positions_table(df, cash, ath)` builds the rich.Table rendered in the Position tab.
- `src/orders.py` — `build_orders_table(orders, action, positions, ath)` filters and renders the Order Buy / Order Sell tables. Sell tab shows Gain% vs avg cost; Buy tab shows % vs ATH.
- `src/chart.py` — `render_chart(plt_ctx, ticker, range_, theme, hide_xaxis, hist)` draws a single-ticker chart. `bulk_fetch_history(tickers, range_)` parallelizes history fetches for many tickers at once.
- `src/performance.py` — `render_performance(plt_ctx, range_, theme)` draws portfolio TWR + benchmark(s). Uses real deposit dates from `data/deposit.csv`.

## Conventions

- **Tokyo Night Storm theme** is registered as a Textual `Theme` so `$foreground`, `$accent`, etc. resolve to TN Storm colors. Use theme variables in CSS where possible; hardcoded hex is OK for backgrounds in `src/tui.tcss`.
- **plotext colors** must be RGB tuples, not hex strings — plotext doesn't parse hex. The `TN_STORM` dict in `tui.py` is the source of truth.
- **plotext theme in TUI widgets**: set `self.theme = "clear"` in `on_mount` to disable textual-plotext's `auto`-theming that otherwise stomps our explicit canvas/axes/ticks colors.
- **Bulk-fetch over per-widget fetch.** All network calls (ATH, prices, chart history) are parallelized at the top of `StockTUI.on_mount` and threaded down to widgets via setters/kwargs. Widgets should not hit the network on their own.

## When working in this repo

- Keep `data/transactions.csv` treated as read-only broker output. Any derived data goes in separate files.
- All formatting/linting via `ruff format .` after edits (per global instructions).
