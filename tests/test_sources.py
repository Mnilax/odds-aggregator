import asyncio

import httpx
import pytest

from odds.sources import kalshi, polymarket


def test_kalshi_dollar_prices_and_legacy_zero():
    assert kalshi.parse_market({"ticker": "K1", "title": "Q?", "yes_ask_dollars": "0.1234",
                                "volume_fp": "5.50"}).yes_price == 0.1234
    assert kalshi.parse_market({"ticker": "K1", "title": "Q?", "yes_ask": 0}).yes_price == 0
    assert kalshi.parse_market({"ticker": "K1", "title": "Q?"}) is None


def test_polymarket_yes_outcome_and_slug():
    item = {"conditionId": "P1", "question": "Q?", "outcomes": '["No", "Yes"]',
            "outcomePrices": '["0.8", "0.2"]', "slug": "question", "active": True}
    market = polymarket.parse_market(item)
    assert market.yes_price == 0.2
    assert market.url == "https://polymarket.com/market/question"
    item["closed"] = True
    assert polymarket.parse_market(item) is None


@pytest.mark.parametrize("provider", [kalshi, polymarket])
def test_mocked_http_response_skips_invalid_records(monkeypatch, provider):
    original_client = httpx.AsyncClient
    monkeypatch.delenv("KALSHI_API_URL", raising=False)
    monkeypatch.delenv("POLYMARKET_API_URL", raising=False)
    def handler(request):
        assert request.url.params["limit"] == "3"
        if provider is kalshi:
            assert request.url.host == "external-api.kalshi.com"
            return httpx.Response(200, json={"markets": [
                {"ticker": "K1", "title": "Q?", "yes_ask_dollars": "0.25"},
                {"ticker": "K2", "title": "Q?", "yes_ask_dollars": "nan"}, "invalid"]})
        assert request.url.host == "gamma-api.polymarket.com"
        assert request.url.path == "/markets/keyset"
        return httpx.Response(200, json={"markets": [
            {"conditionId": "P1", "question": "Q?", "outcomes": '["Yes", "No"]',
             "outcomePrices": '["0.4", "0.6"]'},
            {"conditionId": "P2", "question": "Q?", "outcomes": '["Yes", "No"]',
             "outcomePrices": "invalid"}, "invalid"]})
    monkeypatch.setattr(provider.httpx, "AsyncClient",
                        lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    markets = asyncio.run(provider.fetch_markets(limit=3))
    assert len(markets) == 1


@pytest.mark.parametrize("provider", [kalshi, polymarket])
def test_api_http_errors_are_not_empty_successes(monkeypatch, provider):
    original_client = httpx.AsyncClient
    monkeypatch.setattr(provider.httpx, "AsyncClient",
                        lambda **kwargs: original_client(transport=httpx.MockTransport(
                            lambda request: httpx.Response(503)), **kwargs))
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(provider.fetch_markets())
