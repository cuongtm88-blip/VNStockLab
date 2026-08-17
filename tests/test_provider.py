import pandas as pd
import pytest

from vnstocklab.data.provider import MarketDataError, normalize_ohlcv
from vnstocklab.data.vnstock_provider import VnstockProvider


def test_normalize_ohlcv_accepts_vnstock_time_column() -> None:
    source = pd.DataFrame(
        {
            "time": ["2026-01-03", "2026-01-02"],
            "open": [11, 10],
            "high": [13, 12],
            "low": [10, 9],
            "close": [12, 11],
            "volume": [1200, 1000],
        }
    )
    result = normalize_ohlcv(source)

    assert result.index.name == "date"
    assert result.index.is_monotonic_increasing
    assert result.iloc[-1]["close"] == 12


def test_normalize_ohlcv_rejects_unknown_shape() -> None:
    with pytest.raises(MarketDataError, match="thiếu cột"):
        normalize_ohlcv(pd.DataFrame({"time": ["2026-01-02"], "close": [10]}))


def test_vnstock_provider_converts_rate_limit_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    class ExitingMarket:
        def equity(self, symbol: str) -> "ExitingMarket":
            return self

        def ohlcv(self, count: int, interval: str) -> pd.DataFrame:
            raise SystemExit("Rate limit exceeded")

    monkeypatch.setattr("vnstocklab.data.vnstock_provider.Market", ExitingMarket)

    with pytest.raises(MarketDataError, match="giới hạn request"):
        VnstockProvider().history("FPT")
