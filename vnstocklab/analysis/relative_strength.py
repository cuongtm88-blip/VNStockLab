"""Relative strength versus a market benchmark."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RelativeStrengthAnalysis:
    """Performance of one security relative to its benchmark."""

    available: bool
    score: int
    relative_return_20d: float | None
    relative_return_60d: float | None
    ratio_above_sma20: bool | None
    reasons: tuple[str, ...]


def _period_return(series: pd.Series, periods: int) -> float:
    return float((series.iloc[-1] / series.iloc[-periods - 1] - 1) * 100)


def analyze_relative_strength(
    prices: pd.DataFrame, benchmark: pd.DataFrame | None
) -> RelativeStrengthAnalysis:
    """Compare 20- and 60-session returns with a normalized price ratio."""
    if benchmark is None:
        return RelativeStrengthAnalysis(
            False, 8, None, None, None, ("Chưa có dữ liệu benchmark VN-Index",)
        )

    aligned = pd.concat(
        [prices["close"].rename("stock"), benchmark["close"].rename("benchmark")],
        axis=1,
        join="inner",
    ).dropna()
    if len(aligned) < 61 or (aligned["benchmark"] <= 0).any():
        return RelativeStrengthAnalysis(
            False,
            8,
            None,
            None,
            None,
            ("Benchmark cần tối thiểu 61 phiên giao dịch trùng khớp",),
        )

    stock_20 = _period_return(aligned["stock"], 20)
    market_20 = _period_return(aligned["benchmark"], 20)
    stock_60 = _period_return(aligned["stock"], 60)
    market_60 = _period_return(aligned["benchmark"], 60)
    relative_20 = stock_20 - market_20
    relative_60 = stock_60 - market_60
    ratio = aligned["stock"] / aligned["benchmark"]
    above_sma = bool(ratio.iloc[-1] > ratio.rolling(20).mean().iloc[-1])

    score = 8
    score += 3 if relative_20 >= 3 else 1 if relative_20 > 0 else -2 if relative_20 <= -3 else -1
    score += 3 if relative_60 >= 5 else 1 if relative_60 > 0 else -2 if relative_60 <= -5 else -1
    score += 1 if above_sma else -1
    score = max(0, min(15, score))
    return RelativeStrengthAnalysis(
        True,
        score,
        relative_20,
        relative_60,
        above_sma,
        (
            f"Vượt VN-Index {relative_20:+.2f} điểm % trong 20 phiên",
            f"Vượt VN-Index {relative_60:+.2f} điểm % trong 60 phiên",
            f"Tỷ lệ giá/VN-Index {'trên' if above_sma else 'dưới'} SMA20",
        ),
    )
