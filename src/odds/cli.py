"""CLI for odds aggregator."""
from __future__ import annotations
import typer
from rich.console import Console
from rich.table import Table
from odds.models import Market, MatchedPair
from odds.divergence import calculate_divergence, filter_arb_opportunities
from odds.match import match_markets

app = typer.Typer(help="Cross-platform Odds Aggregator")
console = Console()

@app.command()
def compare(min_spread: float = typer.Option(0.05, "--min-spread"),
            dry_run: bool = typer.Option(False, "--dry-run")):
    """Compare markets across platforms and find divergences."""
    if dry_run:
        _demo_output(min_spread)
    else:
        console.print("[yellow]Set API access in .env for live data[/yellow]")

def _demo_output(min_spread: float):
    a = [Market(id="k1", question="Will GPT-5 launch by Dec 2026?", yes_price=0.72, source="kalshi", url="https://kalshi.com"),
         Market(id="k2", question="EU AI Act enforcement in 2026?", yes_price=0.88, source="kalshi", url="https://kalshi.com")]
    b = [Market(id="p1", question="GPT-5 released before January 2027", yes_price=0.65, source="polymarket", url="https://polymarket.com"),
         Market(id="p2", question="EU AI Act enforcement begins 2026", yes_price=0.91, source="polymarket", url="https://polymarket.com")]
    pairs = match_markets(a, b, threshold=50)
    results = [calculate_divergence(p) for p in pairs]
    filtered = filter_arb_opportunities(results, min_spread)
    table = Table(title="Cross-Platform Divergences")
    table.add_column("Question"); table.add_column("Kalshi", justify="center"); table.add_column("Polymarket", justify="center")
    table.add_column("Spread", justify="center", style="bold"); table.add_column("Net Arb", justify="center"); table.add_column("Match", justify="center")
    for r in filtered:
        table.add_row(r.pair.market_a.question[:45], f"{r.pair.market_a.yes_price:.0%}", f"{r.pair.market_b.yes_price:.0%}",
            f"{r.spread:.1%}", f"{r.potential_arb:.1%}", f"{r.pair.match_score:.0%}")
    console.print(table)
    console.print("\n[dim]⚠️ Arb in prediction markets is rarely free (fees, liquidity, resolve time)[/dim]")

def main(): app()
if __name__ == "__main__": main()
