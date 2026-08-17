import pandas as pd
import pytest

from vnstocklab.data.demo import generate_demo_prices


def test_demo_prices_are_reproducible() -> None:
    first = generate_demo_prices("FPT", periods=100)
    second = generate_demo_prices("FPT", periods=100)

    pd.testing.assert_frame_equal(first, second)
    assert list(first.columns) == ["open", "high", "low", "close", "volume"]
    assert (first["high"] >= first[["open", "close"]].max(axis=1)).all()
    assert (first["low"] <= first[["open", "close"]].min(axis=1)).all()


def test_demo_requires_enough_periods() -> None:
    with pytest.raises(ValueError, match="at least 60"):
        generate_demo_prices("FPT", periods=30)

