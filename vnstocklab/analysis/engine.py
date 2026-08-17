"""Explainable signal aggregation for a stock time series."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from vnstocklab.analysis.candlesticks import (
    CandlestickEvent,
    candlestick_events,
    detect_candlestick_patterns,
)
from vnstocklab.analysis.dow import DowAnalysis, analyze_dow_structure
from vnstocklab.analysis.execution import (
    ExecutionDecision,
    ExecutionRecommendation,
    evaluate_execution_gate,
)
from vnstocklab.analysis.ichimoku import (
    MultiTimeframeIchimoku,
    add_ichimoku,
    analyze_multi_timeframe_ichimoku,
)
from vnstocklab.analysis.indicators import enrich_indicators
from vnstocklab.analysis.levels import (
    SupportResistanceAnalysis,
    analyze_support_resistance,
    apply_zone_candlestick_confirmation,
)
from vnstocklab.analysis.market_breadth import MarketBreadth
from vnstocklab.analysis.patterns import PricePattern, analyze_price_patterns
from vnstocklab.analysis.relative_strength import (
    RelativeStrengthAnalysis,
    analyze_relative_strength,
)
from vnstocklab.analysis.risk import RiskPlan, build_risk_plan
from vnstocklab.analysis.scorecard import TechnicalScorecard, build_scorecard

Signal = ExecutionRecommendation
Trend = Literal["Tăng", "Đi ngang", "Giảm"]


@dataclass(frozen=True)
class AnalysisResult:
    """Latest explainable technical-analysis snapshot."""

    data: pd.DataFrame
    score: int
    signal: Signal
    trend: Trend
    reasons: tuple[str, ...]
    support: float
    resistance: float
    candlestick_events: tuple[CandlestickEvent, ...]
    ichimoku: MultiTimeframeIchimoku
    levels: SupportResistanceAnalysis
    dow: DowAnalysis
    patterns: tuple[PricePattern, ...]
    scorecard: TechnicalScorecard
    relative_strength: RelativeStrengthAnalysis
    risk_plan: RiskPlan
    execution: ExecutionDecision


def analyze(
    prices: pd.DataFrame,
    benchmark: pd.DataFrame | None = None,
    market_breadth: MarketBreadth | None = None,
) -> AnalysisResult:
    """Analyze OHLCV prices with a transparent rule-based scoring model."""
    if len(prices) < 52:
        raise ValueError("Cần ít nhất 52 phiên để phân tích")
    enriched = add_ichimoku(enrich_indicators(prices))
    levels = analyze_support_resistance(enriched)
    enriched = apply_zone_candlestick_confirmation(
        detect_candlestick_patterns(enriched), levels
    )
    enriched_events = candlestick_events(enriched)
    ichimoku = analyze_multi_timeframe_ichimoku(prices, enriched)
    dow = analyze_dow_structure(enriched, levels.breakout)
    patterns = analyze_price_patterns(enriched)
    relative_strength = analyze_relative_strength(prices, benchmark)
    risk_plan = build_risk_plan(enriched, levels, patterns)
    latest = enriched.iloc[-1]
    scorecard = build_scorecard(
        enriched,
        ichimoku,
        dow,
        levels,
        patterns,
        relative_strength,
        risk_plan,
        market_breadth,
    )
    score = scorecard.total
    reasons = [reason for category in scorecard.categories for reason in category.reasons]
    if dow.medium_term.state == "Xu hướng tăng":
        trend: Trend = "Tăng"
    elif dow.medium_term.state == "Xu hướng giảm":
        trend = "Giảm"
    else:
        trend = "Đi ngang"
    execution = evaluate_execution_gate(score, dow, levels, risk_plan, market_breadth)
    signal: Signal = execution.recommendation
    return AnalysisResult(
        data=enriched,
        score=score,
        signal=signal,
        trend=trend,
        reasons=tuple(reasons),
        support=float(latest["support20"]),
        resistance=float(latest["resistance20"]),
        candlestick_events=enriched_events,
        ichimoku=ichimoku,
        levels=levels,
        dow=dow,
        patterns=patterns,
        scorecard=scorecard,
        relative_strength=relative_strength,
        risk_plan=risk_plan,
        execution=execution,
    )
