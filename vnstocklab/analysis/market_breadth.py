"""Cross-sectional market breadth analysis."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MarketBreadth:
    """Latest breadth snapshot plus its daily history."""

    available: bool
    score: int
    state: str
    advances: int
    declines: int
    unchanged: int
    advance_decline_ratio: float
    above_sma20_pct: float
    above_sma50_pct: float
    above_sma200_pct: float
    advancing_volume_pct: float
    symbols: tuple[str, ...]
    history: pd.DataFrame
    reasons: tuple[str, ...]


def unavailable_breadth(reason: str = "Chưa có dữ liệu độ rộng thị trường") -> MarketBreadth:
    """Return a neutral breadth context."""
    return MarketBreadth(
        False,
        5,
        "Chưa có dữ liệu",
        0,
        0,
        0,
        0.0,
        50.0,
        50.0,
        50.0,
        50.0,
        (),
        pd.DataFrame(),
        (reason,),
    )


def analyze_market_breadth(frames: dict[str, pd.DataFrame]) -> MarketBreadth:
    """Calculate equal-weighted breadth from normalized OHLCV histories."""
    usable = {
        symbol.strip().upper(): frame.sort_index()
        for symbol, frame in frames.items()
        if len(frame) >= 201 and {"close", "volume"}.issubset(frame.columns)
    }
    if len(usable) < 3:
        return unavailable_breadth("Cần ít nhất 3 mã có tối thiểu 201 phiên")

    closes = pd.concat(
        {symbol: frame["close"] for symbol, frame in usable.items()}, axis=1
    ).sort_index()
    volumes = pd.concat(
        {symbol: frame["volume"] for symbol, frame in usable.items()}, axis=1
    ).reindex(closes.index)
    returns = closes.pct_change(fill_method=None)
    valid = returns.notna()
    valid_count = valid.sum(axis=1).replace(0, pd.NA)
    advances = (returns > 0).sum(axis=1)
    declines = (returns < 0).sum(axis=1)
    unchanged = valid_count - advances - declines

    history = pd.DataFrame(index=closes.index)
    history["advances"] = advances
    history["declines"] = declines
    history["unchanged"] = unchanged
    history["ad_net"] = advances - declines
    history["ad_line"] = history["ad_net"].cumsum()
    history["above_sma20_pct"] = (
        (closes > closes.rolling(20).mean()).sum(axis=1) / valid_count * 100
    )
    history["above_sma50_pct"] = (
        (closes > closes.rolling(50).mean()).sum(axis=1) / valid_count * 100
    )
    history["above_sma200_pct"] = (
        (closes > closes.rolling(200).mean()).sum(axis=1) / valid_count * 100
    )
    advancing_volume = volumes.where(returns > 0, 0).sum(axis=1)
    declining_volume = volumes.where(returns < 0, 0).sum(axis=1)
    directional_volume = (advancing_volume + declining_volume).replace(0, pd.NA)
    history["advancing_volume_pct"] = advancing_volume / directional_volume * 100
    history = history.dropna(subset=["above_sma200_pct", "advancing_volume_pct"])
    if history.empty:
        return unavailable_breadth("Không có phiên chung đủ dữ liệu để tính độ rộng")

    latest = history.iloc[-1]
    advance_count = int(latest["advances"])
    decline_count = int(latest["declines"])
    total_directional = advance_count + decline_count
    advance_pct = advance_count / total_directional * 100 if total_directional else 50.0
    ratio = advance_count / decline_count if decline_count else float(advance_count)
    composite = (
        advance_pct * 0.25
        + float(latest["above_sma20_pct"]) * 0.20
        + float(latest["above_sma50_pct"]) * 0.20
        + float(latest["above_sma200_pct"]) * 0.20
        + float(latest["advancing_volume_pct"]) * 0.15
    )
    score = max(0, min(10, round(composite / 10)))
    state = (
        "Tích cực mạnh"
        if score >= 8
        else "Tích cực"
        if score >= 6
        else "Trung tính"
        if score >= 4
        else "Tiêu cực"
        if score >= 2
        else "Tiêu cực mạnh"
    )
    return MarketBreadth(
        True,
        score,
        state,
        advance_count,
        decline_count,
        int(latest["unchanged"]),
        ratio,
        float(latest["above_sma20_pct"]),
        float(latest["above_sma50_pct"]),
        float(latest["above_sma200_pct"]),
        float(latest["advancing_volume_pct"]),
        tuple(usable),
        history,
        (
            f"Tăng/giảm: {advance_count}/{decline_count}",
            f"Trên SMA20/50/200: {latest['above_sma20_pct']:.0f}%/"
            f"{latest['above_sma50_pct']:.0f}%/{latest['above_sma200_pct']:.0f}%",
            f"Khối lượng nhóm tăng chiếm {latest['advancing_volume_pct']:.1f}%",
        ),
    )
