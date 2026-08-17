import pandas as pd

from vnstocklab.analysis.market_breadth import analyze_market_breadth
from vnstocklab.data.demo import generate_demo_prices


def _trending_frame(symbol: str, direction: float) -> pd.DataFrame:
    frame = generate_demo_prices(symbol, periods=240)
    multiplier = pd.Series(
        [1 + direction * index / len(frame) for index in range(len(frame))],
        index=frame.index,
    )
    frame["close"] = frame["close"] * multiplier
    final_change = 1.02 if direction > 0 else 0.98
    frame.loc[frame.index[-1], "close"] = frame["close"].iloc[-2] * final_change
    return frame


def test_market_breadth_builds_snapshot_and_history() -> None:
    frames = {
        "AAA": _trending_frame("AAA", 0.8),
        "BBB": _trending_frame("BBB", 0.6),
        "CCC": _trending_frame("CCC", -0.6),
    }

    result = analyze_market_breadth(frames)

    assert result.available
    assert result.advances == 2
    assert result.declines == 1
    assert result.advance_decline_ratio == 2
    assert 0 <= result.score <= 10
    assert 0 <= result.above_sma20_pct <= 100
    assert 0 <= result.advancing_volume_pct <= 100
    assert not result.history.empty


def test_market_breadth_requires_three_long_histories() -> None:
    result = analyze_market_breadth({"FPT": generate_demo_prices("FPT", periods=100)})

    assert not result.available
    assert result.score == 5
