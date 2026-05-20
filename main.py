"""Personal investing copilot — launches the terminal UI."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from tui import StockTUI  # noqa: E402


def main() -> None:
    StockTUI().run()


if __name__ == "__main__":
    main()
