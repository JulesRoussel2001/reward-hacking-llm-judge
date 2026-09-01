"""Per-model list prices and per-call cost, shared by the runners."""

from __future__ import annotations

# USD per million tokens: (input, output).
# Cache read is 0.1x input; cache write (5-minute TTL) is 1.25x input.
PRICES = {
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-4-6": (3.00, 15.00),
}


def row_cost(usage: dict, model: str) -> float:
    """USD for one call from its usage block, at that model's prices."""
    if model not in PRICES:
        raise KeyError(f"no price entry for {model!r}; add one to PRICES")
    p_in, p_out = PRICES[model]
    p_cr, p_cw = p_in * 0.10, p_in * 1.25
    g = lambda k: (usage or {}).get(k) or 0
    return (
        g("input_tokens") * p_in
        + g("output_tokens") * p_out
        + g("cache_read_input_tokens") * p_cr
        + g("cache_creation_input_tokens") * p_cw
    ) / 1_000_000
