"""A static, in-code pricing table — see `docs/architecture/overview.md`'s
bounded-context notes: "treats provider pricing as a versioned, swappable
lookup table, not a hardcoded constant." This is the simplest adapter
satisfying that shape; a real deployment would back `PricingTable` with a
database table an operator can update without a redeploy.

**The dollar figures below are illustrative placeholders, not verified
current provider pricing.** Anthropic/OpenAI/Google list prices change
over time and vary by tier; wire this to your actual provider contract's
rates before trusting any cost figure this service produces. Ollama's
$0.00 is the one real fact here — a locally-run model has no per-token API
fee, whatever it costs you in compute.
"""

from __future__ import annotations

from cost_analytics.domain.entities import PricingRate

_WILDCARD = "*"

# provider -> model (or "*" for "any model from this provider") -> rate
_RATES: dict[str, dict[str, PricingRate]] = {
    "anthropic": {
        _WILDCARD: PricingRate(prompt_price_per_1k=0.003, completion_price_per_1k=0.015),
    },
    "openai": {
        _WILDCARD: PricingRate(prompt_price_per_1k=0.0025, completion_price_per_1k=0.010),
    },
    "gemini": {
        _WILDCARD: PricingRate(prompt_price_per_1k=0.00125, completion_price_per_1k=0.005),
    },
    "ollama": {
        _WILDCARD: PricingRate(prompt_price_per_1k=0.0, completion_price_per_1k=0.0),
    },
}


class StaticPricingTable:
    def get_rate(self, *, provider: str, model: str) -> PricingRate | None:
        provider_rates = _RATES.get(provider)
        if provider_rates is None:
            return None
        return provider_rates.get(model, provider_rates.get(_WILDCARD))
