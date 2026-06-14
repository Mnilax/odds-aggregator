# Cross-Platform Odds Aggregator

Pulls prediction markets from Polymarket + Kalshi, normalizes to a unified schema, fuzzy-matches equivalent markets, and calculates price divergences / arb windows.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

> ⚠️ **Arb in prediction markets is rarely "free"** — consider fees, liquidity, slippage, and resolve-time risk before trading. This tool finds divergences; it does not guarantee profit.

![Divergences](assets/divergences.svg)

## Features

- **Multi-source** — Kalshi REST + Polymarket CLOB clients
- **Fuzzy matching** — rapidfuzz token sort ratio with configurable threshold
- **Arb detection** — spread calculation with fee-aware net arb
- **Rich terminal** — ranked table of divergences with match confidence

## Install

```bash
pip install -e .
```

## Quickstart

### 1. Configure API keys

```bash
cp .env.example .env
```

Add your Kalshi and/or Polymarket API keys to `.env`. Without keys, use `--dry-run`.

### 2. Find divergences

```bash
# Compare markets across platforms, min 5% spread
python -m odds.cli compare --min-spread 0.05

# Demo with sample data (no API keys needed)
python -m odds.cli compare --dry-run

# Custom match threshold
python -m odds.cli compare --min-spread 0.03 --match-threshold 80
```

### Example Output

```
Cross-Platform Divergences

  #  Market                          Kalshi  Polymarket  Spread  Match  Net Arb
  1  Trump wins 2028 popular vote     0.38        0.31   +7.0%    94%    +2.1%
  2  Fed rate cut before Sep 2025     0.62        0.68   −6.0%    91%    −0.9%
  3  Bitcoin > $150K by Dec 2025      0.22        0.28   −6.0%    89%    −1.2%

5 matched markets | min spread: 5% | fees: Kalshi 7%, Polymarket 2%
```

## How It Works

### Market Matching

Markets on Kalshi and Polymarket describe the same events with different wording. The aggregator:
1. **Normalizes** question text (lowercase, strip dates, remove platform-specific prefixes)
2. **Fuzzy-matches** using `rapidfuzz.fuzz.token_sort_ratio` with a configurable threshold (default: 80%)
3. **Validates** matched pairs by checking category and resolution date proximity

### Spread & Arb Calculation

- **Spread** = `price_kalshi − price_polymarket` (positive = Kalshi is higher)
- **Net arb** = spread minus platform fees (Kalshi ~7% on profit, Polymarket ~2%)
- A positive net arb means you could theoretically buy on the cheaper platform and sell on the more expensive one for a profit after fees

### Fee Model

| Platform | Fee Structure |
|----------|--------------|
| Kalshi | ~7% on net profit |
| Polymarket | ~2% on winning shares |

Net arb accounts for both sides. Most small spreads become negative after fees.

## Architecture

```
src/odds/
├── cli.py              # Typer CLI: compare command
├── divergence.py       # Spread + net arb calculation
├── match.py            # Fuzzy matching with rapidfuzz
├── models.py           # Unified market schema
├── normalize.py        # Question text normalization
└── sources/
    ├── kalshi.py        # Kalshi REST API client
    └── polymarket.py    # Polymarket CLOB client
```

## Roadmap

- [ ] Real-time monitoring with configurable refresh interval
- [ ] Slack/Telegram alerts for actionable arbs
- [ ] Historical spread tracking
- [ ] Additional sources (Metaculus, PredictIt)

## License

MIT
