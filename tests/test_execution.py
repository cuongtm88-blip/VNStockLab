from types import SimpleNamespace
from typing import Any, cast

from vnstocklab.analysis.execution import evaluate_execution_gate


def context(
    *,
    risk_reward: float = 2.0,
    medium_trend: str = "Đi ngang",
    breakout_direction: str | None = None,
) -> tuple[Any, Any, Any]:
    dow = SimpleNamespace(medium_term=SimpleNamespace(state=medium_trend))
    breakout = (
        SimpleNamespace(direction=breakout_direction, description="Thủng hỗ trợ")
        if breakout_direction is not None
        else None
    )
    levels = SimpleNamespace(breakout=breakout)
    risk = SimpleNamespace(available=True, risk_reward=risk_reward)
    return cast(Any, dow), cast(Any, levels), cast(Any, risk)


def test_execution_gate_allows_only_risk_aware_buy() -> None:
    dow, levels, risk = context()
    decision = evaluate_execution_gate(70, dow, levels, risk)
    assert decision.recommendation == "MUA THĂM DÒ"
    assert decision.eligible
    assert not decision.blockers


def test_execution_gate_blocks_bad_rr_breakdown_and_downtrend() -> None:
    dow, levels, risk = context(
        risk_reward=0.24, medium_trend="Xu hướng giảm", breakout_direction="down"
    )
    decision = evaluate_execution_gate(70, dow, levels, risk)
    assert decision.recommendation == "CHỜ XÁC NHẬN"
    assert not decision.eligible
    assert len(decision.blockers) == 3


def test_execution_gate_preserves_exit_priority() -> None:
    dow, levels, risk = context()
    decision = evaluate_execution_gate(35, dow, levels, risk)
    assert decision.recommendation == "GIẢM TỶ TRỌNG"
