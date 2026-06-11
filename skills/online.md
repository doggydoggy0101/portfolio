# Skill: Online research

An independent, objective read of the current state from primary web sources. Built to be a neutral counterweight to opinionated YouTuber content. **Never reads or references `skills/youtube.md`, the `skills/youtube/` profiles, `journal/*.md` YouTuber sections, or any third-party commentary tracked elsewhere.** The whole point is independence — if it ever cites a tracked YouTuber, the value of the section collapses.

## Process

Each morning, before optimizer runs, produce three sections in today's journal:

1. **Market snapshot** — macro state from primary data.
2. **Held positions** — one entry per ticker in `data/ira/transactions.csv` (active holdings).
3. **Watchlist + pending orders** — one entry per ticker in `data/watchlist.txt`, plus any ticker in `data/ira/order.csv` (pending orders) that isn't already covered above. Pending-order tickers matter because they're names the user has *already decided* to act on; their state needs fresh research even if they're not in the watchlist file.

The research scope = union of (holdings ∪ watchlist ∪ pending-order tickers). Deduplicate by ticker.

Append to today's journal under `# Independent research`. The full journal-section order (per CLAUDE.md daily flow) is: `# Reconciliation` → `# Portfolio state` → `# YouTube research` (with cross-channel synthesis subsection) → `# Independent research` → `# Regularizer` → `# Optimizer session`. Independent research is the last objective input before regularizer and optimizer consume the journal.

## Per-ticker schema

```markdown
### TICKER — $price (X% from ATH, Y% YTD)
**Last 24-48h news:** one or two lines, with source URL.
**Latest reported quarter:** revenue growth, margins, FCF, anything material. Quarter date.
**Analyst consensus:** average PT, # buys / holds / sells. Source.
**Bull case (1 sentence):** the strongest single argument for owning.
**Bear case (1 sentence):** the strongest single argument against.
**Confidence: high / medium / low.** What would change this view (1 sentence).
```

If a ticker has no material news in the last 24-48h, the section is still produced — just shorter. Consistent shape day-to-day matters for diffability.

## Sources (in priority order)

1. **Primary** — company IR pages, SEC EDGAR (10-Q, 10-K, 8-K), earnings call transcripts on the company's website.
2. **Reuters / Bloomberg / FT / WSJ / Yahoo Finance / CNBC** — for breaking news, analyst consensus, macro data. Cite the URL inline.
3. **Government / Fed primary sources** for macro: BLS (CPI, jobs), BEA (PCE, GDP), Fed (FOMC statements, dot plot), Treasury (yields).
4. **Sentiment indicators** — direct from the source: CBOE for VIX, CNN for F&G, AAII.com for AAII survey, NAAIM.org for NAAIM. Use the actual reading, not someone's commentary.

**Never** YouTube. **Never** cite the YouTubers tracked in `skills/youtube/`, even indirectly. If you find yourself thinking "X said Y," stop and re-derive from primary data.

## Tone discipline

- **Bull AND bear, always both.** This is the load-bearing rule that keeps the section honest.
- **Confidence labels.** High / medium / low. Default low — most claims about future prices should be low-confidence.
- **Falsifiability.** Every bull/bear pair includes "what would change this view." If you can't write one, the view is too vague.
- **No invented price targets.** Only cite analyst consensus PTs from a real source. Don't compute your own "intrinsic value."
- **No editorial.** No "I think," no "looks attractive," no "exciting story." State facts and frame as bull/bear.
- **Cite inline.** Every factual claim that isn't from the local `data/` files needs a URL.

## What this skill does NOT do

- Does not propose orders. That's `optimizer.md`.
- Does not weight YouTubers. The whole point is to ignore them.
- Does not generate themes / sector overlays in v1. Per-ticker is enough.
- Does not edit other journal sections.

## Iteration

This skill will be modified as we learn what's useful. Things on the table:

- Adding a **sector / theme overlay** if per-ticker becomes too granular.
- **Earnings-day deep-dives** when a held position reports.
- **Conditional skip** of held tickers with no news (vs always producing a stub).
- **Macro charts** if we add a chart-rendering tool.
- A **track record** — log each "high-confidence" call and revisit it monthly to calibrate.
