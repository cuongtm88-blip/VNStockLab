"""Rule-based alert detection for watchlists and realtime adapters."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from vnstocklab.analysis.engine import AnalysisResult
from vnstocklab.analysis.market_breadth import MarketBreadth


@dataclass(frozen=True)
class AlertRule:
    symbol: str
    stop_loss: float | None = None
    target_price: float | None = None


@dataclass(frozen=True)
class AlertSnapshot:
    signal: str
    trend: str
    breadth_state: str | None = None


@dataclass(frozen=True)
class AlertEvent:
    event_id: str
    occurred_at: pd.Timestamp
    symbol: str
    category: str
    severity: str
    message: str
    price: float | None
    score: int | None


def _event(
    symbol: str,
    occurred_at: pd.Timestamp,
    category: str,
    severity: str,
    message: str,
    price: float | None,
    score: int | None,
) -> AlertEvent:
    event_id = f"{symbol}|{occurred_at.isoformat()}|{category}|{message}"
    return AlertEvent(event_id, occurred_at, symbol, category, severity, message, price, score)


def detect_symbol_alerts(
    result: AnalysisResult,
    rule: AlertRule,
    previous: AlertSnapshot | None = None,
) -> tuple[tuple[AlertEvent, ...], AlertSnapshot]:
    """Detect actionable symbol events and return the next comparison snapshot."""
    symbol = rule.symbol.strip().upper()
    latest = result.data.iloc[-1]
    occurred_at = pd.Timestamp(result.data.index[-1])
    close = float(latest["close"])
    events: list[AlertEvent] = []
    if result.signal in {"MUA THĂM DÒ", "GIẢM TỶ TRỌNG"} and (
        previous is None or previous.signal != result.signal
    ):
        severity = "Cao" if result.signal == "GIẢM TỶ TRỌNG" else "Trung bình"
        events.append(
            _event(
                symbol,
                occurred_at,
                "Tín hiệu",
                severity,
                f"Tín hiệu chuyển sang {result.signal}",
                close,
                result.score,
            )
        )
    if previous is not None and previous.trend != result.trend:
        events.append(
            _event(
                symbol,
                occurred_at,
                "Xu hướng",
                "Cao" if result.trend == "Giảm" else "Trung bình",
                f"Xu hướng đổi từ {previous.trend} sang {result.trend}",
                close,
                result.score,
            )
        )
    breakout = result.levels.breakout
    if breakout is not None:
        events.append(
            _event(
                symbol,
                occurred_at,
                "Breakout" if breakout.direction == "up" else "Breakdown",
                "Cao" if breakout.confirmed_by_volume else "Trung bình",
                breakout.description,
                close,
                result.score,
            )
        )
    if rule.stop_loss is not None and close <= rule.stop_loss:
        events.append(
            _event(
                symbol,
                occurred_at,
                "Stop-loss",
                "Khẩn cấp",
                f"Giá {close:.2f} đã chạm stop {rule.stop_loss:.2f}",
                close,
                result.score,
            )
        )
    if rule.target_price is not None and close >= rule.target_price:
        events.append(
            _event(
                symbol,
                occurred_at,
                "Mục tiêu",
                "Cao",
                f"Giá {close:.2f} đã chạm mục tiêu {rule.target_price:.2f}",
                close,
                result.score,
            )
        )
    return tuple(events), AlertSnapshot(result.signal, result.trend)


def detect_breadth_alert(
    breadth: MarketBreadth,
    occurred_at: pd.Timestamp,
    previous_state: str | None = None,
) -> AlertEvent | None:
    """Detect a material market breadth regime or extreme reading."""
    if not breadth.available:
        return None
    changed = previous_state is not None and previous_state != breadth.state
    extreme = breadth.score <= 3 or breadth.score >= 7
    if not changed and not extreme:
        return None
    severity = "Cao" if breadth.score <= 3 else "Trung bình"
    return _event(
        "THỊ TRƯỜNG",
        occurred_at,
        "Market Breadth",
        severity,
        f"Breadth: {breadth.state} ({breadth.score}/10)",
        None,
        breadth.score,
    )
