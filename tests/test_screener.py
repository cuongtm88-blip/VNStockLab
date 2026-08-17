import pandas as pd

from vnstocklab.analysis.screener import screen_symbols
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

