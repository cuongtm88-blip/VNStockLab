"""Context-aware Japanese candlestick pattern recognition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

import numpy as np
import pandas as pd

Direction = Literal["bullish", "bearish", "neutral"]


@dataclass(frozen=True)
class CandlestickEvent:
    """A candlestick pattern observed on one trading session."""

    date: pd.Timestamp
    pattern: str
    direction: Direction
    confidence: int
    confirmed: bool
    context: str


def _candle_geometry(data: pd.DataFrame) -> pd.DataFrame:
    geometry = pd.DataFrame(index=data.index)
    geometry["body"] = (data["close"] - data["open"]).abs()
    geometry["range"] = (data["high"] - data["low"]).replace(0, np.nan)
    geometry["upper"] = data["high"] - data[["open", "close"]].max(axis=1)
    geometry["lower"] = data[["open", "close"]].min(axis=1) - data["low"]
    geometry["bull"] = data["close"] > data["open"]
    geometry["bear"] = data["close"] < data["open"]
    return geometry


def detect_candlestick_patterns(data: pd.DataFrame) -> pd.DataFrame:
    """Annotate OHLCV rows with the highest-priority candlestick pattern."""
    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {', '.join(sorted(missing))}")

    result = data.copy()
    geometry = _candle_geometry(result)
    average_body = geometry["body"].rolling(20, min_periods=5).mean()
    small_body = geometry["body"] <= geometry["range"] * 0.1
    meaningful_body = geometry["body"] >= average_body * 0.7

    result["candle_pattern"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result["candle_direction"] = pd.Series(pd.NA, index=result.index, dtype="string")

    def assign(mask: pd.Series, name: str, direction: Direction) -> None:
        available = mask.fillna(False) & result["candle_pattern"].isna()
        result.loc[available, "candle_pattern"] = name
        result.loc[available, "candle_direction"] = direction

    # Three-candle patterns receive precedence over two- and one-candle patterns.
    three_white_soldiers = (
        geometry["bull"]
        & geometry["bull"].shift(1)
        & geometry["bull"].shift(2)
        & (result["close"] > result["close"].shift(1))
        & (result["close"].shift(1) > result["close"].shift(2))
        & meaningful_body
        & meaningful_body.shift(1)
        & meaningful_body.shift(2)
    )
    three_black_crows = (
        geometry["bear"]
        & geometry["bear"].shift(1)
        & geometry["bear"].shift(2)
        & (result["close"] < result["close"].shift(1))
        & (result["close"].shift(1) < result["close"].shift(2))
        & meaningful_body
        & meaningful_body.shift(1)
        & meaningful_body.shift(2)
    )
    first_midpoint = (result["open"].shift(2) + result["close"].shift(2)) / 2
    middle_small = geometry["body"].shift(1) <= average_body.shift(1) * 0.6
    morning_star = (
        geometry["bear"].shift(2)
        & middle_small
        & geometry["bull"]
        & (result["close"] > first_midpoint)
        & meaningful_body.shift(2)
        & meaningful_body
    )
    evening_star = (
        geometry["bull"].shift(2)
        & middle_small
        & geometry["bear"]
        & (result["close"] < first_midpoint)
        & meaningful_body.shift(2)
        & meaningful_body
    )
    assign(morning_star, "Morning Star", "bullish")
    assign(evening_star, "Evening Star", "bearish")
    assign(three_white_soldiers, "Three White Soldiers", "bullish")
    assign(three_black_crows, "Three Black Crows", "bearish")

    previous_body_high = result[["open", "close"]].max(axis=1).shift(1)
    previous_body_low = result[["open", "close"]].min(axis=1).shift(1)
    current_body_high = result[["open", "close"]].max(axis=1)
    current_body_low = result[["open", "close"]].min(axis=1)
    bullish_engulfing = (
        geometry["bull"]
        & geometry["bear"].shift(1)
        & (current_body_low <= previous_body_low)
        & (current_body_high >= previous_body_high)
        & meaningful_body
    )
    bearish_engulfing = (
        geometry["bear"]
        & geometry["bull"].shift(1)
        & (current_body_low <= previous_body_low)
        & (current_body_high >= previous_body_high)
        & meaningful_body
    )
    assign(bullish_engulfing, "Bullish Engulfing", "bullish")
    assign(bearish_engulfing, "Bearish Engulfing", "bearish")

    hammer = (
        (geometry["lower"] >= geometry["body"] * 2)
        & (geometry["upper"] <= geometry["body"] * 0.6)
        & (geometry["body"] / geometry["range"] <= 0.4)
    )
    shooting_star = (
        (geometry["upper"] >= geometry["body"] * 2)
        & (geometry["lower"] <= geometry["body"] * 0.6)
        & (geometry["body"] / geometry["range"] <= 0.4)
    )
    marubozu = (geometry["body"] / geometry["range"] >= 0.9) & meaningful_body
    assign(hammer, "Hammer", "bullish")
    assign(shooting_star, "Shooting Star", "bearish")
    assign(marubozu & geometry["bull"], "Bullish Marubozu", "bullish")
    assign(marubozu & geometry["bear"], "Bearish Marubozu", "bearish")
    assign(small_body, "Doji", "neutral")

    prior_close = result["close"].shift(1)
    prior_sma20 = result.get("sma20", result["close"].rolling(20).mean()).shift(1)
    prior_move = prior_close.pct_change(5)
    down_context = (prior_close < prior_sma20) | (prior_move < -0.03)
    up_context = (prior_close > prior_sma20) | (prior_move > 0.03)
    volume_average = result.get("volume_sma20", result["volume"].rolling(20).mean())
    volume_confirmation = result["volume"] >= volume_average
    atr = result.get("atr14", (result["high"] - result["low"]).rolling(14).mean())
    support = result.get("support20", result["low"].rolling(20).min()).shift(1)
    resistance = result.get("resistance20", result["high"].rolling(20).max()).shift(1)
    near_support = result["low"] <= support + atr * 0.35
    near_resistance = result["high"] >= resistance - atr * 0.35

    bullish = result["candle_direction"].eq("bullish").fillna(False)
    bearish = result["candle_direction"].eq("bearish").fillna(False)
    neutral = result["candle_direction"].eq("neutral").fillna(False)
    context_confirmation = (bullish & (down_context | near_support)) | (
        bearish & (up_context | near_resistance)
    )
    context_confirmation = context_confirmation.fillna(False)
    volume_confirmation = volume_confirmation.fillna(False)
    result["candle_confidence"] = (
        result["candle_pattern"].notna().astype(int)
        + context_confirmation.astype(int)
        + volume_confirmation.astype(int)
    ).where(~neutral, 1)
    result["candle_confirmed"] = (
        ~neutral & context_confirmation & volume_confirmation
    ).astype(bool)
    result["candle_context"] = "Không có mẫu hình"
    result.loc[result["candle_pattern"].notna(), "candle_context"] = "Chưa có xác nhận bối cảnh"
    result.loc[context_confirmation, "candle_context"] = "Phù hợp xu hướng/vùng giá"
    result.loc[result["candle_confirmed"], "candle_context"] = "Được khối lượng xác nhận"
    result.loc[neutral, "candle_context"] = "Tín hiệu do dự, cần nến xác nhận tiếp theo"
    return result


def candlestick_events(data: pd.DataFrame, lookback: int = 30) -> tuple[CandlestickEvent, ...]:
    """Return recent detected patterns for tables and chart annotations."""
    detected = (
        data if "candle_pattern" in data.columns else detect_candlestick_patterns(data)
    ).tail(lookback)
    events: list[CandlestickEvent] = []
    for date, row in detected.loc[detected["candle_pattern"].notna()].iterrows():
        events.append(
            CandlestickEvent(
                date=pd.Timestamp(str(date)),
                pattern=str(row["candle_pattern"]),
                direction=cast(Direction, str(row["candle_direction"])),
                confidence=int(row["candle_confidence"]),
                confirmed=bool(row["candle_confirmed"]),
                context=str(row["candle_context"]),
            )
        )
    return tuple(events)
