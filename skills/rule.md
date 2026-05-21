# Skill: rule.md — Trading Philosophy

The user's investing doctrine. **Name-independent** and **opinion-independent**: this file describes *how* to think about a trade, not *which* trade. The optimizer (`skills/optimizer.md`) consumes this file plus the day's opinions to produce concrete proposals.

This file evolves. Treat every number below as a *starter*; revisit quarterly based on what the journal track record actually shows.

---

## Goal

**Beat the S&P 500 by 1-2% per year on a total-portfolio basis.**

- Year-1 target: portfolio CAGR ≥ SP500 CAGR + 1%.
- Year-2+ target: portfolio CAGR ≥ SP500 CAGR + 2% as confidence in the active sleeve grows.
- Measurement: rolling 12-month total return of the full portfolio vs. SPY/VOO total return over the same window.

Not a goal: huge multipliers, getting rich fast, market timing, predicting recessions. Modest, repeatable outperformance.

---

## Portfolio structure

```
Total portfolio
├─ ~50%  Core sleeve   (VOO; never sold, never traded against)
└─ ~50%  Active sleeve (mean-reversion + momentum buckets + cash)
```

**Core sleeve (VOO).** Untouchable. Bought once, held forever. This is the benchmark itself. Active-sleeve sales never rebalance back into the core; new deposits *can* go to either core or active.

**Active sleeve.** The experiment. Internally split into two buckets and a cash float:

```
Active sleeve
├─ Mean-reversion bucket  (priority; target ~70-80% of active sleeve when invested)
├─ Momentum bucket        (secondary; target ~10-20% of active sleeve)
└─ Cash float             (dry powder; target ~10-20% minimum)
```

The split is a *target*, not a hard rule. Drift is OK. If the bucket weights drift more than ±10 percentage points from target, revisit the split.

---

## Hard constraints (locked — not debatable)

- **US equities only.** No international, no EAFE, no EM.
- **Long only.** No short selling.
- **No options.** No calls, puts, covered calls, spreads.
- **No leverage.** No leveraged or inverse ETFs (no TSLZ, TQQQ, SQQQ, etc.).
- **No crypto.** No BTC, ETH, COIN, MSTR.
- **No pre-IPO / RWA tokens.** No Jarsy, no private-market exposure via tokenization.

These are doctrine. The regularizer doesn't push back on them. Optimizer doesn't propose them. Add new locks here as they emerge.

---

## Mean-reversion strategy (priority)

The bet: a quality company temporarily out of favor reverts toward fair value. The entry has *built-in margin of safety* — you're buying after most of the bad news.

### Entry criteria (all should hold)

1. **Material drawdown from 52-week high.** Optimizer judges what counts as "material" per name; a useful floor is ~20%, but a low-volatility name at -20% can be a stronger setup than a high-volatility name at -40%. The point: the bad news is *mostly already in the price*.
2. **Quality filter:** company has at least one of:
   - Recognized brand/franchise that the market still uses (consumer brands)
   - Mission-critical software with a sticky enterprise customer base
   - Profitable and FCF-positive in the most recent reported quarter
   - Net cash on balance sheet OR debt clearly serviceable
3. **No active earnings collapse:** the latest reported quarter did *not* show revenue declining year-over-year and operating margin compressing simultaneously. Drawdowns from sentiment are fine; drawdowns from fundamental deterioration are not.
4. **Cross-source signal:** at least **2 favorable signals** from the set `{each YouTuber, online research}`. Each YouTuber counts as 1 signal; online research counts as 1 signal. Cross-channel synthesis (the "Where they agree / disagree" tables) is human-readable journal context, not a vote — it's already a derivative of the per-YouTuber views. The number of YouTubers is not fixed; the rule scales naturally.
5. **Regularizer veto:** the **top** named consensus-trade-risk in today's `# Regularizer` → `## Where consensus is forming` section is a hard veto. The first / headline ticker disqualifies, even if every other signal is favorable. Secondary names in that section are warnings only — optimizer can size cautiously but is not required to skip them.

### What counts as "favorable" per signal

| Signal | Favorable when... |
|---|---|
| Any YouTuber | Name is in that YouTuber's **"Highest-conviction names" table** in `skills/youtube.md` with a buy/strong-buy stance (not "avoid"). |
| Online research | **Analyst consensus PT > current price by ≥10%** in today's `# Independent research` section. |

The YouTuber profiles in `skills/youtube.md` are the source of truth for each YouTuber's current conviction set. The youtube skill maintains them: a name joins a YouTuber's conviction table when it has appeared in **≥3 of their last 10 videos** with a consistent thesis; it drops when it hasn't been mentioned in the last 10 videos. Optimizer does **not** re-derive this from journal history each day — it just reads the profile.

### Exit trigger

**Position return ≥ SP500-since-entry-return + 10%** is the **trim trigger**, not a mandatory full exit.
- Example: bought at $100 when SP500 was 7,000. Today SP500 is 7,420 (+6%). Trim threshold = $100 × 1.06 × 1.10 = $116.60.
- **How much to sell at the trigger is optimizer's call**, based on the day's opinions and remaining setup. If momentum is intact, trim lightly; if the thesis looks tired, trim more.
- A second-tier trim at higher levels (e.g., +20% above SP500-since-entry) lets the rest run. Again, exact amount is optimizer's call.

### Fundamental-break exit

If the **quality filter from entry no longer holds** (e.g., revenue and margin both collapse in a subsequent quarter, a material legal/regulatory event, a key catalyst disconfirmed), exit fully — even at a loss. This is the only "stop-loss" in the mean-reversion bucket. There is **no mechanical price-based stop**; drawdowns are expected.

### Position sizing

- **Per-name cap: 20% of active sleeve.** A blown-up single bet costs ≤10% of total portfolio (at the 50/50 sleeve split). The cap is a MAX, not a target — most positions sit well below it. Implies ~5 names if everyone's at cap, ~6-10 names with a mix of sizes.
- **Initial entry: ~5% of active sleeve (~25% of cap).** Leaves room to add on further drawdown.
- **Adds:** triggered when (a) average cost is down ≥10%, *and* (b) the quality filter still holds. Each add is **half the remaining headroom to the cap**, capped at **3 total adds** (so the position approaches the cap after at most 3 adds: 5% → 12.5% → 16% → 20%). Optimizer decides whether to take each add — these are *triggers*, not mandates.
- **Adds stop** if the quality filter is broken or if the position is already at the cap.

---

## Momentum bucket (secondary)

The bet: a winner keeps winning. *No margin of safety* in the entry price — you're buying at strength. Different *sizing* applies; the *exit logic* is the same as mean-reversion.

### Entry criteria (all should hold)

1. **Strong consensus:** **3+ favorable signals** from `{each YouTuber, online research}` (versus 2 for mean-reversion). "Favorable" definitions are the same as in the mean-reversion section above. Momentum entry effectively requires multi-source confirmation, so with too few inputs (e.g., 1 YouTuber + online = 2 total signals) the momentum bucket is dormant.
2. **Catalyst:** a fresh fundamental driver (earnings beat with raised guide, major contract, design win, deal close) — *or* a recent pullback that optimizer judges as a constructive entry point.
3. **Regularizer veto:** the top named consensus-trade-risk in today's regularizer section disqualifies (same rule as mean-reversion).

### Exit trigger

Same as mean-reversion: **Position return ≥ SP500-since-entry-return + 10%** is the trim trigger. How much to sell is optimizer's call.

### Fundamental-break exit

Same as mean-reversion: if the entry catalyst is disconfirmed (e.g., the deal falls apart, the guide is cut, the design win loses to a competitor), exit fully. No mechanical price-based stop.

### Position sizing

- **Per-name cap: 10% of active sleeve** — half the mean-reversion cap because the downside is unfloored.
- **Initial entry: 50% of cap (~5% of active sleeve).** One-shot.
- **No adds.** Momentum entries have no margin of safety; averaging down on a momentum trade compounds the risk that the trend was already over. If a name re-qualifies later under different criteria, that's a new entry, not an add.

### Why no time-based or technical exits

The user is not running a short-term strategy. Trends-break / moving-average / hard-percent stops belong to short-term trading frameworks that punish patience. Exits here are tied to *the goal* (beat SP500 by 10%) or *the thesis* (fundamental break), not to the price chart or the calendar.

---

## Cross-strategy rules

### Single-name and sector caps (across both buckets)

- **Single-name cap (any bucket): 20% of active sleeve (mean-rev) or 10% (momentum).** Same name can't appear in both buckets simultaneously.
- The cap is a **MAX for new entries** — do not intentionally push a name above the cap by buying more.
- Existing positions **can drift above cap** as they appreciate. The default exit ladder (below) handles the natural rebalance over time.
- **Cap violations are warnings, not forced trims.** When a held position drifts above cap, optimizer:
  1. **Surfaces the fact** in every session's proposal list — keeps it visible so the user is never blindsided.
  2. **Proposes an *optional* accelerated trim** (a lower-priced tier of the ladder, separate from the default ladder). User decides yes/no per session.
  3. **Does not auto-trim.** Without explicit user agreement, the position rides until the default exit ladder fires.
- **Single-sector cap: 30% of active sleeve.** Sectors here: SaaS, semis, consumer discretionary, fintech, energy, healthcare, communications, industrials, materials.
- **Single-theme cap: 40% of active sleeve.** Themes are softer than sectors (e.g. "AI infrastructure" includes semis + cloud + power + networking).

### Default exit ladders for held positions

For every **non-core held position**, optimizer maintains a 2-tier sell ladder as standing limit orders in `data/order.csv`:

- **Tier 1 limit price** = `avg_cost × (1 + SP500_return_since_entry) × 1.10`
- **Tier 2 limit price** = `Tier 1 × 1.10` (another +10% above tier 1)
- **Quantities per tier** are optimizer's judgment, per the Sell pacing rule. Default starting pattern: 1 share at each tier (less-aggressive default — accepts a slower full-cap rebalance in exchange for less reactive trading). Optimizer can size higher when conviction is low or position is well over cap.

**Computing the prices.** Use `compute_exit_ladder(ticker)` from `src/position.py`. It loads transactions, computes the **dollar-weighted SPY total return since each buy** (so a position with multiple buys gets the right blended baseline), and returns `{avg_cost, sp500_since_entry, tier1, tier2}`. Optimizer should round the tier prices to whole dollars (or nearest 50¢ for sub-$50 names) for clean broker UI — the difference is negligible.

Do **NOT** use a flat assumption like "+5%" for SP500-since-entry. Each ticker has its own number. The function handles this.

Each session, optimizer:
1. Verifies every non-core held position has a current ladder.
2. Refreshes any stale ladder (e.g., after a position add changed avg_cost, or after a tier fired) — `compute_exit_ladder()` recomputes from the *current* transactions, so a refresh after adds is automatic.
3. After a tier fires, decides whether to roll a fresh tier 2 up (continuing the +10% spacing) or pause until next session.

The ladder lives in `data/order.csv` so the market does the work without requiring an active session.

**Fundamental-break exit** still allows full immediate exit — the entry criteria are dead, no ladder needed.

**Historical note (2026-05-21):** the initial bootstrap of ladders used a flat +5% SP500-since-entry estimate for all positions because `compute_exit_ladder` wasn't written yet. Computed values were within $2-10/share of the orders that were actually placed; user opted to leave the existing orders rather than refresh. From tomorrow onward, optimizer uses the precise function.

### Sell pacing — 2-tier laddered exits

Applies to **all sells**: cap-rebalance trims, exit-trigger trims, and any other proposed sale. Does *not* apply to fundamental-break exits (those sell fully and immediately).

- **2-tier structure:** every proposed sell goes out as **two limit orders at different price points** — a lower-tier (~current price + small premium) and a higher-tier (further premium). Both can be open simultaneously.
- **Sizing is optimizer's judgment**, not hardcoded. Share count per tier depends on the day's opinions, regularizer pressure, position size relative to cap, and the user's per-name conviction. A typical pattern is 1 share at each tier; aggressive trims may go higher, conservative trims lower.
- **Premium levels are also optimizer's judgment.** Typical ranges: tier 1 = current + 1-5%, tier 2 = current + 5-15%, but the actual choice depends on volatility and proximity to recent local highs.
- **Remainder is observed.** Whatever's left after the two tiers is held until the next session, at which point optimizer re-evaluates and may propose another laddered trim if the position is still over cap / still meets the exit trigger.
- **Multi-session rebalance.** A heavily-over-cap position may take several sessions to bring under cap. That's the intended pace — captures upside if the stock keeps running, avoids one-shot regret if the tape reverses, and gives multi-day observation.

For example, a held position might have two sell limit orders at, say, +5% and +15% above the current price — same ticker, different tiers — both sitting in `data/order.csv` until one or both fill.

### Cash discipline

- **Active-sleeve cash floor: 5%.** Below this, do not open new positions until a sale frees up cash. The low floor keeps drag down; the user prefers being deployed over waiting on dips that may not come.
- **Active-sleeve cash ceiling: 30%.** Above this, the strategy is parked — review whether the entry criteria are too restrictive.
- **No forced trades.** If no name passes both rules + opinions on a given day, propose nothing.

### Sleep test

- **No position so large that a -50% drawdown of that name would cost more than 5% of total portfolio.** With 50% active and 20% per-name cap (mean-rev), the math: 50% × 20% × 50% = 5%. Just within sleep test. Tighten the cap if the sleep test gets stricter.

---

## Performance tracking

Each month, compute and log to a `performance.md` or similar:

- Active sleeve return MTD / YTD / rolling 12-month
- VOO (or SPY) return same window
- Active sleeve vs. SP500 spread
- Mean-reversion bucket vs. SP500
- Momentum bucket vs. SP500

If the **active sleeve trails SP500 by more than 3% over a rolling 12-month window**, the strategy is failing and needs revisiting. Don't abandon early; one bad quarter is not signal.

If the **momentum bucket trails SP500 by more than 5% over rolling 12 months**, shrink it to zero and run mean-reversion only.

---

## What this file does NOT contain

- Specific tickers (those come from opinions, filtered through these rules in the optimizer).
- Specific price targets (those come from the online research's analyst consensus citations).
- Macro calls (those come from the online research's market snapshot).
- Conviction levels per name (those come from cross-channel synthesis and the regularizer).

The rules are the *frame*. Opinions fill the frame each day. The optimizer matches names to the frame.

---

## Open items / next discussions

1. **Maximum number of names in active sleeve.** Currently unspecified. Suggestion: 8-12 names total to keep tracking manageable. Want to lock?
2. **Re-deposit policy.** When new cash arrives (paycheck, dividend, etc.), what % goes to core vs. active? Current default: undefined.
3. **Dividend handling.** Reinvest into the position, send to cash float, or send to core? Current default: undefined.
4. **~~Tax sensitivity~~** — **RESOLVED.** Account is a Roth IRA. **All gains are tax-free.** Sales can be made freely without short-term vs long-term capital-gains considerations. Optimizer applies exit triggers symmetrically; no tax-aware modifications.
5. **~~Realized-loss harvesting~~** — **RESOLVED (moot).** Roth IRA, no tax on gains, so no benefit to harvesting losses for tax purposes. Losses are only taken when the fundamental-break exit fires.
6. **~~Earnings-week posture~~** — **RESOLVED.** No special treatment. Regular rules apply through earnings. The fundamental-break exit (already in the rules) handles the only case where an earnings print actually changes the thesis: if revenue and margin both collapse, exit fully. Pre-earnings drawdowns are buying opportunities under the mean-reversion rules; pre-earnings rallies trigger the +10%-above-SP500 trim normally. *No timing around the calendar event.*
7. **News-event posture.** If management changes / regulatory event / etc., default action? Currently: undefined.
8. **Rebalancing.** Does the 50/50 core/active split rebalance, or drift? Currently: drift. Revisit if drift exceeds ±15 pp.
9. **Track-record format.** Where does the monthly performance log live? `journal/performance/`? A spreadsheet? Currently: undefined.
10. **Confidence thresholds in opinions.** Should rules require the online research's confidence to be at least "medium" before a name qualifies? Currently: no explicit minimum.
11. **VOO-dip add (deferred).** A rule for adding 1 share of VOO when VOO dips X% from 52-week high. **Activation conditions:** (a) active-sleeve cash above the 5% floor has accumulated enough to fund a share, AND (b) VOO's share of total portfolio has drifted below 50%. Read today's journal for the current portfolio state to check activation. Revisit when both conditions are within reach.
12. **Personal vetoes happen in the discussion, not in the rules.** Optimizer proposes *every* name that passes the rules, regardless of user history. If the user passes on a name in the discussion (for example, "I don't want to own this one"), the rejection is logged in today's journal under a "Discussion / decisions" section. Tomorrow's optimizer still proposes it if it qualifies — the journal accumulates the user's personal pattern over time but never pre-filters the proposal stream. The rules stay name-independent; personal judgment stays in chat.

Discuss and lock these as we go.
