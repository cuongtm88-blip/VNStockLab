from __future__ import annotations

import numpy as np
import pandas as pd

from vnstocklab.analysis.ichimoku import (
    add_ichimoku,
    analyze_multi_timeframe_ichimoku,
    ichimoku_snapshot,
    resample_weekly,
)


def trend_prices(periods: int = 420, direction: str = "up") -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=periods)
    close = np.linspace(10, 80, periods)
    if direction == "down":
        close = close[::-1]
    return pd.DataFrame(
        {
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(periods, 1_000_000),
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


def test_ichimoku_uses_standard_periods_and_displacement() -> None:
    prices = trend_prices(periods=100)
    result = add_ichimoku(prices)

    expected_tenkan = (prices["high"].iloc[-9:].max() + prices["low"].iloc[-9:].min()) / 2
    expected_kijun = (prices["high"].iloc[-26:].max() + prices["low"].iloc[-26:].min()) / 2
    expected_span_b_at_77 = (
        prices["high"].iloc[:52].max() + prices["low"].iloc[:52].min()
    ) / 2

    assert result.iloc[-1]["tenkan_sen"] == expected_tenkan
    assert result.iloc[-1]["kijun_sen"] == expected_kijun
    assert result.iloc[77]["senkou_span_b"] == expected_span_b_at_77
    assert result.iloc[0]["chikou_span"] == prices.iloc[26]["close"]


def test_snapshot_classifies_clear_uptrend() -> None:
    snapshot = ichimoku_snapshot(add_ichimoku(trend_prices()), "Ngày")

    assert snapshot.state == "Tăng mạnh"
    assert snapshot.price_position == "Trên mây"
    assert snapshot.tk_relation == "Tenkan trên Kijun"
    assert snapshot.future_cloud == "Mây tương lai tăng"
    assert snapshot.chikou_confirmation == "Xác nhận tăng"


def test_multi_timeframe_requires_daily_and_weekly_agreement() -> None:
    result = analyze_multi_timeframe_ichimoku(trend_prices())

    assert result.weekly is not None
    assert result.daily.state == "Tăng mạnh"
    assert result.weekly.state == "Tăng mạnh"
    assert result.aligned
    assert result.score_adjustment == 1


def test_short_history_keeps_daily_result_without_weekly_confirmation() -> None:
    prices = trend_prices(periods=100)
    result = analyze_multi_timeframe_ichimoku(prices)

    assert result.weekly is None
    assert not result.aligned
    assert result.score_adjustment == 0


def test_weekly_resampling_preserves_ohlcv_semantics() -> None:
    prices = trend_prices(periods=10)
    weekly = resample_weekly(prices)
    first_week = prices.loc[: weekly.index[0]]

    assert weekly.iloc[0]["open"] == first_week.iloc[0]["open"]
    assert weekly.iloc[0]["high"] == first_week["high"].max()
    assert weekly.iloc[0]["low"] == first_week["low"].min()
    assert weekly.iloc[0]["close"] == first_week.iloc[-1]["close"]
    assert weekly.iloc[0]["volume"] == first_week["volume"].sum()

