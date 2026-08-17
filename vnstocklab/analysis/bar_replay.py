"""Pure state transitions for historical bar replay trading."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pandas as pd


@dataclass(frozen=True)
class ReplayTrade:
    action: str
    ordered_at: pd.Timestamp
    executed_at: pd.Timestamp
    price: float
    shares: int
    cash_after: float
    realized_pnl: float


@dataclass(frozen=True)
class ReplayAccount:
    cash: float = 100_000_000
    shares: int = 0
    average_price: float = 0.0
    pending_action: str | None = None
    pending_fraction: float = 0.0
    ordered_at: pd.Timestamp | None = None
    trades: tuple[ReplayTrade, ...] = ()


@dataclass(frozen=True)
class ReplayReport:
    """Mark-to-market summary of a replay account."""

    final_equity: float
    total_return_pct: float
    realized_pnl: float
    unrealized_pnl: float
    buy_orders: int
    sell_orders: int
    profitable_sells: int
    win_rate_pct: float


def queue_replay_order(
    account: ReplayAccount,
    action: str,
    ordered_at: pd.Timestamp,
    fraction: float = 1.0,
) -> ReplayAccount:
    """Queue a buy or sell for the next bar's open."""
    if action not in {"buy", "sell"}:
        raise ValueError("Lệnh replay phải là buy hoặc sell")
    if account.pending_action is not None:
        raise ValueError("Đã có một lệnh chờ khớp")
    if action == "buy" and account.cash <= 0:
        raise ValueError("Không còn tiền mặt để mua")
    if action == "sell" and account.shares <= 0:
        raise ValueError("Không có vị thế để bán")
    return replace(
        account,
        pending_action=action,
        pending_fraction=max(0.01, min(1.0, fraction)),
        ordered_at=ordered_at,
    )


def execute_replay_order(
    account: ReplayAccount,
    executed_at: pd.Timestamp,
    open_price: float,
    *,
    fee_rate: float = 0.0015,
    sell_tax_rate: float = 0.001,
    lot_size: int = 100,
    price_scale: float = 1.0,
) -> ReplayAccount:
    """Execute a pending order at the next open, respecting Vietnamese board lots."""
    if account.pending_action is None:
        return account
    if account.ordered_at is None or executed_at <= account.ordered_at:
        raise ValueError("Lệnh chỉ được khớp ở cây nến sau thời điểm đặt")
    if account.pending_action == "buy":
        budget = account.cash * account.pending_fraction
        monetary_price = open_price * price_scale
        shares = int(budget / (monetary_price * (1 + fee_rate)) // lot_size * lot_size)
        if shares <= 0:
            return replace(account, pending_action=None, pending_fraction=0, ordered_at=None)
        cost = shares * monetary_price * (1 + fee_rate)
        total_shares = account.shares + shares
        average_price = (
            account.average_price * account.shares + open_price * shares
        ) / total_shares
        cash = account.cash - cost
        trade = ReplayTrade(
            "Mua", account.ordered_at, executed_at, open_price, shares, cash, 0.0
        )
        return ReplayAccount(
            cash,
            total_shares,
            average_price,
            trades=(*account.trades, trade),
        )

    shares = int(account.shares * account.pending_fraction // lot_size * lot_size)
    shares = account.shares if account.pending_fraction >= 1 else shares
    if shares <= 0:
        return replace(account, pending_action=None, pending_fraction=0, ordered_at=None)
    monetary_price = open_price * price_scale
    proceeds = shares * monetary_price * (1 - fee_rate - sell_tax_rate)
    pnl = proceeds - shares * account.average_price * price_scale * (1 + fee_rate)
    remaining = account.shares - shares
    cash = account.cash + proceeds
    trade = ReplayTrade("Bán", account.ordered_at, executed_at, open_price, shares, cash, pnl)
    return ReplayAccount(
        cash,
        remaining,
        account.average_price if remaining else 0.0,
        trades=(*account.trades, trade),
    )


def replay_equity(
    account: ReplayAccount, close_price: float, price_scale: float = 1.0
) -> float:
    """Mark the simulated account to market."""
    return account.cash + account.shares * close_price * price_scale


def build_replay_report(
    account: ReplayAccount,
    close_price: float,
    initial_cash: float,
    price_scale: float = 1.0,
) -> ReplayReport:
    """Build a compact performance report without mutating replay state."""
    final_equity = replay_equity(account, close_price, price_scale)
    realized_pnl = sum(trade.realized_pnl for trade in account.trades)
    unrealized_pnl = account.shares * (close_price - account.average_price) * price_scale
    sells = [trade for trade in account.trades if trade.action == "Bán"]
    profitable_sells = sum(trade.realized_pnl > 0 for trade in sells)
    return ReplayReport(
        final_equity=final_equity,
        total_return_pct=(final_equity / initial_cash - 1) * 100,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        buy_orders=sum(trade.action == "Mua" for trade in account.trades),
        sell_orders=len(sells),
        profitable_sells=profitable_sells,
        win_rate_pct=profitable_sells / len(sells) * 100 if sells else 0.0,
    )
