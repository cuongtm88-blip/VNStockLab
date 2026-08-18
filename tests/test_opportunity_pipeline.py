import pandas as pd

from vnstocklab.analysis.market_regime import MarketRegime
from vnstocklab.analysis.opportunity_pipeline import (
    build_opportunity_pipeline,
    open_position_symbols,
)
from vnstocklab.analysis.portfolio import PortfolioTransaction


def _regime(score: int = 70) -> MarketRegime:
    return MarketRegime(score, "Tích cực có chọn lọc", "Trung bình", (50, 70), (30, 50), "Mua", ())


def _row(symbol: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "Mã": symbol,
        "Điểm": 70,
        "Tín hiệu": "MUA THĂM DÒ",
        "Xu hướng": "Tăng",
        "Giá": 100.0,
        "Stop-loss": 90.0,
        "Mục tiêu": 120.0,
        "CMF 20": 0.15,
        "ADX 14": 25.0,
        "Breakout": "Tăng",
    }
    row.update(overrides)
    return row


def test_pipeline_classifies_buy_preparation_and_watch() -> None:
    rows = pd.DataFrame(
        [
            _row("FPT"),
            _row("HPG", **{"Điểm": 60, "Tín hiệu": "NẮM GIỮ", "ADX 14": 19}),
            _row("VCB", **{"Điểm": 40, "Xu hướng": "Giảm", "CMF 20": -0.2}),
        ]
    )
    result = build_opportunity_pipeline(rows, _regime())
    stages = dict(zip(result["Mã"], result["Giai đoạn"], strict=True))
    assert stages == {"FPT": "Điểm mua", "HPG": "Chuẩn bị mua", "VCB": "Theo dõi"}


def test_pipeline_prioritizes_held_position_exit_rules() -> None:
    rows = pd.DataFrame(
        [
            _row("FPT", **{"Tín hiệu": "NẮM GIỮ"}),
            _row("HPG", **{"Điểm": 30, "Tín hiệu": "GIẢM TỶ TRỌNG"}),
        ]
    )
    result = build_opportunity_pipeline(rows, _regime(), ("FPT", "HPG"))
    stages = dict(zip(result["Mã"], result["Giai đoạn"], strict=True))
    assert stages == {"FPT": "Đang nắm giữ", "HPG": "Giảm/Bán"}


def test_open_position_symbols_uses_net_share_balance() -> None:
    transactions = [
        PortfolioTransaction(pd.Timestamp("2026-01-01"), "FPT", "Mua", 100, 100),
        PortfolioTransaction(pd.Timestamp("2026-01-02"), "FPT", "Bán", 100, 110),
        PortfolioTransaction(pd.Timestamp("2026-01-03"), "HPG", "Mua", 50, 25),
    ]
    assert open_position_symbols(transactions) == ("HPG",)
