"""Vnstock v4 adapter."""

from __future__ import annotations

from typing import Any

import pandas as pd
from vnstock.ui import Market, Reference  # type: ignore[import-untyped]

from vnstocklab.data.provider import MarketDataError, normalize_ohlcv


class VnstockProvider:
    """Retrieve Vietnamese market data through Vnstock's Unified UI."""

    def history(self, symbol: str, count: int = 300) -> pd.DataFrame:
        """Retrieve daily history and normalize it for the analysis engine."""
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("Mã cổ phiếu không được để trống")
        try:
            raw: Any = Market().equity(normalized_symbol).ohlcv(count=count, interval="1D")
            if not isinstance(raw, pd.DataFrame):
                raise MarketDataError("Nhà cung cấp trả về định dạng không hỗ trợ")
            return normalize_ohlcv(raw)
        except MarketDataError:
            raise
        except SystemExit as error:
            raise MarketDataError(
                "Nguồn Vnstock đã đạt giới hạn request; vui lòng chờ khoảng 1 phút rồi thử lại"
            ) from error
        except Exception as error:
            raise MarketDataError(f"Không thể tải dữ liệu {normalized_symbol}: {error}") from error

    def index_members(self, index: str = "VN30") -> tuple[str, ...]:
        """Retrieve and sanitize members of a Vietnamese index basket."""
        normalized_index = index.strip().upper()
        try:
            raw: Any = Reference().index.members(normalized_index)
            if isinstance(raw, pd.Series):
                values = raw.tolist()
            elif isinstance(raw, pd.DataFrame):
                symbol_column = next(
                    (column for column in raw.columns if str(column).lower() == "symbol"), None
                )
                if symbol_column is None:
                    raise MarketDataError("Danh sách chỉ số không có cột symbol")
                values = raw[symbol_column].tolist()
            else:
                values = list(raw)
            symbols = tuple(dict.fromkeys(str(value).strip().upper() for value in values if value))
            if not symbols:
                raise MarketDataError(f"Không tìm thấy thành phần {normalized_index}")
            return symbols
        except MarketDataError:
            raise
        except Exception as error:
            raise MarketDataError(f"Không thể tải danh sách {normalized_index}: {error}") from error
