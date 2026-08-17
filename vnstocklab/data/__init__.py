"""Market data adapters."""

from vnstocklab.data.demo import VN30_SYMBOLS, generate_demo_prices
from vnstocklab.data.provider import (
    MarketDataError,
    MarketDataProvider,
    MarketTick,
    RealtimeMarketDataProvider,
)
from vnstocklab.data.vnstock_provider import VnstockProvider

__all__ = [
    "VN30_SYMBOLS",
    "MarketDataError",
    "MarketDataProvider",
    "MarketTick",
    "RealtimeMarketDataProvider",
    "VnstockProvider",
    "generate_demo_prices",
]
