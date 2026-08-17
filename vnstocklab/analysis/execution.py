"""Final execution gate applied after technical scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from vnstocklab.analysis.dow import DowAnalysis
from vnstocklab.analysis.levels import SupportResistanceAnalysis
from vnstocklab.analysis.market_breadth import MarketBreadth
from vnstocklab.analysis.risk import RiskPlan

ExecutionRecommendation = Literal[
    "MUA THĂM DÒ", "CHỜ XÁC NHẬN", "NẮM GIỮ", "GIẢM TỶ TRỌNG"
]


@dataclass(frozen=True)
class ExecutionDecision:
    """Explain whether a high technical score is actually executable."""

    recommendation: ExecutionRecommendation
    score_candidate: bool
    eligible: bool
    blockers: tuple[str, ...]
    confirmations: tuple[str, ...]


def evaluate_execution_gate(
    score: int,
    dow: DowAnalysis,
    levels: SupportResistanceAnalysis,
    risk: RiskPlan,
    market_breadth: MarketBreadth | None = None,
) -> ExecutionDecision:
    """Convert a score into a risk-aware final recommendation."""
    if score <= 35:
        return ExecutionDecision(
            "GIẢM TỶ TRỌNG",
            False,
            False,
            ("Điểm tổng hợp ở vùng rủi ro (≤35)",),
            (),
        )
    if score < 65:
        return ExecutionDecision(
            "NẮM GIỮ",
            False,
            False,
            ("Điểm chưa đạt ngưỡng ứng viên mua 65",),
            (),
        )

    blockers: list[str] = []
    confirmations: list[str] = []
    if not risk.available:
        blockers.append("Chưa xây dựng được kế hoạch rủi ro")
    elif risk.risk_reward < 1.5:
        blockers.append(f"Risk/Reward {risk.risk_reward:.2f}R thấp hơn 1,50R")
    else:
        confirmations.append(f"Risk/Reward đạt {risk.risk_reward:.2f}R")

    if levels.breakout is not None and levels.breakout.direction == "down":
        blockers.append(f"Breakdown đang hoạt động: {levels.breakout.description}")
    else:
        confirmations.append("Không có breakdown đang hoạt động")

    if dow.medium_term.state == "Xu hướng giảm":
        blockers.append("Cấu trúc Dow trung hạn vẫn là xu hướng giảm")
    else:
        confirmations.append(f"Dow trung hạn: {dow.medium_term.state.lower()}")

    if market_breadth is not None and market_breadth.available:
        if market_breadth.score < 4:
            blockers.append(
                f"Market Breadth {market_breadth.score}/10 đang ở vùng tiêu cực"
            )
        else:
            confirmations.append(f"Market Breadth đạt {market_breadth.score}/10")
    else:
        confirmations.append("Breadth chưa có dữ liệu nên không dùng làm điều kiện chặn")

    eligible = not blockers
    return ExecutionDecision(
        "MUA THĂM DÒ" if eligible else "CHỜ XÁC NHẬN",
        True,
        eligible,
        tuple(blockers),
        tuple(confirmations),
    )
