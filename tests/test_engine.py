import pytest

from vnstocklab.analysis.engine import analyze
from vnstocklab.analysis.market_breadth import analyze_market_breadth
from vnstocklab.data.demo import generate_demo_prices


def test_analysis_returns_explainable_result() -> None:
    prices = generate_demo_prices("HPG", periods=120)
    result = analyze(prices)

    assert result.signal in {
        "MUA THĂM DÒ",
        "CHỜ XÁC NHẬN",
        "NẮM GIỮ",
        "GIẢM TỶ TRỌNG",
    }
    assert result.trend in {"Tăng", "Đi ngang", "Giảm"}
    assert result.reasons
    assert result.support <= result.resistance
    assert len(result.data) == len(prices)
    assert 0 <= result.score <= 100
    assert result.score == result.scorecard.total
    assert sum(category.maximum for category in result.scorecard.categories) == 100
    assert all(category.score <= category.maximum for category in result.scorecard.categories)
    assert result.risk_plan.available
    assert result.risk_plan.stop_loss < result.risk_plan.entry < result.risk_plan.target
    assert result.risk_plan.risk_reward > 0
    assert result.execution.recommendation == result.signal
    assert {category.name for category in result.scorecard.categories} == {
        "Bối cảnh thị trường",
        "Sức mạnh tương đối",
        "Cấu trúc giá",
        "Chất lượng xu hướng",
        "Dòng tiền",
        "Điểm kích hoạt",
        "Quản trị rủi ro",
    }


def test_analysis_rejects_short_history() -> None:
    prices = generate_demo_prices("HPG", periods=60).iloc[:49]
    with pytest.raises(ValueError, match="52 phiên"):
        analyze(prices)


def test_analysis_uses_available_market_breadth_context() -> None:
    frames = {
        symbol: generate_demo_prices(symbol, periods=220)
        for symbol in ("FPT", "HPG", "VCB")
    }
    breadth = analyze_market_breadth(frames)

    result = analyze(frames["FPT"], market_breadth=breadth)
    category = next(
        item for item in result.scorecard.categories if item.name == "Bối cảnh thị trường"
    )

    assert breadth.available
    assert category.available
    assert category.score == breadth.score
