import pytest

from vnstocklab.analysis.market_regime import MarketRegime
from vnstocklab.analysis.position_sizing import calculate_position_size


def _regime(upper: int = 70) -> MarketRegime:
    return MarketRegime(65, "Tích cực có chọn lọc", "Trung bình", (50, upper), (30, 50), "Mua", ())


def test_position_size_uses_risk_budget_and_vietnamese_lots() -> None:
    plan = calculate_position_size(
        capital=100_000_000,
        cash_available=100_000_000,
        entry_price=50,
        stop_loss=48,
        risk_per_trade_pct=1,
        max_position_pct=30,
        current_stock_exposure_pct=0,
        regime=_regime(),
    )
    assert plan.shares == 500
    assert plan.lots == 5
    assert plan.risk_amount == 1_000_000
    assert plan.limiting_factor == "Ngân sách rủi ro"


def test_position_size_respects_remaining_market_capacity() -> None:
    plan = calculate_position_size(
        capital=100_000_000,
        cash_available=100_000_000,
        entry_price=50,
        stop_loss=45,
        risk_per_trade_pct=10,
        max_position_pct=50,
        current_stock_exposure_pct=66,
        regime=_regime(),
    )
    assert plan.shares == 0
    assert not plan.available
    assert plan.limiting_factor == "Trần cổ phiếu theo thị trường"


def test_position_size_rejects_invalid_stop() -> None:
    with pytest.raises(ValueError, match="Giá vào"):
        calculate_position_size(
            capital=100_000_000,
            cash_available=50_000_000,
            entry_price=50,
            stop_loss=51,
            risk_per_trade_pct=1,
            max_position_pct=20,
            current_stock_exposure_pct=0,
            regime=_regime(),
        )
