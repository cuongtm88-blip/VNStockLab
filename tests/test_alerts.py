from types import SimpleNamespace

import pandas as pd

from vnstocklab.analysis.alerts import AlertRule, AlertSnapshot, detect_symbol_alerts


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
