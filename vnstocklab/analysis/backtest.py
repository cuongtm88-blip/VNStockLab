"""Look-ahead-safe backtesting for the 0–100 technical score."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import sqrt

import pandas as pd

from vnstocklab.analysis.engine import analyze


@dataclass(frozen=True)
class BacktestTrade:
    """One completed long trade."""

    signal_date: pd.Timestamp
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    stop_loss: float
    target: float
    entry_score: int
    exit_reason: str
    return_pct: float
    holding_days: int


@dataclass(frozen=True)
class BacktestResult:
    """Strategy performance, trades and comparable equity curves."""

    equity_curve: pd.DataFrame
    score_history: pd.Series
    trades: tuple[BacktestTrade, ...]
    total_return_pct: float
    benchmark_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate_pct: float
    profit_factor: float
    exposure_pct: float
    initial_capital: float
    final_equity: float


@dataclass(frozen=True)
class _PendingOrder:
    action: str
    signal_date: pd.Timestamp
    score: int
    stop_distance_pct: float = 0.0
    risk_reward: float = 0.0


def _performance_metrics(
    equity: pd.Series,
    benchmark_equity: pd.Series,
    trades: list[BacktestTrade],
    initial_capital: float,
    exposed_sessions: int,
) -> tuple[float, float, float, float, float, float, float, float]:
    total_return = (float(equity.iloc[-1]) / initial_capital - 1) * 100
    benchmark_return = (float(benchmark_equity.iloc[-1]) / initial_capital - 1) * 100
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1 / 365.25)
    cagr = ((float(equity.iloc[-1]) / initial_capital) ** (1 / years) - 1) * 100
    drawdown = equity / equity.cummax() - 1
    max_drawdown = float(drawdown.min() * 100)
    daily_returns = equity.pct_change().dropna()
    volatility = float(daily_returns.std(ddof=1))
    sharpe = (
        float(sqrt(252) * daily_returns.mean() / volatility)
        if volatility > 0 and len(daily_returns) > 1
        else 0.0
    )
    wins = [trade.return_pct for trade in trades if trade.return_pct > 0]
    losses = [trade.return_pct for trade in trades if trade.return_pct < 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0.0
    gross_loss = abs(sum(losses))
    profit_factor = sum(wins) / gross_loss if gross_loss > 0 else float("inf") if wins else 0.0
    exposure = exposed_sessions / len(equity) * 100
    return (
        total_return,
        benchmark_return,
        cagr,
        max_drawdown,
        sharpe,
        win_rate,
        profit_factor,
        exposure,
    )


def run_backtest(
    prices: pd.DataFrame,
    benchmark: pd.DataFrame | None = None,
    *,
    entry_score: int = 65,
    exit_score: int = 35,
    initial_capital: float = 100_000_000,
    fee_rate: float = 0.0015,
    minimum_history: int = 80,
    progress: Callable[[int, int], None] | None = None,
) -> BacktestResult:
    """Backtest score signals with next-open execution and conservative intraday exits."""
    if len(prices) <= minimum_history + 1:
        raise ValueError(f"Cần hơn {minimum_history + 1} phiên để backtest")
    if not 0 <= exit_score < entry_score <= 100:
        raise ValueError("Ngưỡng bán phải nhỏ hơn ngưỡng mua trong khoảng 0–100")
    if initial_capital <= 0 or not 0 <= fee_rate < 0.1:
        raise ValueError("Vốn và phí giao dịch không hợp lệ")

    ordered = prices.sort_index()
    start_signal_index = minimum_history - 1
    signal_indices = range(start_signal_index, len(ordered) - 1)
    scores: dict[pd.Timestamp, int] = {}
    plans: dict[pd.Timestamp, tuple[float, float]] = {}
    total_signals = len(ordered) - minimum_history
    for completed, index in enumerate(signal_indices, start=1):
        date = pd.Timestamp(ordered.index[index])
        benchmark_prefix = benchmark.loc[:date] if benchmark is not None else None
        snapshot = analyze(ordered.iloc[: index + 1], benchmark=benchmark_prefix)
        scores[date] = snapshot.score
        plans[date] = (
            max(snapshot.risk_plan.stop_distance_pct, 0.1),
            max(snapshot.risk_plan.risk_reward, 0.1),
        )
        if progress is not None:
            progress(completed, total_signals)

    cash = initial_capital
    shares = 0.0
    pending: _PendingOrder | None = None
    entry_date: pd.Timestamp | None = None
    entry_signal_date: pd.Timestamp | None = None
    entry_price = 0.0
    entry_score_value = 0
    stop_loss = 0.0
    target = 0.0
    trades: list[BacktestTrade] = []
    equity_values: dict[pd.Timestamp, float] = {}
    exposed_sessions = 0

    for index in range(minimum_history, len(ordered)):
        date = pd.Timestamp(ordered.index[index])
        bar = ordered.iloc[index]
        open_price = float(bar["open"])
        if pending is not None:
            if pending.action == "buy" and shares == 0:
                shares = cash / (open_price * (1 + fee_rate))
                cash = 0.0
                entry_date = date
                entry_signal_date = pending.signal_date
                entry_price = open_price
                entry_score_value = pending.score
                stop_loss = open_price * (1 - pending.stop_distance_pct / 100)
                target = open_price + (open_price - stop_loss) * pending.risk_reward
            elif pending.action == "sell" and shares > 0:
                cash = shares * open_price * (1 - fee_rate)
                effective_entry = entry_price * (1 + fee_rate)
                effective_exit = open_price * (1 - fee_rate)
                trades.append(
                    BacktestTrade(
                        entry_signal_date or date,
                        entry_date or date,
                        date,
                        entry_price,
                        open_price,
                        stop_loss,
                        target,
                        entry_score_value,
                        "Điểm thoát",
                        (effective_exit / effective_entry - 1) * 100,
                        (date - (entry_date or date)).days,
                    )
                )
                shares = 0.0
            pending = None

        if shares > 0:
            exit_price = 0.0
            exit_reason = ""
            if float(bar["low"]) <= stop_loss:
                exit_price, exit_reason = stop_loss, "Stop-loss"
            elif float(bar["high"]) >= target:
                exit_price, exit_reason = target, "Mục tiêu"
            if exit_price > 0:
                cash = shares * exit_price * (1 - fee_rate)
                effective_entry = entry_price * (1 + fee_rate)
                effective_exit = exit_price * (1 - fee_rate)
                trades.append(
                    BacktestTrade(
                        entry_signal_date or date,
                        entry_date or date,
                        date,
                        entry_price,
                        exit_price,
                        stop_loss,
                        target,
                        entry_score_value,
                        exit_reason,
                        (effective_exit / effective_entry - 1) * 100,
                        (date - (entry_date or date)).days,
                    )
                )
                shares = 0.0

        if shares > 0:
            exposed_sessions += 1
        equity_values[date] = cash + shares * float(bar["close"])

        score = scores.get(date)
        if score is not None and index < len(ordered) - 1:
            if shares == 0 and score >= entry_score:
                stop_pct, risk_reward = plans[date]
                pending = _PendingOrder("buy", date, score, stop_pct, risk_reward)
            elif shares > 0 and score <= exit_score:
                pending = _PendingOrder("sell", date, score)

    final_date = pd.Timestamp(ordered.index[-1])
    if shares > 0:
        final_price = float(ordered.iloc[-1]["close"])
        cash = shares * final_price * (1 - fee_rate)
        effective_entry = entry_price * (1 + fee_rate)
        effective_exit = final_price * (1 - fee_rate)
        trades.append(
            BacktestTrade(
                entry_signal_date or final_date,
                entry_date or final_date,
                final_date,
                entry_price,
                final_price,
                stop_loss,
                target,
                entry_score_value,
                "Cuối kỳ",
                (effective_exit / effective_entry - 1) * 100,
                (final_date - (entry_date or final_date)).days,
            )
        )
        equity_values[final_date] = cash

    equity = pd.Series(equity_values, name="Chiến lược", dtype=float)
    first_close = float(ordered.loc[equity.index[0], "close"])
    benchmark_equity = ordered.loc[equity.index, "close"] / first_close * initial_capital
    benchmark_equity = benchmark_equity.rename("Mua & nắm giữ")
    metrics = _performance_metrics(
        equity, benchmark_equity, trades, initial_capital, exposed_sessions
    )
    curve = pd.concat([equity, benchmark_equity], axis=1)
    return BacktestResult(
        curve,
        pd.Series(scores, name="Điểm", dtype=int),
        tuple(trades),
        *metrics,
        initial_capital,
        float(equity.iloc[-1]),
    )
