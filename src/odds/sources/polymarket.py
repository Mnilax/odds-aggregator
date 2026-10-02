"""Public Polymarket Gamma data; https://docs.polymarket.com/market-data/market-details."""
from __future__ import annotations

import json
import os

import httpx

from odds.models import Market

DEFAULT_BASE_URL = "https://gamma-api.polymarket.com"


def parse_market(item: dict) -> Market | None:
    """Match YES by outcome label rather than assuming array ordering."""
    if item.get("closed") or item.get("active") is False:
        return None
    labels = item.get("outcomes", [])
    prices = item.get("outcomePrices", [])
    labels = json.loads(labels) if isinstance(labels, str) else labels
    prices = json.loads(prices) if isinstance(prices, str) else prices
    if not isinstance(labels, list) or not isinstance(prices, list) or len(labels) != len(prices):
        return None
    yes_indices = [i for i, label in enumerate(labels) if str(label).lower() == "yes"]
    if len(yes_indices) != 1 or not item.get("question") or not item.get("conditionId"):
        return None
    slug = item.get("slug")
    return Market(id=item["conditionId"], question=item["question"],
                  yes_price=float(prices[yes_indices[0]]), volume=float(item.get("volume") or 0),
                  close_date=item.get("endDate") or item.get("endDateIso") or "",
                  url=f"https://polymarket.com/market/{slug}" if slug else "",
                  source="polymarket")


async def fetch_markets(limit: int = 100) -> list[Market]:
    """Fetch one bounded page of active markets from the public Gamma API."""
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    base_url = os.getenv("POLYMARKET_API_URL", DEFAULT_BASE_URL).rstrip("/")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{base_url}/markets/keyset",
                                    params={"limit": limit, "active": "true", "closed": "false"})
        response.raise_for_status()
        data = response.json()
    items = data.get("markets") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise TypeError("Invalid Polymarket markets response")
    markets = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        try:
            market = parse_market(item)
        except (ValueError, TypeError, KeyError):
            continue
        if market is not None:
            markets.append(market)
    return markets
