import numpy as np

from vnstocklab.analysis.indicators import enrich_indicators
from vnstocklab.data.demo import generate_demo_prices


def test_enrich_indicators_adds_expected_series() -> None:
    result = enrich_indicators(generate_demo_prices("VCB", periods=100))

    expected = {
        "sma20", "sma50", "macd", "macd_signal", "rsi14", "atr14", "mfi14",
        "obv", "cmf20",
        "adx14", "plus_di14", "minus_di14", "bb_upper", "bb_lower",
        "kc_upper", "kc_lower", "squeeze_on", "squeeze_release",
    }
    assert expected.issubset(result.columns)
    assert np.isfinite(result.iloc[-1][list(expected)].astype(float)).all()
    assert 0 <= result.iloc[-1]["rsi14"] <= 100
    assert 0 <= result.iloc[-1]["mfi14"] <= 100
    assert -1 <= result.iloc[-1]["cmf20"] <= 1
    assert 0 <= result.iloc[-1]["adx14"] <= 100
    assert result["squeeze_on"].dtype == bool
    assert result["squeeze_release"].dtype == bool
