"""Translate screening rows into an actionable opportunity pipeline."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from vnstocklab.analysis.market_regime import MarketRegime
from vnstocklab.analysis.portfolio import PortfolioTransaction

PIPELINE_STAGES: tuple[str, ...] = (
    "Điểm mua",
    "Chuẩn bị mua",
    "Theo dõi",
    "Đang nắm giữ",
    "Giảm/Bán",
)


def open_position_symbols(transactions: Iterable[PortfolioTransaction]) -> tuple[str, ...]:
    """Return symbols with a positive net share balance."""
    balances: dict[str, int] = {}
    for transaction in transactions:
        symbol = transaction.symbol.strip().upper()
        direction = 1 if transaction.action == "Mua" else -1
        balances[symbol] = balances.get(symbol, 0) + direction * transaction.shares
    return tuple(sorted(symbol for symbol, shares in balances.items() if shares > 0))


def build_opportunity_pipeline(
    rows: pd.DataFrame,
    regime: MarketRegime,
    held_symbols: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Classify screened stocks into mutually exclusive trading stages."""
    if rows.empty:
        return rows.copy()
    held = {symbol.strip().upper() for symbol in held_symbols}
    records: list[dict[str, object]] = []
    for _, row in rows.iterrows():
        symbol = str(row["Mã"]).strip().upper()
        score = int(row["Điểm"])
        signal = str(row["Tín hiệu"])
        trend = str(row["Xu hướng"])
        close = float(row["Giá"])
        stop = float(row["Stop-loss"])
        cmf = float(row["CMF 20"])
        adx = float(row["ADX 14"])
        breakout = str(row["Breakout"])
        if symbol in held and (signal == "GIẢM TỶ TRỌNG" or score <= 35 or close <= stop):
            stage = "Giảm/Bán"
            action = "Giảm vị thế hoặc thoát theo kỷ luật stop-loss."
            rationale = "Vị thế đang nắm giữ đã xuất hiện điều kiện phòng thủ."
        elif symbol in held:
            stage = "Đang nắm giữ"
            action = "Tiếp tục nắm giữ và theo dõi stop-loss."
            rationale = "Vị thế chưa vi phạm điều kiện thoát."
        elif (
            regime.score >= 60
            and score >= 65
            and signal == "MUA THĂM DÒ"
            and trend == "Tăng"
            and cmf > 0
            and adx >= 20
        ):
            stage = "Điểm mua"
            action = "Có thể mua từng phần, tuân thủ stop-loss và giới hạn tỷ trọng."
            rationale = "Thị trường cho phép, xu hướng và dòng tiền cùng xác nhận."
        elif (
            regime.score >= 45
            and score >= 55
            and trend != "Giảm"
            and cmf >= 0
            and adx >= 18
        ):
            stage = "Chuẩn bị mua"
            action = "Chờ điểm kích hoạt hoặc breakout có khối lượng xác nhận."
            rationale = "Nền kỹ thuật đạt yêu cầu nhưng chưa đủ xác nhận vào lệnh."
        else:
            stage = "Theo dõi"
            action = "Chưa hành động; tiếp tục theo dõi diễn biến kỹ thuật."
            rationale = (
                "Chế độ thị trường chưa cho phép mở vị thế."
                if regime.score < 45
                else "Điểm, xu hướng hoặc dòng tiền chưa đồng thuận."
            )
        record = row.to_dict()
        record.update(
            {
                "Giai đoạn": stage,
                "Hành động": action,
                "Luận điểm pipeline": rationale,
                "Breakout": breakout,
            }
        )
        records.append(record)
    result = pd.DataFrame.from_records(records)
    priority = {stage: index for index, stage in enumerate(PIPELINE_STAGES)}
    result["_priority"] = result["Giai đoạn"].map(priority)
    return (
        result.sort_values(["_priority", "Điểm"], ascending=[True, False])
        .drop(columns="_priority")
        .reset_index(drop=True)
    )
