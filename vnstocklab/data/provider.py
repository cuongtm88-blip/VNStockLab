"""Market-data provider contracts and shared normalization."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

import pandas as pd


class MarketDataError(RuntimeError):
    """Raised when a remote market-data provider cannot fulfill a request."""


@dataclass(frozen=True)
class MarketTick:
    """Provider-neutral realtime trade/quote update."""

    symbol: str
    timestamp: pd.Timestamp
    price: float
    volume: float
    source: str
    sequence: int | None = None


class RealtimeMarketDataProvider(Protocol):
    """Contract future FireAnt or other streaming adapters must implement."""

    def stream(self, symbols: tuple[str, ...]) -> AsyncIterator[MarketTick]:
        """Yield normalized ticks in provider sequence order."""
        ...


class MarketDataProvider(Protocol):
    """Small provider boundary used by analysis and UI code."""

    def history(self, symbol: str, count: int = 300) -> pd.DataFrame:
        """Return normalized daily OHLCV data."""
        ...

    def index_members(self, index: str = "VN30") -> tuple[str, ...]:
        """Return symbols belonging to an index basket."""
        ...


def normalize_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize common provider output into VNStockLab's OHLCV schema."""
    result = frame.copy()
    result.columns = result.columns.astype(str).str.strip().str.lower()
    date_column = "time" if "time" in result.columns else "date"
    required = {date_column, "open", "high", "low", "close", "volume"}
    missing = required.difference(result.columns)
    if missing:
        raise MarketDataError(f"Dữ liệu thiếu cột: {', '.join(sorted(missing))}")
    if result.empty:
        raise MarketDataError("Nhà cung cấp không trả về dữ liệu")

    result[date_column] = pd.to_datetime(result[date_column], errors="raise")
    columns = ["open", "high", "low", "close", "volume"]
    result[columns] = result[columns].apply(pd.to_numeric, errors="raise")
    normalized = result.loc[:, [date_column, *columns]].rename(columns={date_column: "date"})
    return normalized.sort_values("date").drop_duplicates("date", keep="last").set_index("date")
