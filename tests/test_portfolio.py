import pandas as pd
import pytest

from vnstocklab.analysis.portfolio import (
    PortfolioTransaction,
    build_portfolio,
    suggest_rebalance,
)


def transaction(
    day: int, action: str, shares: int, price: float, fee: float = 0
) -> PortfolioTransaction:
    return PortfolioTransaction(pd.Timestamp(2026, 1, day), "FPT", action, shares, price, fee)


def test_portfolio_tracks_average_cost_and_realized_pnl() -> None:
    summary = build_portfolio(
        [
            transaction(1, "Mua", 100, 100, 10),
            transaction(2, "Mua", 100, 120, 10),
            transaction(3, "Bán", 100, 130, 10),
        ],
        {"FPT": 140},
    )
    position = summary.positions[0]
    assert position.shares == 100
    assert position.average_cost == pytest.approx(110.1)
    assert summary.realized_pnl == pytest.approx(1_980)
    assert summary.unrealized_pnl == pytest.approx(2_990)
    assert summary.total_pnl == pytest.approx(4_970)


def test_portfolio_rejects_short_sale_and_recommends_concentration_reduction() -> None:
    with pytest.raises(ValueError, match="Không đủ"):
        build_portfolio([transaction(1, "Bán", 100, 100)], {})
    assert suggest_rebalance(40, 60, "NẮM GIỮ") == "Giảm tập trung"
    assert suggest_rebalance(10, 70, "MUA THĂM DÒ") == "Có thể gia tăng"
