# Skill: position

Computes the current portfolio state and logs it to today's journal. Runs early in the daily flow (right after reconcile) so every downstream skill — including the optimizer's rule checks — reads from a single, journaled snapshot rather than recomputing.

The python in `src/position.py` is the source of truth for the math. This skill just runs it and writes the output.

## Process

1. **Run the python:**
   ```bash
   python src/position.py
   ```
   It prints a `# Portfolio state` markdown section to stdout. No flags needed for default behavior.

2. **Append the output verbatim to today's journal.** That's it — the python already produces the exact markdown to include.

## What the python computes

For each call:
- Cash = total deposits + sum of sells − sum of buys (from `data/deposit.csv` and `data/transactions.csv`).
- Per-position: shares, avg cost, current price (via `src/price.py`), value, % of active sleeve, % of total portfolio, P&L %.
- Sleeve breakdown: core (VOO by default), active sleeve, cash float.
- Open orders: from `data/order.csv`, with `days_left` to expiry.
- Rule-compliance check:
  - Active-sleeve cash vs the 5% floor / 30% ceiling.
  - Per-name cap vs the 20% mean-rev cap. Reports each violation with the actual %. Violations are warnings per `skills/rule.md` (cap-as-warning rule) — the optimizer surfaces them but does not force trims.

## Why state.py… sorry, position.py exists

Multiple downstream skills need the same derived numbers (position size as % of active, cash compliance, total portfolio value). Without this step they'd each recompute and risk drift if prices move mid-session. Pre-computing once at the top of the day, journaling it, and letting downstream skills *read* it keeps the day's discussion grounded in a single snapshot.

The python is also used by the TUI for the Position tab — that's why the file already had `build_position_view`. The new function `build_state_markdown()` reuses the same pieces and packages them for the journal.

## What this skill does NOT do

- Doesn't propose actions on the rule violations — it just *reports* them. The optimizer reads this section and decides what to do (typically: propose a trim toward cap, propose redeploying cash, etc.).
- Doesn't fetch news or commentary — that's the online research's job.
- Doesn't modify any data file.
- Doesn't take user input — pure compute → write.

## Output schema (what's in the journal section)

```markdown
# Portfolio state — YYYY-MM-DD

## Sleeves
- Core (VOO): $X (Y% of total) [target ~50%]
- Active sleeve: $X (Y% of total)
  - Cash: $X (Y% of active) [floor 5%, ceiling 30%]
  - Invested: $X (Y% of active)
- **Total portfolio: $X**

## Holdings
| ticker | shares | avg cost | current | value | %active | %total | P&L |
...

## Open orders
| ticker | action | limit | qty | days_left |
...

## Rule-compliance check
- Active-sleeve cash: X% — <within bounds | BELOW 5% floor | ABOVE 30% ceiling>
- Per-name cap violations (mean-rev 20%, warning only):
  - TICKER: X% — over 20% mean-rev cap
  (or "- Per-name cap: all positions within 20% mean-rev cap")
```

## Where it sits in the daily loop

```
1. reconcile.md  → update data/* files from broker reality
2. position.md   ← this skill: compute & log state
3. youtube.md
4. online.md
5. regularizer.md
6. optimizer.md  → reads "# Portfolio state" for the rule checks
```
