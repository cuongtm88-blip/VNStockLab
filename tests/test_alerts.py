from types import SimpleNamespace

import pandas as pd

from vnstocklab.analysis.alerts import (
    AlertRule,
    AlertSnapshot,
    alert_rules_from_screening,
    detect_symbol_alerts,
)


def result(signal: str = "MUA THĂM DÒ", trend: str = "Tăng", close: float = 100) -> SimpleNamespace:
    data = pd.DataFrame({"close": [close]}, index=pd.DatetimeIndex([pd.Timestamp("2026-01-05")]))
    return SimpleNamespace(
        data=data,
        signal=signal,
        trend=trend,
        score=70,
        levels=SimpleNamespace(breakout=None),
    )


def test_detects_signal_stop_and_target_without_repeating_unchanged_signal() -> None:
    alerts, snapshot = detect_symbol_alerts(result(), AlertRule("fpt", target_price=95))
    assert {event.category for event in alerts} == {"Tín hiệu", "Mục tiêu"}
    repeated, _ = detect_symbol_alerts(result(), AlertRule("FPT"), snapshot)
    assert not repeated


def test_detects_trend_transition_and_stop_loss() -> None:
    alerts, _ = detect_symbol_alerts(
        result(signal="GIẢM TỶ TRỌNG", trend="Giảm", close=80),
        AlertRule("FPT", stop_loss=90),
        AlertSnapshot("NẮM GIỮ", "Tăng"),
    )
    assert {event.category for event in alerts} == {
        "Tín hiệu",
        "Xu hướng",
        "Stop-loss",
    }


def test_detects_score_threshold_crossing_once() -> None:
    alerts, snapshot = detect_symbol_alerts(
        result(signal="NẮM GIỮ"), AlertRule("FPT", minimum_score=60)
    )
    assert {event.category for event in alerts} == {"Điểm kỹ thuật"}
    repeated, _ = detect_symbol_alerts(
        result(signal="NẮM GIỮ"), AlertRule("FPT", minimum_score=60), snapshot
    )
    assert not repeated


def test_builds_alert_rules_from_screening_rows() -> None:
    rows = pd.DataFrame(
        {"Mã": ["FPT", "HPG"], "Stop-loss": [90.0, 20.0], "Mục tiêu": [120.0, 30.0]}
    )
    rules = alert_rules_from_screening(rows, ("FPT",), minimum_score=65)
    assert rules == (AlertRule("FPT", 90.0, 120.0, 65),)
