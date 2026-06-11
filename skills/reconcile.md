# Skill: reconcile

The first step of the daily flow. Brings the portfolio state file (`data/ira/transactions.csv`) in sync with reality by detecting probable order fills and asking the user to confirm.

The bridge between two files:
- `data/ira/order.csv` (what's pending at the broker)
- `data/ira/transactions.csv` (what's actually executed)

Run only on the **first session of a new day** (per CLAUDE.md daily flow).

## Process

1. **Run the deterministic price check.**
   ```bash
   python -m src.reconcile
   ```
   (Optional `--today YYYY-MM-DD` to override today for testing.) Returns a JSON array — one entry per open order — each tagged with a status:
   - `still_pending` — daily low/high never crossed the limit between `date_added` and today; **not asked about**.
   - `likely_filled` — daily low (for BUY) or high (for SELL) crossed the limit on at least one day. Evidence: the crossing date and the price reached.
   - `expired` — `today > expires`.
   - `unknown` — history fetch failed, history empty, or unsupported action. Surface to the user as a soft prompt ("couldn't auto-check — did this fill?").

2. **Walk the findings with the user, one at a time:**

   - For each `still_pending` row → **say nothing.** No prompt, no journal noise.
   - For each `expired` row → tell the user: "Order X expired on Y, removing from order.csv." Auto-remove on user nod (default yes).
   - For each `likely_filled` row → ask:
     > "Order X (BUY/SELL N shares of TICKER @ $LIMIT) looks like it could have filled on YYYY-MM-DD — that day's [low/high] was $PRICE. Did this actually fill on your broker?"

3. **On user response:**
   - **Yes:** ask for actual fill price (often a few cents off the limit) and fill date. Append a row to `data/ira/transactions.csv` and remove the row from `data/ira/order.csv`.
   - **No:** leave the row in `data/ira/order.csv` unchanged (the broker rejected, or partial fill is still pending).
   - **Expired/cancel:** remove the row from `data/ira/order.csv` with no transaction append.

4. **Log a `# Reconciliation` section** at the top of today's journal:
   - Number of open orders checked.
   - Each prompted row + user's response.
   - Each row appended to transactions.csv.
   - Each row removed from order.csv.

If `data/ira/order.csv` is empty, log just: "No open orders to reconcile."

## Schema for transactions.csv append

`data/ira/transactions.csv` is the broker's raw export — reconcile must match that schema so the loader can still parse the file. The loader (`src/loader.py::load_transactions`) reads these six columns:

| Column | Value | Notes |
|---|---|---|
| `Trade Date` | `MM/DD/YYYY` | user-confirmed fill date (note: slashes, US format) |
| `Type` | `Buy` or `Sell` | capitalized; the loader filters on this — anything else is ignored |
| `Ticker` | from order.csv row | uppercase, no whitespace |
| `Quantity` | shares | broker convention: **positive for BUY, negative for SELL**. The loader takes `.abs()` |
| `Price USD` | per-share USD | user-confirmed fill price (often differs from limit by cents) |
| `Amount USD` | signed total | **BUY: `−(quantity × price)`** (cash out). **SELL: `+(quantity × price)`** (cash in) |

**If the broker export contains additional columns** (settlement date, commission, fees, account number, etc.), preserve the existing header and leave the extra columns empty for reconcile-appended rows. The loader only reads the six above; anything else is ignored on read but should still be present so future broker re-exports merge cleanly.

**Implementation note:** read the existing `data/ira/transactions.csv` with `pd.read_csv` (it'll strip the broker's UTF-8 BOM if present), build a row dict matching all columns (filling unused ones — Post Date, Settlement Date, Commissions, Description, etc. — with empty strings), append, write back. Don't write a fresh header — the file already has one. A typical brokerage export has ~30 columns; the loader only reads six (`Trade Date`, `Type`, `Ticker`, `Quantity`, `Price USD`, `Amount USD`).

## Discipline

- **Never write to transactions.csv without explicit user yes.** Even a "likely_filled" with strong evidence is just a hypothesis until the user checks their broker.
- **Never modify order.csv silently.** Every removal is logged in the journal.
- **Don't fetch news, opinions, or commentary.** That's other skills' job. This skill is pure state-sync.
- **Don't propose new orders.** That's optimizer.md.

## What this skill does NOT do

- Does not propose new orders.
- Does not modify rules, watchlist, or any other skill file.
- Does not run if today's journal already exists (per CLAUDE.md — re-opens skip the daily flow).
- Does not assume fill — user always confirms each "likely_filled" row.

## `src/reconcile.py` — implemented

The deterministic price-check helper is at `src/reconcile.py`. API:

```python
from src.reconcile import reconcile, Finding

findings = reconcile()  # uses data/ira/order.csv and date.today() by default
# Each finding is a dataclass with fields:
#   idx, ticker, action, price, quantity, date_added, expires,
#   status, evidence_date, evidence_price, note
```

The function is pure when called with explicit `orders=` and `today=` args. Network calls are encapsulated in `fetch_history` which can be injected with an alternate implementation if needed.

### Known limitation: same-day intraday hits

The history check uses **daily low / high**, which includes intraday moves. If a limit was crossed on the same day the order was placed but the user placed the order *after* the intraday cross, `likely_filled` is a false positive. The user-confirmation step exists exactly for this case — the user knows the actual placement time and can answer "no, didn't fill."

This is the right tradeoff: false positives → an extra prompt; false negatives → a missed fill the user has to remember manually. We prefer false positives.
