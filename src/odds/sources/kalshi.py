"""Public Kalshi market data; https://docs.kalshi.com/api-reference/market/get-markets."""
from __future__ import annotations

import os

import httpx

from odds.models import Market

DEFAULT_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"


def parse_market(item: dict) -> Market | None:
    """Read current dollar prices, with support for legacy cent fields."""
    price = item.get("yes_ask_dollars")
    if price is None and item.get("yes_ask") is not None:
        price = float(item["yes_ask"]) / 100
    if price is None or not item.get("ticker") or not item.get("title"):
        return None
    return Market(id=item["ticker"], question=item["title"], yes_price=float(price),
                  volume=float(item.get("volume_fp") or item.get("volume") or 0),
                  close_date=item.get("close_time") or "",
                  url="https://kalshi.com/markets/" + item["ticker"], source="kalshi")


async def fetch_markets(limit: int = 100) -> list[Market]:
    """Fetch one bounded page of open markets from the public API."""
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    base_url = os.getenv("KALSHI_API_URL", DEFAULT_BASE_URL).rstrip("/")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{base_url}/markets", params={"status": "open", "limit": limit})
        response.raise_for_status()
        data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get("markets"), list):
        raise TypeError("Invalid Kalshi markets response")
    markets = []
    for item in data["markets"][:limit]:
        if not isinstance(item, dict):
            continue
        try:
            market = parse_market(item)
        except (ValueError, TypeError, KeyError):
            continue
        if market is not None:
            markets.append(market)
    return markets
