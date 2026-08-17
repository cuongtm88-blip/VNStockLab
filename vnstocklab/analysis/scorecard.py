"""Non-overlapping 0–100 technical scorecard."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from vnstocklab.analysis.dow import DowAnalysis
from vnstocklab.analysis.ichimoku import MultiTimeframeIchimoku
from vnstocklab.analysis.levels import SupportResistanceAnalysis
from vnstocklab.analysis.market_breadth import MarketBreadth
from vnstocklab.analysis.patterns import PricePattern
from vnstocklab.analysis.relative_strength import RelativeStrengthAnalysis
from vnstocklab.analysis.risk import RiskPlan


@dataclass(frozen=True)
class CategoryScore:
    """One capped, independently explained score category."""

    name: str
    score: int
    maximum: int
    available: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class TechnicalScorecard:
    """Current provisional scorecard; unavailable categories remain neutral."""

    categories: tuple[CategoryScore, ...]
    total: int


def _structure_score(
    dow: DowAnalysis, ichimoku: MultiTimeframeIchimoku
) -> CategoryScore:
    states = (dow.short_term.state, dow.medium_term.state)
    if states == ("Xu hướng tăng", "Xu hướng tăng"):
        score = 16
    elif states == ("Xu hướng giảm", "Xu hướng giảm"):
        score = 4
    elif "Xu hướng tăng" in states:
        score = 13
    elif "Xu hướng giảm" in states:
        score = 7
    else:
        score = 10
    if ichimoku.daily.state in {"Tăng", "Tăng mạnh"}:
        score += 2
    elif ichimoku.daily.state in {"Giảm", "Giảm mạnh"}:
        score -= 2
    return CategoryScore(
        "Cấu trúc giá",
        max(0, min(20, score)),
        20,
        True,
        (dow.summary, f"Ichimoku ngày: {ichimoku.daily.state.lower()}"),
    )


def _trend_score(data: pd.DataFrame) -> CategoryScore:
    latest = data.iloc[-1]
    bullish = latest["close"] > latest["sma20"] > latest["sma50"]
    bearish = latest["close"] < latest["sma20"] < latest["sma50"]
    adx = float(latest["adx14"])
    positive_direction = latest["plus_di14"] > latest["minus_di14"]
    if bullish and adx >= 25 and positive_direction:
        score = 10
    elif bearish and adx >= 25 and not positive_direction:
        score = 0
    elif bullish and positive_direction:
        score = 8 if adx >= 20 else 7
    elif bearish and not positive_direction:
        score = 2 if adx >= 20 else 3
    else:
        score = 5
    sma_reason = (
        "SMA xếp theo hướng tăng"
        if bullish
        else "SMA xếp theo hướng giảm"
        if bearish
        else "SMA chưa đồng thuận"
    )
    reasons = (
        sma_reason,
        f"ADX14 = {adx:.1f} ({'có xu hướng' if adx >= 25 else 'xu hướng yếu'})",
        f"{'+DI' if positive_direction else '-DI'} đang chiếm ưu thế",
    )
    return CategoryScore("Chất lượng xu hướng", score, 10, True, reasons)


def _money_flow_score(data: pd.DataFrame) -> CategoryScore:
    latest = data.iloc[-1]
    high_volume = latest["volume"] > latest["volume_sma20"] * 1.2
    obv_rising = latest["obv"] > data["obv"].iloc[-6]
    cmf = float(latest["cmf20"])
    score = 8 + (2 if obv_rising else -2)
    score += 3 if cmf > 0.1 else 1 if cmf > 0 else -3 if cmf < -0.1 else -1
    if high_volume:
        score += 2 if latest["close"] > latest["open"] else -2
    reasons = (
        f"OBV 5 phiên {'đi lên' if obv_rising else 'đi xuống'}",
        f"CMF20 = {cmf:+.3f} ({'tích lũy' if cmf > 0 else 'phân phối'})",
        (
            "Khối lượng cao xác nhận phiên tăng" if latest["close"] > latest["open"]
            else "Khối lượng cao xác nhận phiên giảm"
        ) if high_volume else "Khối lượng chưa tạo xác nhận bất thường",
    )
    return CategoryScore(
        "Dòng tiền",
        max(0, min(15, score)),
        15,
        True,
        (*reasons, "MFI chỉ dùng tham khảo và không tham gia điểm"),
    )


def _trigger_score(
    data: pd.DataFrame,
    levels: SupportResistanceAnalysis,
    patterns: tuple[PricePattern, ...],
) -> CategoryScore:
    latest = data.iloc[-1]
    if levels.breakout is not None and levels.breakout.confirmed_by_volume:
        bullish = levels.breakout.direction == "up"
        return CategoryScore(
            "Điểm kích hoạt",
            15 if bullish else 0,
            15,
            True,
            (levels.breakout.description, "Breakout được khối lượng xác nhận"),
        )
    pattern = next(
        (
            item
            for item in patterns
            if item.status in {"Đã breakout", "Retest thành công"} and item.volume_confirmed
        ),
        None,
    )
    if pattern is not None:
        return CategoryScore(
            "Điểm kích hoạt",
            13 if pattern.direction == "bullish" else 2,
            15,
            True,
            (pattern.description, "Chỉ mẫu hình mạnh nhất được tính"),
        )
    if bool(latest["squeeze_release"]):
        bullish = latest["squeeze_momentum"] > 0
        return CategoryScore(
            "Điểm kích hoạt",
            12 if bullish else 3,
            15,
            True,
            (f"Squeeze vừa giải phóng với động lượng {'dương' if bullish else 'âm'}",),
        )
    if bool(latest["candle_confirmed"]):
        bullish = latest["candle_direction"] == "bullish"
        return CategoryScore(
            "Điểm kích hoạt",
            11 if bullish else 4,
            15,
            True,
            (f"Mẫu nến {latest['candle_pattern']} đã được xác nhận",),
        )
    return CategoryScore(
        "Điểm kích hoạt",
        7,
        15,
        True,
        (
            "Giá đang nén trong Bollinger–Keltner" if bool(latest["squeeze_on"])
            else "Chưa có breakout, squeeze release hoặc mẫu nến xác nhận",
        ),
    )


def _risk_score(risk: RiskPlan) -> CategoryScore:
    if not risk.available:
        return CategoryScore("Quản trị rủi ro", 3, 15, False, risk.reasons)
    if risk.risk_reward >= 2.5:
        score = 15
    elif risk.risk_reward >= 2:
        score = 12
    elif risk.risk_reward >= 1.5:
        score = 9
    elif risk.risk_reward >= 1:
        score = 5
    else:
        score = 2
    if risk.atr_pct > 5 or risk.stop_distance_pct > 10:
        score = max(0, score - 2)
    return CategoryScore(
        "Quản trị rủi ro",
        score,
        15,
        True,
        (
            f"Risk/Reward = {risk.risk_reward:.2f}R",
            f"Stop cách giá vào {risk.stop_distance_pct:.2f}%",
            f"ATR bằng {risk.atr_pct:.2f}% giá",
        ),
    )


def build_scorecard(
    data: pd.DataFrame,
    ichimoku: MultiTimeframeIchimoku,
    dow: DowAnalysis,
    levels: SupportResistanceAnalysis,
    patterns: tuple[PricePattern, ...],
    relative_strength: RelativeStrengthAnalysis | None = None,
    risk: RiskPlan | None = None,
    market_breadth: MarketBreadth | None = None,
) -> TechnicalScorecard:
    """Build a capped scorecard without duplicate indicator votes."""
    categories = (
        CategoryScore(
            "Bối cảnh thị trường",
            market_breadth.score if market_breadth is not None else 5,
            10,
            market_breadth.available if market_breadth is not None else False,
            market_breadth.reasons
            if market_breadth is not None
            else ("Chờ Market Breadth Dashboard",),
        ),
        CategoryScore(
            "Sức mạnh tương đối",
            relative_strength.score if relative_strength is not None else 8,
            15,
            relative_strength.available if relative_strength is not None else False,
            relative_strength.reasons
            if relative_strength is not None
            else ("Chờ benchmark VN-Index",),
        ),
        _structure_score(dow, ichimoku),
        _trend_score(data),
        _money_flow_score(data),
        _trigger_score(data, levels, patterns),
        _risk_score(risk)
        if risk is not None
        else CategoryScore("Quản trị rủi ro", 8, 15, False, ("Chờ kế hoạch ATR",)),
    )
    return TechnicalScorecard(categories=categories, total=sum(item.score for item in categories))
