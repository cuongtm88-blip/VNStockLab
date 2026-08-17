import pytest

from vnstocklab.analysis.backtest import run_backtest
from vnstocklab.data.demo import generate_demo_prices


def test_backtest_executes_on_next_session_and_builds_metrics() -> None:
    prices = generate_demo_prices("FPT", periods=120)
    result = run_backtest(
        prices,
        entry_score=1,
        exit_score=0,
        minimum_history=80,
        initial_capital=1_000_000,
    )

    assert not result.equity_curve.empty
    assert result.final_equity == pytest.approx(result.equity_curve["Chiến lược"].iloc[-1])
    assert result.trades
    assert all(trade.signal_date < trade.entry_date for trade in result.trades)
    assert result.max_drawdown_pct <= 0
    assert 0 <= result.win_rate_pct <= 100
    assert 0 <= result.exposure_pct <= 100


def test_backtest_validates_thresholds_and_history() -> None:
    prices = generate_demo_prices("FPT", periods=100)
    with pytest.raises(ValueError, match="Ngưỡng bán"):
        run_backtest(prices, entry_score=50, exit_score=50)
    with pytest.raises(ValueError, match="Cần hơn"):
        run_backtest(prices, minimum_history=99)
