from vnstocklab.analysis.strategy_lab import StrategyConfig, run_strategy_lab
from vnstocklab.data.demo import generate_demo_prices


def test_strategy_lab_builds_multi_symbol_exploration_and_curve() -> None:
    frames = {
        symbol: generate_demo_prices(symbol, periods=207)
        for symbol in ("FPT", "HPG", "VCB")
    }
    benchmark = generate_demo_prices("VNINDEX", periods=207)
    config = StrategyConfig(
        entry_score=1,
        exit_score=0,
        minimum_confirmations=0,
        max_positions=2,
        minimum_history=201,
    )

    result = run_strategy_lab(frames, benchmark, config)

    assert not result.equity_curve.empty
    assert set(result.equity_curve) == {"Danh mục", "VN-Index"}
    assert set(result.exploration["symbol"]) == set(frames)
    assert result.exploration["market_score"].between(0, 10).all()
    assert result.exploration["confirmations"].between(0, 9).all()
    assert 0 <= result.exposure_pct <= 100
    assert result.trades
    assert all(trade.signal_date < trade.entry_date for trade in result.trades)
    assert all(trade.shares % config.lot_size == 0 for trade in result.trades)
