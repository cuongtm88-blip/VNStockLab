"""Technical analysis services."""

from vnstocklab.analysis.alerts import (
    AlertEvent,
    AlertRule,
    AlertSnapshot,
    alert_rules_from_screening,
    detect_breadth_alert,
    detect_symbol_alerts,
)
from vnstocklab.analysis.backtest import BacktestResult, BacktestTrade, run_backtest
from vnstocklab.analysis.bar_replay import (
    ReplayAccount,
    ReplayReport,
    ReplayTrade,
    build_replay_report,
    execute_replay_order,
    queue_replay_order,
    replay_equity,
)
from vnstocklab.analysis.candlesticks import CandlestickEvent, candlestick_events
from vnstocklab.analysis.dow import (
    DowAnalysis,
    DowTimeframe,
    StructureEvent,
    StructurePoint,
    analyze_dow_structure,
    classify_market_structure,
    classify_pivots,
)
from vnstocklab.analysis.engine import AnalysisResult, analyze
from vnstocklab.analysis.execution import ExecutionDecision, evaluate_execution_gate
from vnstocklab.analysis.ichimoku import (
    IchimokuSnapshot,
    MultiTimeframeIchimoku,
    add_ichimoku,
    analyze_multi_timeframe_ichimoku,
    resample_weekly,
)
from vnstocklab.analysis.levels import (
    Breakout,
    Pivot,
    PriceZone,
    SupportResistanceAnalysis,
    analyze_support_resistance,
    detect_pivots,
)
from vnstocklab.analysis.market_breadth import (
    MarketBreadth,
    analyze_market_breadth,
    unavailable_breadth,
)
from vnstocklab.analysis.market_regime import MarketRegime, evaluate_market_regime
from vnstocklab.analysis.opportunity_pipeline import (
    PIPELINE_STAGES,
    build_opportunity_pipeline,
    open_position_symbols,
)
from vnstocklab.analysis.patterns import PricePattern, analyze_price_patterns
from vnstocklab.analysis.portfolio import (
    PortfolioPosition,
    PortfolioSummary,
    PortfolioTransaction,
    build_portfolio,
    suggest_rebalance,
)
from vnstocklab.analysis.position_sizing import PositionSizePlan, calculate_position_size
from vnstocklab.analysis.relative_strength import (
    RelativeStrengthAnalysis,
    analyze_relative_strength,
)
from vnstocklab.analysis.risk import RiskPlan, build_risk_plan
from vnstocklab.analysis.scorecard import CategoryScore, TechnicalScorecard, build_scorecard
from vnstocklab.analysis.screener import ScreeningResult, filter_screening_rows, screen_symbols
from vnstocklab.analysis.strategy_lab import (
    ExplorationRow,
    PortfolioTrade,
    StrategyConfig,
    StrategyLabResult,
    run_strategy_lab,
)

__all__ = [
    "AnalysisResult",
    "AlertEvent",
    "AlertRule",
    "AlertSnapshot",
    "alert_rules_from_screening",
    "BacktestResult",
    "BacktestTrade",
    "Breakout",
    "CandlestickEvent",
    "CategoryScore",
    "DowAnalysis",
    "DowTimeframe",
    "ExplorationRow",
    "ExecutionDecision",
    "IchimokuSnapshot",
    "MultiTimeframeIchimoku",
    "MarketBreadth",
    "MarketRegime",
    "Pivot",
    "PIPELINE_STAGES",
    "PriceZone",
    "PortfolioTrade",
    "PortfolioPosition",
    "PortfolioSummary",
    "PortfolioTransaction",
    "PositionSizePlan",
    "PricePattern",
    "RelativeStrengthAnalysis",
    "ReplayAccount",
    "ReplayReport",
    "ReplayTrade",
    "RiskPlan",
    "ScreeningResult",
    "filter_screening_rows",
    "SupportResistanceAnalysis",
    "StructureEvent",
    "StructurePoint",
    "StrategyConfig",
    "StrategyLabResult",
    "TechnicalScorecard",
    "analyze",
    "analyze_dow_structure",
    "add_ichimoku",
    "analyze_multi_timeframe_ichimoku",
    "analyze_market_breadth",
    "analyze_price_patterns",
    "analyze_relative_strength",
    "analyze_support_resistance",
    "build_scorecard",
    "build_replay_report",
    "build_portfolio",
    "build_opportunity_pipeline",
    "build_risk_plan",
    "candlestick_events",
    "calculate_position_size",
    "classify_pivots",
    "classify_market_structure",
    "detect_pivots",
    "detect_breadth_alert",
    "detect_symbol_alerts",
    "execute_replay_order",
    "evaluate_execution_gate",
    "evaluate_market_regime",
    "queue_replay_order",
    "open_position_symbols",
    "screen_symbols",
    "suggest_rebalance",
    "unavailable_breadth",
    "resample_weekly",
    "replay_equity",
    "run_backtest",
    "run_strategy_lab",
]
