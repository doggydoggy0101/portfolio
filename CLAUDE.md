# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Personal investing copilot. Daily-loop system: ingest world + state + doctrine → discuss → log decisions. Advisory only, never auto-trades.

## Daily session flow

When the user opens a new session and triggers the daily run (asks for "morning brief" / "let's start" / "daily run" / similar):

0. **Fresh clone?** If the account folders under `data/` are missing or empty, this repo was just cloned as a template — do **not** run the daily flow. Read `SETUP.md` and walk the user through onboarding (their broker format, accounts, and doctrine will differ from the author's).

1. **Check if today's journal (`journal/YYYY-MM-DD.md`) exists.**

2. **If YES** — this is a re-open of an already-started day:
   - Read today's journal in full.
   - Wait for the user to direct the discussion. The research is already done.
   - If the journal contains an in-progress optimizer session (proposals not all resolved), offer to continue from where it left off.

3. **If NO** — this is the first session of the day. Initialize the journal with a date header, then run the daily flow in this order. Each step writes a clear `# H1` section so subsequent steps and re-opens can find their inputs.
   1. `skills/reconcile.md` — check open orders against price history; user confirms fills; move filled rows order.csv → transactions.csv.
   2. `skills/position.md` — compute & log portfolio state (sleeves, holdings table with %active / %total, open orders, rule-compliance check).
   3. `skills/youtube.md` — pull new transcripts → summarize via parallel subagents → maintain per-creator conviction tables in their profile files under `skills/youtube/` (gitignored; `template.md` documents the structure).
   4. `skills/online.md` — independent web research per ticker (held + watchlist + pending-order union).
   5. `skills/regularizer.md` — dissent. Reads prior journal sections, produces the load-bearing `**Top flag (hard veto): TICKER**` line.
   6. `skills/optimizer.md` — read everything (including `# Portfolio state` from step 2), propose order adjustments, discuss one-at-a-time with user, append agreed orders to `data/ira/order.csv`, log full session to journal.

Triggers are session-based, not time-based. The user closes and re-opens; the journal-existence check is the only state needed.

## Accounts

There are **two accounts**, each with its own data folder under `data/` (gitignored):

- **`ira`** (`data/ira/`) — the Roth IRA. This is the **actively managed** account: the daily loop, sleeves, exit ladders, cash floor, and the entire `skills/rule.md` doctrine apply *only* here. Gains are tax-free (sell freely; no cap-gains considerations) — which is exactly why this is the **home for the active/trading sleeve**.
- **`general`** (`data/general/`) — the **taxable** brokerage account. **Passive** by design: buy-and-hold VOO for the long term. No sleeves, no ladders, no daily optimizer. It shows in the TUI and tracks performance, but the daily loop does **not** manage it. Being taxable, sales here *do* have capital-gains consequences (mostly moot for buy-and-hold VOO) — which is exactly why this is the **long-term home for the core VOO**.

**Core/active split is measured across *both* accounts (decided 2026-06-15).** The ~50% VOO core target in `skills/rule.md` applies to the **combined** IRA + General total, not the IRA alone. The intended end-state: VOO core lives in the (taxable) General account; the (tax-free) IRA holds the active/trading sleeve. **Transition = freeze-and-migrate:** IRA VOO is **frozen** (no new adds; it is no longer "untouchable") and becomes a migration source — as General accumulates VOO via deposits, matching IRA VOO is sold (tax-free) and redeployed into IRA active names, *but only when an active buy actually passes the rules* (no idle-cash dumps). Net combined VOO stays ~50% throughout; it just changes address. As of 2026-06-15 combined VOO ≈ 48% (all still in the IRA), so this is relocation, not accumulation.

The daily session flow (reconcile → position → … → optimizer) runs against **`ira` only**. `loader.ACCOUNTS = ("ira", "general")`, default account is `"ira"`.

## Data files

Each account folder holds the same three files; the watchlist is shared at the top level. Read the appropriate file when you need facts about an account — do not assume any specific amounts or counts.

- **Trade history:** `data/<account>/transactions.csv` — broker raw export is authoritative. Re-exports replace that account's file wholesale (export each account separately from the broker). Between re-exports, `skills/reconcile.md` appends user-confirmed fills (IRA only). Periodic manual re-export is the reset; any drift becomes visible at that point.
- **Deposit history:** `data/<account>/deposit.csv` — one row per deposit/withdrawal.
- **Open orders:** `data/<account>/order.csv` — pending limit orders mirrored from the brokerage. Optimizer appends new IRA rows on user agreement. Reconcile removes IRA rows on confirmed fill or expiry.
- **Watchlist:** `data/watchlist.txt` — **shared across accounts**, one ticker per line, `#` comments allowed. Filtered against holdings in the TUI.

## Running

```
python main.py
```

Launches the Textual TUI. `Esc` quits, `Ctrl+R` reloads data (re-reads the active account's `data/<account>/*.csv` and refreshes the Position table + Open Orders pane; charts are kept). The **account switch** (IRA / General buttons in the bottom bar, or `Ctrl+1` / `Ctrl+2`) flips the active account and refreshes every pane. The bottom bar also has clickable `Reload` / `Quit` buttons. No subcommands — the TUI is the only entry point.

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
│  Open Orders           │                                  │
│  (active account)      │                                  │
├────────────────────────┴──────────────────────────────────┤
│  General  IRA                      Reload  Quit  09:51:41  │  ← BottomBar
└─────────────────────────────────────────────────────────────┘
```

- **BottomBar** (bottom): a `BottomBar(Horizontal)` replacing Textual's `Footer`/`Header`. Left: account-switch buttons in `loader.ACCOUNTS` order — currently `General` then `IRA` (flat `barbtn` style; the button for `DEFAULT_ACCOUNT` carries the `active` class on launch). Right: `Reload` and `Quit` action buttons + a live clock (`Static`, updated each second). All four are flat `Button`s. `StockTUI.on_button_pressed` routes `acct-*` → `_switch_account`, `btn-reload` → `action_reload`, `btn-quit` → `exit()`. Account switching is **also bound to `Ctrl+N`** (N = button position, so `Ctrl+1` = General, `Ctrl+2` = IRA) via `action_switch_account`; both keyboard and click work. `_switch_account` flips `StockTUI.account`, moves the `active` class, remounts the Performance pane, and repopulates every pane.
- **Performance pane** (top-left): TWR % since first deposit, blue line for Portfolio, orange line for SPY benchmark. Reads the active account (returns blank if that account has no trades yet).
- **Open Orders pane** (bottom-left): `TabbedContent` with Order Buy / Order Sell tabs. Each tab renders a small `rich.Table` filtered from the active account's `order.csv`. Columns: ticker, price, qty, expires, vs-S&P-500-or-vs-ATH (rightmost). Sell's "vs S&P 500" column (green) is the excess over SPY-since-entry if the limit fills — `(limit/avg_cost)/(1+SPY_since_entry) − 1`, so a rule.md ladder order reads +10% at tier 1 and +21% at tier 2 (×1.10 tiers compound); Buy's "vs ATH" column is red.
- **Position tab** (right): rich.Table — Price / Day / Total / Value columns. Each stock spans two text rows. Price cell shows current price on top and `(ATH)` below in dim. CASH and TOTAL rows below.
- **Holdings tab** (right): inner `Tabs` widget at top for time range (1d / 5d / 15d / 1m / 3m / 6m / 1y / max) + scrollable list of per-ticker charts. Border title is `TICKER  $current  ($ATH)` — drops parts that aren't available. Switching range rebuilds the chart widgets (in-place mutation hits a textual-plotext render-state bug).
- **Watchlist tab** (right): same widget as Holdings, fed from the shared `data/watchlist.txt`, filtered to exclude tickers in Holdings.
- Heights: left column is Performance:Orders ≈ 5:8 (Fibonacci ~golden ratio). Right column has `max-width: 64` so it doesn't bloat on wide terminals — the left side expands instead.

## Source files

- `main.py` — single-line launcher: imports `tui.StockTUI` and runs it.
- `src/tui.py` — Textual `StockTUI` app. Defines layout, `BottomBar` (account switch + Reload/Quit + clock), `PerformancePane`, `OrdersView`, `StockChartItem`, `HoldingsView`. Styles in `src/tui.tcss`.
- `src/loader.py` — `load_transactions(account)`, `load_deposits(account)`, `load_dividends(account)`, `load_orders(account)` each read `data/<account>/<file>.csv` (default `account="ira"`); `load_watchlist()` reads the shared `data/watchlist.txt`. `ACCOUNTS` lists the account ids; `account_path(account, filename)` resolves a per-account file.
- `src/portfolio.py` — `compute_book(trades)` walks trades chronologically (FIFO) and returns `(positions_df, realized_pnl)`. `compute_positions(trades)` is a thin wrapper.
- `src/price.py` — `fetch_prices(tickers)` (current + previous close), `fetch_ath(tickers)` (all-time high), `fetch_latest_bar_time(ticker)`. All fetches run in parallel via `ThreadPoolExecutor`.
- `src/position.py` — `build_position_view(trades)` computes the per-position DataFrame; `build_positions_table(df, cash, ath)` builds the rich.Table rendered in the Position tab. `build_state_markdown()` and CLI produce the daily `# Portfolio state` journal section. `compute_sp500_since_entry(ticker)` returns the dollar-weighted SPY total return since each buy; `compute_sp500_since_entry_bulk(trades, tickers)` does the same for many tickers with a single SPY fetch (used by the TUI). `compute_exit_ladder(ticker)` returns the precise 2-tier sell limit prices per `skills/rule.md`.
- `src/order.py` — `build_orders_table(orders, action, positions, ath, spy_since)` filters and renders the Order Buy / Order Sell tables. Sell tab shows % vs SPY-since-entry (falls back to plain gain vs avg cost if SPY data is missing); Buy tab shows % vs ATH.
- `src/chart.py` — `render_chart(plt_ctx, ticker, range_, theme, hide_xaxis, hist)` draws a single-ticker chart. `bulk_fetch_history(tickers, range_)` parallelizes history fetches for many tickers at once.
- `src/performance.py` — `render_performance(plt_ctx, range_, theme, account)` draws portfolio TWR + benchmark(s) for one account. Uses real deposit dates from that account's `deposit.csv`.

## Conventions

- **Tokyo Night Storm theme** is registered as a Textual `Theme` so `$foreground`, `$accent`, etc. resolve to TN Storm colors. Use theme variables in CSS where possible; hardcoded hex is OK for backgrounds in `src/tui.tcss`.
- **plotext colors** must be RGB tuples, not hex strings — plotext doesn't parse hex. The `TN_STORM` dict in `tui.py` is the source of truth.
- **plotext theme in TUI widgets**: set `self.theme = "clear"` in `on_mount` to disable textual-plotext's `auto`-theming that otherwise stomps our explicit canvas/axes/ticks colors.
- **Bulk-fetch over per-widget fetch.** All network calls (ATH, prices, chart history) are parallelized at the top of `StockTUI.on_mount` and threaded down to widgets via setters/kwargs. Widgets should not hit the network on their own.

## When working in this repo

- `data/<account>/transactions.csv` is **broker-authoritative on wholesale re-export** — when the user re-exports an account from the brokerage, that file is replaced wholesale. Between re-exports, `skills/reconcile.md` appends user-confirmed fills to keep the file in sync with reality (only modification mode allowed). No other skill or script writes to it.
- Any *derived* data (positions DataFrame, sleeve breakdown, exit ladders) goes elsewhere — `src/position.py` computes them on demand, `journal/*.md` snapshots them.
- All formatting/linting via `ruff format .` after edits (per global instructions).
