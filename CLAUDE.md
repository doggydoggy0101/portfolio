# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Personal investing copilot. Daily-loop system: ingest world + state + doctrine → discuss → log decisions. Advisory only, never auto-trades.

## Daily session flow

When the user opens a new session and triggers the daily run (asks for "morning brief" / "let's start" / "daily run" / similar):

1. **Check if today's journal (`journal/YYYY-MM-DD.md`) exists.**

2. **If YES** — this is a re-open of an already-started day:
   - Read today's journal in full.
   - Wait for the user to direct the discussion. The research is already done.
   - If the journal contains an in-progress optimizer session (proposals not all resolved), offer to continue from where it left off.

3. **If NO** — this is the first session of the day. Initialize the journal with a date header, then run the daily flow in this order. Each step writes a clear `# H1` section so subsequent steps and re-opens can find their inputs.
   1. `skills/reconcile.md` — check open orders against price history; user confirms fills; move filled rows order.csv → transactions.csv.
   2. `skills/position.md` — compute & log portfolio state (sleeves, holdings table with %active / %total, open orders, rule-compliance check).
   3. `skills/youtube.md` — pull new transcripts → summarize via parallel subagents → maintain per-YouTuber conviction tables in the skill file itself.
   4. `skills/online.md` — independent web research per ticker (held + watchlist + pending-order union).
   5. `skills/regularizer.md` — dissent. Reads prior journal sections, produces the load-bearing `**Top flag (hard veto): TICKER**` line.
   6. `skills/optimizer.md` — read everything (including `# Portfolio state` from step 2), propose order adjustments, discuss one-at-a-time with user, append agreed orders to `data/order.csv`, log full session to journal.

Triggers are session-based, not time-based. The user closes and re-opens; the journal-existence check is the only state needed.

## Data files

All sensitive/personal financial data lives in `data/` (gitignored). Read the appropriate file when you need facts about the account — do not assume any specific amounts or counts.

- **Trade history:** `data/transactions.csv` — broker raw export is authoritative. Re-exports replace the file wholesale. Between re-exports, `skills/reconcile.md` appends user-confirmed fills to keep it in sync with reality. Periodic manual re-export (every few weeks) is the reset; any drift becomes visible at that point.
- **Deposit history:** `data/deposit.csv` — one row per deposit/withdrawal.
- **Open orders:** `data/order.csv` — pending limit orders mirrored from the brokerage. Optimizer appends new rows on user agreement. Reconcile removes rows on confirmed fill or expiry.
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
- **Holdings tab** (right): inner `Tabs` widget at top for time range (1d / 5d / 15d / 1m / 3m / 6m / 1y / max) + scrollable list of per-ticker charts. Border title is `TICKER  $current  ($ATH)` — drops parts that aren't available. Switching range rebuilds the chart widgets (in-place mutation hits a textual-plotext render-state bug).
- **Watchlist tab** (right): same widget as Holdings, fed from `data/watchlist.txt`, filtered to exclude tickers in Holdings.
- Heights: left column is Performance:Orders ≈ 5:8 (Fibonacci ~golden ratio). Right column has `max-width: 64` so it doesn't bloat on wide terminals — the left side expands instead.

## Source files

- `main.py` — single-line launcher: imports `tui.StockTUI` and runs it.
- `src/tui.py` — Textual `StockTUI` app. Defines layout, `PerformancePane`, `OrdersView`, `StockChartItem`, `HoldingsView`. Styles in `src/tui.tcss`.
- `src/loader.py` — `load_transactions()`, `load_deposits()`, `load_orders()`, `load_watchlist()`. Each reads its respective file in `data/`.
- `src/portfolio.py` — `compute_book(trades)` walks trades chronologically (FIFO) and returns `(positions_df, realized_pnl)`. `compute_positions(trades)` is a thin wrapper.
- `src/price.py` — `fetch_prices(tickers)` (current + previous close), `fetch_ath(tickers)` (all-time high), `fetch_latest_bar_time(ticker)`. All fetches run in parallel via `ThreadPoolExecutor`.
- `src/position.py` — `build_position_view(trades)` computes the per-position DataFrame; `build_positions_table(df, cash, ath)` builds the rich.Table rendered in the Position tab. `build_state_markdown()` and CLI produce the daily `# Portfolio state` journal section. `compute_sp500_since_entry(ticker)` returns the dollar-weighted SPY total return since each buy. `compute_exit_ladder(ticker)` returns the precise 2-tier sell limit prices per `skills/rule.md`.
- `src/order.py` — `build_orders_table(orders, action, positions, ath)` filters and renders the Order Buy / Order Sell tables. Sell tab shows Gain% vs avg cost; Buy tab shows % vs ATH.
- `src/chart.py` — `render_chart(plt_ctx, ticker, range_, theme, hide_xaxis, hist)` draws a single-ticker chart. `bulk_fetch_history(tickers, range_)` parallelizes history fetches for many tickers at once.
- `src/performance.py` — `render_performance(plt_ctx, range_, theme)` draws portfolio TWR + benchmark(s). Uses real deposit dates from `data/deposit.csv`.

## Conventions

- **Tokyo Night Storm theme** is registered as a Textual `Theme` so `$foreground`, `$accent`, etc. resolve to TN Storm colors. Use theme variables in CSS where possible; hardcoded hex is OK for backgrounds in `src/tui.tcss`.
- **plotext colors** must be RGB tuples, not hex strings — plotext doesn't parse hex. The `TN_STORM` dict in `tui.py` is the source of truth.
- **plotext theme in TUI widgets**: set `self.theme = "clear"` in `on_mount` to disable textual-plotext's `auto`-theming that otherwise stomps our explicit canvas/axes/ticks colors.
- **Bulk-fetch over per-widget fetch.** All network calls (ATH, prices, chart history) are parallelized at the top of `StockTUI.on_mount` and threaded down to widgets via setters/kwargs. Widgets should not hit the network on their own.

## When working in this repo

- `data/transactions.csv` is **broker-authoritative on wholesale re-export** — when the user re-exports from the brokerage, the file is replaced wholesale. Between re-exports, `skills/reconcile.md` appends user-confirmed fills to keep the file in sync with reality (only modification mode allowed). No other skill or script writes to it.
- Any *derived* data (positions DataFrame, sleeve breakdown, exit ladders) goes elsewhere — `src/position.py` computes them on demand, `journal/*.md` snapshots them.
- All formatting/linting via `ruff format .` after edits (per global instructions).
