"""Dow Theory market-structure classification from confirmed pivots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from vnstocklab.analysis.ichimoku import resample_weekly
from vnstocklab.analysis.levels import Breakout, Pivot, detect_pivots

StructureLabel = Literal["HH", "HL", "LH", "LL"]
MarketStructure = Literal["Xu hướng tăng", "Xu hướng giảm", "Đi ngang", "Chưa xác định"]
StructureEventKind = Literal["BOS tăng", "BOS giảm", "CHoCH tăng", "CHoCH giảm"]


@dataclass(frozen=True)
class StructurePoint:
    """A pivot classified relative to the previous pivot of the same kind."""

    pivot: Pivot
    label: StructureLabel


@dataclass(frozen=True)
class StructureEvent:
    """A structure continuation or change known only on confirmation date."""

    date: pd.Timestamp
    kind: StructureEventKind
    price: float
    volume_confirmed: bool
    description: str


@dataclass(frozen=True)
class DowTimeframe:
    """Dow structure for one pivot sensitivity/timeframe."""

    name: str
    state: MarketStructure
    points: tuple[StructurePoint, ...]
    events: tuple[StructureEvent, ...]
    summary: str


@dataclass(frozen=True)
class DowAnalysis:
    """Short-, medium- and weekly Dow structure agreement."""

    short_term: DowTimeframe
    medium_term: DowTimeframe
    weekly: DowTimeframe
    aligned: bool
    score_adjustment: int
    summary: str


def classify_pivots(pivots: tuple[Pivot, ...]) -> tuple[StructurePoint, ...]:
    """Label highs as HH/LH and lows as HL/LL."""
    previous_high: float | None = None
    previous_low: float | None = None
    points: list[StructurePoint] = []
    for pivot in sorted(pivots, key=lambda item: item.date):
        if pivot.kind == "high":
            if previous_high is not None:
                points.append(StructurePoint(pivot, "HH" if pivot.price > previous_high else "LH"))
            previous_high = pivot.price
        else:
            if previous_low is not None:
                points.append(StructurePoint(pivot, "HL" if pivot.price > previous_low else "LL"))
            previous_low = pivot.price
    return tuple(points)


def classify_market_structure(points: tuple[StructurePoint, ...]) -> MarketStructure:
    highs = [point.label for point in points if point.pivot.kind == "high"]
    lows = [point.label for point in points if point.pivot.kind == "low"]
    if not highs or not lows:
        return "Chưa xác định"
    if highs[-1] == "HH" and lows[-1] == "HL":
        return "Xu hướng tăng"
    if highs[-1] == "LH" and lows[-1] == "LL":
        return "Xu hướng giảm"
    return "Đi ngang"


def _events(data: pd.DataFrame, points: tuple[StructurePoint, ...]) -> tuple[StructureEvent, ...]:
    events: list[StructureEvent] = []
    established_state: MarketStructure = "Chưa xác định"
    seen_points: list[StructurePoint] = []
    volume_average = data["volume"].rolling(20, min_periods=1).mean()
    for point in points:
        previous_state = established_state
        seen_points.append(point)
        current_state = classify_market_structure(tuple(seen_points))
        confirmation_date = point.pivot.confirmed_at or point.pivot.date
        position = min(int(data.index.searchsorted(confirmation_date)), len(data) - 1)
        confirmed = point.pivot.volume >= float(volume_average.iloc[position]) * 1.1
        kind: StructureEventKind | None = None
        if previous_state == "Xu hướng giảm" and point.label == "HH":
            kind = "CHoCH tăng"
        elif previous_state == "Xu hướng tăng" and point.label == "LL":
            kind = "CHoCH giảm"
        elif current_state == "Xu hướng tăng" and point.label == "HH":
            kind = "BOS tăng"
        elif current_state == "Xu hướng giảm" and point.label == "LL":
            kind = "BOS giảm"
        if kind is not None:
            events.append(
                StructureEvent(
                    date=confirmation_date,
                    kind=kind,
                    price=point.pivot.price,
                    volume_confirmed=confirmed,
                    description=f"{kind} được xác nhận tại {point.pivot.price:.2f}",
                )
            )
        if current_state in {"Xu hướng tăng", "Xu hướng giảm"}:
            established_state = current_state
    return tuple(events)


def analyze_timeframe(data: pd.DataFrame, window: int, name: str) -> DowTimeframe:
    """Analyze one timeframe or pivot sensitivity."""
    points = classify_pivots(detect_pivots(data, window=window))
    state = classify_market_structure(points)
    events = _events(data, points)
    recent = ", ".join(point.label for point in points[-4:]) or "chưa đủ pivot"
    return DowTimeframe(
        name=name,
        state=state,
        points=points,
        events=events,
        summary=f"{name}: {state.lower()} ({recent})",
    )


def analyze_dow_structure(data: pd.DataFrame, breakout: Breakout | None) -> DowAnalysis:
    """Combine short, medium and weekly Dow structures with breakout confirmation."""
    short_term = analyze_timeframe(data, window=3, name="Ngắn hạn")
    medium_term = analyze_timeframe(data, window=8, name="Trung hạn")
    weekly_data = resample_weekly(data)
    weekly = analyze_timeframe(weekly_data, window=2, name="Khung tuần")
    bullish = (
        short_term.state == "Xu hướng tăng"
        and medium_term.state == "Xu hướng tăng"
        and weekly.state != "Xu hướng giảm"
    )
    bearish = (
        short_term.state == "Xu hướng giảm"
        and medium_term.state == "Xu hướng giảm"
        and weekly.state != "Xu hướng tăng"
    )
    aligned = bullish or bearish
    breakout_agrees = breakout is not None and breakout.confirmed_by_volume and (
        (bullish and breakout.direction == "up") or (bearish and breakout.direction == "down")
    )
    adjustment = 1 if breakout_agrees and bullish else -1 if breakout_agrees else 0
    if breakout_agrees:
        summary = "Cấu trúc Dow và breakout có khối lượng đồng thuận"
    elif aligned:
        summary = "Cấu trúc Dow đồng thuận nhưng chưa có breakout được xác nhận"
    else:
        summary = "Cấu trúc Dow ngắn hạn, trung hạn và tuần chưa đồng thuận"
    return DowAnalysis(short_term, medium_term, weekly, aligned, adjustment, summary)
