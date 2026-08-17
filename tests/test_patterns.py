from __future__ import annotations

import numpy as np
import pandas as pd

from vnstocklab.analysis.indicators import enrich_indicators
from vnstocklab.analysis.patterns import analyze_price_patterns


def anchored_prices(anchors: list[tuple[int, float]], periods: int) -> pd.DataFrame:
    positions = np.arange(periods)
    close = np.interp(positions, [item[0] for item in anchors], [item[1] for item in anchors])
    dates = pd.bdate_range("2026-01-01", periods=periods)
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 0.15,
            "low": close - 0.15,
            "close": close,
            "volume": np.full(periods, 100_000),
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


def test_detects_double_top_with_measured_target() -> None:
    data = anchored_prices(
        [(0, 10), (10, 15), (20, 11), (30, 15.1), (40, 10), (59, 9)], periods=60
    )
    patterns = analyze_price_patterns(enrich_indicators(data))
    double_top = next(pattern for pattern in patterns if pattern.name == "Hai đỉnh")

    assert double_top.direction == "bearish"
    assert double_top.breakout_level > double_top.target
    assert double_top.invalidation > double_top.breakout_level
    assert double_top.status in {"Đã breakout", "Retest thành công"}


def test_detects_head_and_shoulders_and_waits_for_confirmation() -> None:
    data = anchored_prices(
        [
            (0, 10),
            (10, 15),
            (20, 12),
            (30, 18),
            (40, 12.1),
            (50, 15.2),
            (60, 13),
            (69, 11),
        ],
        periods=70,
    )
    patterns = analyze_price_patterns(enrich_indicators(data))
    pattern = next(pattern for pattern in patterns if pattern.name == "Vai–đầu–vai")

    assert pattern.direction == "bearish"
    assert len(pattern.points) == 5
    assert pattern.end > max(point.date for point in pattern.points)
    assert pattern.target < pattern.breakout_level

