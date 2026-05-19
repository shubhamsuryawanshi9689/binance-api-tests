import os

import pytest
import requests

# Use Binance's public data endpoint by default — it has the same routes
# as api.binance.com but is not geo-blocked, so the suite runs unchanged
# from GitHub Actions / Azure / AWS CI runners.
BASE_URL = os.environ.get("BINANCE_BASE_URL", "https://data-api.binance.vision")
WS_URL = os.environ.get("BINANCE_WS_URL", "wss://data-stream.binance.vision/ws")
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
