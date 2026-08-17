from __future__ import annotations

import pandas as pd

from vnstocklab.analysis.dow import (
    analyze_dow_structure,
    classify_market_structure,
    classify_pivots,
)
from vnstocklab.analysis.indicators import enrich_indicators
from vnstocklab.analysis.levels import Pivot
from vnstocklab.data.demo import generate_demo_prices


def pivot(date: str, price: float, kind: str) -> Pivot:
    return Pivot(
        date=pd.Timestamp(date),
        price=price,
        kind=kind,  # type: ignore[arg-type]
        volume=100_000,
        confirmed_at=pd.Timestamp(date) + pd.Timedelta(days=3),
    )


def test_classifies_higher_and_lower_market_structure() -> None:
    rising = (
        pivot("2026-01-01", 10, "low"),
        pivot("2026-01-05", 15, "high"),
        pivot("2026-01-10", 12, "low"),
        pivot("2026-01-15", 17, "high"),
    )
    points = classify_pivots(rising)

    assert [point.label for point in points] == ["HL", "HH"]
    assert classify_market_structure(points) == "Xu hướng tăng"

    falling = rising + (
        pivot("2026-01-20", 9, "low"),
        pivot("2026-01-25", 14, "high"),
    )
    falling_points = classify_pivots(falling)
    assert [point.label for point in falling_points[-2:]] == ["LL", "LH"]
    assert classify_market_structure(falling_points) == "Xu hướng giảm"


def test_pivot_confirmation_date_is_after_extreme() -> None:
    data = generate_demo_prices("FPT", periods=100)
    dow = analyze_dow_structure(enrich_indicators(data), breakout=None)

    assert dow.short_term.points
    for point in dow.short_term.points:
        assert point.pivot.confirmed_at is not None
        assert point.pivot.confirmed_at > point.pivot.date


def test_dow_score_requires_confirmed_breakout_agreement() -> None:
    data = enrich_indicators(generate_demo_prices("HPG", periods=300))
    result = analyze_dow_structure(data, breakout=None)

    assert result.score_adjustment == 0
    assert result.short_term.state in {
        "Xu hướng tăng",
        "Xu hướng giảm",
        "Đi ngang",
        "Chưa xác định",
    }
    assert result.medium_term.name == "Trung hạn"
    assert result.weekly.name == "Khung tuần"

