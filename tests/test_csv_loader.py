from io import StringIO

import pytest

from vnstocklab.data.csv_loader import load_price_csv


def test_load_price_csv_normalizes_columns() -> None:
    source = StringIO(
        "Date,Open,High,Low,Close,Volume\n"
        "2026-01-02,10,12,9,11,1000\n"
        "2026-01-03,11,13,10,12,1200\n"
    )
    result = load_price_csv(source)

    assert result.index.name == "date"
    assert list(result.columns) == ["open", "high", "low", "close", "volume"]
    assert result.iloc[-1]["close"] == 12


def test_load_price_csv_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="Missing columns"):
        load_price_csv(StringIO("date,close\n2026-01-02,10\n"))

