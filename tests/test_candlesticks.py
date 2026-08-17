from __future__ import annotations

import numpy as np
import pandas as pd

from vnstocklab.analysis.candlesticks import (
    candlestick_events,
    detect_candlestick_patterns,
)
from vnstocklab.analysis.indicators import enrich_indicators


def trending_prices(direction: str = "down", periods: int = 30) -> pd.DataFrame:
    dates = pd.bdate_range("2026-01-01", periods=periods)
    close = np.linspace(20, 10, periods) if direction == "down" else np.linspace(10, 20, periods)
    open_price = close + (0.25 if direction == "down" else -0.25)
    return pd.DataFrame(
        {
            "open": open_price,
            "high": np.maximum(open_price, close) + 0.2,
            "low": np.minimum(open_price, close) - 0.2,
            "close": close,
            "volume": np.full(periods, 100_000),
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


def test_detects_confirmed_bullish_engulfing_in_downtrend() -> None:
    prices = trending_prices()
    prices.iloc[-2] = [10.5, 10.6, 9.9, 10.0, 100_000]
    prices.iloc[-1] = [9.8, 10.9, 9.7, 10.8, 250_000]

    result = detect_candlestick_patterns(enrich_indicators(prices))
    latest = result.iloc[-1]

    assert latest["candle_pattern"] == "Bullish Engulfing"
    assert latest["candle_direction"] == "bullish"
    assert bool(latest["candle_confirmed"])
    assert latest["candle_confidence"] == 3


def test_detects_confirmed_bearish_engulfing_in_uptrend() -> None:
    prices = trending_prices("up")
    prices.iloc[-2] = [19.5, 20.1, 19.4, 20.0, 100_000]
    prices.iloc[-1] = [20.2, 20.3, 19.1, 19.3, 250_000]

    latest = detect_candlestick_patterns(enrich_indicators(prices)).iloc[-1]

    assert latest["candle_pattern"] == "Bearish Engulfing"
    assert latest["candle_direction"] == "bearish"
    assert bool(latest["candle_confirmed"])


def test_detects_hammer_and_doji_without_overstating_neutral_pattern() -> None:
    prices = trending_prices()
    prices.iloc[-2] = [10.2, 10.45, 9.4, 10.4, 200_000]
    prices.iloc[-1] = [10.0, 10.51, 9.5, 10.01, 200_000]

    result = detect_candlestick_patterns(enrich_indicators(prices))

    assert result.iloc[-2]["candle_pattern"] == "Hammer"
    assert result.iloc[-1]["candle_pattern"] == "Doji"
    assert result.iloc[-1]["candle_direction"] == "neutral"
    assert not bool(result.iloc[-1]["candle_confirmed"])
    assert result.iloc[-1]["candle_confidence"] == 1


def test_recent_events_respect_lookback() -> None:
    prices = trending_prices()
    prices.iloc[-1] = [9.8, 10.9, 9.7, 10.8, 250_000]
    detected = detect_candlestick_patterns(enrich_indicators(prices))

    events = candlestick_events(detected, lookback=1)

    assert len(events) == 1
    assert events[0].date == prices.index[-1]

