"""Thin wrappers around Binance public REST + WebSocket endpoints.

Only public, unauthenticated calls — no API key needed. This keeps the
test suite runnable in CI without secrets.
"""
import json
import time
from typing import Any

import requests
import websocket


class BinanceREST:
    """Synchronous wrapper for Binance public REST endpoints."""

    def __init__(self, base_url: str = "https://api.binance.com",
                 session: requests.Session | None = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

    def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def ping(self) -> dict:
        return self._get("/api/v3/ping")

    def server_time(self) -> dict:
        return self._get("/api/v3/time")

    def exchange_info(self, symbol: str | None = None) -> dict:
        params = {"symbol": symbol} if symbol else None
        return self._get("/api/v3/exchangeInfo", params=params)

    def ticker_24hr(self, symbol: str) -> dict:
        return self._get("/api/v3/ticker/24hr", params={"symbol": symbol})

    def order_book(self, symbol: str, limit: int = 100) -> dict:
        return self._get("/api/v3/depth", params={"symbol": symbol, "limit": limit})

    def klines(self, symbol: str, interval: str = "1m", limit: int = 500) -> list:
        return self._get("/api/v3/klines",
                         params={"symbol": symbol, "interval": interval, "limit": limit})

    def recent_trades(self, symbol: str, limit: int = 500) -> list:
        return self._get("/api/v3/trades", params={"symbol": symbol, "limit": limit})

    def avg_price(self, symbol: str) -> dict:
        return self._get("/api/v3/avgPrice", params={"symbol": symbol})


class BinanceWS:
    """Minimal blocking WebSocket reader for Binance public streams.

    Usage:
        with BinanceWS("wss://stream.binance.com:9443/ws/btcusdt@trade") as ws:
            for msg in ws.recv_messages(count=5, timeout=10):
                ...
    """

    def __init__(self, url: str, connect_timeout: float = 10.0):
        self.url = url
        self.connect_timeout = connect_timeout
        self._ws: websocket.WebSocket | None = None

    def __enter__(self) -> "BinanceWS":
        self._ws = websocket.create_connection(self.url, timeout=self.connect_timeout)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._ws is not None:
            try:
                self._ws.close()
            finally:
                self._ws = None

    def recv_messages(self, count: int, timeout: float = 10.0) -> list[dict]:
        """Collect up to `count` JSON messages or stop at deadline."""
        assert self._ws is not None, "WebSocket not connected — use as context manager"
        deadline = time.monotonic() + timeout
        messages: list[dict] = []
        while len(messages) < count and time.monotonic() < deadline:
            remaining = max(0.1, deadline - time.monotonic())
            self._ws.settimeout(remaining)
            try:
                raw = self._ws.recv()
            except websocket.WebSocketTimeoutException:
                break
            messages.append(json.loads(raw))
        return messages
