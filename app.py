"""VNStockLab Streamlit dashboard."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from vnstocklab.analysis import (
    AlertRule,
    AnalysisResult,
    CandlestickEvent,
    DowAnalysis,
    MultiTimeframeIchimoku,
    PortfolioTransaction,
    PricePattern,
    ReplayAccount,
    ScreeningResult,
    StrategyConfig,
    SupportResistanceAnalysis,
    TechnicalScorecard,
    add_ichimoku,
    analyze,
    analyze_dow_structure,
    analyze_market_breadth,
    analyze_multi_timeframe_ichimoku,
    analyze_price_patterns,
    analyze_support_resistance,
    build_portfolio,
    build_replay_report,
    build_scorecard,
    candlestick_events,
    detect_breadth_alert,
    detect_symbol_alerts,
    execute_replay_order,
    queue_replay_order,
    replay_equity,
    run_backtest,
    run_strategy_lab,
    screen_symbols,
    suggest_rebalance,
)
from vnstocklab.data import VN30_SYMBOLS, MarketDataError, VnstockProvider, generate_demo_prices
from vnstocklab.data.csv_loader import load_price_csv
from vnstocklab.storage import SQLiteRepository

st.set_page_config(page_title="VNStockLab", page_icon="📈", layout="wide")


@st.cache_resource
def app_repository() -> SQLiteRepository:
    """Create the process-wide repository; connections remain short-lived per operation."""
    path = Path(os.getenv("VNSTOCKLAB_DB_PATH", "data/vnstocklab.db"))
    return SQLiteRepository(path)


_REPLAY_SHORTCUTS = st.components.v2.component(
    "vnstocklab_replay_shortcuts",
    html="""
<div id="shortcut-help" aria-label="Phím tắt Bar Replay">
  Phím tắt: ← Lùi · → Tiến · Space Phát/Tạm dừng · B Mua · S Bán
</div>
""",
    css="""
#shortcut-help {
  color: var(--st-secondary-text-color, #64748b);
  font-size: 0.82rem;
  padding: 0.15rem 0;
}
""",
    js="""
export default function (component) {
  const { setTriggerValue } = component
  const actions = {
    ArrowLeft: "back",
    ArrowRight: "next",
    " ": "play",
    b: "buy",
    B: "buy",
    s: "sell",
    S: "sell",
  }
  const handleKeydown = (event) => {
    const tag = event.target?.tagName
    if (["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(tag)) return
    const action = actions[event.key]
    if (!action) return
    event.preventDefault()
    setTriggerValue("action", action)
  }
  window.addEventListener("keydown", handleKeydown)
  return () => window.removeEventListener("keydown", handleKeydown)
}
""",
)


def analysis_candlestick_events(result: AnalysisResult) -> tuple[CandlestickEvent, ...]:
    """Read events while tolerating results created before a Streamlit hot reload."""
    cached_events = getattr(result, "candlestick_events", None)
    if cached_events is not None:
        return tuple(cached_events)
    return candlestick_events(result.data)


def analysis_ichimoku(result: AnalysisResult) -> MultiTimeframeIchimoku:
    """Read Ichimoku state while tolerating results created before hot reload."""
    cached_ichimoku = getattr(result, "ichimoku", None)
    if cached_ichimoku is not None:
        return cached_ichimoku
    return analyze_multi_timeframe_ichimoku(result.data)


def analysis_levels(result: AnalysisResult) -> SupportResistanceAnalysis:
    """Read price zones while tolerating results created before hot reload."""
    cached_levels = getattr(result, "levels", None)
    if cached_levels is not None:
        return cached_levels
    return analyze_support_resistance(result.data)


def analysis_dow(result: AnalysisResult) -> DowAnalysis:
    """Read Dow structure while tolerating results created before hot reload."""
    cached_dow = getattr(result, "dow", None)
    if cached_dow is not None:
        return cached_dow
    levels = analysis_levels(result)
    return analyze_dow_structure(result.data, levels.breakout)


def analysis_patterns(result: AnalysisResult) -> tuple[PricePattern, ...]:
    """Read price patterns while tolerating results created before hot reload."""
    cached_patterns = getattr(result, "patterns", None)
    if cached_patterns is not None:
        return tuple(cached_patterns)
    return analyze_price_patterns(result.data)


def analysis_scorecard(result: AnalysisResult) -> TechnicalScorecard:
    """Read the scorecard while tolerating results created before hot reload."""
    cached_scorecard = getattr(result, "scorecard", None)
    if cached_scorecard is not None:
        return cached_scorecard
    return build_scorecard(
        result.data,
        analysis_ichimoku(result),
        analysis_dow(result),
        analysis_levels(result),
        analysis_patterns(result),
        getattr(result, "relative_strength", None),
        getattr(result, "risk_plan", None),
    )


def price_chart(result: AnalysisResult, symbol: str) -> go.Figure:
    """Build the price and volume chart."""
    data = result.data
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.04,
    )
    figure.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            name=symbol,
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(x=data.index, y=data["sma20"], name="SMA 20", line={"width": 1.4}),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(x=data.index, y=data["sma50"], name="SMA 50", line={"width": 1.4}),
        row=1,
        col=1,
    )
    zones = sorted(
        analysis_levels(result).zones,
        key=lambda zone: (zone.strength, -abs(zone.midpoint - float(data.iloc[-1]["close"]))),
        reverse=True,
    )[:6]
    for zone in zones:
        color = "rgba(22, 163, 74, 0.10)" if zone.role == "Hỗ trợ" else "rgba(220, 38, 38, 0.10)"
        figure.add_hrect(
            y0=zone.lower,
            y1=zone.upper,
            fillcolor=color,
            line_width=0,
            annotation_text=f"{zone.role} {zone.strength}/5",
            annotation_position="top right",
            row=1,
            col=1,
        )
    structure_points = analysis_dow(result).short_term.points[-16:]
    if structure_points:
        figure.add_trace(
            go.Scatter(
                x=[point.pivot.date for point in structure_points],
                y=[point.pivot.price for point in structure_points],
                mode="markers+text",
                name="Cấu trúc Dow",
                text=[point.label for point in structure_points],
                textposition=[
                    "top center" if point.pivot.kind == "high" else "bottom center"
                    for point in structure_points
                ],
                marker={"size": 6, "color": "#0f172a"},
                hovertemplate="%{text}: %{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )
    patterns = analysis_patterns(result)
    if patterns:
        primary_pattern = patterns[0]
        pattern_color = "#16a34a" if primary_pattern.direction == "bullish" else "#dc2626"
        figure.add_hline(
            y=primary_pattern.breakout_level,
            line_dash="dash",
            line_color=pattern_color,
            annotation_text=f"{primary_pattern.name}: {primary_pattern.breakout_level:.2f}",
            annotation_position="bottom right",
            row=1,
            col=1,
        )
    detected_events = analysis_candlestick_events(result)
    for direction, color, marker_symbol, label in (
        ("bullish", "#16a34a", "triangle-up", "Mẫu nến tăng"),
        ("bearish", "#dc2626", "triangle-down", "Mẫu nến giảm"),
        ("neutral", "#64748b", "diamond", "Mẫu nến trung tính"),
    ):
        events = [event for event in detected_events if event.direction == direction]
        if not events:
            continue
        dates = [event.date for event in events]
        values = [
            float(data.loc[event.date, "low"] * 0.98)
            if direction == "bullish"
            else float(data.loc[event.date, "high"] * 1.02)
            for event in events
        ]
        figure.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode="markers",
                name=label,
                marker={
                    "color": color,
                    "symbol": marker_symbol,
                    "size": [12 if event.confirmed else 8 for event in events],
                    "line": {"width": 1, "color": "white"},
                },
                customdata=[[event.pattern, event.confidence, event.context] for event in events],
                hovertemplate=(
                    "%{customdata[0]}<br>Độ tin cậy: %{customdata[1]}/3"
                    "<br>%{customdata[2]}<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )
    colors = [
        "#16a34a" if close >= open_ else "#dc2626"
        for open_, close in zip(data["open"], data["close"], strict=True)
    ]
    figure.add_trace(
        go.Bar(x=data.index, y=data["volume"], marker_color=colors, name="Khối lượng"),
        row=2,
        col=1,
    )
    figure.update_layout(
        height=650,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        xaxis_rangeslider_visible=False,
        legend={"orientation": "h", "y": 1.03},
    )
    return figure


def replay_price_chart(
    result: AnalysisResult,
    symbol: str,
    account: ReplayAccount,
) -> go.Figure:
    """Decorate the regular chart with replay executions and risk levels."""
    figure = price_chart(result, symbol)
    for action, color, marker in (
        ("Mua", "#16a34a", "triangle-up"),
        ("Bán", "#dc2626", "triangle-down"),
    ):
        trades = [trade for trade in account.trades if trade.action == action]
        if trades:
            figure.add_trace(
                go.Scatter(
                    x=[trade.executed_at for trade in trades],
                    y=[trade.price for trade in trades],
                    mode="markers",
                    name=f"Lệnh {action.lower()}",
                    marker={
                        "symbol": marker,
                        "size": 15,
                        "color": color,
                        "line": {"width": 1.5, "color": "white"},
                    },
                    customdata=[[trade.shares, trade.realized_pnl] for trade in trades],
                    hovertemplate=(
                        f"{action} %{{customdata[0]:,}} cp @ %{{y:,.2f}}"
                        "<br>PnL thực hiện: %{customdata[1]:,.0f}<extra></extra>"
                    ),
                ),
                row=1,
                col=1,
            )
    if account.shares > 0:
        levels = (
            (account.average_price, "Giá vốn", "#2563eb", "solid"),
            (result.risk_plan.stop_loss, "Stop tham chiếu", "#dc2626", "dash"),
            (result.risk_plan.target, "Target tham chiếu", "#16a34a", "dash"),
        )
        for value, label, color, dash in levels:
            figure.add_hline(
                y=value,
                line_color=color,
                line_dash=dash,
                annotation_text=f"{label}: {value:.2f}",
                annotation_position="top left",
                row=1,
                col=1,
            )
    return figure


def indicator_chart(result: AnalysisResult) -> go.Figure:
    """Build momentum and money-flow panels."""
    data = result.data
    figure = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08)
    figure.add_trace(go.Scatter(x=data.index, y=data["rsi14"], name="RSI 14"), row=1, col=1)
    figure.add_hline(y=70, line_dash="dash", line_color="#dc2626", row=1, col=1)
    figure.add_hline(y=30, line_dash="dash", line_color="#16a34a", row=1, col=1)
    figure.add_trace(go.Scatter(x=data.index, y=data["cmf20"], name="CMF 20"), row=2, col=1)
    figure.add_hline(y=0, line_dash="dash", line_color="#64748b", row=2, col=1)
    figure.add_trace(go.Scatter(x=data.index, y=data["obv"], name="OBV"), row=3, col=1)
    figure.update_layout(height=560, margin={"l": 20, "r": 20, "t": 20, "b": 20})
    return figure


def trend_risk_chart(result: AnalysisResult, symbol: str) -> go.Figure:
    """Build ADX/DMI and Bollinger–Keltner panels."""
    data = result.data
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.36, 0.64],
        vertical_spacing=0.08,
    )
    figure.add_trace(go.Scatter(x=data.index, y=data["adx14"], name="ADX 14"), row=1, col=1)
    figure.add_trace(go.Scatter(x=data.index, y=data["plus_di14"], name="+DI 14"), row=1, col=1)
    figure.add_trace(go.Scatter(x=data.index, y=data["minus_di14"], name="-DI 14"), row=1, col=1)
    figure.add_hline(y=25, line_dash="dash", line_color="#64748b", row=1, col=1)
    figure.add_trace(
        go.Scatter(x=data.index, y=data["close"], name=symbol, line={"color": "#111827"}),
        row=2,
        col=1,
    )
    for column, name, color, dash in (
        ("bb_upper", "Bollinger trên", "#2563eb", "solid"),
        ("bb_lower", "Bollinger dưới", "#2563eb", "solid"),
        ("kc_upper", "Keltner trên", "#f59e0b", "dash"),
        ("kc_lower", "Keltner dưới", "#f59e0b", "dash"),
    ):
        figure.add_trace(
            go.Scatter(
                x=data.index,
                y=data[column],
                name=name,
                line={"color": color, "dash": dash, "width": 1},
            ),
            row=2,
            col=1,
        )
    figure.update_layout(
        height=620,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        legend={"orientation": "h", "y": 1.03},
    )
    return figure


def ichimoku_chart(result: AnalysisResult, symbol: str) -> go.Figure:
    """Build a candlestick chart with Ichimoku lines and Kumo cloud."""
    data = result.data if "tenkan_sen" in result.data.columns else add_ichimoku(result.data)
    figure = go.Figure()
    figure.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            name=symbol,
        )
    )
    bullish_cloud = data["senkou_span_a"] >= data["senkou_span_b"]
    for mask, fill_color, cloud_name in (
        (bullish_cloud, "rgba(22, 163, 74, 0.14)", "Kumo tăng"),
        (~bullish_cloud, "rgba(220, 38, 38, 0.14)", "Kumo giảm"),
    ):
        figure.add_trace(
            go.Scatter(
                x=data.index,
                y=data["senkou_span_a"].where(mask),
                mode="lines",
                line={"width": 0},
                showlegend=False,
                hoverinfo="skip",
                connectgaps=False,
            )
        )
        figure.add_trace(
            go.Scatter(
                x=data.index,
                y=data["senkou_span_b"].where(mask),
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor=fill_color,
                name=cloud_name,
                hoverinfo="skip",
                connectgaps=False,
            )
        )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["senkou_span_a"],
            name="Senkou A",
            line={"color": "rgba(22, 163, 74, 0.65)", "width": 1},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["senkou_span_b"],
            name="Senkou B",
            line={"color": "rgba(220, 38, 38, 0.65)", "width": 1},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["tenkan_sen"],
            name="Tenkan-sen",
            line={"color": "#2563eb", "width": 1.4},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["kijun_sen"],
            name="Kijun-sen",
            line={"color": "#f59e0b", "width": 1.4},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=data.index,
            y=data["chikou_span"],
            name="Chikou Span",
            line={"color": "#7c3aed", "width": 1, "dash": "dot"},
        )
    )
    figure.update_layout(
        height=650,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        xaxis_rangeslider_visible=False,
        legend={"orientation": "h", "y": 1.03},
    )
    return figure


@st.cache_data(ttl=900, show_spinner=False)
def live_prices(symbol: str, count: int = 300) -> pd.DataFrame:
    """Load live-provider history with a short cache to conserve request quota."""
    return VnstockProvider().history(symbol, count=count)


@st.cache_data(ttl=3600, show_spinner=False)
def index_members(index: str) -> tuple[str, ...]:
    """Load index constituents with an hourly cache."""
    return VnstockProvider().index_members(index)


class CachedVnstockProvider:
    """Use the UI's per-symbol cache across screener and breadth requests."""

    def __init__(self, on_load: object | None = None) -> None:
        self.on_load = on_load
        self.rate_limited = False

    def history(self, symbol: str, count: int = 300) -> pd.DataFrame:
        if callable(self.on_load):
            self.on_load(symbol)
        if self.rate_limited:
            raise MarketDataError("Đã dừng lượt tải vì nguồn Vnstock đang giới hạn request")
        try:
            return live_prices(symbol, count)
        except MarketDataError as error:
            if "giới hạn request" in str(error):
                self.rate_limited = True
            raise

    def index_members(self, index: str = "VN30") -> tuple[str, ...]:
        return index_members(index)


class DemoBasketProvider:
    """Deterministic provider for testing multi-symbol workflows without API quota."""

    def history(self, symbol: str, count: int = 300) -> pd.DataFrame:
        return generate_demo_prices(symbol, periods=count)

    def index_members(self, index: str = "VN30") -> tuple[str, ...]:
        return VN30_SYMBOLS


def run_market_screen(symbols: tuple[str, ...], source: str) -> ScreeningResult:
    """Run a basket analysis with visible per-symbol loading progress."""
    total_requests = len(symbols) + 1
    loaded = 0
    progress = st.progress(0.0, text="Chuẩn bị tải dữ liệu...")

    def update_progress(symbol: str) -> None:
        nonlocal loaded
        loaded += 1
        progress.progress(
            min(loaded / total_requests, 1.0),
            text=f"Đang tải {symbol} ({loaded}/{total_requests})",
        )

    provider = (
        CachedVnstockProvider(update_progress)
        if source == "Thị trường thực"
        else DemoBasketProvider()
    )
    try:
        return screen_symbols(symbols, provider)
    finally:
        progress.empty()


def render_analysis() -> None:
    """Render the single-symbol analysis workspace."""
    with st.sidebar:
        st.header("Phân tích cổ phiếu")
        source = st.radio("Nguồn", ["Thị trường thực", "Dữ liệu demo", "Tải CSV"])
        symbol = st.text_input("Mã cổ phiếu", value="FPT", max_chars=12).strip().upper()
        uploaded = None
        if source == "Tải CSV":
            uploaded = st.file_uploader(
                "CSV gồm date, open, high, low, close, volume", type=["csv"]
            )
        if source == "Dữ liệu demo":
            st.info("Dữ liệu demo chỉ dùng để khám phá tính năng.")

    benchmark: pd.DataFrame | None = None
    benchmark_warning: str | None = None
    try:
        if uploaded is not None:
            prices = load_price_csv(uploaded)
        elif source == "Thị trường thực":
            with st.spinner(f"Đang tải dữ liệu {symbol}..."):
                if symbol == "VNINDEX":
                    prices = live_prices(symbol)
                    benchmark = prices
                else:
                    prices = live_prices(symbol)
                    try:
                        benchmark = live_prices("VNINDEX")
                    except MarketDataError as error:
                        benchmark_warning = str(error)
        else:
            prices = generate_demo_prices(symbol)
            benchmark = generate_demo_prices("VNINDEX")
        result = analyze(prices, benchmark=benchmark)
    except (ValueError, MarketDataError) as error:
        st.error(str(error))
        return

    latest = result.data.iloc[-1]
    previous = result.data.iloc[-2]
    price_change = (latest["close"] / previous["close"] - 1) * 100
    last_date = result.data.index[-1].strftime("%d/%m/%Y")
    st.caption(f"Phiên dữ liệu gần nhất: {last_date}")
    if benchmark_warning is not None:
        st.warning(
            f"Không tải được VN-Index; Relative Strength tạm giữ trung lập. {benchmark_warning}"
        )

    metric_columns = st.columns(6)
    metric_columns[0].metric("Giá đóng cửa", f"{latest['close']:,.2f}", f"{price_change:+.2f}%")
    metric_columns[1].metric("Xu hướng", result.trend)
    metric_columns[2].metric("Tín hiệu", result.signal)
    metric_columns[3].metric("Điểm tổng hợp", f"{result.score}/100")
    levels = analysis_levels(result)
    support_value = (
        levels.nearest_support.midpoint if levels.nearest_support is not None else result.support
    )
    resistance_value = (
        levels.nearest_resistance.midpoint
        if levels.nearest_resistance is not None
        else result.resistance
    )
    metric_columns[4].metric("Hỗ trợ gần nhất", f"{support_value:,.2f}")
    metric_columns[5].metric("Kháng cự gần nhất", f"{resistance_value:,.2f}")
    if result.execution.score_candidate:
        if result.execution.eligible:
            st.success(
                "Cổng thực thi đạt: " + "; ".join(result.execution.confirmations)
            )
        else:
            st.warning(
                "Điểm đạt ngưỡng nhưng chưa được mua: "
                + "; ".join(result.execution.blockers)
            )

    (
        price_tab,
        indicator_tab,
        trend_risk_tab,
        candle_tab,
        ichimoku_tab,
        level_tab,
        dow_tab,
        pattern_tab,
        explanation_tab,
    ) = st.tabs(
        [
            "Giá & khối lượng",
            "Động lượng & dòng tiền",
            "Sức mạnh xu hướng & rủi ro",
            "Mô hình nến",
            "Ichimoku",
            "Vùng giá",
            "Cấu trúc Dow",
            "Mẫu hình giá",
            "Luận điểm",
        ]
    )
    with price_tab:
        st.plotly_chart(price_chart(result, symbol), width="stretch")
    with indicator_tab:
        relative = result.relative_strength
        with st.container(horizontal=True):
            st.metric(
                "RS 20 phiên",
                f"{relative.relative_return_20d:+.2f} điểm %"
                if relative.relative_return_20d is not None
                else "Chưa có benchmark",
                border=True,
            )
            st.metric(
                "RS 60 phiên",
                f"{relative.relative_return_60d:+.2f} điểm %"
                if relative.relative_return_60d is not None
                else "Chưa có benchmark",
                border=True,
            )
            st.metric("CMF 20", f"{latest['cmf20']:+.3f}", border=True)
            st.metric(
                "OBV 5 phiên",
                "Đi lên" if latest["obv"] > result.data["obv"].iloc[-6] else "Đi xuống",
                border=True,
            )
        st.plotly_chart(indicator_chart(result), width="stretch")
    with trend_risk_tab:
        risk = result.risk_plan
        squeeze_state = (
            "Vừa giải phóng"
            if bool(latest["squeeze_release"])
            else "Đang nén"
            if bool(latest["squeeze_on"])
            else "Không nén"
        )
        with st.container(horizontal=True):
            st.metric("ADX 14", f"{latest['adx14']:.1f}", border=True)
            st.metric(
                "DMI chiếm ưu thế",
                "+DI" if latest["plus_di14"] > latest["minus_di14"] else "-DI",
                border=True,
            )
            st.metric("Squeeze", squeeze_state, border=True)
            st.metric("ATR / giá", f"{risk.atr_pct:.2f}%", border=True)
        with st.container(horizontal=True):
            st.metric("Giá vào tham chiếu", f"{risk.entry:,.2f}", border=True)
            st.metric(
                "Stop-loss",
                f"{risk.stop_loss:,.2f}",
                f"-{risk.stop_distance_pct:.2f}%",
                delta_color="inverse",
                border=True,
            )
            st.metric("Mục tiêu", f"{risk.target:,.2f}", border=True)
            st.metric("Risk/Reward", f"{risk.risk_reward:.2f}R", border=True)
        st.plotly_chart(trend_risk_chart(result, symbol), width="stretch")
        for reason in risk.reasons:
            st.markdown(f"- {reason}")
        st.caption(
            "Các mức là kế hoạch kỹ thuật tham chiếu cho vị thế mua mới, không phải lệnh giao dịch."
        )
    with candle_tab:
        st.caption(
            "Marker lớn là mẫu đã được xác nhận bởi bối cảnh xu hướng/vùng giá và khối lượng."
        )
        detected_events = analysis_candlestick_events(result)
        if detected_events:
            event_rows = pd.DataFrame(
                [
                    {
                        "Ngày": event.date.strftime("%d/%m/%Y"),
                        "Mẫu nến": event.pattern,
                        "Hướng": {
                            "bullish": "Tăng",
                            "bearish": "Giảm",
                            "neutral": "Trung tính",
                        }[event.direction],
                        "Tin cậy": event.confidence,
                        "Xác nhận": "Có" if event.confirmed else "Chưa",
                        "Bối cảnh": event.context,
                    }
                    for event in reversed(detected_events)
                ]
            )
            st.dataframe(
                event_rows,
                width="stretch",
                hide_index=True,
                column_config={
                    "Tin cậy": st.column_config.ProgressColumn(min_value=0, max_value=3),
                },
            )
        else:
            st.info("Không phát hiện mẫu nến trong 30 phiên gần nhất.")
    with ichimoku_tab:
        ichimoku = analysis_ichimoku(result)
        with st.container(horizontal=True):
            st.metric("Khung ngày", ichimoku.daily.state, f"{ichimoku.daily.score:+d}", border=True)
            if ichimoku.weekly is not None:
                st.metric(
                    "Khung tuần",
                    ichimoku.weekly.state,
                    f"{ichimoku.weekly.score:+d}",
                    border=True,
                )
            else:
                st.metric("Khung tuần", "Chưa đủ dữ liệu", border=True)
            st.metric(
                "Đồng thuận",
                "Có" if ichimoku.aligned else "Chưa",
                f"{ichimoku.score_adjustment:+d} điểm",
                border=True,
            )
        st.plotly_chart(ichimoku_chart(result, symbol), width="stretch")
        st.markdown(f"**{ichimoku.summary}**")
        daily_column, weekly_column = st.columns(2)
        with daily_column:
            st.markdown("**Luận điểm khung ngày**")
            for reason in ichimoku.daily.reasons:
                st.markdown(f"- {reason}")
        with weekly_column:
            st.markdown("**Luận điểm khung tuần**")
            if ichimoku.weekly is None:
                st.info("Cần tối thiểu 52 tuần dữ liệu để đánh giá khung tuần.")
            else:
                for reason in ichimoku.weekly.reasons:
                    st.markdown(f"- {reason}")
    with level_tab:
        active_zones = [zone for zone in levels.zones if zone.status != "Đã phá vỡ"]
        with st.container(horizontal=True):
            st.metric("Pivot đã xác nhận", len(levels.pivots), border=True)
            st.metric("Vùng giá", len(levels.zones), border=True)
            st.metric("Vùng đang theo dõi", len(active_zones), border=True)
            st.metric(
                "Breakout phiên gần nhất",
                (
                    "Tăng"
                    if levels.breakout is not None and levels.breakout.direction == "up"
                    else "Giảm"
                    if levels.breakout is not None
                    else "Không"
                ),
                border=True,
            )
        if levels.zones:
            zone_rows = pd.DataFrame(
                [
                    {
                        "Vùng dưới": zone.lower,
                        "Vùng trên": zone.upper,
                        "Vai trò": zone.role,
                        "Trạng thái": zone.status,
                        "Số lần chạm": zone.touches,
                        "Độ mạnh": zone.strength,
                        "KL tương đối": zone.average_volume_ratio,
                        "Lần chạm cuối": zone.last_touch.strftime("%d/%m/%Y"),
                    }
                    for zone in sorted(
                        levels.zones,
                        key=lambda item: abs(item.midpoint - float(latest["close"])),
                    )
                ]
            )
            zone_rows[["Vùng dưới", "Vùng trên", "KL tương đối"]] = zone_rows[
                ["Vùng dưới", "Vùng trên", "KL tương đối"]
            ].round(2)
            st.dataframe(
                zone_rows,
                width="stretch",
                hide_index=True,
                column_config={
                    "Độ mạnh": st.column_config.ProgressColumn(min_value=0, max_value=5),
                },
            )
        else:
            st.info("Chưa có đủ pivot gần nhau để hình thành vùng giá đáng tin cậy.")
        if levels.breakout is not None:
            if levels.breakout.confirmed_by_volume:
                st.success(f"{levels.breakout.description}; khối lượng đã xác nhận.")
            else:
                st.warning(f"{levels.breakout.description}; chưa có xác nhận khối lượng.")
    with dow_tab:
        dow = analysis_dow(result)
        with st.container(horizontal=True):
            st.metric("Ngắn hạn", dow.short_term.state, border=True)
            st.metric("Trung hạn", dow.medium_term.state, border=True)
            st.metric("Khung tuần", dow.weekly.state, border=True)
            st.metric(
                "Đồng thuận",
                "Có" if dow.aligned else "Chưa",
                f"{dow.score_adjustment:+d} điểm",
                border=True,
            )
        st.markdown(f"**{dow.summary}**")
        recent_points = dow.short_term.points[-20:]
        if recent_points:
            point_rows = pd.DataFrame(
                [
                    {
                        "Ngày cực trị": point.pivot.date.strftime("%d/%m/%Y"),
                        "Ngày xác nhận": (
                            point.pivot.confirmed_at.strftime("%d/%m/%Y")
                            if point.pivot.confirmed_at is not None
                            else point.pivot.date.strftime("%d/%m/%Y")
                        ),
                        "Nhãn": point.label,
                        "Loại": "Đỉnh" if point.pivot.kind == "high" else "Đáy",
                        "Giá": point.pivot.price,
                    }
                    for point in reversed(recent_points)
                ]
            )
            point_rows["Giá"] = point_rows["Giá"].round(2)
            st.dataframe(point_rows, width="stretch", hide_index=True)
        events = dow.short_term.events[-10:]
        if events:
            st.markdown("**Sự kiện cấu trúc gần đây**")
            event_rows = pd.DataFrame(
                [
                    {
                        "Ngày xác nhận": event.date.strftime("%d/%m/%Y"),
                        "Sự kiện": event.kind,
                        "Mức giá": event.price,
                        "Khối lượng xác nhận": "Có" if event.volume_confirmed else "Chưa",
                    }
                    for event in reversed(events)
                ]
            )
            event_rows["Mức giá"] = event_rows["Mức giá"].round(2)
            st.dataframe(event_rows, width="stretch", hide_index=True)
    with pattern_tab:
        patterns = analysis_patterns(result)
        active_patterns = [pattern for pattern in patterns if pattern.status != "Thất bại"]
        confirmed_patterns = [
            pattern
            for pattern in patterns
            if pattern.status in {"Đã breakout", "Retest thành công"}
        ]
        with st.container(horizontal=True):
            st.metric("Mẫu phát hiện", len(patterns), border=True)
            st.metric("Đang hoạt động", len(active_patterns), border=True)
            st.metric("Đã breakout", len(confirmed_patterns), border=True)
        if patterns:
            pattern_rows = pd.DataFrame(
                [
                    {
                        "Mẫu hình": pattern.name,
                        "Hướng": "Tăng" if pattern.direction == "bullish" else "Giảm",
                        "Trạng thái": pattern.status,
                        "Biên breakout": pattern.breakout_level,
                        "Mục tiêu": pattern.target,
                        "Vô hiệu": pattern.invalidation,
                        "Tin cậy": pattern.confidence,
                        "KL xác nhận": "Có" if pattern.volume_confirmed else "Chưa",
                    }
                    for pattern in patterns
                ]
            )
            numeric = ["Biên breakout", "Mục tiêu", "Vô hiệu"]
            pattern_rows[numeric] = pattern_rows[numeric].round(2)
            st.dataframe(
                pattern_rows,
                width="stretch",
                hide_index=True,
                column_config={
                    "Tin cậy": st.column_config.ProgressColumn(min_value=0, max_value=5),
                },
            )
            primary = patterns[0]
            if primary.status in {"Đã breakout", "Retest thành công"}:
                st.success(primary.description)
            elif primary.status == "Thất bại":
                st.error(f"{primary.name} đã bị vô hiệu.")
            else:
                st.info(primary.description)
        else:
            st.info("Chưa phát hiện mẫu hình giá cốt lõi đủ điều kiện.")
    with explanation_tab:
        st.subheader(f"Kết luận: {result.signal}")
        if result.execution.blockers:
            st.markdown("**Điều kiện đang chặn thực thi**")
            for blocker in result.execution.blockers:
                st.write(f"- {blocker}")
        if result.execution.confirmations:
            st.markdown("**Điều kiện đã xác nhận**")
            for confirmation in result.execution.confirmations:
                st.write(f"- {confirmation}")
        scorecard = analysis_scorecard(result)
        score_rows = pd.DataFrame(
            [
                {
                    "Nhóm": category.name,
                    "Điểm": category.score,
                    "Tối đa": category.maximum,
                    "Trạng thái": "Hoạt động" if category.available else "Chờ dữ liệu",
                    "Luận điểm": "; ".join(category.reasons),
                }
                for category in scorecard.categories
            ]
        )
        st.dataframe(
            score_rows,
            width="stretch",
            hide_index=True,
            column_config={
                "Điểm": st.column_config.ProgressColumn(min_value=0, max_value=20),
            },
        )
        st.caption("Các nhóm chưa triển khai được giữ ở mức trung tính và ghi rõ “Chờ dữ liệu”.")
        st.warning(
            "Kết quả mang tính tham khảo và giáo dục, không phải khuyến nghị đầu tư. "
            "Luôn kết hợp quản trị rủi ro và thông tin cơ bản."
        )


def render_screener() -> None:
    """Render a quota-conscious index screener."""
    st.subheader("Sàng lọc kỹ thuật")
    st.caption("Các mã được tải tuần tự để tôn trọng giới hạn của nguồn dữ liệu miễn phí.")
    controls = st.columns([1, 1, 1, 2])
    source = controls[0].selectbox(
        "Nguồn", ["Thị trường thực", "Dữ liệu demo"], key="screen_source"
    )
    index = controls[1].selectbox("Rổ chỉ số", ["VN30"], key="screen_index")
    limit = controls[2].number_input("Số mã", min_value=3, max_value=17, value=10, step=1)

    if source == "Dữ liệu demo":
        default_symbols = ", ".join(VN30_SYMBOLS[: int(limit)])
    else:
        try:
            available = index_members(index)
            default_symbols = ", ".join(available[: int(limit)])
        except MarketDataError as error:
            st.warning(f"Không tải được thành phần {index}; dùng danh sách dự phòng. {error}")
            default_symbols = ", ".join(VN30_SYMBOLS[: int(limit)])

    raw_symbols = controls[3].text_input("Danh sách mã", value=default_symbols)
    symbols = tuple(part.strip().upper() for part in raw_symbols.split(",") if part.strip())[
        : int(limit)
    ]
    if not st.button("Chạy sàng lọc", type="primary", disabled=not symbols):
        st.info("Chọn danh sách mã và bấm “Chạy sàng lọc”.")
        return

    screened = run_market_screen(symbols, source)
    if screened.rows.empty:
        st.error("Không có mã nào đủ dữ liệu để phân tích.")
    else:
        display = screened.rows.copy()
        numeric_columns = [
            "Giá",
            "% thay đổi",
            "RSI 14",
            "MFI 14",
            "CMF 20",
            "RS 20 phiên",
            "ADX 14",
            "Stop-loss",
            "Mục tiêu",
            "R/R",
            "Hỗ trợ",
            "Kháng cự",
        ]
        display[numeric_columns] = display[numeric_columns].round(2)
        st.dataframe(
            display,
            width="stretch",
            hide_index=True,
            column_config={
                "% thay đổi": st.column_config.NumberColumn(format="%+.2f%%"),
                "Điểm": st.column_config.ProgressColumn(min_value=0, max_value=100),
            },
        )
    if screened.errors:
        with st.expander(f"{len(screened.errors)} mã không xử lý được"):
            for error in screened.errors:
                st.write(error)


def render_market_breadth() -> None:
    """Render equal-weighted breadth for a selected market basket."""
    st.subheader("Độ rộng thị trường")
    st.caption(
        "Bối cảnh hiện tính theo tối đa 17 mã đại diện do giới hạn 20 request/phút; "
        "adapter realtime sau này có thể mở rộng toàn thị trường."
    )
    controls = st.columns([1, 1, 1, 2])
    source = controls[0].selectbox(
        "Nguồn", ["Thị trường thực", "Dữ liệu demo"], key="breadth_source"
    )
    index = controls[1].selectbox("Rổ chỉ số", ["VN30"], key="breadth_index")
    limit = controls[2].number_input(
        "Số mã", min_value=3, max_value=17, value=12, step=1, key="breadth_limit"
    )
    if source == "Dữ liệu demo":
        default_symbols = ", ".join(VN30_SYMBOLS[: int(limit)])
    else:
        try:
            available = index_members(index)
            default_symbols = ", ".join(available[: int(limit)])
        except MarketDataError as error:
            st.warning(f"Không tải được thành phần {index}; dùng danh sách dự phòng. {error}")
            default_symbols = ", ".join(VN30_SYMBOLS[: int(limit)])
    raw_symbols = controls[3].text_input(
        "Danh sách mã", value=default_symbols, key="breadth_symbols"
    )
    symbols = tuple(part.strip().upper() for part in raw_symbols.split(",") if part.strip())[
        : int(limit)
    ]
    if not st.button("Tính độ rộng", type="primary", disabled=len(symbols) < 3, key="run_breadth"):
        st.info("Chọn ít nhất 3 mã và bấm “Tính độ rộng”.")
        return

    screened = run_market_screen(symbols, source)
    breadth = screened.breadth
    if not breadth.available:
        st.error("; ".join(breadth.reasons))
        return

    with st.container(horizontal=True):
        st.metric("Trạng thái", breadth.state, f"{breadth.score}/10", border=True)
        st.metric("Tăng / giảm", f"{breadth.advances} / {breadth.declines}", border=True)
        st.metric("A/D Ratio", f"{breadth.advance_decline_ratio:.2f}", border=True)
        st.metric("KL nhóm tăng", f"{breadth.advancing_volume_pct:.1f}%", border=True)
    with st.container(horizontal=True):
        st.metric("Trên SMA20", f"{breadth.above_sma20_pct:.1f}%", border=True)
        st.metric("Trên SMA50", f"{breadth.above_sma50_pct:.1f}%", border=True)
        st.metric("Trên SMA200", f"{breadth.above_sma200_pct:.1f}%", border=True)
        st.metric("Số mã hợp lệ", len(breadth.symbols), border=True)

    history = breadth.history.tail(120).copy()
    chart_left, chart_right = st.columns(2)
    with chart_left, st.container(border=True):
        st.markdown("**Đường Advance/Decline**")
        ad_chart = history[["ad_line"]].rename(columns={"ad_line": "A/D Line"})
        st.line_chart(ad_chart, height=320)
    with chart_right, st.container(border=True):
        st.markdown("**Tỷ lệ cổ phiếu trên đường trung bình**")
        ma_chart = history[["above_sma20_pct", "above_sma50_pct", "above_sma200_pct"]].rename(
            columns={
                "above_sma20_pct": "Trên SMA20",
                "above_sma50_pct": "Trên SMA50",
                "above_sma200_pct": "Trên SMA200",
            }
        )
        st.line_chart(ma_chart, height=320)
    st.markdown("**Các mã trong mẫu**")
    if not screened.rows.empty:
        summary_columns = [
            "Mã",
            "Tín hiệu",
            "Điểm",
            "% thay đổi",
            "ADX 14",
            "Squeeze",
            "CMF 20",
        ]
        summary = screened.rows[summary_columns].copy()
        summary[["% thay đổi", "ADX 14", "CMF 20"]] = summary[
            ["% thay đổi", "ADX 14", "CMF 20"]
        ].round(2)
        st.dataframe(
            summary,
            width="stretch",
            hide_index=True,
            column_config={
                "Điểm": st.column_config.ProgressColumn(min_value=0, max_value=100),
                "% thay đổi": st.column_config.NumberColumn(format="%+.2f%%"),
            },
        )
    if screened.errors:
        with st.expander(f"{len(screened.errors)} lỗi dữ liệu"):
            for error in screened.errors:
                st.write(error)


def render_backtest() -> None:
    """Render a next-session, fee-aware score strategy backtest."""
    st.subheader("Backtest chiến lược điểm 0–100")
    st.caption(
        "Tín hiệu hình thành sau giá đóng cửa và chỉ khớp tại giá mở cửa phiên kế tiếp. "
        "Nếu stop-loss và mục tiêu cùng chạm trong một phiên, hệ thống ưu tiên stop-loss."
    )
    with st.form("backtest_controls", border=False):
        controls = st.columns([1, 1, 1, 1, 1, 1])
        source = controls[0].selectbox(
            "Nguồn", ["Dữ liệu demo", "Thị trường thực"], key="backtest_source"
        )
        symbol = controls[1].text_input("Mã", value="FPT", max_chars=12).strip().upper()
        periods = int(
            controls[2].number_input("Số phiên", min_value=120, max_value=600, value=180, step=20)
        )
        entry_score = int(
            controls[3].number_input("Điểm mua", min_value=1, max_value=100, value=65)
        )
        exit_score = int(controls[4].number_input("Điểm bán", min_value=0, max_value=99, value=35))
        fee_pct = float(
            controls[5].number_input(
                "Phí mỗi chiều (%)", min_value=0.0, max_value=2.0, value=0.15, step=0.05
            )
        )
        submitted = st.form_submit_button("Chạy backtest", type="primary", disabled=not symbol)
    if not submitted:
        st.info("Điều chỉnh tham số và bấm “Chạy backtest”.")
        return
    if exit_score >= entry_score:
        st.error("Điểm bán phải nhỏ hơn điểm mua.")
        return

    try:
        if source == "Thị trường thực":
            prices = live_prices(symbol, periods)
            try:
                benchmark = live_prices("VNINDEX", periods)
            except MarketDataError:
                benchmark = None
                st.warning("Không tải được VN-Index; Relative Strength giữ mức trung lập.")
        else:
            prices = generate_demo_prices(symbol, periods=periods)
            benchmark = generate_demo_prices("VNINDEX", periods=periods)
    except (ValueError, MarketDataError) as error:
        st.error(str(error))
        return

    progress_bar = st.progress(0.0, text="Khởi tạo backtest...")

    def update_backtest_progress(completed: int, total: int) -> None:
        progress_bar.progress(
            completed / total,
            text=f"Đang tính tín hiệu {completed}/{total}",
        )

    try:
        result = run_backtest(
            prices,
            benchmark,
            entry_score=entry_score,
            exit_score=exit_score,
            fee_rate=fee_pct / 100,
            progress=update_backtest_progress,
        )
    except ValueError as error:
        st.error(str(error))
        return
    finally:
        progress_bar.empty()

    profit_factor = "∞" if result.profit_factor == float("inf") else f"{result.profit_factor:.2f}"
    with st.container(horizontal=True):
        st.metric("Lợi nhuận", f"{result.total_return_pct:+.2f}%", border=True)
        st.metric("Mua & nắm giữ", f"{result.benchmark_return_pct:+.2f}%", border=True)
        st.metric("CAGR", f"{result.cagr_pct:+.2f}%", border=True)
        st.metric("Max drawdown", f"{result.max_drawdown_pct:.2f}%", border=True)
    with st.container(horizontal=True):
        st.metric("Tỷ lệ thắng", f"{result.win_rate_pct:.1f}%", border=True)
        st.metric("Sharpe", f"{result.sharpe_ratio:.2f}", border=True)
        st.metric("Profit factor", profit_factor, border=True)
        st.metric("Số giao dịch", len(result.trades), border=True)
        st.metric("Thời gian nắm giữ", f"{result.exposure_pct:.1f}%", border=True)

    curve = result.equity_curve.rename_axis("Ngày")
    with st.container(border=True):
        st.markdown("**Đường cong vốn**")
        st.line_chart(curve, height=360)
    score_chart = result.score_history.to_frame()
    score_chart["Ngưỡng mua"] = entry_score
    score_chart["Ngưỡng bán"] = exit_score
    with st.container(border=True):
        st.markdown("**Lịch sử điểm tín hiệu**")
        st.line_chart(score_chart, height=280)

    st.markdown("**Nhật ký giao dịch**")
    if result.trades:
        trades = pd.DataFrame(
            [
                {
                    "Ngày tín hiệu": trade.signal_date,
                    "Ngày mua": trade.entry_date,
                    "Ngày bán": trade.exit_date,
                    "Giá mua": trade.entry_price,
                    "Giá bán": trade.exit_price,
                    "Điểm mua": trade.entry_score,
                    "Lý do bán": trade.exit_reason,
                    "Lợi nhuận (%)": trade.return_pct,
                    "Số ngày": trade.holding_days,
                }
                for trade in result.trades
            ]
        )
        st.dataframe(
            trades,
            width="stretch",
            hide_index=True,
            column_config={
                "Ngày tín hiệu": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Ngày mua": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Ngày bán": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Giá mua": st.column_config.NumberColumn(format="%.2f"),
                "Giá bán": st.column_config.NumberColumn(format="%.2f"),
                "Lợi nhuận (%)": st.column_config.NumberColumn(format="%+.2f%%"),
            },
        )
    else:
        st.info("Không phát sinh giao dịch với bộ ngưỡng hiện tại.")
    st.warning(
        "Backtest chưa bao gồm trượt giá, thuế bán và giới hạn thanh khoản; "
        "kết quả quá khứ không đảm bảo hiệu quả tương lai."
    )


def render_strategy_lab() -> None:
    """Render a ranked multi-symbol portfolio backtest and Exploration."""
    st.subheader("Strategy Lab — backtest danh mục")
    st.caption(
        "Mô phỏng nhiều mã trên một quỹ vốn chung, dùng Breadth và toàn bộ hệ thống "
        "khuyến nghị; tín hiệu cuối ngày chỉ được khớp ở phiên kế tiếp."
    )
    with st.form("strategy_lab_controls", border=False):
        first = st.columns([1, 2, 1, 1, 1, 1])
        source = first[0].selectbox("Nguồn", ["Dữ liệu demo", "Thị trường thực"])
        raw_symbols = first[1].text_input("Danh sách mã", value="FPT, HPG, VCB")
        periods = int(first[2].number_input("Số phiên", 205, 600, 220, 20))
        entry_score = int(first[3].number_input("Điểm mua", 1, 100, 65))
        exit_score = int(first[4].number_input("Điểm bán", 0, 99, 35))
        confirmations = int(first[5].number_input("Xác nhận tối thiểu", 0, 9, 5))
        second = st.columns(6)
        max_positions = int(second[0].number_input("Vị thế tối đa", 1, 10, 3))
        risk_pct = float(second[1].number_input("Rủi ro/lệnh (%)", 0.1, 5.0, 1.0, 0.1))
        max_weight = float(second[2].number_input("Tỷ trọng tối đa (%)", 5.0, 100.0, 35.0))
        fee_pct = float(second[3].number_input("Phí (%)", 0.0, 2.0, 0.15, 0.05))
        tax_pct = float(second[4].number_input("Thuế bán (%)", 0.0, 2.0, 0.1, 0.05))
        slippage_pct = float(second[5].number_input("Trượt giá (%)", 0.0, 2.0, 0.1, 0.05))
        third = st.columns(3)
        trailing_atr = float(third[0].number_input("Trailing stop ATR", 0.5, 10.0, 2.5, 0.5))
        max_holding = int(third[1].number_input("Nắm giữ tối đa", 5, 250, 60, 5))
        capital = float(
            third[2].number_input("Vốn ban đầu", 1_000_000, 10_000_000_000, 100_000_000, 10_000_000)
        )
        submitted = st.form_submit_button("Chạy Strategy Lab", type="primary")
    if not submitted:
        st.info("Cấu hình chiến lược và bấm “Chạy Strategy Lab”.")
        return
    symbols = tuple(
        dict.fromkeys(part.strip().upper() for part in raw_symbols.split(",") if part.strip())
    )
    if len(symbols) < 3:
        st.error("Cần ít nhất 3 mã để tính Market Breadth lịch sử.")
        return
    config = StrategyConfig(
        entry_score=entry_score,
        exit_score=exit_score,
        minimum_confirmations=confirmations,
        max_positions=max_positions,
        risk_per_trade_pct=risk_pct,
        max_position_pct=max_weight,
        fee_pct=fee_pct,
        sell_tax_pct=tax_pct,
        slippage_pct=slippage_pct,
        trailing_atr=trailing_atr,
        max_holding_sessions=max_holding,
        initial_capital=capital,
    )
    try:
        if source == "Dữ liệu demo":
            frames = {symbol: generate_demo_prices(symbol, periods) for symbol in symbols}
            benchmark = generate_demo_prices("VNINDEX", periods)
        else:
            frames = {symbol: live_prices(symbol, periods) for symbol in symbols}
            benchmark = live_prices("VNINDEX", periods)
    except (ValueError, MarketDataError) as error:
        st.error(str(error))
        return
    bar = st.progress(0.0, text="Khởi tạo Strategy Lab...")

    def update(completed: int, total: int) -> None:
        bar.progress(completed / total, text=f"Phân tích {completed}/{total} ảnh chụp")

    try:
        result = run_strategy_lab(frames, benchmark, config, update)
    except ValueError as error:
        st.error(str(error))
        return
    finally:
        bar.empty()
    profit_factor = "∞" if result.profit_factor == float("inf") else f"{result.profit_factor:.2f}"
    with st.container(horizontal=True):
        st.metric("Lợi nhuận", f"{result.total_return_pct:+.2f}%", border=True)
        st.metric("CAGR", f"{result.cagr_pct:+.2f}%", border=True)
        st.metric("Max drawdown", f"{result.max_drawdown_pct:.2f}%", border=True)
        st.metric(
            "Sharpe / Sortino",
            f"{result.sharpe_ratio:.2f} / {result.sortino_ratio:.2f}",
            border=True,
        )
    with st.container(horizontal=True):
        st.metric("Tỷ lệ thắng", f"{result.win_rate_pct:.1f}%", border=True)
        st.metric("Profit factor", profit_factor, border=True)
        st.metric("Expectancy", f"{result.expectancy_pct:+.2f}%", border=True)
        st.metric("Số giao dịch", len(result.trades), border=True)
        st.metric("Exposure", f"{result.exposure_pct:.1f}%", border=True)
    with st.container(border=True):
        st.markdown("**Đường cong vốn danh mục**")
        st.line_chart(result.equity_curve, height=360)
    exploration_tab, trades_tab = st.tabs(["Exploration", "Giao dịch"])
    with exploration_tab:
        latest_date = result.exploration["date"].max()
        exploration = result.exploration[result.exploration["date"] == latest_date].copy()
        exploration = exploration.sort_values("rank_score", ascending=False)
        st.caption(f"Ảnh chụp cuối kỳ: {pd.Timestamp(latest_date):%d/%m/%Y}")
        st.dataframe(exploration, width="stretch", hide_index=True)
    with trades_tab:
        if result.trades:
            trades = pd.DataFrame([trade.__dict__ for trade in result.trades])
            st.dataframe(trades, width="stretch", hide_index=True)
        else:
            st.info("Không có giao dịch với cấu hình hiện tại.")
    st.warning(
        "Strategy Lab là mô phỏng nghiên cứu. Hãy kiểm định thêm out-of-sample và "
        "walk-forward trước khi dùng vốn thật."
    )


def render_portfolio_manager() -> None:
    """Render transaction accounting, portfolio risk, and rebalance guidance."""
    st.subheader("Portfolio Manager")
    st.caption(
        "Theo dõi giá vốn, lãi/lỗ và tỷ trọng từ sổ giao dịch. Dữ liệu được lưu bền "
        "trong SQLite trên máy này."
    )
    repository = app_repository()
    if not st.session_state.get("portfolio_storage_loaded", False):
        stored_transactions = repository.list_portfolio_transactions()
        session_transactions = list(st.session_state.get("portfolio_transactions", []))
        if session_transactions and not stored_transactions:
            for transaction in session_transactions:
                repository.add_portfolio_transaction(transaction)
            stored_transactions = session_transactions
        st.session_state.portfolio_transactions = stored_transactions
        st.session_state.portfolio_storage_loaded = True
    source = st.segmented_control(
        "Nguồn định giá",
        ["Dữ liệu demo", "Thị trường thực"],
        default="Dữ liệu demo",
        key="portfolio_source",
        persist_state="session",
    )
    with st.form("portfolio_transaction_form", border=True):
        inputs = st.columns([1, 1, 1, 1, 1, 1])
        transaction_date = inputs[0].date_input("Ngày giao dịch")
        symbol = inputs[1].text_input("Mã", value="FPT", max_chars=12).strip().upper()
        action = inputs[2].selectbox("Loại lệnh", ["Mua", "Bán"])
        shares = int(inputs[3].number_input("Khối lượng", 100, step=100, value=100))
        price = float(inputs[4].number_input("Giá", 0.01, step=1.0, value=100.0))
        fee = float(inputs[5].number_input("Phí", 0.0, step=1_000.0, value=0.0))
        submitted = st.form_submit_button("Thêm giao dịch", type="primary", icon=":material/add:")
    if submitted:
        candidate = PortfolioTransaction(
            pd.Timestamp(transaction_date), symbol, action, shares, price, fee
        )
        transactions = [*st.session_state.portfolio_transactions, candidate]
        validation_prices = {item.symbol: item.price for item in transactions}
        try:
            build_portfolio(transactions, validation_prices)
        except ValueError as error:
            st.error(str(error))
        else:
            repository.add_portfolio_transaction(candidate)
            st.session_state.portfolio_transactions = transactions
            st.toast(f"Đã thêm lệnh {action.lower()} {shares:,} cp {symbol}")

    transactions = list(st.session_state.portfolio_transactions)
    if not transactions:
        st.info("Chưa có giao dịch. Hãy thêm lệnh mua đầu tiên để tạo danh mục.")
        return
    net_shares: dict[str, int] = {}
    for item in transactions:
        direction = 1 if item.action == "Mua" else -1
        net_shares[item.symbol] = net_shares.get(item.symbol, 0) + direction * item.shares
    active_symbols = [symbol for symbol, quantity in net_shares.items() if quantity > 0]
    current_prices: dict[str, float] = {}
    analyses: dict[str, AnalysisResult] = {}
    try:
        with st.spinner("Đang định giá và phân tích danh mục..."):
            for item in active_symbols:
                frame = (
                    generate_demo_prices(item, 260)
                    if source == "Dữ liệu demo"
                    else live_prices(item, 260)
                )
                current_prices[item] = float(frame.iloc[-1]["close"])
                analyses[item] = analyze(frame)
        summary = build_portfolio(transactions, current_prices)
    except (ValueError, MarketDataError) as error:
        st.error(str(error))
        return

    return_pct = summary.total_pnl / summary.cost_basis * 100 if summary.cost_basis else 0.0
    with st.container(horizontal=True):
        st.metric("Giá trị danh mục", f"{summary.market_value:,.0f}", border=True)
        st.metric("Tổng PnL", f"{summary.total_pnl:,.0f}", f"{return_pct:+.2f}%", border=True)
        st.metric("PnL đã chốt", f"{summary.realized_pnl:,.0f}", border=True)
        st.metric("PnL chưa chốt", f"{summary.unrealized_pnl:,.0f}", border=True)
        st.metric("Tỷ trọng lớn nhất", f"{summary.max_weight_pct:.1f}%", border=True)
        risk_label = "Cao" if summary.concentration_index > 0.25 else "Kiểm soát"
        st.metric(
            "Rủi ro tập trung",
            risk_label,
            f"HHI {summary.concentration_index:.2f}",
            border=True,
        )

    rows = []
    for position in summary.positions:
        result = analyses[position.symbol]
        rows.append(
            {
                "Mã": position.symbol,
                "Khối lượng": position.shares,
                "Giá vốn": position.average_cost,
                "Giá hiện tại": position.current_price,
                "Giá trị": position.market_value,
                "PnL chưa chốt": position.unrealized_pnl,
                "Tỷ trọng (%)": position.weight_pct,
                "Điểm": result.score,
                "Tín hiệu": result.signal,
                "Gợi ý": suggest_rebalance(position.weight_pct, result.score, result.signal),
            }
        )
    positions = pd.DataFrame(rows)
    chart_tab, ledger_tab = st.tabs(["Danh mục và tái cơ cấu", "Sổ giao dịch"])
    with chart_tab:
        chart_data = positions[["Mã", "Tỷ trọng (%)"]].set_index("Mã")
        st.bar_chart(chart_data, y="Tỷ trọng (%)", horizontal=True, height=260)
        st.dataframe(
            positions,
            width="stretch",
            hide_index=True,
            column_config={
                "Giá vốn": st.column_config.NumberColumn(format="%.2f"),
                "Giá hiện tại": st.column_config.NumberColumn(format="%.2f"),
                "Giá trị": st.column_config.NumberColumn(format="%,.0f"),
                "PnL chưa chốt": st.column_config.NumberColumn(format="%,.0f"),
                "Tỷ trọng (%)": st.column_config.ProgressColumn(
                    min_value=0, max_value=100, format="%.1f%%"
                ),
                "Điểm": st.column_config.ProgressColumn(min_value=0, max_value=100),
            },
        )
    with ledger_tab:
        st.dataframe(
            pd.DataFrame([item.__dict__ for item in transactions]),
            width="stretch",
            hide_index=True,
        )
        actions = st.container(horizontal=True)
        if actions.button("Hoàn tác giao dịch cuối", icon=":material/undo:"):
            repository.delete_last_portfolio_transaction()
            st.session_state.portfolio_transactions = repository.list_portfolio_transactions()
            st.rerun()
        if actions.button("Xóa toàn bộ sổ", icon=":material/delete:"):
            repository.clear_portfolio_transactions()
            st.session_state.portfolio_transactions = []
            st.rerun()

    st.warning(
        "Gợi ý tái cơ cấu dựa trên quy tắc kỹ thuật và mức tập trung, không thay thế "
        "đánh giá cơ bản, thanh khoản hay tư vấn đầu tư cá nhân."
    )


def render_alert_center() -> None:
    """Render a provider-neutral watchlist scanner and event journal."""
    st.subheader("Alert Center")
    st.caption(
        "Quét danh sách theo dõi bằng toàn bộ bộ máy phân tích. Cùng giao diện cảnh báo "
        "này sẽ nhận dữ liệu từ adapter realtime trong giai đoạn tích hợp nhà cung cấp."
    )
    repository = app_repository()
    if not st.session_state.get("alert_storage_loaded", False):
        stored_history = repository.list_alert_events()
        stored_rules = repository.list_alert_rules()
        session_rules = list(st.session_state.get("alert_rules", []))
        if session_rules and not stored_rules:
            for rule in session_rules:
                repository.upsert_alert_rule(rule)
            stored_rules = session_rules
        session_history = list(st.session_state.get("alert_history", []))
        if session_history and not stored_history:
            repository.add_alert_events(iter(session_history))
            stored_history = session_history
        st.session_state.alert_rules = stored_rules
        st.session_state.alert_history = stored_history
        st.session_state.alert_seen_ids = {event.event_id for event in stored_history}
        st.session_state.alert_snapshots = repository.list_alert_snapshots()
        st.session_state.alert_breadth_state = repository.get_metadata("alert_breadth_state")
        st.session_state.alert_storage_loaded = True
    st.session_state.setdefault("alert_latest_rows", [])

    settings = st.container(horizontal=True, vertical_alignment="bottom")
    source = settings.segmented_control(
        "Nguồn dữ liệu",
        ["Dữ liệu demo", "Thị trường thực"],
        default="Dữ liệu demo",
        key="alert_source",
        persist_state="session",
    )
    with st.form("alert_rule_form", border=True):
        inputs = st.columns([1, 1, 1, 1])
        symbol = inputs[0].text_input("Mã", value="FPT", max_chars=12).strip().upper()
        stop = float(inputs[1].number_input("Stop-loss (0 = tắt)", 0.0, step=1.0))
        target = float(inputs[2].number_input("Mục tiêu (0 = tắt)", 0.0, step=1.0))
        add_rule = inputs[3].form_submit_button(
            "Thêm/cập nhật", type="primary", icon=":material/notifications_active:"
        )
    if add_rule:
        if not symbol:
            st.error("Mã cổ phiếu không được để trống.")
        else:
            rule = AlertRule(symbol, stop or None, target or None)
            repository.upsert_alert_rule(rule)
            rules = [item for item in st.session_state.alert_rules if item.symbol != symbol]
            st.session_state.alert_rules = [*rules, rule]
            st.toast(f"Đã cập nhật cảnh báo cho {symbol}")

    rules = list(st.session_state.alert_rules)
    if not rules:
        st.info("Hãy thêm ít nhất một mã vào danh sách theo dõi.")
        return
    rule_rows = pd.DataFrame(
        [
            {
                "Mã": rule.symbol,
                "Stop-loss": rule.stop_loss,
                "Mục tiêu": rule.target_price,
            }
            for rule in rules
        ]
    )
    watchlist, controls = st.columns([4, 1])
    watchlist.dataframe(rule_rows, width="stretch", hide_index=True)
    remove_symbol = controls.selectbox("Xóa mã", [rule.symbol for rule in rules])
    if controls.button("Xóa khỏi danh sách", icon=":material/delete:", width="stretch"):
        repository.delete_alert_rule(remove_symbol)
        st.session_state.alert_rules = [rule for rule in rules if rule.symbol != remove_symbol]
        st.session_state.alert_snapshots.pop(remove_symbol, None)
        st.rerun()
    scan = settings.button(
        "Quét cảnh báo", type="primary", icon=":material/radar:", width="content"
    )
    if scan:
        try:
            with st.spinner("Đang tải dữ liệu và quét cảnh báo..."):
                frames = {
                    rule.symbol: (
                        generate_demo_prices(rule.symbol, 260)
                        if source == "Dữ liệu demo"
                        else live_prices(rule.symbol, 260)
                    )
                    for rule in rules
                }
                benchmark = (
                    generate_demo_prices("VNINDEX", 260)
                    if source == "Dữ liệu demo"
                    else live_prices("VNINDEX", 260)
                )
                breadth = analyze_market_breadth(frames)
                new_events = []
                latest_rows = []
                snapshots = dict(st.session_state.alert_snapshots)
                for rule in rules:
                    result = analyze(frames[rule.symbol], benchmark, breadth)
                    events, snapshot = detect_symbol_alerts(
                        result, rule, snapshots.get(rule.symbol)
                    )
                    snapshots[rule.symbol] = snapshot
                    new_events.extend(events)
                    latest = result.data.iloc[-1]
                    latest_rows.append(
                        {
                            "Mã": rule.symbol,
                            "Giá": float(latest["close"]),
                            "Điểm": result.score,
                            "Tín hiệu": result.signal,
                            "Xu hướng": result.trend,
                            "Stop": rule.stop_loss,
                            "Mục tiêu": rule.target_price,
                        }
                    )
                breadth_date = max(pd.Timestamp(frame.index[-1]) for frame in frames.values())
                breadth_event = detect_breadth_alert(
                    breadth, breadth_date, st.session_state.alert_breadth_state
                )
                if breadth_event is not None:
                    new_events.append(breadth_event)
                seen = set(st.session_state.alert_seen_ids)
                unique_events = [event for event in new_events if event.event_id not in seen]
                st.session_state.alert_seen_ids = seen | {event.event_id for event in unique_events}
                st.session_state.alert_history = [
                    *unique_events,
                    *st.session_state.alert_history,
                ]
                st.session_state.alert_snapshots = snapshots
                st.session_state.alert_breadth_state = breadth.state if breadth.available else None
                st.session_state.alert_latest_rows = latest_rows
                repository.add_alert_events(iter(unique_events))
                repository.upsert_alert_snapshots(snapshots)
                if breadth.available:
                    repository.set_metadata("alert_breadth_state", breadth.state)
            if unique_events:
                st.toast(f"Phát hiện {len(unique_events)} cảnh báo mới", icon="🔔")
            else:
                st.toast("Không có cảnh báo mới")
        except (ValueError, MarketDataError) as error:
            st.error(str(error))

    latest_rows = list(st.session_state.alert_latest_rows)
    history = list(st.session_state.alert_history)
    with st.container(horizontal=True):
        st.metric("Mã theo dõi", len(rules), border=True)
        st.metric("Tổng sự kiện", len(history), border=True)
        st.metric(
            "Mức khẩn cấp/cao",
            sum(event.severity in {"Khẩn cấp", "Cao"} for event in history),
            border=True,
        )
        st.metric(
            "Lần quét gần nhất",
            "Đã quét" if latest_rows else "Chưa quét",
            border=True,
        )
    status_tab, history_tab = st.tabs(["Trạng thái hiện tại", "Nhật ký sự kiện"])
    with status_tab:
        if latest_rows:
            st.dataframe(
                pd.DataFrame(latest_rows),
                width="stretch",
                hide_index=True,
                column_config={
                    "Giá": st.column_config.NumberColumn(format="%.2f"),
                    "Điểm": st.column_config.ProgressColumn(min_value=0, max_value=100),
                },
            )
        else:
            st.info("Bấm “Quét cảnh báo” để tạo ảnh chụp trạng thái đầu tiên.")
    with history_tab:
        if history:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Thời điểm dữ liệu": event.occurred_at,
                            "Mã": event.symbol,
                            "Loại": event.category,
                            "Mức độ": event.severity,
                            "Nội dung": event.message,
                            "Giá": event.price,
                            "Điểm": event.score,
                        }
                        for event in history
                    ]
                ),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("Chưa phát hiện sự kiện nào.")
        if st.button("Xóa nhật ký", icon=":material/delete_sweep:"):
            repository.clear_alert_events()
            st.session_state.alert_history = []
            st.session_state.alert_seen_ids = set()
            st.rerun()


def advance_replay(steps: int = 1) -> None:
    """Advance replay state and execute a queued order on the next open."""
    prices = st.session_state.replay_prices
    for _ in range(steps):
        cursor = int(st.session_state.replay_cursor)
        if cursor >= len(prices) - 1:
            st.session_state.replay_playing = False
            break
        cursor += 1
        date = pd.Timestamp(prices.index[cursor])
        account = execute_replay_order(
            st.session_state.replay_account,
            date,
            float(prices.iloc[cursor]["open"]),
            price_scale=1_000,
        )
        st.session_state.replay_cursor = cursor
        st.session_state.replay_account = account
        st.session_state.replay_snapshots[cursor] = account


def rewind_replay() -> None:
    """Move back one bar and restore the account snapshot for that bar."""
    start = int(st.session_state.replay_start)
    cursor = int(st.session_state.replay_cursor)
    if cursor <= start:
        return
    cursor -= 1
    st.session_state.replay_cursor = cursor
    st.session_state.replay_account = st.session_state.replay_snapshots[cursor]
    st.session_state.replay_snapshots = {
        index: account
        for index, account in st.session_state.replay_snapshots.items()
        if index <= cursor
    }
    st.session_state.replay_playing = False


def toggle_replay() -> None:
    """Toggle automatic playback before the replay fragment reruns."""
    st.session_state.replay_playing = not st.session_state.replay_playing


def reset_replay() -> None:
    """Restore the selected starting bar and initial account."""
    start = int(st.session_state.replay_start)
    account = ReplayAccount(cash=float(st.session_state.replay_initial_cash))
    st.session_state.replay_cursor = start
    st.session_state.replay_account = account
    st.session_state.replay_snapshots = {start: account}
    st.session_state.replay_playing = False


def clear_replay_state() -> None:
    """Clear the active replay while preserving setup widget values."""
    setup_keys = {
        "replay_setup_source",
        "replay_setup_symbol",
        "replay_setup_periods",
        "replay_setup_start_date",
        "replay_setup_breadth",
        "replay_setup_cash",
    }
    for key in [
        key
        for key in st.session_state
        if key.startswith("replay_") and key not in setup_keys
    ]:
        del st.session_state[key]


def handle_replay_shortcut() -> None:
    """Apply a CCv2 keyboard trigger before the replay fragment is rendered."""
    payload = st.session_state.get("replay_keyboard_shortcuts")
    action = getattr(payload, "action", None)
    if action == "back":
        rewind_replay()
    elif action == "next":
        advance_replay()
    elif action == "play":
        toggle_replay()
    elif action in {"buy", "sell"}:
        cursor = int(st.session_state.replay_cursor)
        prices = st.session_state.replay_prices
        date = pd.Timestamp(prices.index[cursor])
        fraction = float(st.session_state.get("replay_order_fraction", 50)) / 100
        try:
            account = queue_replay_order(
                st.session_state.replay_account, action, date, fraction
            )
            st.session_state.replay_account = account
            st.session_state.replay_snapshots[cursor] = account
        except ValueError:
            pass


@st.fragment(run_every=1)
def render_bar_replay() -> None:
    """Render an AmiBroker-style historical bar replay workspace."""
    st.subheader("Bar Replay")
    st.caption(
        "Mỗi lần chỉ tiết lộ thêm dữ liệu đến nến hiện tại. Lệnh giả lập được đặt sau "
        "đóng cửa và khớp tại giá mở cửa nến kế tiếp."
    )
    if "replay_prices" not in st.session_state:
        with st.form("replay_setup", border=False):
            setup = st.columns([1, 1, 1, 1.2, 2, 1])
            source = setup[0].selectbox(
                "Nguồn",
                ["Dữ liệu demo", "Thị trường thực"],
                key="replay_setup_source",
                persist_state="session",
            )
            symbol = (
                setup[1]
                .text_input(
                    "Mã",
                    value="FPT",
                    max_chars=12,
                    key="replay_setup_symbol",
                    persist_state="session",
                )
                .strip()
                .upper()
            )
            periods = int(
                setup[2].number_input(
                    "Số phiên",
                    220,
                    600,
                    260,
                    20,
                    key="replay_setup_periods",
                    persist_state="session",
                )
            )
            requested_start_date = setup[3].date_input(
                "Ngày bắt đầu",
                value=pd.Timestamp("2026-01-19").date(),
                key="replay_setup_start_date",
                persist_state="session",
            )
            breadth_text = setup[4].text_input(
                "Mã tính Breadth",
                value="FPT, HPG, VCB",
                key="replay_setup_breadth",
                persist_state="session",
            )
            initial_cash = float(
                setup[5].number_input(
                    "Vốn",
                    1_000_000,
                    10_000_000_000,
                    100_000_000,
                    10_000_000,
                    key="replay_setup_cash",
                    persist_state="session",
                )
            )
            submitted = st.form_submit_button(
                "Khởi tạo replay", type="primary", key="replay_setup_submit"
            )
        if not submitted:
            st.info("Chọn dữ liệu và bấm “Khởi tạo replay”.")
            return
        breadth_symbols = tuple(
            dict.fromkeys(
                [symbol]
                + [part.strip().upper() for part in breadth_text.split(",") if part.strip()]
            )
        )[:3]
        if len(breadth_symbols) < 3:
            st.error("Cần ít nhất 3 mã để tính Market Breadth lịch sử.")
            return
        try:
            if source == "Dữ liệu demo":
                prices = generate_demo_prices(symbol, periods)
                benchmark = generate_demo_prices("VNINDEX", periods)
                breadth_frames = {
                    item: generate_demo_prices(item, periods) for item in breadth_symbols
                }
            else:
                prices = live_prices(symbol, periods)
                benchmark = live_prices("VNINDEX", periods)
                breadth_frames = {item: live_prices(item, periods) for item in breadth_symbols}
        except (ValueError, MarketDataError) as error:
            st.error(str(error))
            return
        requested_start = pd.Timestamp(requested_start_date).normalize()
        requested_position = int(prices.index.searchsorted(requested_start))
        start = max(52, min(requested_position, len(prices) - 1))
        actual_start = pd.Timestamp(prices.index[start]).normalize()
        if requested_position >= len(prices):
            start_notice = (
                f"Dữ liệu chỉ có đến {actual_start:%d/%m/%Y}; "
                "replay bắt đầu tại phiên cuối cùng hiện có."
            )
        elif requested_position < 52:
            start_notice = (
                f"Không đủ 52 phiên khởi động trước {requested_start:%d/%m/%Y}; "
                f"replay bắt đầu từ {actual_start:%d/%m/%Y}."
            )
        elif actual_start != requested_start:
            start_notice = (
                f"{requested_start:%d/%m/%Y} không phải phiên có dữ liệu; "
                f"đã chọn phiên kế tiếp {actual_start:%d/%m/%Y}."
            )
        else:
            start_notice = ""
        account = ReplayAccount(cash=initial_cash)
        st.session_state.replay_prices = prices
        st.session_state.replay_benchmark = benchmark
        st.session_state.replay_breadth_frames = breadth_frames
        st.session_state.replay_symbol = symbol
        st.session_state.replay_source = source
        st.session_state.replay_start_notice = start_notice
        st.session_state.replay_start = start
        st.session_state.replay_cursor = start
        st.session_state.replay_account = account
        st.session_state.replay_initial_cash = initial_cash
        st.session_state.replay_snapshots = {start: account}
        st.session_state.replay_playing = False
        st.rerun()

    prices = st.session_state.replay_prices
    if st.session_state.get("replay_source") == "Dữ liệu demo":
        st.warning(
            "Bạn đang chạy dữ liệu demo được sinh giả lập. Để tái hiện FPT giai đoạn "
            "19/01/2026, hãy bấm “Thiết lập mới” và chọn “Thị trường thực”."
        )
    if st.session_state.get("replay_start_notice"):
        st.info(st.session_state.replay_start_notice)
    if st.session_state.replay_playing:
        advance_replay(int(st.session_state.get("replay_speed", 1)))
    cursor = int(st.session_state.replay_cursor)
    date = pd.Timestamp(prices.index[cursor])

    cursor = int(st.session_state.replay_cursor)
    date = pd.Timestamp(prices.index[cursor])
    prefix = prices.iloc[: cursor + 1]
    benchmark = st.session_state.replay_benchmark.loc[:date]
    breadth_prefixes = {
        symbol: frame.loc[:date] for symbol, frame in st.session_state.replay_breadth_frames.items()
    }
    breadth = analyze_market_breadth(breadth_prefixes)
    result = analyze(prefix, benchmark, breadth)
    latest = result.data.iloc[-1]
    account = st.session_state.replay_account
    equity = replay_equity(account, float(latest["close"]), price_scale=1_000)
    unrealized = (
        account.shares * (float(latest["close"]) - account.average_price) * 1_000
    )

    st.caption(
        f"Nến {cursor + 1}/{len(prices)} · {date:%d/%m/%Y} · "
        f"còn {len(prices) - cursor - 1} nến chưa được tiết lộ"
    )
    with st.container(horizontal=True):
        st.metric("Giá", f"{latest['close']:,.2f}", border=True)
        st.metric("Điểm / tín hiệu", f"{result.score}/100 · {result.signal}", border=True)
        st.metric("Breadth", f"{breadth.state} · {breadth.score}/10", border=True)
        st.metric("Tiền mặt", f"{account.cash:,.0f}", border=True)
        st.metric("Vị thế", f"{account.shares:,} cp", border=True)
        st.metric("Tài sản", f"{equity:,.0f}", f"PnL mở {unrealized:,.0f}", border=True)

    order_controls = st.columns([1, 1, 1, 3])
    fraction = order_controls[0].selectbox(
        "Quy mô lệnh", [25, 50, 75, 100], index=1, key="replay_order_fraction"
    )
    buy_requested = order_controls[1].button(
        "Đặt lệnh mua", type="primary", width="stretch", key="replay_buy"
    )
    if buy_requested:
        try:
            account = queue_replay_order(account, "buy", date, fraction / 100)
            st.session_state.replay_account = account
            st.session_state.replay_snapshots[cursor] = account
        except ValueError as error:
            st.warning(str(error))
    sell_requested = order_controls[2].button(
        "Đặt lệnh bán", width="stretch", key="replay_sell"
    )
    if sell_requested:
        try:
            account = queue_replay_order(account, "sell", date, fraction / 100)
            st.session_state.replay_account = account
            st.session_state.replay_snapshots[cursor] = account
        except ValueError as error:
            st.warning(str(error))
    order_controls[3].info(
        f"Lệnh chờ: {account.pending_action or 'Không'} · Giá vào tham chiếu "
        f"{result.risk_plan.entry:.2f} · Stop {result.risk_plan.stop_loss:.2f} · "
        f"Target {result.risk_plan.target:.2f}"
    )
    if result.execution.score_candidate and not result.execution.eligible:
        st.warning("Chưa nên mua: " + "; ".join(result.execution.blockers))

    with st.container(border=True, gap="small"):
        toolbar = st.container(
            horizontal=True,
            horizontal_alignment="distribute",
            vertical_alignment="bottom",
        )
        toolbar.button(
            "Lùi",
            icon=":material/skip_previous:",
            key="replay_back",
            on_click=rewind_replay,
        )
        play_label = "Tạm dừng" if st.session_state.replay_playing else "Phát"
        toolbar.button(
            play_label,
            icon=":material/play_pause:",
            key="replay_play",
            on_click=toggle_replay,
        )
        toolbar.button(
            "Tiến",
            icon=":material/skip_next:",
            key="replay_next",
            on_click=advance_replay,
        )
        toolbar.button(
            "+5 nến", key="replay_next_5", on_click=advance_replay, args=(5,)
        )
        toolbar.button(
            "Đặt lại",
            icon=":material/restart_alt:",
            key="replay_reset",
            on_click=reset_replay,
        )
        toolbar.select_slider(
            "Tốc độ",
            [1, 2, 5],
            value=1,
            key="replay_speed",
            format_func=lambda value: f"{value} nến/giây",
        )
        toolbar.button(
            "Thiết lập mới",
            icon=":material/tune:",
            key="replay_new_setup",
            on_click=clear_replay_state,
        )
        _REPLAY_SHORTCUTS(
            key="replay_keyboard_shortcuts",
            on_action_change=handle_replay_shortcut,
        )

    st.plotly_chart(
        replay_price_chart(result, st.session_state.replay_symbol, account),
        width="stretch",
    )
    analysis_tab, ledger_tab, report_tab = st.tabs(
        ["Phân tích tại nến hiện tại", "Nhật ký replay", "Báo cáo phiên"]
    )
    with analysis_tab:
        score_rows = pd.DataFrame(
            [
                {
                    "Nhóm": category.name,
                    "Điểm": category.score,
                    "Tối đa": category.maximum,
                    "Luận điểm": "; ".join(category.reasons),
                }
                for category in result.scorecard.categories
            ]
        )
        st.dataframe(score_rows, width="stretch", hide_index=True)
    with ledger_tab:
        if account.trades:
            st.dataframe(
                pd.DataFrame([trade.__dict__ for trade in account.trades]),
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("Chưa có lệnh nào được khớp.")
    with report_tab:
        report = build_replay_report(
            account,
            float(latest["close"]),
            float(st.session_state.replay_initial_cash),
            price_scale=1_000,
        )
        with st.container(horizontal=True):
            st.metric("Lợi nhuận", f"{report.total_return_pct:+.2f}%", border=True)
            st.metric("PnL thực hiện", f"{report.realized_pnl:,.0f}", border=True)
            st.metric("PnL chưa thực hiện", f"{report.unrealized_pnl:,.0f}", border=True)
            st.metric("Tỷ lệ bán có lãi", f"{report.win_rate_pct:.1f}%", border=True)
            st.metric(
                "Lệnh mua / bán",
                f"{report.buy_orders} / {report.sell_orders}",
                border=True,
            )
        if not account.trades:
            st.info("Hãy thực hiện giao dịch để bắt đầu đánh giá quyết định replay.")
        elif report.sell_orders == 0:
            st.info("Chưa có lệnh bán; kết quả hiện tại vẫn là PnL đánh dấu theo thị trường.")
        elif report.total_return_pct > 0 and report.win_rate_pct >= 50:
            st.success("Phiên replay đang có lợi nhuận và đa số quyết định thoát lệnh có lãi.")
        else:
            st.warning(
                "Kết quả chưa ổn định. Hãy đối chiếu điểm tín hiệu, Breadth và mức stop "
                "tại các thời điểm đặt lệnh trong nhật ký."
            )
        if st.button("Kết thúc phiên replay", type="secondary", key="replay_finish"):
            for key in [key for key in st.session_state if key.startswith("replay_")]:
                del st.session_state[key]
            st.rerun()


st.title("VNStockLab")
st.caption("Không gian phân tích kỹ thuật cổ phiếu Việt Nam")
workspace = st.segmented_control(
    "Không gian làm việc",
    [
        "Phân tích một mã",
        "Bộ sàng lọc",
        "Độ rộng thị trường",
        "Bar Replay",
        "Strategy Lab",
        "Portfolio Manager",
        "Alert Center",
    ],
    default="Phân tích một mã",
    label_visibility="collapsed",
)
if workspace == "Phân tích một mã":
    render_analysis()
elif workspace == "Bộ sàng lọc":
    render_screener()
elif workspace == "Độ rộng thị trường":
    render_market_breadth()
elif workspace == "Bar Replay":
    render_bar_replay()
elif workspace == "Portfolio Manager":
    render_portfolio_manager()
elif workspace == "Alert Center":
    render_alert_center()
else:
    render_strategy_lab()
