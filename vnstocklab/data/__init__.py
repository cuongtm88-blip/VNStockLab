"""Market data adapters."""

from vnstocklab.data.baskets import BASKET_FALLBACKS, MARKET_BASKETS, basket_fallback
from vnstocklab.data.demo import VN30_SYMBOLS, generate_demo_prices
from vnstocklab.data.provider import (
    MarketDataError,
    MarketDataProvider,
    MarketTick,
    RealtimeMarketDataProvider,
)
from vnstocklab.data.vnstock_provider import VnstockProvider

__all__ = [
    "BASKET_FALLBACKS",
    "MARKET_BASKETS",
    "VN30_SYMBOLS",
    "basket_fallback",
    "MarketDataError",
    "MarketDataProvider",
    "MarketTick",
    "RealtimeMarketDataProvider",
    "VnstockProvider",
    "generate_demo_prices",
]
