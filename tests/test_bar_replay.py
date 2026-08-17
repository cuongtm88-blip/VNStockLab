import pandas as pd
import pytest

from vnstocklab.analysis.bar_replay import (
    ReplayAccount,
    build_replay_report,
    execute_replay_order,
    queue_replay_order,
    replay_equity,
)


def test_replay_order_executes_only_on_next_bar_and_respects_board_lot() -> None:
    signal_date = pd.Timestamp("2026-01-05")
    account = queue_replay_order(ReplayAccount(cash=3_000_000), "buy", signal_date, 0.5)

    with pytest.raises(ValueError, match="cây nến sau"):
        execute_replay_order(account, signal_date, 10_000)

    account = execute_replay_order(account, pd.Timestamp("2026-01-06"), 10_000)
    assert account.shares % 100 == 0
    assert account.shares > 0
    assert account.trades[0].ordered_at < account.trades[0].executed_at
    assert replay_equity(account, 11_000) > account.cash


def test_replay_sell_realizes_pnl_and_clears_position() -> None:
    account = queue_replay_order(
        ReplayAccount(cash=2_000_000), "buy", pd.Timestamp("2026-01-05"), 1
    )
    account = execute_replay_order(account, pd.Timestamp("2026-01-06"), 10_000)
    account = queue_replay_order(account, "sell", pd.Timestamp("2026-01-07"), 1)
    account = execute_replay_order(account, pd.Timestamp("2026-01-08"), 11_000)

    assert account.shares == 0
    assert account.average_price == 0
    assert account.trades[-1].realized_pnl > 0

    report = build_replay_report(account, 11_000, 2_000_000)
    assert report.final_equity == pytest.approx(account.cash)
    assert report.realized_pnl > 0
    assert report.total_return_pct > 0
    assert report.buy_orders == 1
    assert report.sell_orders == 1
    assert report.profitable_sells == 1
    assert report.win_rate_pct == 100


def test_replay_can_scale_thousand_dong_market_prices() -> None:
    account = queue_replay_order(
        ReplayAccount(cash=100_000_000), "buy", pd.Timestamp("2026-01-22"), 0.5
    )
    account = execute_replay_order(
        account, pd.Timestamp("2026-01-23"), 102.19, price_scale=1_000
    )
    assert account.shares == 400
    assert account.average_price == pytest.approx(102.19)
    assert replay_equity(account, 103, price_scale=1_000) < 101_000_000
