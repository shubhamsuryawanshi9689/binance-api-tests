from decimal import Decimal

import pytest

from utils.binance_client import BinanceREST


@pytest.fixture(scope="module")
def client(base_url, http_session):
    return BinanceREST(base_url=base_url, session=http_session)


# ---------- /api/v3/ticker/24hr -------------------------------------------

@pytest.mark.market_data
def test_ticker_24hr_required_fields(client, symbol):
    t = client.ticker_24hr(symbol)
    for key in ("symbol", "lastPrice", "highPrice", "lowPrice", "volume",
                "openTime", "closeTime", "priceChange", "priceChangePercent"):
        assert key in t, f"{symbol} 24hr ticker missing {key}: {t!r}"
    assert t["symbol"] == symbol


@pytest.mark.market_data
def test_ticker_24hr_high_low_sanity(client, symbol):
    t = client.ticker_24hr(symbol)
    high = Decimal(t["highPrice"])
    low = Decimal(t["lowPrice"])
    last = Decimal(t["lastPrice"])
    assert high >= low, f"{symbol}: high {high} < low {low}"
    assert low <= last <= high, \
        f"{symbol}: last {last} outside [{low}, {high}] window"


# ---------- /api/v3/depth -------------------------------------------------

@pytest.mark.market_data
def test_order_book_structure(client, symbol):
    book = client.order_book(symbol, limit=20)
    assert "bids" in book and "asks" in book
    assert "lastUpdateId" in book
    assert len(book["bids"]) > 0, f"{symbol} bids empty"
    assert len(book["asks"]) > 0, f"{symbol} asks empty"


@pytest.mark.market_data
def test_order_book_not_crossed(client, symbol):
    """Best bid must be strictly less than best ask — a crossed book is a
    bug. Same invariant our 3rdEye book-builder enforced."""
    book = client.order_book(symbol, limit=5)
    best_bid = Decimal(book["bids"][0][0])
    best_ask = Decimal(book["asks"][0][0])
    assert best_bid < best_ask, \
        f"{symbol} crossed book: bid {best_bid} >= ask {best_ask}"


@pytest.mark.market_data
def test_order_book_bids_descending_asks_ascending(client, symbol):
    book = client.order_book(symbol, limit=50)
    bid_prices = [Decimal(p) for p, _ in book["bids"]]
    ask_prices = [Decimal(p) for p, _ in book["asks"]]
    assert bid_prices == sorted(bid_prices, reverse=True), \
        f"{symbol} bids not strictly descending"
    assert ask_prices == sorted(ask_prices), \
        f"{symbol} asks not strictly ascending"


# ---------- /api/v3/klines ------------------------------------------------

@pytest.mark.market_data
@pytest.mark.parametrize("interval", ["1m", "5m", "1h", "1d"])
def test_klines_shape(client, interval):
    """Klines return list-of-lists, each with exactly 12 fields."""
    rows = client.klines("BTCUSDT", interval=interval, limit=10)
    assert len(rows) == 10, f"expected 10 klines, got {len(rows)}"
    for row in rows:
        assert len(row) == 12, f"each kline should have 12 fields, got {len(row)}"


@pytest.mark.market_data
def test_klines_ohlc_invariants(client, symbol):
    """For every candle: low ≤ open/close ≤ high. A broken candle here
    poisons backtests and live strategy P&L."""
    rows = client.klines(symbol, interval="1m", limit=50)
    for i, row in enumerate(rows):
        _open, high, low, close = Decimal(row[1]), Decimal(row[2]), Decimal(row[3]), Decimal(row[4])
        assert low <= _open <= high, \
            f"{symbol} kline[{i}] open {_open} outside [{low}, {high}]"
        assert low <= close <= high, \
            f"{symbol} kline[{i}] close {close} outside [{low}, {high}]"


@pytest.mark.market_data
def test_klines_are_time_ordered(client, symbol):
    rows = client.klines(symbol, interval="1m", limit=100)
    open_times = [r[0] for r in rows]
    assert open_times == sorted(open_times), \
        f"{symbol} klines not in ascending openTime order"


# ---------- /api/v3/trades & /avgPrice -----------------------------------

@pytest.mark.market_data
def test_recent_trades_have_required_fields(client, symbol):
    trades = client.recent_trades(symbol, limit=10)
    assert len(trades) > 0
    for t in trades:
        for key in ("id", "price", "qty", "time", "isBuyerMaker"):
            assert key in t, f"trade missing {key}: {t!r}"
        assert Decimal(t["price"]) > 0
        assert Decimal(t["qty"]) > 0


@pytest.mark.market_data
def test_avg_price_within_24h_band(client, symbol):
    """Current average price must lie inside the 24h high/low band."""
    avg = Decimal(client.avg_price(symbol)["price"])
    t = client.ticker_24hr(symbol)
    high, low = Decimal(t["highPrice"]), Decimal(t["lowPrice"])
    assert low <= avg <= high, \
        f"{symbol} avg {avg} outside 24h band [{low}, {high}]"
