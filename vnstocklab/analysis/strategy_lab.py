"""Portfolio Strategy Lab using VNStockLab's complete recommendation engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import floor, sqrt
from typing import Any

import pandas as pd

from vnstocklab.analysis.engine import AnalysisResult, analyze
from vnstocklab.analysis.market_breadth import analyze_market_breadth


@dataclass(frozen=True)
class StrategyConfig:
    """AmiBroker-style portfolio and execution settings."""

    entry_score: int = 65
    exit_score: int = 35
    minimum_confirmations: int = 5
    max_positions: int = 5
    risk_per_trade_pct: float = 1.0
    max_position_pct: float = 25.0
    fee_pct: float = 0.15
    sell_tax_pct: float = 0.1
    slippage_pct: float = 0.1
    lot_size: int = 100
    trailing_atr: float = 2.5
    max_holding_sessions: int = 60
    initial_capital: float = 100_000_000
    minimum_history: int = 201


@dataclass(frozen=True)
class ExplorationRow:
    """All indicator evidence used to accept, rank or reject a symbol."""

    date: pd.Timestamp
    symbol: str
    score: int
    rank_score: int
    confirmations: int
    eligible: bool
    signal: str
    trend: str
    market_score: int
    relative_strength_score: int
    structure_score: int
    trend_score: int
    money_flow_score: int
    trigger_score: int
    risk_score: int
    sma: bool
    macd: bool
    rsi: bool
    mfi: bool
    adx_dmi: bool
    obv_cmf: bool
    ichimoku: bool
    dow: bool
    price_action: bool
    stop_distance_pct: float
    risk_reward: float
    atr: float


@dataclass(frozen=True)
class PortfolioTrade:
    symbol: str
    signal_date: pd.Timestamp
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    shares: int
    entry_price: float
    exit_price: float
    return_pct: float
    pnl: float
    exit_reason: str
    holding_sessions: int
    entry_score: int
    confirmations: int


@dataclass(frozen=True)
class StrategyLabResult:
    equity_curve: pd.DataFrame
    trades: tuple[PortfolioTrade, ...]
    exploration: pd.DataFrame
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate_pct: float
    profit_factor: float
    expectancy_pct: float
    exposure_pct: float
    final_equity: float


@dataclass
class _Position:
    symbol: str
    signal_date: pd.Timestamp
    entry_date: pd.Timestamp
    shares: int
    entry_price: float
    stop: float
    target: float
    sessions: int
    entry_score: int
    confirmations: int


def _scalar(frame: pd.DataFrame, date: pd.Timestamp, column: str) -> float:
    """Read one numeric cell safely even if a provider returned a duplicate date."""
    value: Any = frame.loc[date, column]
    if isinstance(value, pd.Series):
        value = value.iloc[-1]
    return float(value)


def _explore(
    date: pd.Timestamp,
    symbol: str,
    result: AnalysisResult,
    config: StrategyConfig,
) -> ExplorationRow:
    latest = result.data.iloc[-1]
    category = {item.name: item.score for item in result.scorecard.categories}
    checks = {
        "sma": bool(latest["close"] > latest["sma20"] > latest["sma50"]),
        "macd": bool(latest["macd"] > latest["macd_signal"]),
        "rsi": bool(45 <= latest["rsi14"] <= 75),
        "mfi": bool(35 <= latest["mfi14"] <= 80),
        "adx_dmi": bool(latest["adx14"] >= 20 and latest["plus_di14"] > latest["minus_di14"]),
        "obv_cmf": bool(latest["cmf20"] > 0 and latest["obv"] > result.data["obv"].iloc[-6]),
        "ichimoku": result.ichimoku.daily.state in {"Tăng", "Tăng mạnh"},
        "dow": result.dow.medium_term.state == "Xu hướng tăng",
        "price_action": bool(
            latest["candle_confirmed"]
            or latest["squeeze_release"]
            or (result.levels.breakout is not None and result.levels.breakout.direction == "up")
            or any(pattern.direction == "bullish" for pattern in result.patterns)
        ),
    }
    confirmations = sum(checks.values())
    eligible = (
        result.score >= config.entry_score
        and confirmations >= config.minimum_confirmations
        and result.execution.eligible
    )
    return ExplorationRow(
        date,
        symbol,
        result.score,
        result.score + confirmations,
        confirmations,
        eligible,
        result.signal,
        result.trend,
        category["Bối cảnh thị trường"],
        category["Sức mạnh tương đối"],
        category["Cấu trúc giá"],
        category["Chất lượng xu hướng"],
        category["Dòng tiền"],
        category["Điểm kích hoạt"],
        category["Quản trị rủi ro"],
        checks["sma"],
        checks["macd"],
        checks["rsi"],
        checks["mfi"],
        checks["adx_dmi"],
        checks["obv_cmf"],
        checks["ichimoku"],
        checks["dow"],
        checks["price_action"],
        result.risk_plan.stop_distance_pct,
        result.risk_plan.risk_reward,
        float(latest["atr14"]),
    )


def _validate(frames: dict[str, pd.DataFrame], config: StrategyConfig) -> None:
    if len(frames) < 2:
        raise ValueError("Strategy Lab cần ít nhất 2 mã")
    if not 0 <= config.exit_score < config.entry_score <= 100:
        raise ValueError("Ngưỡng bán phải nhỏ hơn ngưỡng mua")
    if config.minimum_history < 201:
        raise ValueError("Cần ít nhất 201 phiên để sử dụng Market Breadth và SMA200")
    if config.max_positions < 1 or config.lot_size < 1:
        raise ValueError("Cấu hình danh mục không hợp lệ")


def run_strategy_lab(
    frames: dict[str, pd.DataFrame],
    benchmark: pd.DataFrame,
    config: StrategyConfig | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> StrategyLabResult:
    """Run a ranked, shared-cash portfolio backtest without future data leakage."""
    config = config or StrategyConfig()
    _validate(frames, config)
    normalized = {symbol.upper(): frame.sort_index() for symbol, frame in frames.items()}
    common_dates = sorted(set.intersection(*(set(frame.index) for frame in normalized.values())))
    if len(common_dates) <= config.minimum_history + 1:
        raise ValueError("Không đủ lịch sử giao nhau giữa các mã")
    dates = pd.DatetimeIndex(common_dates)
    signal_dates = dates[config.minimum_history - 1 : -1]
    snapshots: dict[tuple[pd.Timestamp, str], ExplorationRow] = {}
    rows: list[ExplorationRow] = []
    total = len(signal_dates) * len(normalized)
    completed = 0
    for date in signal_dates:
        prefixes = {symbol: frame.loc[:date] for symbol, frame in normalized.items()}
        breadth = analyze_market_breadth(prefixes)
        for symbol, prefix in prefixes.items():
            result = analyze(prefix, benchmark.loc[:date], breadth)
            row = _explore(pd.Timestamp(date), symbol, result, config)
            snapshots[(pd.Timestamp(date), symbol)] = row
            rows.append(row)
            completed += 1
            if progress is not None:
                progress(completed, total)

    cash = config.initial_capital
    positions: dict[str, _Position] = {}
    pending_entries: list[ExplorationRow] = []
    pending_exits: dict[str, str] = {}
    trades: list[PortfolioTrade] = []
    equity_values: dict[pd.Timestamp, float] = {}
    exposed = 0

    for date in dates[config.minimum_history:]:
        date = pd.Timestamp(date)
        for symbol, reason in list(pending_exits.items()):
            position = positions.get(symbol)
            if position is None:
                continue
            raw_price = _scalar(normalized[symbol], date, "open")
            price = raw_price * (1 - config.slippage_pct / 100)
            proceeds = position.shares * price * (
                1 - (config.fee_pct + config.sell_tax_pct) / 100
            )
            cost = position.shares * position.entry_price * (1 + config.fee_pct / 100)
            cash += proceeds
            trades.append(
                PortfolioTrade(
                    symbol, position.signal_date, position.entry_date, date,
                    position.shares, position.entry_price, price,
                    (proceeds / cost - 1) * 100, proceeds - cost, reason,
                    position.sessions, position.entry_score, position.confirmations,
                )
            )
            del positions[symbol]
        pending_exits.clear()

        marked_equity = cash + sum(
            position.shares * _scalar(normalized[symbol], date, "open")
            for symbol, position in positions.items()
        )
        slots = config.max_positions - len(positions)
        for candidate in sorted(pending_entries, key=lambda item: item.rank_score, reverse=True):
            if slots <= 0 or candidate.symbol in positions:
                continue
            raw_price = _scalar(normalized[candidate.symbol], date, "open")
            price = raw_price * (1 + config.slippage_pct / 100)
            stop_distance = max(price * candidate.stop_distance_pct / 100, 0.01)
            risk_budget = marked_equity * config.risk_per_trade_pct / 100
            cap_budget = marked_equity * config.max_position_pct / 100
            shares = min(
                floor(risk_budget / stop_distance / config.lot_size) * config.lot_size,
                floor(cap_budget / price / config.lot_size) * config.lot_size,
                floor(cash / (price * (1 + config.fee_pct / 100)) / config.lot_size)
                * config.lot_size,
            )
            if shares < config.lot_size:
                continue
            cash -= shares * price * (1 + config.fee_pct / 100)
            positions[candidate.symbol] = _Position(
                candidate.symbol, candidate.date, date, shares, price,
                price - stop_distance,
                price + stop_distance * max(candidate.risk_reward, 0.5),
                0, candidate.score, candidate.confirmations,
            )
            slots -= 1
        pending_entries = []

        for symbol, position in list(positions.items()):
            frame = normalized[symbol]
            exit_price = position.stop if _scalar(frame, date, "low") <= position.stop else (
                position.target if _scalar(frame, date, "high") >= position.target else 0.0
            )
            if exit_price:
                reason = "Stop-loss" if exit_price == position.stop else "Mục tiêu"
                proceeds = position.shares * exit_price * (
                    1 - (config.fee_pct + config.sell_tax_pct) / 100
                )
                cost = position.shares * position.entry_price * (1 + config.fee_pct / 100)
                cash += proceeds
                trades.append(
                    PortfolioTrade(
                        symbol, position.signal_date, position.entry_date, date,
                        position.shares, position.entry_price, exit_price,
                        (proceeds / cost - 1) * 100, proceeds - cost, reason,
                        position.sessions, position.entry_score, position.confirmations,
                    )
                )
                del positions[symbol]
                continue
            position.sessions += 1
            current = snapshots.get((date, symbol))
            if current is not None:
                position.stop = max(
                    position.stop,
                    _scalar(frame, date, "close") - config.trailing_atr * current.atr,
                )
                if current.score <= config.exit_score:
                    pending_exits[symbol] = "Điểm thoát"
            if position.sessions >= config.max_holding_sessions:
                pending_exits[symbol] = "Quá thời gian"

        if positions:
            exposed += 1
        equity_values[date] = cash + sum(
            position.shares * _scalar(normalized[symbol], date, "close")
            for symbol, position in positions.items()
        )
        candidates = [
            snapshots[(date, symbol)]
            for symbol in normalized
            if (date, symbol) in snapshots and snapshots[(date, symbol)].eligible
        ]
        pending_entries = candidates

    final_date = pd.Timestamp(dates[-1])
    for symbol, position in list(positions.items()):
        price = _scalar(normalized[symbol], final_date, "close")
        proceeds = position.shares * price * (1 - (config.fee_pct + config.sell_tax_pct) / 100)
        cost = position.shares * position.entry_price * (1 + config.fee_pct / 100)
        cash += proceeds
        trades.append(
            PortfolioTrade(
                symbol, position.signal_date, position.entry_date, final_date,
                position.shares, position.entry_price, price, (proceeds / cost - 1) * 100,
                proceeds - cost, "Cuối kỳ", position.sessions,
                position.entry_score, position.confirmations,
            )
        )
    equity_values[final_date] = cash
    equity = pd.Series(equity_values, name="Danh mục", dtype=float)
    returns = equity.pct_change().dropna()
    total_return = (cash / config.initial_capital - 1) * 100
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1 / 365.25)
    cagr = ((cash / config.initial_capital) ** (1 / years) - 1) * 100
    max_drawdown = float((equity / equity.cummax() - 1).min() * 100)
    volatility = float(returns.std())
    sharpe = float(sqrt(252) * returns.mean() / volatility) if volatility > 0 else 0.0
    downside = float(returns[returns < 0].std())
    sortino = float(sqrt(252) * returns.mean() / downside) if downside > 0 else 0.0
    wins = [trade.return_pct for trade in trades if trade.return_pct > 0]
    losses = [trade.return_pct for trade in trades if trade.return_pct < 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0.0
    profit_factor = sum(wins) / abs(sum(losses)) if losses else float("inf") if wins else 0.0
    expectancy = sum(trade.return_pct for trade in trades) / len(trades) if trades else 0.0
    benchmark_curve = benchmark.reindex(equity.index).ffill()["close"]
    benchmark_curve = benchmark_curve / benchmark_curve.iloc[0] * config.initial_capital
    curve = pd.concat([equity, benchmark_curve.rename("VN-Index")], axis=1)
    exploration = pd.DataFrame([row.__dict__ for row in rows])
    return StrategyLabResult(
        curve, tuple(trades), exploration, total_return, cagr, max_drawdown,
        sharpe, sortino, win_rate, profit_factor, expectancy,
        exposed / len(equity) * 100, cash,
    )
