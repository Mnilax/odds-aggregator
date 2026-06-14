"""Fuzzy matching of equivalent markets across platforms."""
from __future__ import annotations
from rapidfuzz import fuzz
from odds.models import Market, MatchedPair
from odds.normalize import normalize_question

def match_markets(
    markets_a: list[Market], markets_b: list[Market],
    threshold: float = 75.0,
) -> list[MatchedPair]:
    """Match equivalent markets between two platforms using fuzzy matching."""
    pairs = []
    used_b = set()

    for a in markets_a:
        best_score = 0.0
        best_b = None
        norm_a = normalize_question(a.question)

        for i, b in enumerate(markets_b):
            if i in used_b:
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
