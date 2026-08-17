"""Objective pivot-based price-pattern recognition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from vnstocklab.analysis.levels import Pivot, detect_pivots

PatternDirection = Literal["bullish", "bearish"]
PatternStatus = Literal["Đang hình thành", "Đã breakout", "Retest thành công", "Thất bại"]


@dataclass(frozen=True)
class PricePattern:
    """A measurable chart pattern and its actionable levels."""

    name: str
    direction: PatternDirection
    status: PatternStatus
    start: pd.Timestamp
    end: pd.Timestamp
    breakout_level: float
    target: float
    invalidation: float
    confidence: int
    volume_confirmed: bool
    points: tuple[Pivot, ...]
    description: str


def _pattern_status(
    data: pd.DataFrame,
    direction: PatternDirection,
    breakout_level: float,
    invalidation: float,
    pattern_end: pd.Timestamp,
    atr: float,
) -> tuple[PatternStatus, bool]:
    later = data.loc[data.index > pattern_end]
    if later.empty:
        return "Đang hình thành", False
    rolling_volume = data["volume"].rolling(20, min_periods=1).mean()
    if direction == "bullish":
        breakout_rows = later.loc[later["close"] > breakout_level]
        if breakout_rows.empty:
            return ("Thất bại", False) if float(data.iloc[-1]["close"]) < invalidation else (
                "Đang hình thành",
                False,
            )
        breakout_date = breakout_rows.index[0]
        breakout_position = int(data.index.searchsorted(breakout_date))
        volume_confirmed = float(data.loc[breakout_date, "volume"]) >= float(
            rolling_volume.iloc[breakout_position]
        ) * 1.2
        after = later.loc[later.index > breakout_date]
        retested = (
            (after["low"] <= breakout_level + atr * 0.35)
            & (after["close"] > breakout_level)
        ).any()
    else:
        breakout_rows = later.loc[later["close"] < breakout_level]
        if breakout_rows.empty:
            return ("Thất bại", False) if float(data.iloc[-1]["close"]) > invalidation else (
                "Đang hình thành",
                False,
            )
        breakout_date = breakout_rows.index[0]
        breakout_position = int(data.index.searchsorted(breakout_date))
        volume_confirmed = float(data.loc[breakout_date, "volume"]) >= float(
            rolling_volume.iloc[breakout_position]
        ) * 1.2
        after = later.loc[later.index > breakout_date]
        retested = (
            (after["high"] >= breakout_level - atr * 0.35)
            & (after["close"] < breakout_level)
        ).any()
    return ("Retest thành công" if retested else "Đã breakout"), volume_confirmed


def _make_pattern(
    data: pd.DataFrame,
    name: str,
    direction: PatternDirection,
    points: tuple[Pivot, ...],
    breakout_level: float,
    target: float,
    invalidation: float,
    atr: float,
) -> PricePattern:
    pattern_end = max(point.confirmed_at or point.date for point in points)
    status, volume_confirmed = _pattern_status(
        data, direction, breakout_level, invalidation, pattern_end, atr
    )
    confidence = min(
        5,
        2
        + int(len(points) >= 5)
        + int(volume_confirmed)
        + int(status == "Retest thành công"),
    )
    action = "vượt" if direction == "bullish" else "thủng"
    return PricePattern(
        name=name,
        direction=direction,
        status=status,
        start=min(point.date for point in points),
        end=pattern_end,
        breakout_level=breakout_level,
        target=target,
        invalidation=invalidation,
        confidence=confidence,
        volume_confirmed=volume_confirmed,
        points=points,
        description=f"{name}: chờ/đã {action} {breakout_level:.2f}, mục tiêu {target:.2f}",
    )


def _reversal_patterns(
    data: pd.DataFrame, highs: list[Pivot], lows: list[Pivot], atr: float
) -> list[PricePattern]:
    patterns: list[PricePattern] = []
    tolerance = atr
    if len(highs) >= 2:
        first, second = highs[-2:]
        between = [low for low in lows if first.date < low.date < second.date]
        if between and abs(first.price - second.price) <= tolerance:
            neckline = min(low.price for low in between)
            height = max(first.price, second.price) - neckline
            patterns.append(
                _make_pattern(
                    data,
                    "Hai đỉnh",
                    "bearish",
                    (first, *between, second),
                    neckline,
                    neckline - height,
                    max(first.price, second.price) + atr * 0.5,
                    atr,
                )
            )
    if len(lows) >= 2:
        first, second = lows[-2:]
        between = [high for high in highs if first.date < high.date < second.date]
        if between and abs(first.price - second.price) <= tolerance:
            neckline = max(high.price for high in between)
            height = neckline - min(first.price, second.price)
            patterns.append(
                _make_pattern(
                    data,
                    "Hai đáy",
                    "bullish",
                    (first, *between, second),
                    neckline,
                    neckline + height,
                    min(first.price, second.price) - atr * 0.5,
                    atr,
                )
            )
    if len(highs) >= 3:
        left, head, right = highs[-3:]
        between = [low for low in lows if left.date < low.date < right.date]
        shoulders_match = abs(left.price - right.price) <= tolerance
        head_is_higher = head.price > max(left.price, right.price) + atr
        if len(between) >= 2 and shoulders_match and head_is_higher:
            neckline = sum(low.price for low in between[-2:]) / 2
            patterns.append(
                _make_pattern(
                    data,
                    "Vai–đầu–vai",
                    "bearish",
                    (left, between[-2], head, between[-1], right),
                    neckline,
                    neckline - (head.price - neckline),
                    head.price + atr * 0.5,
                    atr,
                )
            )
    if len(lows) >= 3:
        left, head, right = lows[-3:]
        between = [high for high in highs if left.date < high.date < right.date]
        shoulders_match = abs(left.price - right.price) <= tolerance
        head_is_lower = head.price < min(left.price, right.price) - atr
        if len(between) >= 2 and shoulders_match and head_is_lower:
            neckline = sum(high.price for high in between[-2:]) / 2
            patterns.append(
                _make_pattern(
                    data,
                    "Vai–đầu–vai ngược",
                    "bullish",
                    (left, between[-2], head, between[-1], right),
                    neckline,
                    neckline + (neckline - head.price),
                    head.price - atr * 0.5,
                    atr,
                )
            )
    return patterns


def _consolidation_pattern(
    data: pd.DataFrame, highs: list[Pivot], lows: list[Pivot], atr: float
) -> PricePattern | None:
    if len(highs) < 3 or len(lows) < 3:
        return None
    recent_highs = highs[-3:]
    recent_lows = lows[-3:]
    recent_dates = [pivot.date for pivot in (*recent_highs, *recent_lows)]
    if (max(recent_dates) - min(recent_dates)).days > 180:
        return None
    high_prices = np.array([pivot.price for pivot in recent_highs])
    low_prices = np.array([pivot.price for pivot in recent_lows])
    high_slope = float(np.polyfit(np.arange(3), high_prices, 1)[0])
    low_slope = float(np.polyfit(np.arange(3), low_prices, 1)[0])
    high_level = float(high_prices.mean())
    low_level = float(low_prices.mean())
    width = high_level - low_level
    if width < atr * 1.5:
        return None
    flat_threshold = atr * 0.25
    points = tuple(sorted((*recent_highs, *recent_lows), key=lambda pivot: pivot.date))
    direction: PatternDirection
    if abs(high_slope) <= flat_threshold and low_slope > flat_threshold:
        name, direction, breakout = "Tam giác tăng", "bullish", high_level
        target, invalidation = breakout + width, low_level - atr * 0.5
    elif abs(low_slope) <= flat_threshold and high_slope < -flat_threshold:
        name, direction, breakout = "Tam giác giảm", "bearish", low_level
        target, invalidation = breakout - width, high_level + atr * 0.5
    elif high_slope < -flat_threshold and low_slope > flat_threshold:
        current = float(data.iloc[-1]["close"])
        direction = "bullish" if current >= (high_level + low_level) / 2 else "bearish"
        name = "Tam giác cân"
        breakout = high_prices[-1] if direction == "bullish" else low_prices[-1]
        target = breakout + width if direction == "bullish" else breakout - width
        invalidation = low_prices[-1] if direction == "bullish" else high_prices[-1]
    elif np.ptp(high_prices) <= atr and np.ptp(low_prices) <= atr:
        current = float(data.iloc[-1]["close"])
        direction = "bullish" if current >= (high_level + low_level) / 2 else "bearish"
        name = "Nền chữ nhật"
        breakout = high_level if direction == "bullish" else low_level
        target = breakout + width if direction == "bullish" else breakout - width
        invalidation = low_level if direction == "bullish" else high_level
    else:
        return None
    return _make_pattern(
        data, name, direction, points, breakout, target, invalidation, atr
    )


def analyze_price_patterns(data: pd.DataFrame) -> tuple[PricePattern, ...]:
    """Detect the deliberately small, backtestable pattern set."""
    pivots = detect_pivots(data, window=3)
    highs = [pivot for pivot in pivots if pivot.kind == "high"]
    lows = [pivot for pivot in pivots if pivot.kind == "low"]
    atr = (
        float(data["atr14"].iloc[-1])
        if "atr14" in data.columns and pd.notna(data["atr14"].iloc[-1])
        else float((data["high"] - data["low"]).tail(14).mean())
    )
    patterns = _reversal_patterns(data, highs, lows, atr)
    consolidation = _consolidation_pattern(data, highs, lows, atr)
    if consolidation is not None:
        patterns.append(consolidation)
    return tuple(sorted(patterns, key=lambda pattern: pattern.end, reverse=True))
