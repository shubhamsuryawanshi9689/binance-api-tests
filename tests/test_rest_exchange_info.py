import pytest

from utils.binance_client import BinanceREST


@pytest.fixture(scope="module")
def client(base_url, http_session):
    return BinanceREST(base_url=base_url, session=http_session)


@pytest.fixture(scope="module")
def exchange_info(client):
    return client.exchange_info()


def test_top_level_keys_present(exchange_info):
    for key in ("timezone", "serverTime", "symbols", "rateLimits", "exchangeFilters"):
        assert key in exchange_info, f"exchangeInfo missing top-level key: {key}"


def test_timezone_is_utc(exchange_info):
    assert exchange_info["timezone"] == "UTC", \
        f"Binance documents timezone as UTC, got {exchange_info['timezone']!r}"


def test_rate_limits_have_required_fields(exchange_info):
    rate_limits = exchange_info["rateLimits"]
    assert len(rate_limits) > 0, "rateLimits should not be empty"
    for rl in rate_limits:
        for key in ("rateLimitType", "interval", "intervalNum", "limit"):
            assert key in rl, f"rateLimit entry missing {key}: {rl!r}"
        assert rl["intervalNum"] > 0
        assert rl["limit"] > 0


def test_btcusdt_is_listed_and_trading(exchange_info):
    symbols = {s["symbol"]: s for s in exchange_info["symbols"]}
    assert "BTCUSDT" in symbols, "BTCUSDT must be present on Binance"
    btc = symbols["BTCUSDT"]
    assert btc["status"] == "TRADING", \
        f"BTCUSDT status expected TRADING, got {btc['status']!r}"
    assert btc["baseAsset"] == "BTC"
    assert btc["quoteAsset"] == "USDT"


def test_filtered_query_returns_single_symbol(client):
    """Calling exchangeInfo with ?symbol=ETHUSDT must return only ETHUSDT."""
    resp = client.exchange_info(symbol="ETHUSDT")
    symbols = resp["symbols"]
    assert len(symbols) == 1, f"expected exactly 1 symbol, got {len(symbols)}"
    assert symbols[0]["symbol"] == "ETHUSDT"


@pytest.mark.parametrize("sym", ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
def test_symbol_has_required_filters(exchange_info, sym):
    """Every tradable symbol must declare PRICE_FILTER and LOT_SIZE — these
    are what order-validation logic relies on in any trading platform."""
    symbols = {s["symbol"]: s for s in exchange_info["symbols"]}
    assert sym in symbols, f"{sym} not listed"
    filter_types = {f["filterType"] for f in symbols[sym]["filters"]}
    for required in ("PRICE_FILTER", "LOT_SIZE"):
        assert required in filter_types, \
            f"{sym} missing {required} filter (present: {filter_types})"
