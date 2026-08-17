"""Multi-symbol technical screener."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from vnstocklab.analysis.engine import analyze
from vnstocklab.analysis.market_breadth import (
    MarketBreadth,
    analyze_market_breadth,
    unavailable_breadth,
)
from vnstocklab.data.provider import MarketDataProvider


@dataclass(frozen=True)
class ScreeningResult:
    """Screening table plus per-symbol provider failures."""

    rows: pd.DataFrame
    errors: tuple[str, ...]
    breadth: MarketBreadth


def screen_symbols(
    symbols: tuple[str, ...],
    provider: MarketDataProvider,
    count: int = 300,
    benchmark_symbol: str = "VNINDEX",
) -> ScreeningResult:
    """Analyze symbols sequentially to respect free-provider request limits."""
    records: list[dict[str, object]] = []
    errors: list[str] = []
    normalized_symbols = tuple(
        dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip())
    )
    try:
        benchmark = provider.history(benchmark_symbol, count=count)
    except (RuntimeError, ValueError) as error:
        benchmark = None
        errors.append(f"{benchmark_symbol}: {error}; điểm Relative Strength giữ trung lập")

    frames: dict[str, pd.DataFrame] = {}
    for symbol in normalized_symbols:
        try:
            frames[symbol] = provider.history(symbol, count=count)
        except (RuntimeError, ValueError) as error:
            errors.append(f"{symbol}: {error}")
    breadth = (
        analyze_market_breadth(frames)
        if frames
        else unavailable_breadth("Không tải được dữ liệu thành phần")
    )

    for symbol, prices in frames.items():
        try:
            analysis = analyze(prices, benchmark=benchmark, market_breadth=breadth)
            latest = analysis.data.iloc[-1]
            previous = analysis.data.iloc[-2]
            primary_pattern = analysis.patterns[0] if analysis.patterns else None
            records.append(
                {
                    "Mã": symbol,
                    "Tín hiệu": analysis.signal,
                    "Xu hướng": analysis.trend,
                    "Điểm": analysis.score,
                    "Giá": float(latest["close"]),
                    "% thay đổi": float((latest["close"] / previous["close"] - 1) * 100),
                    "RSI 14": float(latest["rsi14"]),
                    "MFI 14": float(latest["mfi14"]),
                    "CMF 20": float(latest["cmf20"]),
                    "RS 20 phiên": analysis.relative_strength.relative_return_20d,
                    "ADX 14": float(latest["adx14"]),
                    "Squeeze": (
                        "Giải phóng"
                        if bool(latest["squeeze_release"])
                        else "Đang nén"
                        if bool(latest["squeeze_on"])
                        else "Không"
                    ),
                    "Stop-loss": analysis.risk_plan.stop_loss,
                    "Mục tiêu": analysis.risk_plan.target,
                    "R/R": analysis.risk_plan.risk_reward,
                    "Ichimoku": analysis.ichimoku.daily.state,
                    "Đồng thuận tuần": "Có" if analysis.ichimoku.aligned else "Chưa",
                    "Dow ngắn hạn": analysis.dow.short_term.state,
                    "Dow trung hạn": analysis.dow.medium_term.state,
                    "Mẫu hình": primary_pattern.name if primary_pattern is not None else "Không",
                    "Trạng thái mẫu": (
                        primary_pattern.status if primary_pattern is not None else "Không"
                    ),
                    "Hỗ trợ": (
                        analysis.levels.nearest_support.midpoint
                        if analysis.levels.nearest_support is not None
                        else analysis.support
                    ),
                    "Kháng cự": (
                        analysis.levels.nearest_resistance.midpoint
                        if analysis.levels.nearest_resistance is not None
                        else analysis.resistance
                    ),
                    "Breakout": (
                        "Tăng"
                        if analysis.levels.breakout is not None
                        and analysis.levels.breakout.direction == "up"
                        else "Giảm"
                        if analysis.levels.breakout is not None
                        else "Không"
                    ),
                }
            )
        except (RuntimeError, ValueError) as error:
            errors.append(f"{symbol}: {error}")

    rows = pd.DataFrame.from_records(records)
    if not rows.empty:
        rows = rows.sort_values(["Điểm", "% thay đổi"], ascending=False).reset_index(drop=True)
    return ScreeningResult(rows=rows, errors=tuple(errors), breadth=breadth)
