"""Read the raw brokerage transaction CSV and normalize it."""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Each account has its own subfolder (data/<account>/{transactions,deposit,order}.csv).
# The watchlist is shared across accounts and lives at the top level.
# ACCOUNTS is the UI display order (left→right); DEFAULT_ACCOUNT is the one
# selected on launch (independent of order).
ACCOUNTS = ("general", "ira")
DEFAULT_ACCOUNT = "ira"
WATCHLIST_TXT = DATA_DIR / "watchlist.txt"


def account_path(account: str, filename: str) -> Path:
    """Resolve a per-account data file, e.g. account_path('ira', 'order.csv')."""
    return DATA_DIR / account / filename


def load_transactions(account: str = DEFAULT_ACCOUNT, path: Path | None = None) -> pd.DataFrame:
    """Return a clean trades DataFrame for `account`.

    Columns: date, ticker, action ('buy'|'sell'), quantity (positive),
    price (per share, USD), amount (signed USD: negative=buy, positive=sell).
    """
    raw = pd.read_csv(path if path is not None else account_path(account, "transactions.csv"))
    trades = raw[raw["Type"].isin(["Buy", "Sell"])].copy()
    trades["date"] = pd.to_datetime(trades["Trade Date"], format="%m/%d/%Y")
    trades["ticker"] = trades["Ticker"].str.strip()
    trades["action"] = trades["Type"].str.lower()
    trades["quantity"] = (
        trades["Quantity"].astype(float).abs()
    )  # broker signs sells negative; we use action + positive qty
    trades["price"] = trades["Price USD"].astype(float)
    trades["amount"] = trades["Amount USD"].astype(float)
    return (
        trades[["date", "ticker", "action", "quantity", "price", "amount"]]
        .sort_values("date")
        .reset_index(drop=True)
    )


def load_dividends(account: str = DEFAULT_ACCOUNT, path: Path | None = None) -> pd.DataFrame:
    """Dividend/income cash rows from `account` (Type contains 'Dividend').

    Columns: date, ticker, amount (positive USD cash received). These add to cash
    like a sell, but never touch positions or realized P&L (no shares change hands).
    """
    raw = pd.read_csv(path if path is not None else account_path(account, "transactions.csv"))
    div = raw[raw["Type"].astype(str).str.contains("Dividend", case=False, na=False)].copy()
    if div.empty:
        return pd.DataFrame(columns=["date", "ticker", "amount"])
    div["date"] = pd.to_datetime(div["Trade Date"], format="%m/%d/%Y")
    div["ticker"] = div["Ticker"].str.strip()
    div["amount"] = div["Amount USD"].astype(float)
    return div[["date", "ticker", "amount"]].sort_values("date").reset_index(drop=True)


def load_deposits(account: str = DEFAULT_ACCOUNT, path: Path | None = None) -> pd.DataFrame:
    """Return deposits/withdrawals DataFrame for `account`: columns date, amount, notes.

    Positive `amount` = deposit into the account, negative = withdrawal.
    """
    df = pd.read_csv(path if path is not None else account_path(account, "deposit.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)
    return df.sort_values("date").reset_index(drop=True)


def load_orders(account: str = DEFAULT_ACCOUNT, path: Path | None = None) -> pd.DataFrame:
    """Return open-orders DataFrame for `account`: ticker, action, price, quantity, date_added, expires, note."""
    path = path if path is not None else account_path(account, "order.csv")
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["date_added"] = pd.to_datetime(df["date_added"])
    df["expires"] = pd.to_datetime(df["expires"])
    df["ticker"] = df["ticker"].str.strip()
    df["action"] = df["action"].str.strip().str.lower()
    df["price"] = df["price"].astype(float)
    df["quantity"] = df["quantity"].astype(int)
    return df.sort_values("date_added").reset_index(drop=True)


def load_watchlist(path: Path = WATCHLIST_TXT) -> list[str]:
    """Return list of tickers from `watchlist.txt`. Blank lines / `#` comments ignored."""
    if not path.exists():
        return []
    tickers = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tickers.append(line.upper())
    return tickers
