# Skill: optimizer

The final step of the daily flow. Reads all prior journal sections + rules + portfolio state, generates a list of proposed order adjustments, walks them with the user one at a time, appends agreed orders to `data/ira/order.csv`, and logs the full session to today's journal.

Assumes by the time it runs:
- Today's journal has `# Reconciliation`, `# Portfolio state`, `# YouTube research` (with cross-channel synthesis subsections), `# Independent research`, `# Regularizer` sections.
- `data/ira/transactions.csv` has been updated by reconcile.md to reflect confirmed fills.
- `data/ira/order.csv` has been updated by reconcile.md (filled rows removed, still-pending rows kept).
- `src/position.py` is available with `compute_exit_ladder(ticker)` for precise per-position 2-tier sell limits.

## Inputs

- `skills/rule.md` — constraints, exit triggers, position caps, hard lines + conviction-read sizing, regularizer veto rule.
- `skills/youtube/youtube_*.md` — per-creator conviction tables (the "current mindset" of each tracked YouTuber).
- Today's journal — all prior sections.
- Previous journal — one-day-back context (rejected proposals, prior session's decisions, recurring user concerns).
- `data/ira/transactions.csv` — holdings, cost basis, realized P&L.
- `data/ira/order.csv` — pending orders not yet filled.
- `data/watchlist.txt` — candidate tickers.

## Process

### 1. Compute the candidate universe

Tickers that warrant consideration today:
- **Held positions** — every ticker the user currently owns.
- **Watchlist tickers** — every non-held ticker on the watchlist.
- **Pending-order tickers** — if a name has an open order, check whether the order should be modified or canceled.
- **New buy ideas to surface proactively** — names that look interesting *today*, even if not held or watchlisted: creators' conviction-table picks, names with a material drawdown **and** analyst upside in today's online research, recent earnings beats with raised targets. The optimizer's job is to **bring candidates to the table**, not only react to the user's. Surface a ranked shortlist as options (see step 3a). It is fine — expected on most days — for the shortlist to be short or empty; **never manufacture an idea to fill it.**

### 2. Apply rules to each candidate

Walk every ticker through the rule checks defined in `skills/rule.md`:

- **Position size check.** Over cap? At cap? Room to add? Cap violations are *warnings* (per rule.md cap-as-warning rule), not forced trims — surface them and offer an *optional* accelerated trim; the default exit ladder will rebalance naturally otherwise.
- **Default exit ladder maintenance.** For every non-core held position, verify a current 2-tier sell ladder exists in `data/ira/order.csv`. Call `compute_exit_ladder(ticker)` for the precise tier 1 / tier 2 prices. Propose new ladders for positions without one; propose refreshes when avg_cost has changed (e.g., after an add).
- **Hard lines (pass/fail).** Per rule.md: material drawdown, quality, no earnings collapse, **not overvalued** (analyst PT ≥ price + 10% — a bright line), and the regularizer top-flag veto. If any fails, it's not actionable — but keep it on the discussion slate, marked blocked + which line failed.
- **Conviction read → size.** Once the hard lines pass, weigh the favorable opinion evidence (creators who *cover* the name + degree of analyst upside; a creator who doesn't cover it counts as nothing). Translate to a **strong / moderate / thin** read and size accordingly (full ~5% / starter ~2.5% / toe-hold ~1-2%). State the weighting in writing. Conviction sets size, not yes/no.
- **Regularizer veto.** Parse `**Top flag (hard veto): TICKER**` from today's regularizer section. If a candidate ticker matches the top flag, disqualify it.
- **Quality filter** (mean-reversion) — does the entry criterion hold?
- **Catalyst** (momentum) — fresh driver?
- **Exit trigger math** (for held) — position return ≥ SP500-since-entry-return + 10%? Use `compute_sp500_since_entry(ticker)` from `src/position.py` for the precise per-position SPY-since-entry; do NOT use a flat assumption.
- **Add trigger** (for held, not at cap) — average cost down ≥10% with quality intact?
- **Fundamental-break exit** — has the quality filter from entry stopped holding?

Each ticker either generates a proposal or is silently skipped. Optimizer judges sizing within the caps defined in rule.md.

### 3. Generate the proposal list

For each ticker that warrants action, build a proposal with:
- **Action** — BUY / SELL / TRIM / CANCEL / MODIFY
- **Rule that fired** — exactly which clause in rule.md generated this proposal
- **Conviction read** — strong / moderate / thin, naming which sources are favorable and how they're weighted
- **Case for / case against** — the bull case in one or two lines, then the pushback (the risk if it's wrong). Every idea carries both.
- **Regularizer status** — top flag? warning? neither?
- **Suggested size** — scaled to the conviction read, within the position cap
- **Suggested price** — limit price (often pegged to recent close or analyst consensus PT)
- **Suggested expires** — typically **180 days** (matches the user's broker GTC default and existing orders). Optimizer can shorten for time-sensitive proposals; users can override per proposal.

### 4. Open with the full slate, then drill in

Lead with **two groups** so the user always has options to *consider*, not just defenses to react to:

```
=== Today's slate ===

A) Ideas to consider — new buys (options, not mandates):
  1. <TICKER> — <one-line setup> — conviction <strong/moderate/thin>, ~X% — [actionable]
  2. <TICKER> — <one-line setup> — [blocked: <hard line that failed>] (discussion only)
  ...
  (If nothing compelling: "No strong new buys today. Closest is <TICKER>, not there because <reason>." Do NOT manufacture ideas.)

B) Position management — held / orders:
  1. <ACTION> <TICKER> — <one-line summary>
  ...
  (If none: "Holdings in compliance; no management actions today.")

---
Item 1 of N: <ACTION> <TICKER>

**Why:** <which rule fired, with the math — or, for a new idea, the setup>
**Conviction read:** <strong / moderate / thin — which sources favorable, how weighted>
**Case for / against:** <bull case> // <the pushback>
**Regularizer:** <top flag / warning / clear>
**Suggested size:** <amount scaled to conviction, with cap check>
**Suggested price:** <limit>
**Suggested expires:** <date>
**What would change this view:** <falsifiable condition>

→ Awaiting user response (yes / no / modify / discuss).
```

The Ideas group is the new contract: the optimizer **proactively recommends** candidates worth a look (with the case against attached) — the user no longer has to invent buys just to get a pushback. Recommending is not urging: every idea ships with its own dissent, and "nothing compelling today" is a valid, common slate.

### 5. Walk one proposal at a time

For each proposal, take user response:

- **Yes** — lock the decision. Move to next.
- **No** — lock the rejection (with optional reason). Move to next.
- **Modify** — user adjusts size/price/expires. Confirm the modified version. Lock. Move to next.
- **Discuss** — engage substantively. Don't push back hard, but answer questions and surface relevant data from the journal. Once the user is ready, ask yes/no/modify.
- **Override** — when the user directs a buy that **fails a hard line** (overvalued, regularizer veto, below the cash floor) or goes against the conviction read, do it if they insist — it's an advisory system, the user's call — but **log it as an explicit override**, not a silent rule-break: name which line it broke, the user's reason, and the optimizer's one-line dissent. Overrides are *tracked* (see below), not forbidden.

After proposal N is decided, present proposal N+1. **Do not batch.** Sequential.

**Overrides are a feature, not a failure.** They give the user agency while keeping the discipline visible: because each is logged with its blocker and the dissent, the **monthly/quarterly review** (per rule.md "revisit based on what the journal track record shows") can ask the only question that matters — did the overrides beat just holding VOO? That turns friction into evidence, and tells us whether to relax a rule or trust it more.

### 6. End-of-session summary

When all proposals have been decided, write a `# Optimizer session` block to today's journal:

```markdown
# Optimizer session — YYYY-MM-DD

## Proposed adjustments
1. ...
2. ...
3. ...

## Decisions
1. **<ACTION> <TICKER>** ✓ Agreed [or ✗ Rejected, or ✎ Modified] — <one-line reason if relevant>
2. ...
3. ...

## Discussion notes
- <any substantive points raised during the chat>

## Overrides (if any)
- <TICKER> — broke <which hard line / against conviction read>; user reason: <...>; optimizer dissent: <one line>

## Appended to data/ira/order.csv
- date_added=YYYY-MM-DD, ticker=..., action=..., price=..., quantity=..., expires=..., note=...
- (one line per agreed order)

## Not appended
- <TICKER> — user said no, reason: <if given>
- <TICKER> — user said modify but never finalized the new terms
```

### 7. Write to data/ira/order.csv

For every agreed (or modified-then-agreed) proposal, append a row to `data/ira/order.csv`. Columns: `date_added,ticker,action,price,quantity,expires,note`.

- `date_added` — today's date.
- `note` — optional brief reason, e.g., "exit trigger fired" or "dip entry per rules".

Cancels remove the existing row, not append. Modifications can either be implemented as remove-and-append or as an in-place edit.

## Proposal generation rules

A proposal must always include:

- Concrete **action**, **size**, **price**, **expires**.
- The exact **rule clause** from `skills/rule.md` that justifies the proposal (cite the section header, e.g., "Mean-reversion → Exit trigger").
- The **opinion vote count** with named sources.
- A one-sentence **falsifiability statement** — "what would change this view."

A proposal must never:

- Recommend an action that violates a hard constraint (long-only, no options, US-only, etc.).
- Exceed the per-name position cap.
- Push cash below the 5% floor.
- Include a vetoed ticker (top flag in regularizer).
- Add to a momentum position (momentum is one-shot per rule.md).

## Persona / tone in chat

- **Direct.** State the proposal. State the rule. State the opinion count. Move on.
- **Cite, don't editorialize.** Bull/bear framing comes from journal sections, not the optimizer's own voice.
- **Don't push.** If user says no, accept and move on. No "are you sure?"
- **Engage on discuss.** When user asks why, surface relevant data from journal sections (cite which section / which YouTuber / which online-research bullet). Don't invent reasoning.
- **No emoji unless user uses them first.**
- **Don't propose new rules during the chat.** Rule changes are out-of-band (separate sessions where the user explicitly wants to revise rule.md).

## What optimizer does NOT do

- Does not fetch new data — everything it needs is already in today's journal + skills/youtube/*.md + data/ira/*.csv.
- Does not run other skills.
- Does not place orders at the broker — output is just `data/ira/order.csv` rows.
- Does not modify `skills/rule.md`, `skills/youtube.md`, the `skills/youtube/` profiles, or any other skill file.
- Does not propose vetoed names.
- Does not auto-decide. Every order requires explicit user yes.
- Does not log discussion turn-by-turn in journal. Only the end-of-session summary is journaled.

## Sleep test / safety

- If applying any proposal would put **active-sleeve cash below the 5% floor**, the proposal is deferred ("waiting for cash to rebuild from a trim").
- If proposing **adds** to a position, the math respects the cap and the 3-add limit (per rule.md mean-reversion).
- If a held position is **over the per-name cap**, the optimizer **surfaces the warning every session** and **offers an optional accelerated trim** (lower-priced tier than the default ladder). It does **not** force a trim — without explicit user yes, the position rides until the default exit ladder fires. (Per rule.md cap-as-warning rule.)
- The regularizer top flag is a hard veto, no override.

## In-session re-open behavior

If the user closes mid-session and re-opens later the same day:
- CLAUDE.md sees today's journal exists → reads it → finds in-progress `# Optimizer session` block (e.g., 2 of 3 proposals resolved).
- Offer: "We were partway through optimizer; proposal 3 is still pending. Pick up there, or restart?"
- If continue: replay proposal 3 from the journal.
- If restart: clear the partial session block and re-run optimizer from scratch (uses the same journal context, so prior research isn't re-done).

## Iteration ideas (post-v1)

- **Track record per proposal type** — does mean-reversion sleeve actually beat SP500? Momentum?
- **Pre-earnings flag** — surface "earnings in N days" as informational, without changing rules.
- **Multi-name dependencies** — e.g., "buy CRM needs cash; propose TSLA trim first, then ask about CRM."
- **User-rejected pattern detection** — if the user has rejected CAKE in 5 of the last 5 sessions, optimizer can note that pattern (without filtering) so the user sees their own consistency.
- **Confidence-weighted sizing** — high-confidence rule matches get larger initial sizes within the cap; low-confidence get smaller.
