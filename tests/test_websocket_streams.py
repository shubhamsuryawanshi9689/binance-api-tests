from decimal import Decimal

import pytest

from utils.binance_client import BinanceWS


pytestmark = pytest.mark.websocket


def stream_url(ws_url: str, stream: str) -> str:
    return f"{ws_url}/{stream}"


def test_trade_stream_message_schema(ws_url):
    """btcusdt@trade — every message must carry symbol, price, qty, event-time."""
    with BinanceWS(stream_url(ws_url, "btcusdt@trade")) as ws:
        msgs = ws.recv_messages(count=3, timeout=15)
    assert len(msgs) >= 1, "did not receive any trade messages in 15s"
    for m in msgs:
        assert m.get("e") == "trade", f"unexpected event type: {m!r}"
        assert m.get("s") == "BTCUSDT"
        assert Decimal(m["p"]) > 0
        assert Decimal(m["q"]) > 0
        assert isinstance(m["E"], int)  # event time ms
        assert isinstance(m["T"], int)  # trade time ms


def test_trade_stream_event_time_monotonic(ws_url):
    """Per-symbol event time E must be non-decreasing — a regression means
    the upstream dispatcher dropped or reordered frames."""
    with BinanceWS(stream_url(ws_url, "btcusdt@trade")) as ws:
        msgs = ws.recv_messages(count=8, timeout=20)
    times = [m["E"] for m in msgs]
    assert times == sorted(times), f"event times not monotonic: {times}"


def test_kline_1m_stream(ws_url):
    """btcusdt@kline_1m — verify k.o ≤ k.h, k.o ≥ k.l, etc."""
    with BinanceWS(stream_url(ws_url, "btcusdt@kline_1m")) as ws:
        msgs = ws.recv_messages(count=2, timeout=15)
    assert len(msgs) >= 1
    for m in msgs:
        assert m["e"] == "kline"
        k = m["k"]
        _open, high, low, close = Decimal(k["o"]), Decimal(k["h"]), Decimal(k["l"]), Decimal(k["c"])
        assert low <= _open <= high
        assert low <= close <= high


def test_partial_depth_stream(ws_url):
    """btcusdt@depth10@100ms — partial book snapshot every 100 ms."""
    with BinanceWS(stream_url(ws_url, "btcusdt@depth10@100ms")) as ws:
        msgs = ws.recv_messages(count=3, timeout=10)
    assert len(msgs) >= 1
    for m in msgs:
        assert "bids" in m and "asks" in m
        assert len(m["bids"]) <= 10
        assert len(m["asks"]) <= 10
        if m["bids"] and m["asks"]:
            assert Decimal(m["bids"][0][0]) < Decimal(m["asks"][0][0]), \
                f"crossed book in depth stream: {m!r}"


def test_ticker_stream_carries_24h_stats(ws_url):
    """btcusdt@ticker — must include 24h high (h), low (l), volume (v)."""
    with BinanceWS(stream_url(ws_url, "btcusdt@ticker")) as ws:
        msgs = ws.recv_messages(count=2, timeout=15)
    assert len(msgs) >= 1
    for m in msgs:
        assert m["e"] == "24hrTicker"
        assert Decimal(m["h"]) >= Decimal(m["l"]), "ticker high < low"
        assert Decimal(m["v"]) >= 0
