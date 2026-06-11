# <Creator Name> — @<handle> (slug: `<slug>`)

> **This is the template / structure example.** It is the only file in this folder
> that is committed to git. Real channel profiles live in `youtube_<slug>.md` files
> alongside it and are **gitignored** — each user picks their own creators, so the
> public project ships the *mechanism* (this template + `skills/youtube.md`), never
> *whose* views are tracked.
>
> To add a creator: copy this file to `youtube_<slug>.md`, fill it in, and the
> `skills/youtube.md` daily process will pick it up automatically (it reads every
> `youtube_*.md` in this folder). `<slug>` is the short id passed to
> `python -m src.youtube "@handle" --label <slug>`.

**Style:** One-paragraph description of how they invest — long/short, concentrated/diversified, trading cadence, account size if public, any signature moves (hedges, DCA, trims).

**Time horizon:** Typical holding period and how tactical vs. structural they are.

## Worldview

Numbered list of their core, repeated theses (the lenses they see the market through). One per recurring framework — e.g. a master sector thesis, a macro stance, a contrarian call, a narrative pattern. Capture what they actually argue, not your opinion of it.

1. **<Thesis headline>.** What they claim and why; the names attached to it.
2. ...

## Trust more (their strong points)

- Where their analysis is rigorous / data-grounded / internally consistent — the parts worth using as input.

## Discount (their weak points)

- Where they're biased, sloppy, unfalsifiable, or talking their book — the parts to down-weight.

## Sector preferences

| Sector | Stance | Names they track |
|---|---|---|
| <sector> | ✅ strong / ⚠️ selective / ❌ avoid | TICK, TICK |

## Signal-weighting rules (operational)

- **N+ videos, same thesis** → strong signal (surface in optimizer).
- **fewer / drive-by** → soft signal or noise.
- **New buy / trim / explicit avoid** → how to adjust the signal.
- **Sponsored content** → how to treat it (usually: discount entirely).
- **Cross-channel agreement / disagreement** → flag for own research.

## Vested-interest flags

- Concentrations, owned products, affiliate/sponsor relationships, paid funnels — anything that biases what they say. Used to discount accordingly.

## Highest-conviction names (<Creator>)

Last updated: YYYY-MM-DD. Add a name when it appears in ≥3 of their last 10 videos with a consistent thesis (sponsored picks don't count); drop when missing from the last 10 with no other reaffirmation. **This table is what `skills/rule.md` reads** to check "is this creator favorable on TICKER" — keep it fresh.

| ticker | stance | thesis (one line) | last reaffirmed |
|---|---|---|---|
| TICK | strong buy / buy / watch / avoid | one-line current thesis | YYYY-MM-DD |

Names previously tracked but **not** reaffirmed in the last 10 videos (eligible for drop): ...
