"""Polymarket CLOB client."""
from __future__ import annotations
import httpx
from odds.models import Market

async def fetch_markets(limit: int = 100) -> list[Market]:
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://clob.polymarket.com/markets", params={"limit": limit, "active": True})
        resp.raise_for_status()
        data = resp.json()
    items = data if isinstance(data, list) else data.get("data", [])
    return [Market(id=m.get("condition_id",""), question=m.get("question",""),
        yes_price=float(m.get("tokens",[{}])[0].get("price",0.5)) if m.get("tokens") else 0.5,
        volume=float(m.get("volume",0)), close_date=m.get("end_date_iso",""),
        url=f"https://polymarket.com/event/{m.get('condition_id','')}", source="polymarket") for m in items]
