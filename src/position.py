"""Position view: shared helpers for the rich.Table used by the TUI's Position tab,
plus a markdown builder used by `skills/position.md` to log portfolio state to the
daily journal."""

import pandas as pd
from rich import box
from rich.table import Table

from loader import load_transactions  # noqa: F401  (re-export convenience)
from portfolio import compute_positions
from price import fetch_prices


def _price_ath(price: float, ath: float | None, *, bold: bool = False) -> str:
    """Two-line cell: $price on top, dim 'ATH $X' below (omitted if no ATH)."""
    if pd.isna(price):
        return "-"
    price_part = f"${price:,.2f}"
    if bold:
        price_part = f"[bold]{price_part}[/]"
    if ath is None or pd.isna(ath):
        return price_part
    return f"{price_part}\n[dim](${ath:,.2f})[/dim]"


def _money(x: float, *, signed: bool = False, bold: bool = False) -> str:
    if pd.isna(x):
        return "-"
    if signed:
        sign = "+" if x >= 0 else "-"
        s = f"{sign}${abs(x):,.2f}"
        color = "green" if x >= 0 else "red"
        style = f"bold {color}" if bold else color
        return f"[{style}]{s}[/]"
    s = f"${x:,.2f}"
    return f"[bold]{s}[/]" if bold else s


def _money_pct(money: float, pct: float, *, bold: bool = False) -> str:
    """Two-line cell: $amount on top, (%) below — only the % is colored."""
    if pd.isna(money) or pd.isna(pct):
        return "-"
    sign = "+" if money >= 0 else "-"
    pct_sign = "+" if pct >= 0 else ""
    color = "green" if pct >= 0 else "red"
    money_part = f"{sign}${abs(money):,.2f}"
    pct_part = f"({pct_sign}{pct:.2f}%)"
    if bold:
        money_part = f"[bold]{money_part}[/]"
        pct_part = f"[bold {color}]{pct_part}[/]"
    else:
        pct_part = f"[{color}]{pct_part}[/]"
    return f"{money_part}\n{pct_part}"


def _value_qty(value: float, shares: float, *, bold: bool = False) -> str:
    """Two-line cell: $value on top, (qty) below in dim style."""
    if pd.isna(value):
        return "-"
    qty_str = str(int(shares)) if shares == int(shares) else f"{shares:.4f}"
    value_part = f"${value:,.2f}"
    if bold:
        value_part = f"[bold]{value_part}[/]"
    return f"{value_part}\n[dim]({qty_str})[/dim]"


def build_position_view(trades: pd.DataFrame) -> pd.DataFrame:
    """Compute the per-position DataFrame for display.

    Returns DataFrame indexed by ticker with columns:
    shares, avg_cost, cost_basis, price, prev_close, price_ts, prev_ts,
    value, day_gl, day_gl_pct, total_gl, total_gl_pct.
    Sorted by value (largest first).
    """
    positions = compute_positions(trades)
    if positions.empty:
        return pd.DataFrame()
    prices = fetch_prices(positions.index.tolist())
    df = positions.join(prices)
    df["value"] = df["shares"] * df["price"]
    df["day_gl"] = df["shares"] * (df["price"] - df["prev_close"])
    df["day_gl_pct"] = (df["price"] - df["prev_close"]) / df["prev_close"] * 100
    df["total_gl"] = df["value"] - df["cost_basis"]
    df["total_gl_pct"] = df["total_gl"] / df["cost_basis"] * 100
    return df.sort_values("value", ascending=False)


def build_positions_table(
    df: pd.DataFrame,
    cash: float,
    ath: dict[str, float] | None = None,
    deposits_total: float | None = None,
) -> Table:
    """Build the rich.Table shown in the TUI's Position tab.

    Each stock row spans two text rows: number on top, secondary value below in parens.
    `ath` (optional): {ticker: all-time high} — shown below price as "ATH $X".
    `deposits_total` (optional): net deposits — when given, the TOTAL row's Value cell
    shows total gain vs deposits below the portfolio value.
    """
    ath = ath or {}
    table = Table(box=box.ROUNDED)
    cols = [
        ("", "left"),
        ("Price", "right"),
        ("Day", "right"),
        ("Total", "right"),
        ("Value", "right"),
    ]
    for name, justify in cols:
        table.add_column(name, justify=justify)

    for ticker, r in df.iterrows():
        table.add_row(
            ticker,
            _price_ath(r["price"], ath.get(ticker)),
            _money_pct(r["day_gl"], r["day_gl_pct"]),
            _money_pct(r["total_gl"], r["total_gl_pct"]),
            _value_qty(r["value"], r["shares"]),
        )

    table.add_row("CASH", "—", "—", "—", _money(cash))

    if not df.empty:
        stocks_value = df["value"].sum()
        stocks_cost = df["cost_basis"].sum()
        stocks_day_gl = df["day_gl"].sum()
        stocks_total_gl = df["total_gl"].sum()
        stocks_prev_value = (df["prev_close"] * df["shares"]).sum()
        day_gl_pct_total = stocks_day_gl / (stocks_prev_value + cash) * 100
        total_gl_pct = stocks_total_gl / stocks_cost * 100  # cash excluded from denominator

        table.add_section()
        total_value = stocks_value + cash
        value_cell = _money(total_value, bold=True)
        if deposits_total:  # second line: total earned vs net deposits
            value_cell += "\n" + _money(total_value - deposits_total, signed=True)
        table.add_row(
            "[bold]TOTAL[/]",
            "",
            _money_pct(stocks_day_gl, day_gl_pct_total, bold=True),
            _money_pct(stocks_total_gl, total_gl_pct, bold=True),
            value_cell,
        )

    return table


# ---------------------------------------------------------------------------
# Markdown builder for the journal (consumed by skills/position.md)
# ---------------------------------------------------------------------------


def _compute_cash(
    trades: pd.DataFrame, deposits: pd.DataFrame, dividends: pd.DataFrame | None = None
) -> float:
    """Cash = deposits + sells - buys + dividends. buys are stored as negative `amount`."""
    total_dep = float(deposits["amount"].sum())
    buys = float(trades.loc[trades["amount"] < 0, "amount"].sum())  # negative
    sells = float(trades.loc[trades["amount"] > 0, "amount"].sum())  # positive
    div = 0.0 if dividends is None else float(dividends["amount"].sum())  # dividend cash
    return total_dep + buys + sells + div


def compute_sp500_since_entry_bulk(
    trades: pd.DataFrame, tickers: list[str] | None = None, today=None
) -> dict[str, float]:
    """Dollar-weighted SPY total return since each buy, for many tickers at once.

    One SPY history fetch covers all tickers (bulk-fetch convention for the TUI).
    For positions with multiple buys at different dates, weight each buy's
    SPY return by its dollar cost. Returns {ticker: fraction} (0.05 = 5%).
    Uses SPY auto-adjusted close (dividends reinvested) as the SP500 proxy.
    """
    from datetime import date as _date

    import yfinance as yf

    if today is None:
        today = _date.today()

    buys = trades[trades["action"] == "buy"]
    if tickers is not None:
        buys = buys[buys["ticker"].isin(tickers)]
    if buys.empty:
        return {}

    earliest = buys["date"].min().date()
    spy = yf.Ticker("SPY").history(
        start=earliest.strftime("%Y-%m-%d"),
        end=(today + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        auto_adjust=True,
    )["Close"]
    if spy.empty:
        return {}
    # Normalize SPY index to naive dates so we can compare with buy dates
    spy.index = spy.index.tz_localize(None).normalize()
    spy_today = float(spy.iloc[-1])

    out: dict[str, float] = {}
    for ticker, group in buys.groupby("ticker"):
        total_basis = 0.0
        weighted = 0.0
        for _, t in group.iterrows():
            buy_date = pd.Timestamp(t["date"]).normalize()
            cost = abs(float(t["amount"]))  # positive number for cost basis
            on_or_after = spy[spy.index >= buy_date]
            if on_or_after.empty:
                continue
            spy_at_buy = float(on_or_after.iloc[0])
            ret = spy_today / spy_at_buy - 1.0
            weighted += ret * cost
            total_basis += cost
        out[str(ticker)] = weighted / total_basis if total_basis > 0 else 0.0
    return out


def compute_sp500_since_entry(ticker: str, today=None) -> float:
    """Single-ticker convenience wrapper around `compute_sp500_since_entry_bulk`."""
    from loader import load_transactions

    result = compute_sp500_since_entry_bulk(load_transactions(), [ticker], today=today)
    return result.get(ticker, 0.0)


def compute_exit_ladder(ticker: str, today=None) -> dict:
    """Per-position 2-tier exit ladder per skills/rule.md.

    Tier 1 = avg_cost × (1 + SP500_since_entry) × 1.10
    Tier 2 = Tier 1 × 1.10
    """
    sp500 = compute_sp500_since_entry(ticker, today=today)
    positions = compute_positions(load_transactions())
    if ticker not in positions.index:
        return {"error": f"{ticker} not held"}
    avg_cost = float(positions.loc[ticker, "avg_cost"])
    shares = float(positions.loc[ticker, "shares"])
    tier1 = avg_cost * (1 + sp500) * 1.10
    tier2 = tier1 * 1.10
    return {
        "ticker": ticker,
        "shares": shares,
        "avg_cost": avg_cost,
        "sp500_since_entry": sp500,
        "tier1": tier1,
        "tier2": tier2,
    }


def build_state_markdown(today=None, core_ticker: str = "VOO", account: str = "ira") -> str:
    """Render the current portfolio state as a markdown section for the journal.

    The daily active loop runs on the IRA account (sleeves, ladders, rules);
    `account` is exposed for completeness but defaults to "ira".

    Shape:
      # Portfolio state — YYYY-MM-DD
      ## Sleeves
      ## Holdings
      ## Open orders
      ## Rule-compliance check
    """
    from datetime import date

    from loader import load_deposits, load_dividends, load_orders, load_transactions

    if today is None:
        today = date.today()

    trades = load_transactions(account)
    deposits = load_deposits(account)
    dividends = load_dividends(account)
    orders = load_orders(account)

    cash = _compute_cash(trades, deposits, dividends)
    df = build_position_view(trades)

    if not df.empty and core_ticker in df.index:
        core_value = float(df.loc[core_ticker, "value"])
        active_invested = float(df.drop(core_ticker)["value"].sum())
    else:
        core_value = 0.0
        active_invested = float(df["value"].sum()) if not df.empty else 0.0

    active_total = active_invested + cash
    total_portfolio = core_value + active_total

    lines: list[str] = []
    lines.append(f"# Portfolio state — {today.isoformat()}")
    lines.append("")

    # Sleeves
    lines.append("## Sleeves")
    if total_portfolio > 0:
        core_pct = core_value / total_portfolio * 100
        active_pct = active_total / total_portfolio * 100
        lines.append(
            f"- Core ({core_ticker}): ${core_value:,.2f} ({core_pct:.1f}% of total) [target ~50%]"
        )
        lines.append(f"- Active sleeve: ${active_total:,.2f} ({active_pct:.1f}% of total)")
        if active_total > 0:
            cash_pct = cash / active_total * 100
            inv_pct = active_invested / active_total * 100
            lines.append(
                f"  - Cash: ${cash:,.2f} ({cash_pct:.1f}% of active) [floor 5%, ceiling 30%]"
            )
            lines.append(f"  - Invested: ${active_invested:,.2f} ({inv_pct:.1f}% of active)")
    else:
        lines.append("- (no positions, no cash)")
    lines.append(f"- **Total portfolio: ${total_portfolio:,.2f}**")
    lines.append("")

    # Holdings
    if not df.empty:
        lines.append("## Holdings")
        lines.append("")
        lines.append("| ticker | shares | avg cost | current | value | %active | %total | P&L |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for ticker, r in df.iterrows():
            pct_active = (
                r["value"] / active_total * 100
                if active_total > 0 and ticker != core_ticker
                else 0.0
            )
            pct_total = r["value"] / total_portfolio * 100 if total_portfolio > 0 else 0.0
            note = " (core)" if ticker == core_ticker else ""
            shares_str = (
                str(int(r["shares"])) if r["shares"] == int(r["shares"]) else f"{r['shares']:.4f}"
            )
            lines.append(
                f"| {ticker}{note} | {shares_str} | ${r['avg_cost']:.2f} | ${r['price']:.2f} | "
                f"${r['value']:,.2f} | {pct_active:.1f}% | {pct_total:.1f}% | {r['total_gl_pct']:+.1f}% |"
            )
        lines.append("")

    # Open orders
    if not orders.empty:
        lines.append("## Open orders")
        lines.append("")
        lines.append("| ticker | action | limit | qty | days_left |")
        lines.append("|---|---|---:|---:|---:|")
        for _, o in orders.iterrows():
            days_left = (o["expires"].date() - today).days
            lines.append(
                f"| {o['ticker']} | {o['action']} | ${o['price']:.2f} | "
                f"{int(o['quantity'])} | {days_left} |"
            )
        lines.append("")

    # Rule-compliance check
    lines.append("## Rule-compliance check")
    lines.append("")
    if active_total > 0:
        cash_pct = cash / active_total * 100
        if cash_pct < 5:
            lines.append(f"- Active-sleeve cash: {cash_pct:.1f}% — **BELOW 5% floor**")
        elif cash_pct > 30:
            lines.append(f"- Active-sleeve cash: {cash_pct:.1f}% — **ABOVE 30% ceiling**")
        else:
            lines.append(
                f"- Active-sleeve cash: {cash_pct:.1f}% — within bounds [5% floor, 30% ceiling]"
            )

    # Per-name cap (20% mean-rev cap; momentum 10% cap not enforced here — optimizer's job to distinguish bucket)
    violations: list[str] = []
    if not df.empty and active_total > 0:
        for ticker, r in df.iterrows():
            if ticker == core_ticker:
                continue
            pct = r["value"] / active_total * 100
            if pct > 20:
                violations.append(f"  - {ticker}: {pct:.1f}% — over 20% mean-rev cap")
    if violations:
        lines.append("- Per-name cap violations (mean-rev 20%):")
        lines.extend(violations)
    else:
        lines.append("- Per-name cap: all positions within 20% mean-rev cap")

    return "\n".join(lines)


if __name__ == "__main__":
    print(build_state_markdown())
