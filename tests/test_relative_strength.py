import pandas as pd

from vnstocklab.analysis.relative_strength import analyze_relative_strength
from vnstocklab.data.demo import generate_demo_prices


def test_relative_strength_detects_outperformance() -> None:
    benchmark = generate_demo_prices("VNINDEX", periods=100)
    stock = benchmark.copy()
    stock["close"] = stock["close"] * pd.Series(
        [1 + index * 0.001 for index in range(len(stock))], index=stock.index
    )

    result = analyze_relative_strength(stock, benchmark)

    assert result.available
    assert result.relative_return_20d is not None and result.relative_return_20d > 0
    assert result.relative_return_60d is not None and result.relative_return_60d > 0
    assert result.ratio_above_sma20 is True
    assert result.score > 8


def test_relative_strength_is_neutral_without_benchmark() -> None:
    result = analyze_relative_strength(generate_demo_prices("FPT"), None)

    assert not result.available
    assert result.score == 8
    assert result.relative_return_20d is None
