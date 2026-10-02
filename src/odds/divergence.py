"""Divergence and arb calculations — pure functions."""
from __future__ import annotations

from odds.models import DivergenceResult, MatchedPair

DEFAULT_FEE_RATE = 0.02  # 2% per side

def calculate_divergence(pair: MatchedPair, fee_rate: float = DEFAULT_FEE_RATE) -> DivergenceResult:
    """Calculate spread and potential arb for a matched pair."""
    if not 0 <= fee_rate <= 1:
        raise ValueError("fee_rate must be between 0 and 1")
    spread = pair.market_a.yes_price - pair.market_b.yes_price
    direction = "a_higher" if spread > 0 else "b_higher" if spread < 0 else "equal"
    gross_arb = abs(spread)
    net_arb = max(0, gross_arb - 2 * fee_rate)
    return DivergenceResult(pair=pair, spread=round(abs(spread), 4), direction=direction, potential_arb=round(net_arb, 4))

def filter_arb_opportunities(results: list[DivergenceResult], min_spread: float = 0.05) -> list[DivergenceResult]:
    """Filter and rank arb opportunities."""
    filtered = [r for r in results if r.spread >= min_spread]
    return sorted(filtered, key=lambda r: r.potential_arb, reverse=True)

def is_true_arb(spread: float, fee_rate: float = DEFAULT_FEE_RATE) -> bool:
    """Check if spread exceeds fees for a true arb."""
    return spread > 2 * fee_rate
