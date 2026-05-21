# Skill: YouTube research

Pull, summarize, and weight the views of a small set of trusted YouTubers as input to the morning loop. Each YouTuber has a profile below; **read the relevant profile before summarizing that channel's videos** — it's the lens.

## Process (every morning, before optimizer runs)

1. **Find the last journal date.** `ls journal/` → pick the latest `YYYY-MM-DD.md` other than today's. Call this `LAST`. If no prior journal, default `LAST = today - 14 days`.

2. **For each tracked channel** (see Profiles below), pull new transcripts:

   ```bash
   python -m src.youtube "@HANDLE" --since LAST --dump /tmp/yt_<slug>/ --label <slug>
   ```

   - `<slug>` is the short identifier (e.g. `fe` for Financial Education).
   - One transcript file per video at `/tmp/yt_<slug>/<slug>_NN_<videoid>.txt`.
   - First two lines of each file = title + published date + URL.
   - If a transcript is missing (`has_transcript: false` in stdout JSON), skip — note it in the journal as "no transcript available."

3. **Summarize each video in parallel via subagents.** One `general-purpose` agent per transcript file. Prompt template:
   - Tell the agent **which YouTuber's profile applies** (paste/reference the relevant section).
   - Use the per-video output schema below.
   - Cap each summary at ~250 words.

4. **Append to today's journal** under a `# YouTube research` section (H1). Structure:
   - `# <YouTuber name> — @handle` (H1) per YouTuber — the per-channel sections are H1 so they're easy to scan.
   - Cross-cutting themes for that YouTuber across the new batch (3-5 bullets, H2).
   - Per-video summary blocks (H3, using the per-video output schema below).
   - End with **highest-conviction names this batch** for that YouTuber, ranked by repetition.
   - After all per-YouTuber sections, write **`# Where the three agree`** and **`# Where the three disagree`** as the cross-channel synthesis (H1 each). These are *contextual* journal sections — not voting inputs (per `skills/rule.md`).

5. **Cross-channel synthesis (`# Where the three agree` / `# Where the three disagree`) is written by this skill** at the end of the YouTube section, derived from the per-YouTuber conviction tables. Rule-relevant only as context — *not* a separate vote (rule.md counts per-YouTuber tables, not the synthesis tables).

### When there are no new videos

Most channels post weekly or less; on any given day most channels will have 0 new videos. When a channel has no new videos since the last journal date:
- **Do not roll over** the previous journal's content into today's. The conviction tables in this file (`skills/youtube.md`) are the canonical state; duplicating their content into the journal creates noise.
- Today's journal section reads: `**[Channel name]:** No new videos since [last journal date]. Conviction state in skills/youtube.md is current.`
- Optimizer and rules read the conviction tables in this file when they need to know what the YouTuber currently thinks. Today's journal does not need to mirror the profile content.

6. **Maintain each YouTuber's "Highest-conviction names" table** in their profile section below. This table is what `skills/rule.md` reads to check "is this YouTuber favorable on TICKER" — so keeping it fresh is load-bearing for the optimizer.
   - **Add a ticker to the table** when it has appeared in **≥3 of the YouTuber's last 10 videos** with a consistent thesis (no flip-flops, e.g., from buy to sell within the batch). Sponsored-video picks (e.g., Nicolas's #moomoo episodes) do **not** count toward the 3 — they're framed as product output, not the YouTuber's organic conviction.
   - **Drop a ticker from the table** when it has not been mentioned in the YouTuber's last 10 videos *and* there's no other reaffirmation visible. Conviction has lapsed.
   - **Update stance** (buy / strong buy / watch / avoid) when the latest video changes the thesis.
   - Treat the profile as a small living database. Daily run only needs to touch the rows that changed.

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
- A YouTuber buying a name **they didn't already own** is a stronger signal than another mention of an existing holding.
- Specific short-term price targets ("X to $400 in 4 months") = ignore the timeline, keep the direction.
- Paid-group / Patreon / course promotion is universal — strip it out.
- **Where YouTubers disagree, flag it explicitly in the optimizer.** Disagreement is information, not noise.

---

# Profiles

## Jeremy Lefebvre — @FinancialEducation (slug: `fe`)

**Style:** Long-only US equities. Concentrated public account (~$3.5M). Holds 12-20 names. Adds weekly via DCA. Sells rarely; trims occasionally. Uses leveraged inverse ETFs (TSLZ) for short-term hedges.

**Time horizon:** 3-5 years on most picks, 10+ on a few ("AMZN forever"). Will trade tactically with VIX/oil/Fed catalysts on the margin.

### Worldview

1. **Bullish on AI, but Mag 7 is capex-constrained.** Loves the AI infrastructure layer (AMD especially — escalating targets, $1,000-$2,000 multi-year, max-bull $5T cap "bigger than NVDA") and SaaS-as-agent-substrate (CRM, NOW, ADBE; NOW is currently his favorite of the three). Has *trimmed* META and GOOGL because $125-200B capex will compress FCF/EPS for years even as revenue keeps growing — though he gives AMZN/GOOGL/MSFT a pass when cloud accelerates (AWS +28%) and singles out META for capex with "no clear payoff."
2. **"Generational opportunity in SaaS"** — repeats monthly. Fwd P/E 10-25 + 15-25% revenue growth = his sweet spot. CRM (fwd P/E 12-14), NOW (~22-25), ADBE (~10-11) are the trio.
3. **Beaten-down consumer brands are a separate thesis.** NKE, ELF, EL, CELH, BBWI, CAKE, RVLV, WYNN, HNST — cycle/sentiment trade, 3-year horizon, brand-moat framing. **Not** an AI-rotation play; it's a rate-cut + sentiment-recovery play. Frames it as "37% of Russell 3000 in >30% drawdown; semis carry the tape; capital rotates here when semis top in 2026-2027."
4. **Money-market overhang is the macro bull case.** $8.2-8.5T sitting in money-market funds heading to $9-10T = structural buying pressure that prevents real crashes and forces capital into equities once Fed cuts. This is the floor under his "no recession" framing.
5. **Crypto: skeptical of the current cycle.** BTC down ~35% from ATH, ETH ~50%+. Won't buy HOOD until BTC bottoms. Avoids COIN, MSTR.
6. **Macro: kangaroo decade, not crash.** Sees sideways volatility around a slowly rising index. No recession base case. VIX is his buy signal (>25 buy, >30 amp, >50 all-in). SoFi has been graduated to a featured long-term compounder ("next Palantir," $50 in 5y / $100+ long-term).

### Trust more (his strong points)

- Tracks SaaS valuations diligently: fwd P/E, FCF, revenue growth, dollar amounts of buybacks.
- Consumer-brand turnaround thesis is internally consistent and fundamentals-grounded.
- Position sizing on long-term picks is disciplined — slow DCA, doesn't chase.
- Names he repeats across 6+ videos with the same thesis = high-conviction reads.

### Discount (his weak points)

- Short-term price targets ("AMD $400 in 4 months") are bravado. Trust direction, ignore timeline.
- BTC bottom predictions are unfalsifiable and recycled.
- Every drawdown is reframed as "buy the dip" — no mechanism to flag a real bear market.
- "Bull/base/bear probability 70/15/15" style claims are made-up precision.
- Heavy self-promotion of paid private group (thousandx.com) embedded throughout — strip it.
- Personally talks his book on RH and brands he likes as a customer (BBWI).

### Sector preferences

| Sector | Stance | Names he tracks |
|---|---|---|
| SaaS / enterprise software | ✅ strong | CRM, NOW, ADBE, INTU, PANW, CRWD |
| Consumer brands (beaten down) | ✅ strong | NKE, ELF, EL, CELH, BBWI, CAKE, HNST, RVLV |
| Semis (secular AI) | ✅ strong | AMD ; NVDA neutral |
| Financial services | ✅ moderate | AXP, SOFI, PYPL |
| Mag 7 hyperscalers | ⚠️ owns cautiously | META, AMZN ; trimming GOOGL |
| Consumer staples / retail | ⚠️ selective | WMT avoid (overvalued) |
| Memory / commodity semis | ❌ avoid | MU |
| Crypto-adjacent equities | ❌ avoid for now | HOOD, COIN, MSTR |
| International | ❌ avoid | none |
| Tesla | ❌ short via hedge | TSLZ |

### Signal-weighting rules (operational)

- **6+ videos, same thesis** → strong signal. Surface as a candidate in the optimizer.
- **3-5 videos, same thesis** → soft signal. Note in journal; research before proposing.
- **1-2 videos, drive-by mention** → noise unless he explicitly *buys* it (new position).
- **He buys a name he didn't already own** → bump signal one tier up.
- **He sells/trims a name he held heavily** → strong signal in *the other direction*; surface explicitly.
- **He explicitly avoids / calls out a name** → counter-signal; useful for filtering watchlist.

### Vested-interest flags

- His public account is mostly disclosed in each video — when he says "I bought $X today," that's an actual position change, weight accordingly.
- His paid group (thousandx.com) is pitched heavily — anything *exclusive* to the paid group ("members got this first") is unverifiable; downgrade.

---

## Tom Nash — @TomNashTV (slug: `tn`)

**Style:** Long-only US equities. Hyper-concentrated: ~40% PLTR / 40% SPY / 20% TSLA (sometimes phrased as 60% PLTR+TSLA / 40% SPY). Buy-and-hold, DCA, double-down on dips. Trims winners on a rule (10% at +50%, 20% at +100%). Channel positions itself as "boring, structured, anti-trader."

**Time horizon:** 5-25 years. Cites Vanguard millionaire study (87% deployed, 92% long-term, 1% panic-sold COVID). Most of his price targets are 5y horizons.

### Worldview

1. **PLTR + TSLA are flagships.** PLTR appears in 9/10 recent videos with bear/base/bull of $150/$493/$1,231 over 5y. He's been long since 2020/2022, defends every drawdown. TSLA is co-flagship with a robotics-bigger-than-AI thesis.
2. **AI picks-and-shovels via an 8-layer infrastructure stack.** Original framing: compute (NVDA, AMD), foundry (TSM), litho (ASML), memory (MU), networking (ANET), data/observability (MDB, DDOG), cybersecurity (CRWD, ZS), power (CEG, BE, VRT), cloud/ecosystem (MSFT, AMZN, GOOG, ORCL). Generic LLM/chatbot hype is the distraction; the infra makes the money.
3. **Mega-cap mispricing.** Repeats that MSFT, AMZN, GOOG are 2-3× undervalued vs his "intrinsic value" estimates ($1,420 MSFT, $1,000 AMZN). Compares current fwd P/E (19-26) to 5y averages (40-60) to call them cheap.
4. **"AI is generational, not dot-com 2.0."** NASDAQ +120% post-ChatGPT vs +400% post-Netscape; current P/E ~24 vs ~33 in 1999. "We're in inning 2-3." Dismisses Burry.
5. **Anti-macro / anti-news cycle.** Peter Lynch's "10 minutes a year." Oil doesn't cause inflation (Friedman). BRICS dismissed. Iran war = buying opportunity (history: wars round-trip in ~12 months).
6. **Concentration framed as conviction.** Admits the 40-60% PLTR position contradicts the diversified Vanguard-millionaire portrait but spins it as informed conviction.

### Trust more (his strong points)

- **The 8-layer AI infrastructure framing** is internally consistent and worth using as a mental map even if you don't act on each pick.
- **Specific multiples vs historical averages** (e.g. NVDA 2027 fwd P/E 15 vs 5y avg 64; AMZN fwd P/E 24 vs 56 in 2020) is real data and useful for sizing claims.
- **Rules-based trim/DCA framework** is disciplined: +50%/trim 10%, +100%/trim 20%, -10% off ATH / 2× DCA, -20% on stock / 2× DCA. Worth borrowing as a structure.
- **Names that repeat 4+ times across videos** = real conviction. The 8-layer set (PLTR, NVDA, AMD, ANET, CRWD, MU, ASML, TSM, MSFT, AMZN, GOOG, MDB, DDOG, BE, CEG, VRT, ORCL) is his actual book.

### Discount (his weak points)

- **"Intrinsic value" targets are made up.** $1,420 MSFT / $1,000 AMZN have no published model. Treat as direction-only.
- **PLTR is his identity.** 9/10 videos. He sized in before the run, brags constantly, defends every drawdown with analogies rather than engaging the bear case. Anything PLTR-related is biased long; not a useful objective signal.
- **Survivorship bragging.** Every name comes with "+X% since I added it." Never mentions losers (none even cited).
- **Anti-macro stance is convenient.** Dismisses macro/news *except* when an oil-shock narrative gives him a buy-the-dip pitch. Two-faced.
- **Sloppy math.** Misspoken P/E figures appear in multiple videos ("AMD 4 P/E," "AMD 160% discount") — discount specific numerical claims unless he restates them.
- **Heavy paid funnel.** Stock MVP 2.0 (price-doubling urgency), Roy Academy, Patreon, "free" Saturday masterclass. The "free" lead magnets all funnel paid product.
- **No bear cases, ever.** Every drawdown is "buy the dip." No defined invalidation criteria.

### Sector preferences

| Sector | Stance | Names he tracks |
|---|---|---|
| AI compute / semis | ✅ strong | NVDA, AMD, ASML, TSM, MU |
| Networking / cybersecurity | ✅ strong | ANET, CRWD, ZS |
| Data / observability | ✅ moderate | MDB, DDOG |
| AI power / datacenter | ✅ strong | CEG, BE, VRT |
| Cloud / mega-cap tech | ✅ strong | MSFT, AMZN, GOOG, ORCL |
| AI software / SaaS apps | ⚠️ mostly avoid | PATH (UiPath) is rare pick; dismisses "chatbot" apps |
| Tesla | ✅ flagship | TSLA |
| Palantir | ✅ flagship | PLTR |
| Consumer discretionary | ❌ never covers | (CRM, ELF, NKE, NOW, CELH, etc. — total blindspot) |
| Financial services | ❌ rarely | SOFI mentioned once as afterthought |
| Energy / commodities | ❌ avoid | "oil doesn't cause inflation" |
| International | ❌ avoid | US-only |
| Crypto-adjacent | ❌ avoid | (no coverage) |

### Signal-weighting rules (operational)

- **5+ videos, consistent thesis** → strong signal. PLTR, TSLA, AMZN, NVDA, CRWD, AMD, GOOGL all hit this bar.
- **3-4 videos** → soft signal (his picks-and-shovels infrastructure roster — ANET, MSFT, MU, ASML, BE, CEG, VRT, ORCL).
- **1-2 videos** → noise, unless it's a deep-dive video specifically on that name.
- **PLTR-specific** → bias-correct downward. His 9/10 repetition is identity, not new information.
- **Cross-channel agreement with Jeremy** (e.g. AMD) → strongest signal — both bullish via different frameworks.
- **Cross-channel disagreement** (e.g. TSLA, GOOGL) → flag for your own research, don't auto-act.

### Vested-interest flags

- **PLTR concentration:** 40% of his portfolio. Anything bullish on PLTR is talking his book.
- **TSLA concentration:** 20%. Same.
- **Stock MVP scorecard:** his own SaaS product. The "objective" scoring he cites (PLTR 98/100, NVDA 88/100) is generated by his own tool he sells. Treat as marketing.
- **Past-picks list (CRWD/ANET/BE/PLTR/VRT/CEG):** he replays the same winner roster across videos as social proof. Useful info but inflates his apparent hit rate.

---

## Nicolas Young — @nicolasyounglive (slug: `ny`)

**Style:** Bilingual creator (audio Chinese, English captions available; English titles with Chinese full-width punctuation `？`, `！`, `——`). Long-biased but rules-based — explicit cash allocation (15-30%), sentiment-indicator triggers (NAAIM, AAII, BofA B&B, Buffett, Shiller CAPE), trims into strength.

**Time horizon:** 2-5 years thematic + tactical short-term overlay. Heavy macro / geopolitics integration. AI semiconductor cycle thesis runs through 2028-2030.

### Worldview

1. **AI-stack thesis is his master frame.** Memory (MU, SNDK) → packaging (TSM, INTC, ASE, UMC) → optical/networking (GLW, CIEN, COHR, LITE, CRDO) → energy (BE, GEV, CAT, PWR) → compute (NVDA, AMD, AVGO, MRVL). Layer-by-layer sequencing — memory and packaging first because they're the AI bottlenecks.
2. **Trump-watching as a primary signal.** Tracks Trump's OGE Form 278-T disclosures (Q1 2026: ~$450M, 2:1 buy:sell). Trades around his verbal "buy" calls. Treats Hormuz / Iran / oil / Fed-chair as Trump-driven variables. Hero-worship framing ("never doubt a president who is a billionaire").
3. **MAG7 bifurcation — different from Jeremy and Tom.** GOOGL + AMZN = strong buy ("must hold"). MSFT, META, AAPL, TSLA, PLTR = mostly avoid. Reasoning: MSFT now "Amazon's little brother" after OpenAI–AMZN $5B/2GW deal; META's $80B AI capex wasted; TSLA autos declining vs Chinese EVs; PLTR at 259× P/E needs 233-333% growth to re-rate.
4. **Anti-SaaS framing.** Calls ADBE, NOW, CRM "AI value traps" — Claude Code makes the software cheap to replicate. **Direct contradiction of Jeremy's "SaaS-as-agent-substrate" thesis.**
5. **Quant sentiment discipline.** Uses NAAIM (>100 sell), AAII (bull>50/bear<25), BofA B&B (sell 80-90), Buffett Indicator, Shiller CAPE, Fear/Greed Index with named thresholds. More rigorous than the other two on this dimension.
6. **Cash-allocation rules.** 15-30% cash via moomoo Cash Plus (advertised 3% or 8.1%). Deploy at VIX ~40 or Fear/Greed ~9. Trim 10-30% on strength.
7. **Pre-IPO / quantum speculative bucket.** Uses Jarsy (RWA tokenization platform) for SpaceX, Anthropic, OpenAI, Perplexity, Neuralink, Waymo. Caps individual speculative picks at <1% of assets. Quantum: IONQ, QBTS, QUBT.
8. **"Doom-then-buy" narrative pattern.** Every video title predicts a pullback then immediately frames it as the next generational buying opportunity. Heads-I-win-tails-you-wait.

### Trust more (his strong points)

- **AI-stack sequencing** (memory → packaging → optical → energy → compute) is internally consistent and well-mapped. Strongest single content contribution.
- **Sentiment indicators with named thresholds** — NAAIM 71→94 in batch, BofA B&B 77 (sell zone 80-90), Buffett 227, Shiller CAPE 40.4 (top 5% historical). Useful as input even if you don't act on his individual picks.
- **Specific MAG7 disaggregation** — most contrarian view in the YouTuber set. Concrete reasoning per name (e.g. "MSFT lost its position because of OpenAI–AMZN deal").
- **Cash-allocation discipline** is rule-based not vibes-based.
- **Names appearing in 6+ videos** = his actual book (AMZN, NVDA, AMD, MU, SNDK, BE, INTC, TSM, GLW, GEV).

### Discount (his weak points)

- **Sponsored videos are product demos, not theses.** The 5/6-May moomoo episode said "avoid NVDA" — directly contradicts his non-sponsored episodes. **Filter out sponsored picks entirely when synthesizing.**
- **Trump-worship overdrives the analysis.** Hero-worship language ("never doubt a president who is a billionaire") and inferring positions from OGE Form 278-T amounts (no prices, no final holdings) are unfalsifiable. Direction of his read may still be useful; the "Trump did X so I'm doing Y" causal chain is not.
- **"Doom-then-buy" is structural** — he can never be wrong because both outcomes confirm the narrative.
- **Self-built "AI analytical pipeline"** (Claude Code + moomoo Skills + paid APIs) is cited as authority but undisclosed. Treat as unverifiable.
- **Probability calls are vibes dressed as numbers.** "34% crash / 42% sideways / 14% melt-up / 10% stagflation" — looks rigorous, is made up.
- **Survivorship bragging** (300% QQQ-call win, "spot-on" calls). Routine.
- **Heavy sponsor rotation** — moomoo, Investing.com Pro, ELSA Speak, Saily, Surfshark, Jarsy, WarrenAI. Sometimes the entire video is structured around the sponsor.

### Sector preferences

| Sector | Stance | Names he tracks |
|---|---|---|
| AI memory / storage | ✅ strong | MU, SNDK, DRAM ETF |
| AI packaging / foundry | ✅ strong | TSM, INTC, ASE, UMC |
| AI optical / networking | ✅ strong | GLW, CIEN, NOK, COHR, LITE, CRDO |
| AI energy / power | ✅ strong | BE, GEV, CAT, PWR |
| AI compute | ✅ strong | NVDA, AMD, AVGO, MRVL, QCOM |
| MAG7 — Google + Amazon | ✅ strong | GOOGL, AMZN |
| MAG7 — Microsoft, Meta, Apple, Tesla | ❌ avoid | MSFT (now AMZN's "little brother"), META (capex wasted), AAPL (AI weak), TSLA (Chinese EVs + Musk backlash) |
| SaaS / enterprise software | ❌ "AI value trap" | CRM, NOW, ADBE — Claude Code replicates them |
| Palantir | ❌ avoid | 259× P/E priced for 233-333% growth |
| Oracle / capex-heavy | ❌ avoid | ORCL (-$5.9B FCF, debt +40% to $124B) |
| Defense | ⚠️ watch | ANDRL ($20B Pentagon contract) |
| Gold / silver / commodities | ✅ hedge | GDX, GLD, SLV, URA (just sold +50% YTD), GSG |
| Quantum | ⚠️ speculative | IONQ, QBTS, QUBT (post-Nvidia Ising) |
| Pre-IPO / RWA | ⚠️ speculative | SpaceX, Anthropic, OpenAI, Perplexity, Neuralink, Waymo via Jarsy |
| International | ⚠️ selective | 0050 Taiwan; otherwise US-concentrated |
| Crypto | ❌ avoid | (no coverage) |

### Signal-weighting rules (operational)

- **6+ videos, same thesis** → strong signal (his AI-stack core: AMZN, NVDA, AMD, MU, SNDK, BE, INTC, TSM, GLW, GEV, GOOGL).
- **3-5 videos** → soft signal (AVGO, MRVL, SOXX/SMH, GDX, CAT).
- **1-2 videos** → noise unless deep-dive.
- **Sponsored video (#moomoo, etc.)** → **discount entirely.** The picks are framed as AI-tool outputs, not his thesis.
- **Cross-channel agreement** (e.g. AMD: all 3 bullish) → strongest signal.
- **Direct disagreement with Jeremy** (e.g. SaaS-as-agent vs SaaS-as-value-trap; GOOGL trim vs buy) → flag for your own research.
- **Trump-OGE-driven calls** → keep direction, discard "Trump did X" causal chain.

### Vested-interest flags

- **Heavy sponsor integration** — moomoo (signup-bonus stock and Cash Plus rate are advertising), Investing.com Pro (affiliate code "nicholas"), ELSA Speak (code NICK), Saily, Surfshark, Jarsy (RWA pre-IPO platform he profits from when viewers sign up).
- **Self-built tools framed as authority** — Claude Max ($200/mo), moomoo Skills, Codex. He cites these as the source of his "AI-derived" picks. Unverifiable.
- **Pre-IPO platform pitch (Jarsy)** has counterparty + liquidity risk; he doesn't dwell on it.
- **Hero-worship framing of Trump** colors his analysis of geopolitics, oil, Fed; treat the political layer as opinion.
