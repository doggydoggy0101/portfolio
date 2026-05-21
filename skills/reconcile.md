# Skill: reconcile

The first step of the daily flow. Brings the portfolio state file (`data/transactions.csv`) in sync with reality by detecting probable order fills and asking the user to confirm.

The bridge between two files:
- `data/order.csv` (what's pending at the broker)
- `data/transactions.csv` (what's actually executed)

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
   - **Yes:** ask for actual fill price (often a few cents off the limit) and fill date. Append a row to `data/transactions.csv` and remove the row from `data/order.csv`.
   - **No:** leave the row in `data/order.csv` unchanged (the broker rejected, or partial fill is still pending).
   - **Expired/cancel:** remove the row from `data/order.csv` with no transaction append.

4. **Log a `# Reconciliation` section** at the top of today's journal:
   - Number of open orders checked.
   - Each prompted row + user's response.
   - Each row appended to transactions.csv.
   - Each row removed from order.csv.

If `data/order.csv` is empty, log just: "No open orders to reconcile."

## Schema for transactions.csv append

The CSV header (don't write it, just match the row format): `date,ticker,action,quantity,price,amount`.

For a confirmed fill row:
- `date` — user-confirmed fill date (YYYY-MM-DD).
- `ticker` — from order.csv row.
- `action` — `buy` or `sell` from order.csv row.
- `quantity` — from order.csv row.
- `price` — user-confirmed fill price (often differs from limit by cents).
- `amount` — computed: `−(quantity × price)` for buys, `+(quantity × price)` for sells. Negative = cash out, positive = cash in.

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

findings = reconcile()  # uses data/order.csv and date.today() by default
# Each finding is a dataclass with fields:
#   idx, ticker, action, price, quantity, date_added, expires,
#   status, evidence_date, evidence_price, note
```

The function is pure when called with explicit `orders=` and `today=` args. Network calls are encapsulated in `fetch_history` which can be injected with an alternate implementation if needed.

### Known limitation: same-day intraday hits

The history check uses **daily low / high**, which includes intraday moves. If a limit was crossed on the same day the order was placed but the user placed the order *after* the intraday cross, `likely_filled` is a false positive. The user-confirmation step exists exactly for this case — the user knows the actual placement time and can answer "no, didn't fill."

This is the right tradeoff: false positives → an extra prompt; false negatives → a missed fill the user has to remember manually. We prefer false positives.
