"""Explainable market-regime classification and exposure guidance."""

from __future__ import annotations

from dataclasses import dataclass

from vnstocklab.analysis.market_breadth import MarketBreadth


@dataclass(frozen=True)
class MarketRegime:
    """Market context translated into portfolio-level operating guidance."""

    score: int
    state: str
    risk_level: str
    stock_allocation: tuple[int, int]
    cash_allocation: tuple[int, int]
    buy_policy: str
    reasons: tuple[str, ...]


def evaluate_market_regime(
    *,
    index_score: int,
    index_trend: str,
    close: float,
    sma20: float,
    sma50: float,
    breadth: MarketBreadth,
) -> MarketRegime:
    """Combine index health, breadth, and MA structure into a 0–100 regime score."""
    technical_component = max(0, min(100, index_score))
    breadth_component = breadth.score * 10 if breadth.available else 50
    if close > sma20 > sma50:
        structure_component = 100
        structure_reason = "VNINDEX nằm trên SMA20 và SMA50, cấu trúc tăng đồng thuận"
    elif close < sma20 < sma50:
        structure_component = 0
        structure_reason = "VNINDEX nằm dưới SMA20 và SMA50, cấu trúc giảm đồng thuận"
    elif close > sma50:
        structure_component = 65
        structure_reason = "VNINDEX còn trên SMA50 nhưng cấu trúc ngắn hạn chưa đồng thuận"
    else:
        structure_component = 35
        structure_reason = "VNINDEX dưới SMA50, ưu tiên bảo toàn vốn"
    trend_adjustment = 5 if index_trend == "Tăng" else -5 if index_trend == "Giảm" else 0
    score = round(
        technical_component * 0.45
        + breadth_component * 0.35
        + structure_component * 0.20
        + trend_adjustment
    )
    score = max(0, min(100, score))

    if score >= 75:
        state = "Tấn công"
        risk_level = "Thấp"
        stock_allocation = (70, 90)
        buy_policy = "Cho phép mua xác nhận và gia tăng vị thế ở mã dẫn dắt."
    elif score >= 60:
        state = "Tích cực có chọn lọc"
        risk_level = "Trung bình"
        stock_allocation = (50, 70)
        buy_policy = "Ưu tiên mã mạnh hơn thị trường; mua từng phần tại điểm xác nhận."
    elif score >= 45:
        state = "Thận trọng"
        risk_level = "Cao"
        stock_allocation = (25, 50)
        buy_policy = "Chỉ mua thăm dò tỷ trọng nhỏ; không mua đuổi và siết stop-loss."
    else:
        state = "Phòng thủ"
        risk_level = "Rất cao"
        stock_allocation = (0, 25)
        buy_policy = "Tạm dừng mua mới; ưu tiên tiền mặt và giảm các vị thế yếu."
    cash_allocation = (100 - stock_allocation[1], 100 - stock_allocation[0])
    reasons = (
        f"Điểm kỹ thuật VNINDEX: {technical_component}/100",
        (
            f"Độ rộng thị trường: {breadth.state} ({breadth.score}/10)"
            if breadth.available
            else "Độ rộng chưa đủ dữ liệu, giữ thành phần này ở mức trung tính"
        ),
        structure_reason,
        f"Xu hướng VNINDEX: {index_trend}",
    )
    return MarketRegime(
        score,
        state,
        risk_level,
        stock_allocation,
        cash_allocation,
        buy_policy,
        reasons,
    )
