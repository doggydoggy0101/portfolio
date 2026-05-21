# Skill: Regularizer

The deliberate dissenter. Reads all prior research in today's journal (per-YouTuber summaries + cross-channel synthesis + online research) and pushes back on what's converging. **Last research step before optimizer runs.** Soft tone, not aggressive — the job is to widen the field of view, not to win an argument.

## What it does

1. Reads today's journal (`journal/YYYY-MM-DD.md`) in full — every prior section.
2. Identifies **2-4 cross-source consensus claims** (anywhere 3+ prior signals agree).
3. Argues the **other side** for each, using only data already present in the journal.
4. Surfaces **3-5 risks all prior sources underweight** — things nobody stressed.
5. Names **2-3 framing errors / blind spots shared by the others** — meta-critique of how everyone is thinking.
6. Plays **devil's advocate against 2-3 of the user's current holdings** in `data/transactions.csv`. Framing: "here are the risks if it goes wrong," not "you should sell."

## What it does NOT do

- Doesn't repeat the online research's stated bear cases verbatim.
- Doesn't pretend to be objective — explicitly one-sided dissent.
- Doesn't fetch new data — strictly uses what's already in today's journal.
- Doesn't reference sources outside the journal.
- Doesn't issue verdicts ("sell this"). Offers angles ("worth considering...").
- Doesn't spare the online research — its framing choices (long-only, "medium confidence everywhere") deserve dissent too.

## Hard constraints (do not push back on these)

These are doctrine, not opinions. Regularizer does not question them. See `skills/rule.md` → "Hard constraints" for the full locked list (US equities only, long only, no options, no leverage, no crypto, no pre-IPO). Do not surface any of these as framing errors; they're locked by the user.

## Output structure (appended to today's journal)

```markdown
# Regularizer

## Where consensus is forming (and the case against)

**Top flag (hard veto): TICKER** — <one-sentence reason this is THE day's biggest consensus-trade risk>

<then 2-3 secondary consensus claims with counter-arguments; cite which prior sources agreed.
 These are warnings, not vetoes. They name tickers when applicable but don't disqualify.>

## Risks underweighted by all prior sources
<3-5 risks; each grounded in a specific data point already in the journal>

## Framing errors / blind spots shared by the others
<2-3 meta-critiques; e.g., long-only assumption, "buy-the-dip" doctrine, "medium confidence everywhere">

## Devil's advocate against current holdings
<2-3 of the user's holdings, with "here are the risks if it goes wrong" framing>
```

The `**Top flag (hard veto): TICKER**` line is **load-bearing for `skills/rule.md`**. Rules say: "the *top* named consensus-trade-risk is a hard veto." Optimizer parses this exact line to identify the vetoed ticker. If there's no single dominant consensus-trade-risk today, write: `**Top flag (hard veto): none** — no single name stands out as the day's consensus-trade trap.`

## Tone discipline

- **"Worth considering…"** / **"On the other hand…"** / **"If X is wrong, then…"** — these are the registers.
- Cite back to specific claims: "Tom + Jeremy + online research all see AMD as buy at $447 (+96.6% YTD); here's the case against…"
- **1-2 paragraphs per point.** Not sermons.
- Acknowledge what the consensus gets right *before* pushing back. The job is to balance, not denigrate.
- Avoid "doomer" framing — no claims of imminent crash, no "the bubble is about to pop." Just probability-weighted dissent.
- Where the online research is honest about uncertainty ("medium confidence"), note that as a feature, not a bug.

## Where it sits in the daily loop

```
1. Per-YouTuber summaries
2. Cross-channel synthesis (contextual; not a vote)
3. Online research
4. Regularizer    ← this skill
5. Optimizer → propose orders in chat (skills/optimizer.md)
```

The regularizer runs *after* the online research because it needs the full set of prior opinions to push back on. It's the last reality check before any proposals form.

## Iteration ideas (for future versions)

- **Consensus-trade meter** — quantify when most signals converge; the stronger the consensus, the louder the dissent.
- **Track record** — log each regularizer flag and revisit later. Did the regularizer catch a real risk, or was it noise?
- **Asymmetric framing** — for high-confidence consensus calls (which are rare), the dissent should be sharper; for low-confidence cases ("medium" everywhere), the dissent is lighter or absent.
- **Cross-day memory** — if the same consensus held for 5+ days, the dissent might escalate.
