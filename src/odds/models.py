"""Shared data models."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Market(BaseModel):
    id: str
    question: str
    yes_price: float = Field(ge=0, le=1, allow_inf_nan=False)
    volume: float = Field(default=0, ge=0, allow_inf_nan=False)
    close_date: str = ""
    url: str = ""
    source: str = ""

class MatchedPair(BaseModel):
    market_a: Market
    market_b: Market
    match_score: float = Field(ge=0, le=1)
    spread: float = 0
    arb_opportunity: bool = False

class DivergenceResult(BaseModel):
    pair: MatchedPair
    spread: float
    direction: str  # "a_higher" or "b_higher"
    potential_arb: float = 0  # after fees
