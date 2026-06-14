"""Kalshi market client."""
from __future__ import annotations
import httpx
from odds.models import Market

async def fetch_markets(limit: int = 100) -> list[Market]:
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://trading-api.kalshi.com/trade-api/v2/markets", params={"status": "open", "limit": limit})
        resp.raise_for_status()
        data = resp.json()
    return [Market(id=m.get("ticker",""), question=m.get("title",""), yes_price=m.get("yes_ask",50)/100,
        volume=m.get("volume",0), close_date=m.get("close_time",""),
        url=f"https://kalshi.com/markets/{m.get('ticker','')}", source="kalshi") for m in data.get("markets",[])]
