# Skill: YouTube research

Pull, summarize, and weight the views of a small set of trusted YouTubers as input to the morning loop. Each tracked creator has a **profile file** at `skills/youtube/youtube_<slug>.md`; **read the relevant profile before summarizing that channel's videos** — it's the lens.

## Channel profiles (where the creators are defined)

The tracked creators are **not listed in this file**. Each one is a `youtube_<slug>.md` file in `skills/youtube/`. That folder is **gitignored** — the creator set is private, chosen per user; this project ships only the mechanism, never whose views are tracked.

- **To discover the tracked channels:** read every `skills/youtube/youtube_*.md`. Each file's H1 header gives the creator name, `@handle`, and `slug` (e.g. `# Creator Name — @handle (slug: xx)`).
- **`skills/youtube/template.md`** (committed) documents the required structure of a profile file. To add a creator, copy it to `youtube_<slug>.md` and fill it in — no code or rule change needed.
- Each profile file is a small **living database** for that creator: worldview, trust/discount notes, sector table, signal-weighting rules, vested-interest flags, and a **Highest-conviction names** table. The conviction table is what `skills/rule.md` reads — keeping it fresh is load-bearing for the optimizer.

## Process (every morning, before optimizer runs)

1. **Find the last journal date.** `ls journal/` → pick the latest `YYYY-MM-DD.md` other than today's. Call this `LAST`. If no prior journal, default `LAST = today - 14 days`.

2. **For each tracked channel** (one `youtube_<slug>.md` per creator in `skills/youtube/` — read them all), pull new transcripts:

   ```bash
   python -m src.youtube "@HANDLE" --since LAST --dump /tmp/yt_<slug>/ --label <slug>
   ```

   - `<slug>` and `@HANDLE` come from that creator's profile-file header.
   - One transcript file per video at `/tmp/yt_<slug>/<slug>_NN_<videoid>.txt`.
   - First two lines of each file = title + published date + URL.
   - If a transcript is missing (`has_transcript: false` in stdout JSON), skip — note it in the journal as "no transcript available."

3. **Summarize each video in parallel via subagents.** One `general-purpose` agent per transcript file. Prompt template:
   - Tell the agent **which creator's profile applies** (reference the relevant `skills/youtube/youtube_<slug>.md`).
   - Use the per-video output schema below.
   - Cap each summary at ~250 words.

4. **Append to today's journal** under a `# YouTube research` section (H1). Structure:
   - `# <Creator name> — @handle` (H1) per creator — the per-channel sections are H1 so they're easy to scan.
   - Cross-cutting themes for that creator across the new batch (3-5 bullets, H2).
   - Per-video summary blocks (H3, using the per-video output schema below).
   - End with **highest-conviction names this batch** for that creator, ranked by repetition.
   - After all per-creator sections, write **`# Where the channels agree`** and **`# Where the channels disagree`** as the cross-channel synthesis (H1 each). These are *contextual* journal sections — not voting inputs (per `skills/rule.md`).

5. **Cross-channel synthesis is written by this skill** at the end of the YouTube section, derived from the per-creator conviction tables. Rule-relevant only as context — *not* a separate vote (rule.md counts per-creator tables, not the synthesis).

### When there are no new videos

Most channels post weekly or less; on any given day most channels will have 0 new videos. When a channel has no new videos since the last journal date:
- **Do not roll over** the previous journal's content into today's. Each creator's profile file (`skills/youtube/youtube_<slug>.md`) is the canonical conviction state; duplicating it into the journal creates noise.
- Today's journal section reads: `**[Creator name]:** No new videos since [last journal date]. Conviction state in skills/youtube/youtube_<slug>.md is current.`
- Optimizer and rules read the conviction tables in the profile files when they need to know what a creator currently thinks. Today's journal does not need to mirror the profile content.

6. **Maintain each creator's "Highest-conviction names" table** in their profile file (`skills/youtube/youtube_<slug>.md`). This table is what `skills/rule.md` reads to check "is this creator favorable on TICKER" — so keeping it fresh is load-bearing for the optimizer.
   - **Add a ticker to the table** when it has appeared in **≥3 of the creator's last 10 videos** with a consistent thesis (no flip-flops, e.g., from buy to sell within the batch). Sponsored-video picks do **not** count toward the 3 — they're framed as product output, not organic conviction.
   - **Drop a ticker from the table** when it has not been mentioned in the creator's last 10 videos *and* there's no other reaffirmation visible. Conviction has lapsed.
   - **Update stance** (buy / strong buy / watch / avoid) when the latest video changes the thesis.
   - Treat the profile as a small living database. A daily run only needs to touch the rows that changed.

## Per-video output schema

```markdown
### <video title> — <YYYY-MM-DD>
**Thesis (1-2 sentences):** ...
**Tickers mentioned:**
- TICKER — stance (buy/sell/watch/avoid/discuss) — one-line reasoning
**Macro view:** rates / Fed / inflation / recession / market direction — only what's said.
**Key numbers / predictions:** specific price targets, percentages, dates. None → "none."
**Caveats:** self-contradictions, hedged claims, opinion-as-fact, paid-promo embedded.
```

## Calibration (applies to all channels)

- Treat clickbait titles ("GREATEST STOCK EVER", "EMERGENCY") as **noise**. Read the actual thesis inside.
- A name mentioned **across multiple videos with the same thesis** is a stronger signal than a one-off pick.
- A creator buying a name **they didn't already own** is a stronger signal than another mention of an existing holding.
- Specific short-term price targets ("X to $400 in 4 months") = ignore the timeline, keep the direction.
- Paid-group / Patreon / course promotion is universal — strip it out.
- **Where creators disagree, flag it explicitly in the optimizer.** Disagreement is information, not noise.
