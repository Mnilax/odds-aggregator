from typer.testing import CliRunner

from odds import cli
from odds.match import match_markets
from odds.models import Market


def market(question, price=0.5, date=""):
    return Market(id="x", question=question, yes_price=price, close_date=date)


def test_similar_questions_with_different_numbers_are_rejected():
    assert match_markets([market("Bitcoin above $100000 in 2026?")],
                         [market("Bitcoin above $150000 in 2026?")], threshold=50) == []
    assert match_markets([market("GPT-5 released in 2026?")],
                         [market("GPT-5 released in 2027?")], threshold=50) == []


def test_incompatible_or_invalid_close_dates_are_rejected():
    a = [market("Will Q happen?", date="2026-12-31T00:00:00Z")]
    assert match_markets(a, [market("Will Q happen?", date="2027-12-31")]) == []
    assert match_markets(a, [market("Will Q happen?", date="invalid")]) == []
    assert len(match_markets(a, [market("Will Q happen?", date="2026-12-31")])) == 1


def test_documented_compare_command_and_live_pipeline(monkeypatch):
    runner = CliRunner()
    assert runner.invoke(cli.app, ["compare", "--dry-run", "--match-threshold", "80"]).exit_code == 0
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    async def kalshi_fetch(**kwargs):
        return [market("Question?", 0.75)]
    async def poly_fetch(**kwargs):
        return [market("Question?", 0.6)]
    monkeypatch.setattr(cli.kalshi, "fetch_markets", kalshi_fetch)
    monkeypatch.setattr(cli.polymarket, "fetch_markets", poly_fetch)
    result = runner.invoke(cli.app, ["compare", "--fee-rate", "0.01"])
    assert result.exit_code == 0, result.output
    assert "15.0%" in result.output and "13.0%" in result.output


def test_live_provider_error_is_nonzero(monkeypatch):
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    async def unavailable(**kwargs):
        raise RuntimeError("fixture offline")
    monkeypatch.setattr(cli.kalshi, "fetch_markets", unavailable)
    result = CliRunner().invoke(cli.app, ["compare"])
    assert result.exit_code == 1 and "fixture offline" in result.output
