import time

import pytest

from utils.binance_client import BinanceREST


@pytest.fixture(scope="module")
def client(base_url, http_session):
    return BinanceREST(base_url=base_url, session=http_session)


@pytest.mark.smoke
def test_ping_returns_empty_object(client):
    """GET /api/v3/ping must return {} — Binance uses this for liveness."""
    resp = client.ping()
    assert resp == {}, f"ping should return empty dict, got: {resp!r}"


@pytest.mark.smoke
def test_server_time_has_required_field(client):
    resp = client.server_time()
    assert "serverTime" in resp, f"missing 'serverTime' key, payload={resp!r}"
    assert isinstance(resp["serverTime"], int), \
        f"serverTime should be int (ms epoch), got {type(resp['serverTime']).__name__}"


def test_server_time_within_drift_tolerance(client):
    """Local clock vs. Binance server clock must agree within 5 seconds.

    Same check we ran in production against exchange order routers —
    a skewed clock breaks signed REST and time-in-force orders."""
    local_ms = int(time.time() * 1000)
    server_ms = client.server_time()["serverTime"]
    drift_seconds = abs(server_ms - local_ms) / 1000
    assert drift_seconds < 5, (
        f"Clock drift {drift_seconds:.2f}s exceeds 5s tolerance "
        f"(local={local_ms}, server={server_ms})"
    )
