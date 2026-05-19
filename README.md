# Binance Public API — Automated Test Suite

A Python `pytest` test suite for **Binance's public REST and WebSocket endpoints** — covering market data, exchange metadata, system endpoints, and live streaming feeds.

Built to mirror the kind of black-box automation I ran for **3.6 years** against a real HFT trading platform (3rdEye / Wallstreet Algo Trading) that integrated Binance, Kraken, NSE/Fyers, and IBKR.

---

## What it covers

| Suite | Endpoints / Streams | What is validated |
|---|---|---|
| `test_rest_system.py` | `/api/v3/ping`, `/api/v3/time` | Connectivity, server-time drift vs. local clock (<5 s) |
| `test_rest_exchange_info.py` | `/api/v3/exchangeInfo` | Schema, symbol filters (PRICE_FILTER, LOT_SIZE, MIN_NOTIONAL), permissions |
| `test_rest_market_data.py` | `/ticker/24hr`, `/depth`, `/klines`, `/trades`, `/avgPrice` | Field types, ordering invariants (asks ascending, bids descending), OHLC sanity (low ≤ open/close ≤ high), kline interval coverage |
| `test_websocket_streams.py` | `wss://stream.binance.com:9443/ws` — `trade`, `kline_1m`, `depth`, `ticker` streams | Message schema, monotonic event-time, stream-name routing, graceful disconnect |

---

## Why this matters for trading systems

The same invariants I tested in production at 3rdEye:

- **Order-book integrity** — bids must descend, asks must ascend, no crossed book
- **Server-time skew** — every order-router clock is sanity-checked against exchange time
- **Kline OHLC** — `low ≤ min(open, close)` and `high ≥ max(open, close)`, else strategy P&L is wrong
- **WebSocket event ordering** — `E` (event time) must be monotonic per symbol or you've dropped a frame

These checks ran on every CI build in a 7-stage GitLab pipeline I maintained.

---

## Quick start

```bash
# Clone
git clone https://github.com/shubhamsuryawanshi9689/binance-api-tests.git
cd binance-api-tests

# Install
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
pip install -r requirements.txt

# Run everything
pytest -v

# Run only REST tests (fast, no network blocking)
pytest -v -m "not websocket"

# Run only WebSocket tests
pytest -v -m websocket

# Run a single file
pytest -v tests/test_rest_market_data.py

# Generate HTML report
pytest --html=report.html --self-contained-html
```

---

## Project layout

```
binance-api-tests/
├── README.md
├── requirements.txt
├── pytest.ini
├── conftest.py                       # fixtures: base URL, session, symbols-under-test
├── tests/
│   ├── test_rest_system.py
│   ├── test_rest_exchange_info.py
│   ├── test_rest_market_data.py
│   └── test_websocket_streams.py
├── utils/
│   └── binance_client.py             # thin REST + WebSocket wrappers (no API key needed)
└── .github/workflows/tests.yml       # GitHub Actions CI (runs on every push)
```

---

## Design choices

- **No API key, no signed endpoints.** This is a public-API suite — safe to run in CI without secrets. The signed-endpoint flow (HMAC SHA-256) is documented but not exercised here to keep the repo runnable for reviewers.
- **Parametrized symbols.** Every market-data test runs across `BTCUSDT`, `ETHUSDT`, `BNBUSDT` via `@pytest.mark.parametrize` — catches per-symbol regressions without copy-pasting tests.
- **WebSocket tests are time-boxed.** Each stream test collects N frames or times out after 10 s — never hangs CI.
- **Failure-friendly assertions.** Every assertion has a custom message that prints the offending payload — faster to triage than a bare `AssertionError`.

---

## CI

GitHub Actions runs the full REST suite on every push (`.github/workflows/tests.yml`). WebSocket tests run nightly to avoid burning rate limits during PR churn.

---

## What's next

- [ ] Add HMAC-signed account endpoints (testnet only) for order placement / cancel / query
- [ ] Add `pytest-benchmark` for latency tracking on `/depth` and `/ticker/24hr`
- [ ] Compare REST snapshot vs. WebSocket diff stream to detect feed gaps
- [ ] Dockerize and push to Docker Hub

---

## About me

**Shubham Suryawanshi** — Software Test Engineer, 3.6 yrs, FinTech / HFT trading
Nashik, India — open to global roles (Dubai, EU, ANZ, SEA, India, remote)
[linkedin.com/in/shubham-suryawanshi-FinTech](https://linkedin.com/in/shubham-suryawanshi-FinTech) · shubhamsuryawanshi9689@gmail.com
