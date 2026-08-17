"""Deterministic demo data used before a live provider is configured."""

from __future__ import annotations

import numpy as np
import pandas as pd

VN30_SYMBOLS: tuple[str, ...] = (
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "LPB", "MBB", "MSN", "MWG", "PLX", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
)


def generate_demo_prices(symbol: str, periods: int = 300) -> pd.DataFrame:
    """Generate reproducible daily OHLCV data for UI exploration."""
    if periods < 60:
        raise ValueError("periods must be at least 60")

    seed = sum((index + 1) * ord(char) for index, char in enumerate(symbol.upper()))
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=periods)
    returns = rng.normal(0.0005, 0.018, periods)
    close = 30 * np.exp(np.cumsum(returns))
    open_price = close * (1 + rng.normal(0, 0.006, periods))
    spread = rng.uniform(0.004, 0.025, periods)
    high = np.maximum(open_price, close) * (1 + spread)
    low = np.minimum(open_price, close) * (1 - spread)
    volume = rng.lognormal(mean=14.3, sigma=0.45, size=periods).astype("int64")

    return pd.DataFrame(
        {"open": open_price, "high": high, "low": low, "close": close, "volume": volume},
        index=pd.DatetimeIndex(dates, name="date"),
    ).round({"open": 2, "high": 2, "low": 2, "close": 2})

