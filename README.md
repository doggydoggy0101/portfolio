# portfolio

Two surfaces sharing one folder:

- **TUI** — visual dashboard: holdings, performance, open orders, charts. Read-only.
- **Claude Code** — drives the daily session. Reads doctrine + state + opinions, proposes orders, logs decisions.


## Run

```
pip install -r requirements.txt
python main.py
```

Keys: `Esc` quits, `Ctrl+R` reloads.

## Layout

```
.
├── CLAUDE.md             AI orchestrator; daily session flow lives here
├── README.md             this file
├── main.py               TUI launcher (one-liner)
├── requirements.txt
├── pyproject.toml        ruff config
├── skills/               AI skill files — one per step of the daily loop
│   ├── reconcile.md      step 1: sync data/order.csv ↔ data/transactions.csv
│   ├── position.md       step 2: compute portfolio state, log to journal
│   ├── youtube.md        step 3: pull + summarize YouTuber videos
│   ├── online.md         step 4: independent web research per ticker
│   ├── regularizer.md    step 5: deliberate dissent + hard-veto flag
│   ├── rule.md           trading doctrine (constraints + exit triggers)
│   └── optimizer.md      step 6: propose orders, walk discussion, log
├── src/
│   ├── tui.py            Textual app (styles in tui.tcss)
│   ├── loader.py         CSV/TXT loaders for data/
│   ├── portfolio.py      FIFO cost-basis computation
│   ├── position.py       per-position view + portfolio-state markdown +
│   │                       compute_exit_ladder() for 2-tier sell limits
│   ├── price.py          yfinance price/ATH fetchers
│   ├── order.py          rich.Table builder for the Open Orders pane
│   ├── chart.py          per-ticker plotext charts
│   ├── performance.py    portfolio TWR vs benchmarks
│   ├── reconcile.py      deterministic price-cross check for open orders
│   └── youtube.py        channel resolver + transcript fetcher
├── data/                 personal state (gitignored)
└── journal/              AI loop log, one .md per day (gitignored)
```

## Data file formats

All in `data/` (gitignored).

### `transactions.csv` — broker raw export

Re-exported wholesale from the brokerage every few weeks. Between re-exports, `skills/reconcile.md` appends user-confirmed fills.

Columns (broker format — preserved verbatim from export):

| Column | Notes |
|---|---|
| `Trade Date` | `MM/DD/YYYY` |
| `Type` | `Buy` or `Sell` (other rows ignored on load) |
| `Ticker` | `AAPL` etc. |
| `Quantity` | absolute number of shares |
| `Price USD` | per-share price |
| `Amount USD` | signed total: negative for buys, positive for sells |

### `order.csv` — pending limit orders

Format used by reconcile + optimizer:

```
date_added,ticker,action,price,quantity,expires,note
```

- `date_added`, `expires`: `YYYY-MM-DD`
- `action`: `buy` or `sell`
- `quantity`: integer share count
- `note`: optional, free-text reason

### `deposit.csv` — cash flows in/out of the account

```
date,amount,notes
```

- `date`: any pandas-parseable
- `amount`: positive = deposit in, negative = withdrawal out
- `notes`: free-text (e.g., `"2025 tax year contribution"`)

### `watchlist.txt` — tickers to track

One ticker per line, `#` for comments. Convention: held positions are also listed here so the watchlist represents the full universe of names the optimizer should consider.

## Daily session

See `CLAUDE.md` for the full flow. Brief version:

1. Open Claude Code in a terminal in this repo.
2. Ask for the morning brief.
3. CLAUDE.md checks if `journal/YYYY-MM-DD.md` exists.
   - **Yes** → read it, wait for direction.
   - **No** → run reconcile → position → youtube → online → regularizer → optimizer.
4. Optimizer walks proposed orders one-at-a-time. Agreed orders append to `data/order.csv`.
5. Optimizer logs the session (proposals + decisions + reasoning) to today's journal.
