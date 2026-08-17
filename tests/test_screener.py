import pandas as pd

from vnstocklab.analysis.screener import filter_screening_rows, screen_symbols
from vnstocklab.data.demo import generate_demo_prices


class FakeProvider:
    def history(self, symbol: str, count: int = 300) -> pd.DataFrame:
        if symbol == "BAD":
            raise RuntimeError("provider unavailable")
        return generate_demo_prices(symbol, periods=count)

    def index_members(self, index: str = "VN30") -> tuple[str, ...]:
        return ("FPT", "HPG")


def test_screen_symbols_ranks_results_and_keeps_errors() -> None:
    result = screen_symbols(("fpt", "BAD", "hpg", "FPT"), FakeProvider(), count=100)

    assert set(result.rows["Mã"]) == {"FPT", "HPG"}
    assert result.rows["Điểm"].is_monotonic_decreasing
    assert result.errors == ("BAD: provider unavailable",)


def test_filter_screening_rows_combines_technical_conditions() -> None:
    rows = pd.DataFrame(
        [
            {
                "Mã": "FPT",
                "Điểm": 75,
                "Tín hiệu": "MUA THĂM DÒ",
                "Xu hướng": "Tăng",
                "RSI 14": 58.0,
                "CMF 20": 0.18,
                "ADX 14": 27.0,
            },
            {
                "Mã": "HPG",
                "Điểm": 45,
                "Tín hiệu": "NẮM GIỮ",
                "Xu hướng": "Giảm",
                "RSI 14": 72.0,
                "CMF 20": -0.1,
                "ADX 14": 18.0,
            },
        ]
    )

    result = filter_screening_rows(
        rows,
        minimum_score=60,
        signals=("MUA THĂM DÒ",),
        trends=("Tăng",),
        rsi_range=(40, 65),
        minimum_cmf=0,
        minimum_adx=20,
    )

    assert result["Mã"].tolist() == ["FPT"]
