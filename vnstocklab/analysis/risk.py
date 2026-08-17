"""ATR-based trade risk planning."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from vnstocklab.analysis.levels import SupportResistanceAnalysis
from vnstocklab.analysis.patterns import PricePattern


@dataclass(frozen=True)
class RiskPlan:
    """A long-side entry, invalidation and target plan."""

    available: bool
    entry: float
    stop_loss: float
    target: float
    risk_per_share: float
    reward_per_share: float
    risk_reward: float
    stop_distance_pct: float
    atr_pct: float
    reasons: tuple[str, ...]


def build_risk_plan(
    data: pd.DataFrame,
    levels: SupportResistanceAnalysis,
    patterns: tuple[PricePattern, ...],
) -> RiskPlan:
    """Build a conservative long plan from ATR, nearby zones and price patterns."""
    latest = data.iloc[-1]
    entry = float(latest["close"])
    atr = float(latest["atr14"])
    atr_stop = entry - 2 * atr

    stop_candidates = [atr_stop]
    stop_reasons = ["Stop ATR: thấp hơn giá vào 2 ATR"]
    if levels.nearest_support is not None and levels.nearest_support.lower < entry:
        stop_candidates.append(levels.nearest_support.lower - 0.25 * atr)
        stop_reasons.append("Có xét biên dưới vùng hỗ trợ gần nhất")
    bullish_pattern = next(
        (pattern for pattern in patterns if pattern.direction == "bullish"), None
    )
    if bullish_pattern is not None and bullish_pattern.invalidation < entry:
        stop_candidates.append(bullish_pattern.invalidation)
        stop_reasons.append(f"Có xét mức vô hiệu của {bullish_pattern.name}")
    stop_loss = max(value for value in stop_candidates if value < entry)
    risk = entry - stop_loss

    target_candidates: list[float] = []
    target_reasons: list[str] = []
    if levels.nearest_resistance is not None and levels.nearest_resistance.midpoint > entry:
        target_candidates.append(levels.nearest_resistance.midpoint)
        target_reasons.append("Mục tiêu tại kháng cự gần nhất")
    if bullish_pattern is not None and bullish_pattern.target > entry:
        target_candidates.append(bullish_pattern.target)
        target_reasons.append(f"Mục tiêu của {bullish_pattern.name}")
    if target_candidates:
        target = min(target_candidates)
    else:
        target = entry + 2 * risk
        target_reasons.append("Chưa có kháng cự phù hợp; dùng mục tiêu kỹ thuật 2R")

    reward = target - entry
    risk_reward = reward / risk if risk > 0 else 0.0
    stop_distance_pct = risk / entry * 100
    atr_pct = atr / entry * 100
    return RiskPlan(
        available=risk > 0 and reward > 0,
        entry=entry,
        stop_loss=stop_loss,
        target=target,
        risk_per_share=risk,
        reward_per_share=reward,
        risk_reward=risk_reward,
        stop_distance_pct=stop_distance_pct,
        atr_pct=atr_pct,
        reasons=(*stop_reasons, *target_reasons),
    )
