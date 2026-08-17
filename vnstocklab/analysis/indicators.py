"""Dependency-light technical indicators."""

from __future__ import annotations

import numpy as np
import pandas as pd


def enrich_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    """Return prices enriched with trend, momentum, volatility and money-flow indicators."""
    result = prices.copy()
    close = result["close"]
    high = result["high"]
    low = result["low"]
    volume = result["volume"]

    result["sma20"] = close.rolling(20).mean()
    result["sma50"] = close.rolling(50).mean()
    result["ema12"] = close.ewm(span=12, adjust=False).mean()
    result["ema26"] = close.ewm(span=26, adjust=False).mean()
    result["macd"] = result["ema12"] - result["ema26"]
    result["macd_signal"] = result["macd"].ewm(span=9, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    relative_strength = gain / loss.replace(0, np.nan)
    result["rsi14"] = 100 - (100 / (1 + relative_strength))

    true_range = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1
    ).max(axis=1)
    result["atr14"] = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()

    upward_move = high.diff()
    downward_move = -low.diff()
    plus_dm = upward_move.where((upward_move > downward_move) & (upward_move > 0), 0.0)
    minus_dm = downward_move.where((downward_move > upward_move) & (downward_move > 0), 0.0)
    smoothed_tr = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    result["plus_di14"] = 100 * plus_dm.ewm(
        alpha=1 / 14, adjust=False, min_periods=14
    ).mean() / smoothed_tr.replace(0, np.nan)
    result["minus_di14"] = 100 * minus_dm.ewm(
        alpha=1 / 14, adjust=False, min_periods=14
    ).mean() / smoothed_tr.replace(0, np.nan)
    directional_sum = result["plus_di14"] + result["minus_di14"]
    directional_difference = (result["plus_di14"] - result["minus_di14"]).abs()
    dx = 100 * directional_difference / directional_sum.replace(0, np.nan)
    result["adx14"] = dx.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()

    result["bb_middle"] = close.rolling(20).mean()
    deviation = close.rolling(20).std(ddof=0)
    result["bb_upper"] = result["bb_middle"] + 2 * deviation
    result["bb_lower"] = result["bb_middle"] - 2 * deviation
    result["kc_middle"] = close.ewm(span=20, adjust=False).mean()
    atr20 = true_range.ewm(alpha=1 / 20, adjust=False, min_periods=20).mean()
    result["kc_upper"] = result["kc_middle"] + 1.5 * atr20
    result["kc_lower"] = result["kc_middle"] - 1.5 * atr20
    result["squeeze_on"] = (result["bb_upper"] < result["kc_upper"]) & (
        result["bb_lower"] > result["kc_lower"]
    )
    result["squeeze_release"] = result["squeeze_on"].shift(fill_value=False) & ~result[
        "squeeze_on"
    ]
    result["squeeze_momentum"] = close - (
        (high.rolling(20).max() + low.rolling(20).min()) / 2 + result["sma20"]
    ) / 2
    result["volume_sma20"] = volume.rolling(20).mean()

    typical_price = (high + low + close) / 3
    raw_flow = typical_price * volume
    direction = typical_price.diff()
    positive_flow = raw_flow.where(direction > 0, 0.0).rolling(14).sum()
    negative_flow = raw_flow.where(direction < 0, 0.0).rolling(14).sum()
    money_ratio = positive_flow / negative_flow.replace(0, np.nan)
    result["mfi14"] = 100 - (100 / (1 + money_ratio))

    signed_volume = np.sign(close.diff()).fillna(0) * volume
    result["obv"] = signed_volume.cumsum()
    money_flow_multiplier = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    money_flow_volume = money_flow_multiplier.fillna(0) * volume
    result["cmf20"] = money_flow_volume.rolling(20).sum() / volume.rolling(20).sum().replace(
        0, np.nan
    )

    result["support20"] = low.rolling(20).min()
    result["resistance20"] = high.rolling(20).max()
    return result
