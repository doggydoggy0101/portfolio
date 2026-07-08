# SETUP.md — first-run onboarding

You cloned a *template*. The code and the skill files ship; the data, the accounts, and the trading doctrine are personal — you build yours here, once.

> **If you are Claude:** you're probably reading this because `data/` is missing or empty (CLAUDE.md routes here when the daily flow can't find account data). Walk the user through the checklist below **interactively, one step at a time** — ask what their broker/accounts look like, write the files with them, and adapt code where their format differs. Don't invent placeholder trades or deposits; everything here comes from the user.

## 0. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 1. Accounts

Decide your account structure, then make it real in two places:

- `src/loader.py` — `ACCOUNTS` (folder names, UI display order) and `DEFAULT_ACCOUNT`. One account is fine: `ACCOUNTS = ("ira",)`.
- `CLAUDE.md` → "Accounts" section — currently describes the author's setup (an actively-managed Roth IRA + a passive taxable VOO account, with a freeze-and-migrate plan between them). **Rewrite it to describe *your* accounts** — which one the daily loop manages, what the others are for. Claude reads this file every session; if it describes someone else's accounts, it will manage someone else's portfolio.

Then create the folders:

```bash
mkdir -p data/<account>          # one per entry in ACCOUNTS
```

## 2. Data files (per account)

Three files per account folder, one shared watchlist. Formats in README.md → "Data file formats".

- **`data/<account>/transactions.csv`** — your broker's raw trade export. The loader (`src/loader.py`) reads six columns: `Trade Date` (MM/DD/YYYY), `Type` (`Buy`/`Sell`; rows with `Dividend` in Type are read as dividend cash), `Ticker`, `Quantity`, `Price USD`, `Amount USD` (signed: negative=buy). **If your broker exports different column names/formats, don't hand-edit every export — ask Claude to adapt `load_transactions` / `load_dividends` to your broker's schema once.** That's the intended customization point; nothing downstream touches the raw columns.
- **`data/<account>/deposit.csv`** — header `date,amount,notes`, one row per cash deposit/withdrawal since the account opened. Needed for cash math and the performance chart.
- **`data/<account>/order.csv`** — header `date_added,ticker,action,price,quantity,expires,note`, then your currently-open limit orders (empty below the header is fine). No commas inside `note`.
- **`data/watchlist.txt`** — one ticker per line, `#` comments. Convention: held names are listed too, so the file is the full universe the optimizer considers.

## 3. Doctrine — the important one

`skills/rule.md` is **the author's** trading doctrine, not a default you should inherit: beat the S&P 500 by 1-2%/yr, ~50% VOO core, 20% per-name caps, 2-tier exit ladders, a 5% cash floor, US-equities-only hard constraints. Your goal is probably different — and every number downstream (position sizing, exit triggers, vetoes) flows from this file.

Go through it with Claude, section by section:

```
Read skills/rule.md top to bottom with me. For each section, explain what it
does in the daily loop, then ask me whether it matches my goal and risk
tolerance. Rewrite the numbers and constraints to mine. My goal is: <...>
```

Keep the *structure* (hard lines, conviction→size, exit ladders, regularizer veto) unless you have a reason not to — it's what makes the loop auditable. Change the *numbers and goals* freely.

## 4. Opinion sources (optional)

The YouTube step (`skills/youtube.md`) summarizes creators **you** trust. Profiles live in `skills/youtube/youtube_<slug>.md` — gitignored, so the template ships the mechanism, never whose views are tracked.

- Per creator: copy `skills/youtube/template.md` → `youtube_<slug>.md` and fill it in with Claude (or just tell Claude "add creator @handle" and describe why you trust them).
- No creators? Skip — with no profile files the step is a no-op, and the loop runs on independent web research alone.

## 5. Verify

```bash
python main.py        # TUI should show your positions, cash, and performance
```

Cross-check the TOTAL row against your broker's app — if it's off, the usual suspects are missing deposits or a mis-mapped export column. Then start your first session: open Claude Code here and ask for the **morning brief**.
