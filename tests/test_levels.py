from __future__ import annotations

import numpy as np
import pandas as pd

from vnstocklab.analysis.levels import (
    Pivot,
    PriceZone,
    SupportResistanceAnalysis,
    apply_zone_candlestick_confirmation,
    cluster_zones,
    detect_pivots,
)


def price_frame(highs: list[float], lows: list[float] | None = None) -> pd.DataFrame:
    dates = pd.bdate_range("2026-01-01", periods=len(highs))
    low_values = lows if lows is not None else [value - 2 for value in highs]
    close = [(high + low) / 2 for high, low in zip(highs, low_values, strict=True)]
    return pd.DataFrame(
        {
            "open": close,
            "high": highs,
            "low": low_values,
            "close": close,
            "volume": np.full(len(highs), 100_000),
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


def test_detect_pivots_requires_bars_on_both_sides() -> None:
    data = price_frame([10, 11, 14, 11, 10, 11, 14.1, 11, 15])

    pivots = detect_pivots(data, window=1)
    high_positions = [pivot.date for pivot in pivots if pivot.kind == "high"]

    assert data.index[2] in high_positions
    assert data.index[6] in high_positions
    assert data.index[-1] not in high_positions


def test_clustered_resistance_changes_role_after_breakout_and_retest() -> None:
    data = price_frame([10, 11, 10.5, 11.1, 10.5, 10.8, 12, 11.8, 12.2])
    data.loc[data.index[7], ["low", "close"]] = [11.1, 11.7]
    pivots = (
        Pivot(data.index[1], 11.0, "high", 100_000),
        Pivot(data.index[3], 11.1, "high", 120_000),
    )

    zones = cluster_zones(data, pivots, tolerance=0.3)

    assert len(zones) == 1
    assert zones[0].original_role == "Kháng cự"
    assert zones[0].role == "Hỗ trợ"
    assert zones[0].status == "Đổi vai"
    assert zones[0].touches == 2


def test_strong_zone_and_volume_confirm_latest_candle() -> None:
    data = price_frame([12, 11.5, 11, 10.8, 10.6])
    data["atr14"] = 0.8
    data["volume_sma20"] = 100_000
    data.loc[data.index[-1], "volume"] = 150_000
    data["candle_pattern"] = pd.Series(pd.NA, index=data.index, dtype="string")
    data["candle_direction"] = pd.Series(pd.NA, index=data.index, dtype="string")
    data["candle_confirmed"] = False
    data["candle_confidence"] = 0
    data["candle_context"] = "Không có mẫu hình"
    data.loc[data.index[-1], ["candle_pattern", "candle_direction"]] = ["Hammer", "bullish"]
    zone = PriceZone(
        lower=9.8,
        upper=10.2,
        midpoint=10.0,
        role="Hỗ trợ",
        original_role="Hỗ trợ",
        status="Đang hoạt động",
        touches=3,
        strength=4,
        last_touch=data.index[-2],
        average_volume_ratio=1.2,
    )
    analysis = SupportResistanceAnalysis((), (zone,), zone, None, None)

    result = apply_zone_candlestick_confirmation(data, analysis)

    assert bool(result.iloc[-1]["candle_confirmed"])
    assert result.iloc[-1]["candle_confidence"] == 3
    assert "vùng giá mạnh" in result.iloc[-1]["candle_context"]

