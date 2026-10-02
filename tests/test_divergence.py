"""Tests for divergence calculations."""
from odds.models import Market, MatchedPair
from odds.divergence import calculate_divergence, filter_arb_opportunities, is_true_arb
from odds.match import match_markets
from odds.normalize import normalize_question

def test_calculate_divergence():
    pair = MatchedPair(
        market_a=Market(id="a", question="Q?", yes_price=0.75, source="kalshi"),
        market_b=Market(id="b", question="Q?", yes_price=0.65, source="polymarket"),
        match_score=0.95, spread=0.10)
    r = calculate_divergence(pair)
    assert r.spread == 0.10
    assert r.direction == "a_higher"
    assert r.potential_arb == 0.06  # 0.10 - 2*0.02

def test_filter_arb():
    pairs = [
        MatchedPair(market_a=Market(id="1",question="A",yes_price=0.50,source="k"),
                     market_b=Market(id="2",question="A",yes_price=0.48,source="p"), match_score=0.9, spread=0.02),
        MatchedPair(market_a=Market(id="3",question="B",yes_price=0.70,source="k"),
                     market_b=Market(id="4",question="B",yes_price=0.60,source="p"), match_score=0.9, spread=0.10),
    ]
    results = [calculate_divergence(p) for p in pairs]
    filtered = filter_arb_opportunities(results, min_spread=0.05)
    assert len(filtered) == 1
    assert filtered[0].spread == 0.10

def test_is_true_arb():
    assert is_true_arb(0.10)
    assert not is_true_arb(0.03)
    assert not is_true_arb(0.04)

def test_normalize_question():
    assert normalize_question("Will GPT-5 Launch?") == "will gpt5 launch"

def test_match_markets():
    a = [Market(id="1", question="Will GPT-5 be released in 2026?", yes_price=0.7, source="k")]
    b = [Market(id="2", question="GPT-5 released in 2026", yes_price=0.6, source="p")]
    pairs = match_markets(a, b, threshold=40)
    assert len(pairs) == 1
    assert pairs[0].spread > 0
