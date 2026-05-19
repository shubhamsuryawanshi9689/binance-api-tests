import pytest
import requests

BASE_URL = "https://api.binance.com"
WS_URL = "wss://stream.binance.com:9443/ws"
SYMBOLS_UNDER_TEST = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def ws_url():
    return WS_URL


@pytest.fixture(scope="session")
def http_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "binance-api-tests/1.0 (+pytest)"})
    yield s
    s.close()


@pytest.fixture(params=SYMBOLS_UNDER_TEST)
def symbol(request):
    return request.param
