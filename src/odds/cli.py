"""CLI for odds aggregator."""
from __future__ import annotations

import asyncio

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from odds.divergence import calculate_divergence, filter_arb_opportunities
from odds.match import match_markets
from odds.models import Market
from odds.sources import kalshi, polymarket

app = typer.Typer(help="Cross-platform Odds Aggregator")
console = Console()

@app.callback()
def commands():
    """Compare public markets across platforms."""


async def _live_pairs(limit, match_threshold):
    markets_a, markets_b = await asyncio.gather(kalshi.fetch_markets(limit=limit),
                                               polymarket.fetch_markets(limit=limit))
    return match_markets(markets_a, markets_b, threshold=match_threshold)

@app.command()
def compare(min_spread: float = typer.Option(0.05, "--min-spread", min=0, max=1),
            dry_run: bool = typer.Option(False, "--dry-run"),
            match_threshold: float = typer.Option(80, "--match-threshold", min=0, max=100),
            limit: int = typer.Option(100, "--limit", min=1, max=1000),
            fee_rate: float = typer.Option(0.02, "--fee-rate", min=0, max=1)):
    """Compare markets across platforms and find divergences."""
    if dry_run:
        _demo_output(min_spread, match_threshold, fee_rate)
    else:
        load_dotenv()
        try:
            pairs = asyncio.run(_live_pairs(limit, match_threshold))
            _render_pairs(pairs, min_spread, fee_rate)
            if not pairs:
                console.print("No candidate matches in the bounded source pages.")
        except Exception as error:  # noqa: BLE001 - CLI boundary reports source failures.
            console.print(f"Comparison failed: {error}", markup=False)
            raise typer.Exit(1)

def _demo_output(min_spread: float, match_threshold: float, fee_rate: float):
    a = [Market(id="k1", question="Will GPT-5 launch by Dec 2026?", yes_price=0.72, source="kalshi", url="https://kalshi.com"),
         Market(id="k2", question="EU AI Act enforcement in 2026?", yes_price=0.88, source="kalshi", url="https://kalshi.com")]
    b = [Market(id="p1", question="Will GPT-5 launch by Dec 2026?", yes_price=0.65, source="polymarket", url="https://polymarket.com"),
         Market(id="p2", question="EU AI Act enforcement begins 2026", yes_price=0.91, source="polymarket", url="https://polymarket.com")]
    pairs = match_markets(a, b, threshold=match_threshold)
    _render_pairs(pairs, min_spread, fee_rate)


def _render_pairs(pairs, min_spread, fee_rate):
    results = [calculate_divergence(p, fee_rate=fee_rate) for p in pairs]
    filtered = filter_arb_opportunities(results, min_spread)
    table = Table(title="Cross-Platform Divergences")
    table.add_column("Question"); table.add_column("Kalshi", justify="center"); table.add_column("Polymarket", justify="center")
    table.add_column("Spread", justify="center", style="bold"); table.add_column("Fee-adjusted estimate", justify="center"); table.add_column("Match", justify="center")
    for r in filtered:
        table.add_row(r.pair.market_a.question[:45], f"{r.pair.market_a.yes_price:.0%}", f"{r.pair.market_b.yes_price:.0%}",
            f"{r.spread:.1%}", f"{r.potential_arb:.1%}", f"{r.pair.match_score:.0%}")
    console.print(table)
    console.print("\n[dim]⚠️ Arb in prediction markets is rarely free (fees, liquidity, resolve time)[/dim]")

def main(): app()
if __name__ == "__main__": main()
