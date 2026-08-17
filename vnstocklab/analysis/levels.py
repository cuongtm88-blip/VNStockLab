"""Swing pivots and ATR-clustered support/resistance zones."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

PivotKind = Literal["high", "low"]
ZoneRole = Literal["Hỗ trợ", "Kháng cự"]
ZoneStatus = Literal["Đang hoạt động", "Đã phá vỡ", "Đổi vai"]
BreakoutDirection = Literal["up", "down"]


@dataclass(frozen=True)
class Pivot:
    """Confirmed local price extreme."""

    date: pd.Timestamp
    price: float
    kind: PivotKind
    volume: float
    confirmed_at: pd.Timestamp | None = None


@dataclass(frozen=True)
class PriceZone:
    """Cluster of nearby pivots representing a price area."""

    lower: float
    upper: float
    midpoint: float
    role: ZoneRole
    original_role: ZoneRole
    status: ZoneStatus
    touches: int
    strength: int
    last_touch: pd.Timestamp
    average_volume_ratio: float


@dataclass(frozen=True)
class Breakout:
    """Latest confirmed close outside a previously active zone."""

    direction: BreakoutDirection
    zone_midpoint: float
    confirmed_by_volume: bool
    description: str


@dataclass(frozen=True)
class SupportResistanceAnalysis:
    """Latest support/resistance map used by UI and signal scoring."""

    pivots: tuple[Pivot, ...]
    zones: tuple[PriceZone, ...]
    nearest_support: PriceZone | None
    nearest_resistance: PriceZone | None
    breakout: Breakout | None


def detect_pivots(data: pd.DataFrame, window: int = 3) -> tuple[Pivot, ...]:
    """Detect pivots confirmed by ``window`` bars on both sides."""
    if window < 1:
        raise ValueError("Pivot window phải từ 1 trở lên")
    if len(data) < window * 2 + 1:
        return ()
    pivots: list[Pivot] = []
    for position in range(window, len(data) - window):
        row = data.iloc[position]
        nearby = data.iloc[position - window : position + window + 1]
        high = float(row["high"])
        low = float(row["low"])
        if high == float(nearby["high"].max()) and (nearby["high"] == high).sum() == 1:
            pivots.append(
                Pivot(
                    pd.Timestamp(str(data.index[position])),
                    high,
                    "high",
                    float(row["volume"]),
                    pd.Timestamp(str(data.index[position + window])),
                )
            )
        if low == float(nearby["low"].min()) and (nearby["low"] == low).sum() == 1:
            pivots.append(
                Pivot(
                    pd.Timestamp(str(data.index[position])),
                    low,
                    "low",
                    float(row["volume"]),
                    pd.Timestamp(str(data.index[position + window])),
                )
            )
    return tuple(pivots)


def _zone_status(
    data: pd.DataFrame,
    pivots: list[Pivot],
    lower: float,
    upper: float,
    original_role: ZoneRole,
    tolerance: float,
) -> tuple[ZoneRole, ZoneStatus]:
    last_pivot_date = max(pivot.date for pivot in pivots)
    later = data.loc[data.index > last_pivot_date]
    current_close = float(data.iloc[-1]["close"])
    if original_role == "Kháng cự" and current_close > upper:
        breakout_rows = later.loc[later["close"] > upper]
        if breakout_rows.empty:
            return "Hỗ trợ", "Đã phá vỡ"
        after_breakout = later.loc[later.index > breakout_rows.index[0]]
        retested = (
            (after_breakout["low"] <= upper + tolerance)
            & (after_breakout["close"] > upper)
        ).any()
        return "Hỗ trợ", "Đổi vai" if retested else "Đã phá vỡ"
    if original_role == "Hỗ trợ" and current_close < lower:
        breakout_rows = later.loc[later["close"] < lower]
        if breakout_rows.empty:
            return "Kháng cự", "Đã phá vỡ"
        after_breakout = later.loc[later.index > breakout_rows.index[0]]
        retested = (
            (after_breakout["high"] >= lower - tolerance)
            & (after_breakout["close"] < lower)
        ).any()
        return "Kháng cự", "Đổi vai" if retested else "Đã phá vỡ"
    return ("Hỗ trợ", "Đang hoạt động") if current_close >= upper else (
        "Kháng cự",
        "Đang hoạt động",
    )


def cluster_zones(
    data: pd.DataFrame, pivots: tuple[Pivot, ...], tolerance: float
) -> tuple[PriceZone, ...]:
    """Cluster pivots by price proximity and score each resulting zone."""
    if tolerance <= 0:
        raise ValueError("Zone tolerance phải lớn hơn 0")
    clusters: list[list[Pivot]] = []
    for pivot in sorted(pivots, key=lambda item: item.price):
        matching = next(
            (
                cluster
                for cluster in clusters
                if abs(pivot.price - sum(item.price for item in cluster) / len(cluster))
                <= tolerance
            ),
            None,
        )
        if matching is None:
            clusters.append([pivot])
        else:
            matching.append(pivot)

    average_volume = float(data["volume"].rolling(20, min_periods=1).mean().iloc[-1])
    zones: list[PriceZone] = []
    for cluster in clusters:
        if len(cluster) < 2:
            continue
        midpoint = sum(pivot.price for pivot in cluster) / len(cluster)
        lower = min(pivot.price for pivot in cluster) - tolerance * 0.2
        upper = max(pivot.price for pivot in cluster) + tolerance * 0.2
        high_count = sum(pivot.kind == "high" for pivot in cluster)
        original_role: ZoneRole = "Kháng cự" if high_count >= len(cluster) / 2 else "Hỗ trợ"
        role, status = _zone_status(data, cluster, lower, upper, original_role, tolerance)
        volume_ratio = (
            sum(pivot.volume for pivot in cluster) / len(cluster) / average_volume
            if average_volume > 0
            else 1.0
        )
        last_touch = max(pivot.date for pivot in cluster)
        last_touch_position = int(data.index.searchsorted(last_touch))
        age = max(0, len(data) - 1 - last_touch_position)
        recency_point = 1 if age <= 60 else 0
        strength = min(5, 1 + min(2, len(cluster) - 1) + int(volume_ratio >= 1.1) + recency_point)
        zones.append(
            PriceZone(
                lower=lower,
                upper=upper,
                midpoint=midpoint,
                role=role,
                original_role=original_role,
                status=status,
                touches=len(cluster),
                strength=strength,
                last_touch=last_touch,
                average_volume_ratio=volume_ratio,
            )
        )
    return tuple(sorted(zones, key=lambda zone: zone.midpoint))


def analyze_support_resistance(
    data: pd.DataFrame, window: int = 3, tolerance_atr: float = 0.6
) -> SupportResistanceAnalysis:
    """Build the current zone map and detect the latest breakout."""
    pivots = detect_pivots(data, window=window)
    atr = (
        float(data["atr14"].iloc[-1])
        if "atr14" in data.columns and pd.notna(data["atr14"].iloc[-1])
        else float((data["high"] - data["low"]).tail(14).mean())
    )
    tolerance = max(atr * tolerance_atr, float(data.iloc[-1]["close"]) * 0.002)
    zones = cluster_zones(data, pivots, tolerance)
    close = float(data.iloc[-1]["close"])
    supports = [zone for zone in zones if zone.role == "Hỗ trợ" and zone.upper <= close + tolerance]
    resistances = [
        zone for zone in zones if zone.role == "Kháng cự" and zone.lower >= close - tolerance
    ]
    nearest_support = max(supports, key=lambda zone: zone.midpoint, default=None)
    nearest_resistance = min(resistances, key=lambda zone: zone.midpoint, default=None)

    breakout: Breakout | None = None
    previous_close = float(data.iloc[-2]["close"])
    volume_average = float(data["volume"].rolling(20).mean().iloc[-1])
    volume_confirmed = float(data.iloc[-1]["volume"]) >= volume_average * 1.2
    for zone in zones:
        if previous_close <= zone.upper < close:
            breakout = Breakout(
                "up",
                zone.midpoint,
                volume_confirmed,
                f"Giá đóng cửa vượt vùng {zone.lower:.2f}–{zone.upper:.2f}",
            )
        elif previous_close >= zone.lower > close:
            breakout = Breakout(
                "down",
                zone.midpoint,
                volume_confirmed,
                f"Giá đóng cửa thủng vùng {zone.lower:.2f}–{zone.upper:.2f}",
            )
    return SupportResistanceAnalysis(
        pivots=pivots,
        zones=zones,
        nearest_support=nearest_support,
        nearest_resistance=nearest_resistance,
        breakout=breakout,
    )


def apply_zone_candlestick_confirmation(
    data: pd.DataFrame, analysis: SupportResistanceAnalysis
) -> pd.DataFrame:
    """Confirm only the latest candle when it aligns with a nearby strong zone and volume."""
    result = data.copy()
    latest = result.iloc[-1]
    if pd.isna(latest.get("candle_pattern")) or latest.get("candle_direction") == "neutral":
        return result
    atr = float(latest["atr14"])
    volume_confirmed = float(latest["volume"]) >= float(latest["volume_sma20"])
    near_support = analysis.nearest_support is not None and (
        float(latest["low"]) - analysis.nearest_support.upper <= atr
    )
    near_resistance = analysis.nearest_resistance is not None and (
        analysis.nearest_resistance.lower - float(latest["high"]) <= atr
    )
    direction_matches = (latest["candle_direction"] == "bullish" and near_support) or (
        latest["candle_direction"] == "bearish" and near_resistance
    )
    if direction_matches and volume_confirmed:
        index = result.index[-1]
        result.loc[index, "candle_confirmed"] = True
        result.loc[index, "candle_confidence"] = max(
            3, int(result.loc[index, "candle_confidence"])
        )
        result.loc[index, "candle_context"] = "Được vùng giá mạnh và khối lượng xác nhận"
    return result
