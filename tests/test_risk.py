import pytest

from vnstocklab.analysis.engine import analyze
from vnstocklab.data.demo import generate_demo_prices


def test_atr_risk_plan_values_are_consistent() -> None:
    result = analyze(generate_demo_prices("FPT", periods=300))
    plan = result.risk_plan

    assert plan.risk_per_share == pytest.approx(plan.entry - plan.stop_loss)
    assert plan.reward_per_share == pytest.approx(plan.target - plan.entry)
    assert plan.risk_reward == pytest.approx(plan.reward_per_share / plan.risk_per_share)
    assert plan.stop_distance_pct == pytest.approx(plan.risk_per_share / plan.entry * 100)
    assert plan.atr_pct > 0


def test_risk_category_is_active_and_capped() -> None:
    result = analyze(generate_demo_prices("HPG", periods=300))
    category = next(
        item for item in result.scorecard.categories if item.name == "Quản trị rủi ro"
    )

    assert category.available
    assert 0 <= category.score <= category.maximum == 15
