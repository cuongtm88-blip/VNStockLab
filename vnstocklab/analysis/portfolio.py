"""Portfolio accounting and risk summaries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PortfolioTransaction:
    date: pd.Timestamp
    symbol: str
    action: str
    shares: int
    price: float
    fee: float = 0.0


@dataclass(frozen=True)
class PortfolioPosition:
    symbol: str
    shares: int
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    weight_pct: float


@dataclass(frozen=True)
class PortfolioSummary:
    positions: tuple[PortfolioPosition, ...]
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    max_weight_pct: float
    concentration_index: float


def build_portfolio(
    transactions: Sequence[PortfolioTransaction],
    current_prices: Mapping[str, float],
) -> PortfolioSummary:
    """Apply transactions chronologically using moving-average cost accounting."""
    state: dict[str, dict[str, float]] = {}
    for transaction in sorted(transactions, key=lambda item: item.date):
        symbol = transaction.symbol.strip().upper()
        if transaction.action not in {"Mua", "Bán"}:
            raise ValueError("Giao dịch phải là Mua hoặc Bán")
        if transaction.shares <= 0 or transaction.price <= 0 or transaction.fee < 0:
            raise ValueError("Khối lượng, giá và phí giao dịch không hợp lệ")
        item = state.setdefault(symbol, {"shares": 0, "cost": 0.0, "realized": 0.0})
        shares = int(item["shares"])
        if transaction.action == "Mua":
            item["shares"] = shares + transaction.shares
            item["cost"] += transaction.shares * transaction.price + transaction.fee
            continue
        if transaction.shares > shares:
            raise ValueError(f"Không đủ cổ phiếu {symbol} để bán")
        average_cost = item["cost"] / shares
        item["realized"] += (
            transaction.shares * transaction.price
            - transaction.fee
            - transaction.shares * average_cost
        )
        item["shares"] = shares - transaction.shares
        item["cost"] -= transaction.shares * average_cost

    raw_positions: list[tuple[str, int, float, float, float]] = []
    for symbol, item in state.items():
        shares = int(item["shares"])
        if shares <= 0:
            continue
        if symbol not in current_prices:
            raise ValueError(f"Thiếu giá hiện tại của {symbol}")
        average_cost = item["cost"] / shares
        current_price = float(current_prices[symbol])
        raw_positions.append((symbol, shares, average_cost, current_price, float(item["realized"])))
    market_value = sum(shares * price for _, shares, _, price, _ in raw_positions)
    positions = tuple(
        PortfolioPosition(
            symbol=symbol,
            shares=shares,
            average_cost=average_cost,
            current_price=current_price,
            market_value=shares * current_price,
            unrealized_pnl=shares * (current_price - average_cost),
            realized_pnl=realized,
            weight_pct=shares * current_price / market_value * 100 if market_value else 0.0,
        )
        for symbol, shares, average_cost, current_price, realized in raw_positions
    )
    realized_pnl = sum(float(item["realized"]) for item in state.values())
    unrealized_pnl = sum(position.unrealized_pnl for position in positions)
    weights = [position.weight_pct / 100 for position in positions]
    return PortfolioSummary(
        positions=positions,
        market_value=market_value,
        cost_basis=sum(float(item["cost"]) for item in state.values()),
        unrealized_pnl=unrealized_pnl,
        realized_pnl=realized_pnl,
        total_pnl=realized_pnl + unrealized_pnl,
        max_weight_pct=max((position.weight_pct for position in positions), default=0.0),
        concentration_index=sum(weight**2 for weight in weights),
    )


def suggest_rebalance(weight_pct: float, score: int, signal: str) -> str:
    """Return a transparent rule-based portfolio action."""
    if signal == "GIẢM TỶ TRỌNG" or score <= 35:
        return "Giảm tỷ trọng"
    if weight_pct > 30:
        return "Giảm tập trung"
    if score >= 65 and weight_pct < 20:
        return "Có thể gia tăng"
    return "Nắm giữ"
