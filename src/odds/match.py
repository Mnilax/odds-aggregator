"""Fuzzy matching of equivalent markets across platforms."""
from __future__ import annotations

import re
from datetime import UTC, datetime

from rapidfuzz import fuzz

from odds.models import Market, MatchedPair
from odds.normalize import normalize_question


def _compatible_events(a: Market, b: Market) -> bool:
    # A high text score cannot establish equivalence across differing strikes or event dates.
    if set(re.findall(r"\d+(?:\.\d+)?", a.question)) != set(re.findall(r"\d+(?:\.\d+)?", b.question)):
        return False
    if a.close_date and b.close_date:
        try:
            dates = [datetime.fromisoformat(date) for date in (a.close_date, b.close_date)]
            dates = [date.replace(tzinfo=UTC) if date.tzinfo is None else date for date in dates]
        except ValueError:
            return False
        if abs((dates[0] - dates[1]).total_seconds()) > 3 * 86400:
            return False
    return True

def match_markets(
    markets_a: list[Market], markets_b: list[Market],
    threshold: float = 75.0,
) -> list[MatchedPair]:
    """Match equivalent markets between two platforms using fuzzy matching."""
    if not 0 <= threshold <= 100:
        raise ValueError("threshold must be between 0 and 100")
    pairs = []
    used_b = set()

    for a in markets_a:
        best_score = 0.0
        best_b = None
        norm_a = normalize_question(a.question)

        for i, b in enumerate(markets_b):
            if i in used_b or not _compatible_events(a, b):
                continue
            norm_b = normalize_question(b.question)
            score = fuzz.token_sort_ratio(norm_a, norm_b)
            if score > best_score:
                best_score = score
                best_b = (i, b)

        if best_b and best_score >= threshold:
            idx, b = best_b
            used_b.add(idx)
            spread = abs(a.yes_price - b.yes_price)
            pairs.append(MatchedPair(
                market_a=a, market_b=b,
                match_score=best_score / 100,
                spread=round(spread, 4),
                arb_opportunity=spread > 0.05,
            ))

    return sorted(pairs, key=lambda p: p.spread, reverse=True)
