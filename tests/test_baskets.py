from vnstocklab.data.baskets import BASKET_FALLBACKS, MARKET_BASKETS, basket_fallback


def test_supported_baskets_have_non_empty_fallbacks() -> None:
    assert set(MARKET_BASKETS.values()) == set(BASKET_FALLBACKS)
    assert all(len(symbols) >= 17 for symbols in BASKET_FALLBACKS.values())


def test_basket_fallback_normalizes_index_and_defaults_to_vn30() -> None:
    assert basket_fallback(" hnx30 ") == BASKET_FALLBACKS["HNX30"]
    assert basket_fallback("unknown") == BASKET_FALLBACKS["VN30"]
