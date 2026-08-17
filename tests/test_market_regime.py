from vnstocklab.analysis.market_breadth import unavailable_breadth
from vnstocklab.analysis.market_regime import evaluate_market_regime


def test_bullish_regime_recommends_high_stock_exposure() -> None:
    breadth = unavailable_breadth()
    breadth = breadth.__class__(
        **{**breadth.__dict__, "available": True, "score": 9, "state": "Tích cực mạnh"}
    )
    result = evaluate_market_regime(
        index_score=85,
        index_trend="Tăng",
        close=1300,
        sma20=1270,
        sma50=1230,
        breadth=breadth,
    )
    assert result.state == "Tấn công"
    assert result.stock_allocation == (70, 90)
    assert result.cash_allocation == (10, 30)


def test_bearish_regime_prioritizes_cash() -> None:
    breadth = unavailable_breadth()
    breadth = breadth.__class__(
        **{**breadth.__dict__, "available": True, "score": 1, "state": "Tiêu cực mạnh"}
    )
    result = evaluate_market_regime(
        index_score=25,
        index_trend="Giảm",
        close=1100,
        sma20=1150,
        sma50=1200,
        breadth=breadth,
    )
    assert result.state == "Phòng thủ"
    assert result.stock_allocation == (0, 25)
    assert result.cash_allocation == (75, 100)


def test_missing_breadth_is_neutral_instead_of_blocking() -> None:
    result = evaluate_market_regime(
        index_score=60,
        index_trend="Đi ngang",
        close=1250,
        sma20=1240,
        sma50=1230,
        breadth=unavailable_breadth(),
    )
    assert 0 <= result.score <= 100
    assert "chưa đủ dữ liệu" in result.reasons[1]
