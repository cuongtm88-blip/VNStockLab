"""Ichimoku Kinko Hyo and multi-timeframe confirmation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

IchimokuState = Literal["Tăng mạnh", "Tăng", "Trung tính", "Giảm", "Giảm mạnh"]


@dataclass(frozen=True)
class IchimokuSnapshot:
    """Explainable Ichimoku state for one timeframe."""

    timeframe: str
    score: int
    state: IchimokuState
    price_position: str
    tk_relation: str
    tk_cross: str
    future_cloud: str
    chikou_confirmation: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class MultiTimeframeIchimoku:
    """Daily/weekly Ichimoku agreement used by the signal engine."""

    daily: IchimokuSnapshot
    weekly: IchimokuSnapshot | None
    aligned: bool
    score_adjustment: int
    summary: str


def add_ichimoku(data: pd.DataFrame) -> pd.DataFrame:
    """Add standard 9/26/52 Ichimoku lines without forward-looking calculations."""
    if len(data) < 52:
        raise ValueError("Cần ít nhất 52 phiên để tính Ichimoku")
    result = data.copy()
    high9 = result["high"].rolling(9).max()
    low9 = result["low"].rolling(9).min()
    high26 = result["high"].rolling(26).max()
    low26 = result["low"].rolling(26).min()
    high52 = result["high"].rolling(52).max()
    low52 = result["low"].rolling(52).min()

    result["tenkan_sen"] = (high9 + low9) / 2
    result["kijun_sen"] = (high26 + low26) / 2
    result["senkou_a_projected"] = (result["tenkan_sen"] + result["kijun_sen"]) / 2
    result["senkou_b_projected"] = (high52 + low52) / 2
    result["senkou_span_a"] = result["senkou_a_projected"].shift(26)
    result["senkou_span_b"] = result["senkou_b_projected"].shift(26)
    result["chikou_span"] = result["close"].shift(-26)
    return result


def resample_weekly(data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily OHLCV into Friday-labelled weekly candles."""
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("Dữ liệu đa khung thời gian cần DatetimeIndex")
    weekly = data[["open", "high", "low", "close", "volume"]].resample("W-FRI").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    return weekly.dropna(subset=["open", "high", "low", "close"])


def ichimoku_snapshot(data: pd.DataFrame, timeframe: str) -> IchimokuSnapshot:
    """Classify the latest Ichimoku state with transparent component scores."""
    enriched = data if "tenkan_sen" in data.columns else add_ichimoku(data)
    latest = enriched.iloc[-1]
    score = 0
    reasons: list[str] = []

    cloud_a = latest["senkou_span_a"]
    cloud_b = latest["senkou_span_b"]
    cloud_is_projected = pd.isna(cloud_a) or pd.isna(cloud_b)
    if cloud_is_projected:
        cloud_a = latest["senkou_a_projected"]
        cloud_b = latest["senkou_b_projected"]
    cloud_top = max(float(cloud_a), float(cloud_b))
    cloud_bottom = min(float(cloud_a), float(cloud_b))
    close = float(latest["close"])
    if close > cloud_top:
        price_position = "Trên mây"
        score += 2
        reasons.append("Giá nằm trên mây Kumo")
    elif close < cloud_bottom:
        price_position = "Dưới mây"
        score -= 2
        reasons.append("Giá nằm dưới mây Kumo")
    else:
        price_position = "Trong mây"
        reasons.append("Giá nằm trong vùng cân bằng Kumo")

    if latest["tenkan_sen"] > latest["kijun_sen"]:
        tk_relation = "Tenkan trên Kijun"
        score += 1
        reasons.append("Tenkan-sen nằm trên Kijun-sen")
    elif latest["tenkan_sen"] < latest["kijun_sen"]:
        tk_relation = "Tenkan dưới Kijun"
        score -= 1
        reasons.append("Tenkan-sen nằm dưới Kijun-sen")
    else:
        tk_relation = "Tenkan bằng Kijun"
        reasons.append("Tenkan-sen và Kijun-sen chưa phân kỳ")

    previous = enriched.iloc[-2]
    if (
        previous["tenkan_sen"] <= previous["kijun_sen"]
        and latest["tenkan_sen"] > latest["kijun_sen"]
    ):
        tk_cross = "Giao cắt tăng"
        reasons.append("Tenkan-sen vừa cắt lên Kijun-sen")
    elif (
        previous["tenkan_sen"] >= previous["kijun_sen"]
        and latest["tenkan_sen"] < latest["kijun_sen"]
    ):
        tk_cross = "Giao cắt giảm"
        reasons.append("Tenkan-sen vừa cắt xuống Kijun-sen")
    else:
        tk_cross = "Không có giao cắt mới"

    if latest["senkou_a_projected"] > latest["senkou_b_projected"]:
        future_cloud = "Mây tương lai tăng"
        score += 1
        reasons.append("Senkou A dự phóng nằm trên Senkou B")
    else:
        future_cloud = "Mây tương lai giảm"
        score -= 1
        reasons.append("Senkou A dự phóng không vượt Senkou B")

    comparison_high = enriched["high"].shift(26).iloc[-1]
    comparison_low = enriched["low"].shift(26).iloc[-1]
    if close > comparison_high:
        chikou_confirmation = "Xác nhận tăng"
        score += 1
        reasons.append("Giá hiện tại vượt vùng giá 26 phiên trước")
    elif close < comparison_low:
        chikou_confirmation = "Xác nhận giảm"
        score -= 1
        reasons.append("Giá hiện tại thấp hơn vùng giá 26 phiên trước")
    else:
        chikou_confirmation = "Chưa xác nhận"
        reasons.append("Chikou chưa tách khỏi vùng giá quá khứ")

    state: IchimokuState
    if score >= 4:
        state = "Tăng mạnh"
    elif score >= 2:
        state = "Tăng"
    elif score <= -4:
        state = "Giảm mạnh"
    elif score <= -2:
        state = "Giảm"
    else:
        state = "Trung tính"
    if cloud_is_projected:
        reasons.append("Khung dữ liệu ngắn: vị trí giá được so với mây dự phóng hiện tại")
    return IchimokuSnapshot(
        timeframe=timeframe,
        score=score,
        state=state,
        price_position=price_position,
        tk_relation=tk_relation,
        tk_cross=tk_cross,
        future_cloud=future_cloud,
        chikou_confirmation=chikou_confirmation,
        reasons=tuple(reasons),
    )


def analyze_multi_timeframe_ichimoku(
    daily_prices: pd.DataFrame, daily_enriched: pd.DataFrame | None = None
) -> MultiTimeframeIchimoku:
    """Analyze daily and derived weekly frames, adjusting only on agreement."""
    daily_data = daily_enriched if daily_enriched is not None else add_ichimoku(daily_prices)
    daily = ichimoku_snapshot(daily_data, "Ngày")
    weekly_prices = resample_weekly(daily_prices)
    if len(weekly_prices) < 52:
        return MultiTimeframeIchimoku(
            daily=daily,
            weekly=None,
            aligned=False,
            score_adjustment=0,
            summary="Chưa đủ 52 tuần để xác nhận Ichimoku đa khung thời gian",
        )
    weekly_data = add_ichimoku(weekly_prices)
    weekly = ichimoku_snapshot(weekly_data, "Tuần")
    bullish_states = {"Tăng", "Tăng mạnh"}
    bearish_states = {"Giảm", "Giảm mạnh"}
    bullish_alignment = daily.state in bullish_states and weekly.state in bullish_states
    bearish_alignment = daily.state in bearish_states and weekly.state in bearish_states
    aligned = bullish_alignment or bearish_alignment
    adjustment = 1 if bullish_alignment else -1 if bearish_alignment else 0
    if bullish_alignment:
        summary = "Ichimoku ngày và tuần đồng thuận tăng"
    elif bearish_alignment:
        summary = "Ichimoku ngày và tuần đồng thuận giảm"
    else:
        summary = (
            f"Ichimoku chưa đồng thuận: ngày {daily.state.lower()}, "
            f"tuần {weekly.state.lower()}"
        )
    return MultiTimeframeIchimoku(
        daily=daily,
        weekly=weekly,
        aligned=aligned,
        score_adjustment=adjustment,
        summary=summary,
    )
