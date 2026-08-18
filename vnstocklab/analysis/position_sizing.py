"""Risk-first position sizing for Vietnamese cash equities."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor

from vnstocklab.analysis.market_regime import MarketRegime


@dataclass(frozen=True)
class PositionSizePlan:
    """Explainable maximum order size after all portfolio constraints."""

    available: bool
    shares: int
    lots: int
    capital_required: float
    risk_amount: float
    risk_budget: float
    position_weight_pct: float
    market_capacity_remaining: float
    limiting_factor: str
    reasons: tuple[str, ...]


def calculate_position_size(
    *,
    capital: float,
    cash_available: float,
    entry_price: float,
    stop_loss: float,
    risk_per_trade_pct: float,
    max_position_pct: float,
    current_stock_exposure_pct: float,
    regime: MarketRegime,
    lot_size: int = 100,
    price_scale: float = 1_000,
    fee_pct: float = 0.15,
) -> PositionSizePlan:
    """Calculate a lot-rounded order constrained by risk, cash and market regime."""
    if capital <= 0 or cash_available < 0:
        raise ValueError("Vốn phải dương và tiền mặt khả dụng không được âm.")
    if entry_price <= 0 or stop_loss <= 0 or stop_loss >= entry_price:
        raise ValueError("Giá vào phải lớn hơn stop-loss và cả hai phải dương.")
    if risk_per_trade_pct <= 0 or max_position_pct <= 0:
        raise ValueError("Rủi ro mỗi lệnh và tỷ trọng tối đa phải lớn hơn 0.")
    if not 0 <= current_stock_exposure_pct <= 100:
        raise ValueError("Tỷ trọng cổ phiếu hiện tại phải nằm trong khoảng 0–100%.")
    if lot_size <= 0 or price_scale <= 0 or fee_pct < 0:
        raise ValueError("Lô, hệ số giá và phí giao dịch không hợp lệ.")

    entry_value = entry_price * price_scale
    risk_per_share = (entry_price - stop_loss) * price_scale
    fee_multiplier = 1 + fee_pct / 100
    risk_budget = capital * risk_per_trade_pct / 100
    position_budget = capital * min(max_position_pct, regime.stock_allocation[1]) / 100
    remaining_exposure_pct = max(
        0.0, regime.stock_allocation[1] - current_stock_exposure_pct
    )
    market_capacity = capital * remaining_exposure_pct / 100

    limits = {
        "Ngân sách rủi ro": risk_budget / risk_per_share,
        "Tỷ trọng tối đa mỗi mã": position_budget / (entry_value * fee_multiplier),
        "Tiền mặt khả dụng": cash_available / (entry_value * fee_multiplier),
        "Trần cổ phiếu theo thị trường": market_capacity / (entry_value * fee_multiplier),
    }
    limiting_factor = min(limits, key=limits.get)
    raw_shares = max(0, floor(limits[limiting_factor] / lot_size) * lot_size)
    capital_required = raw_shares * entry_value * fee_multiplier
    risk_amount = raw_shares * risk_per_share
    position_weight = capital_required / capital * 100
    reasons = (
        f"Ngân sách rủi ro {risk_per_trade_pct:.2f}%: {risk_budget:,.0f} đồng",
        f"Giới hạn mỗi mã: {max_position_pct:.1f}% tài khoản",
        f"Chế độ {regime.state}: trần cổ phiếu {regime.stock_allocation[1]}%",
        f"Dư địa cổ phiếu còn lại: {remaining_exposure_pct:.1f}% tài khoản",
    )
    return PositionSizePlan(
        available=raw_shares >= lot_size,
        shares=raw_shares,
        lots=raw_shares // lot_size,
        capital_required=capital_required,
        risk_amount=risk_amount,
        risk_budget=risk_budget,
        position_weight_pct=position_weight,
        market_capacity_remaining=market_capacity,
        limiting_factor=limiting_factor,
        reasons=reasons,
    )
