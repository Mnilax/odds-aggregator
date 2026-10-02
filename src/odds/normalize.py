"""Normalize markets to unified schema."""
from __future__ import annotations

import re

from odds.models import Market


def normalize_question(q: str) -> str:
    """Normalize question text for matching."""
    q = q.lower().strip()
    q = re.sub(r"[^a-z0-9\s]", "", q)
    q = re.sub(r"\s+", " ", q)
    return q

def normalize_market(m: Market) -> Market:
    """Return market with normalized question for matching."""
    return Market(**{**m.model_dump(), "question": normalize_question(m.question)})
