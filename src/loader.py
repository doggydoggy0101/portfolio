"""Read the raw brokerage transaction CSV and normalize it."""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"
DEPOSIT_CSV = DATA_DIR / "deposit.csv"
ORDER_CSV = DATA_DIR / "order.csv"
WATCHLIST_TXT = DATA_DIR / "watchlist.txt"


def load_transactions(path: Path = TRANSACTIONS_CSV) -> pd.DataFrame:
    """Return a clean trades DataFrame.

    Columns: date, ticker, action ('buy'|'sell'), quantity (positive),
    price (per share, USD), amount (signed USD: negative=buy, positive=sell).
    """
    raw = pd.read_csv(path)
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


def load_deposits(path: Path = DEPOSIT_CSV) -> pd.DataFrame:
    """Return deposits/withdrawals DataFrame: columns date, amount, notes.

    Positive `amount` = deposit into the account, negative = withdrawal.
    """
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)
    return df.sort_values("date").reset_index(drop=True)


def load_orders(path: Path = ORDER_CSV) -> pd.DataFrame:
    """Return open-orders DataFrame: ticker, action, price, quantity, date_added, expires, note."""
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
