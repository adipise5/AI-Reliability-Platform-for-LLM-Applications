from __future__ import annotations

from cost_analytics.infrastructure.pricing import StaticPricingTable


def test_get_rate_falls_back_to_the_provider_wildcard():
    table = StaticPricingTable()

    rate = table.get_rate(provider="anthropic", model="some-future-claude-model")

    assert rate is not None
    assert rate.prompt_price_per_1k > 0


def test_get_rate_returns_none_for_an_unknown_provider():
    table = StaticPricingTable()

    assert table.get_rate(provider="totally-unknown-vendor", model="x") is None


def test_ollama_is_priced_at_zero():
    table = StaticPricingTable()

    rate = table.get_rate(provider="ollama", model="llama3.1")

    assert rate is not None
    assert rate.prompt_price_per_1k == 0.0
    assert rate.completion_price_per_1k == 0.0


def test_pricing_rate_cost_for_computes_the_blended_cost():
    from cost_analytics.domain.entities import PricingRate

    rate = PricingRate(prompt_price_per_1k=1.0, completion_price_per_1k=2.0)

    cost = rate.cost_for(prompt_tokens=2000, completion_tokens=1000)

    assert cost == 2.0 + 2.0
