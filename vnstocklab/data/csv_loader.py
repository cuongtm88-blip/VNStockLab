"""CSV market-data ingestion and validation."""

from __future__ import annotations

from typing import BinaryIO, TextIO

import pandas as pd

REQUIRED_COLUMNS = frozenset({"date", "open", "high", "low", "close", "volume"})


def load_price_csv(source: BinaryIO | TextIO) -> pd.DataFrame:
    """Load a normalized OHLCV CSV, rejecting malformed market data."""
    frame = pd.read_csv(source)
    frame.columns = frame.columns.str.strip().str.lower()
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")

    result = frame.loc[:, ["date", "open", "high", "low", "close", "volume"]].copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise")
    for column in ("open", "high", "low", "close", "volume"):
        result[column] = pd.to_numeric(result[column], errors="raise")
    if result.empty:
        raise ValueError("CSV contains no price rows")
    if (result[["open", "high", "low", "close", "volume"]] < 0).any().any():
        raise ValueError("Price and volume values cannot be negative")
    if (result["high"] < result[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("High price is inconsistent with OHLC values")
    if (result["low"] > result[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("Low price is inconsistent with OHLC values")

    return result.sort_values("date").drop_duplicates("date", keep="last").set_index("date")

