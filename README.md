# Trading Competition Scanner

Multi-timeframe trading analysis system for World Trading Tournament competition.

## 🚀 Quick Start (Competition Day)
# WTT Suggestion Scanner (Suggestion-only)

This repository provides a suggestion engine that continuously (or on-demand) fetches market data, computes technical indicators, scores symbols, and outputs ranked suggestions for manual review. Automatic order execution (auto-trading) has been removed.

## Key points

- Purpose: Suggest symbols (crypto or other mapped instruments) to consider during events like the World Trading Tournament (WTT).
- No auto-trading: all execution is manual; the auto-execution components were removed for safety and because they were not implemented.
- Cleaned: old `logs/` and runtime caches were removed to reduce repository noise.

## Quick Start

1. Update API tokens:

```bash
python3 update_tokens.py
```

2. Verify API connectivity:

```bash
python3 test_api.py
```

3. Run the scanner:

```bash
python3 main.py           # full scan
python3 main.py --test    # limited symbols (dev)
python3 main.py --once    # single run
```

Common options: `--test`, `--once`, `--interval N`, `--top N`.

## Requirements

```bash
pip install pandas numpy requests
```

Optional (for nicer terminal output):

```bash
pip install rich
```

## Files kept (and what they do)

- `config.py` — API credentials, symbol lists, timeframes, and tunable parameters
- `update_tokens.py` — Helper to refresh API tokens
- `test_api.py` — API connectivity tester
- `data_fetcher.py` — Parallelized data collection layer
- `indicators.py` — RSI, MACD, EMA, ATR and other indicator implementations
- `scanner.py` — Multi-timeframe signal detection and scoring
- `filter_crypto.py` — Helpers for crypto-only filtering (optional)
- `dashboard.py` — Terminal display logic for suggestions
- `main.py` — CLI runner / orchestrator
- `symbols_auto_mapped.json`, `symbols_crypto_only.json` — symbol maps

## What I removed

Removed files related to automatic trading execution and their docs:

- `auto_trader.py`
- `auto_trader_interactive.py`
- `AUTO_TRADER_GUIDE.md`
- `AUTO_TRADER_SETUP.md`
- `AUTO_TRADER_TEST.md`

Additionally, runtime `logs/` and Python cache directories were deleted from the workspace.

## Configuration

Edit `config.py` to customize:

- Symbols to scan
- Timeframes (default: 5m, 15m, 1h)
- Indicator periods and scoring thresholds
- Concurrency / rate-limiting settings

## Typical workflow

1. Update tokens and confirm connectivity.
2. Run `main.py --test --once` during development to validate outputs.
3. For live monitoring, run `main.py` (optionally with `--interval N`).
4. Manually review the top suggestions and execute trades on your chosen platform.

## Development notes

- The scanner computes multi-timeframe alignment and momentum indicators, then ranks symbols by a composite score.
- The codebase is intentionally split: fetching, indicator calculations, scanning logic, and presentation are modular.

## Next steps (offer)

- I can archive the removed logs into a zip before permanent deletion.
- I can further prune docs or consolidate the scanner into a single CLI script.
- I can expand this README with sample outputs, configuration examples, and developer notes.

---

If you want any deleted files restored or prefer a different cleanup scope, tell me which files and I will revert or archive them.

## Full Guide — Usage, Tokens, and Configuration

This section consolidates the information previously scattered across project docs. Read each short subsection and follow the examples.

### 1) Purpose

This project scrapes market data, computes technical indicators across multiple timeframes, ranks symbols by a composite score, and outputs suggestions for manual review. It explicitly does not place trades.

### 2) Installation

Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install pandas numpy requests
```

Optional niceties:

```bash
pip install rich
```

### 3) Bearer token & API credentials

The scanner requires valid API credentials to fetch market data. There are two supported approaches:

- Recommended: use `update_tokens.py` which helps fetch and write required tokens into `config.py` or a local `.env` that `config.py` reads.
- Manual: copy the `Authorization` Bearer header and any `tradetoken` JWT from your browser's DevTools (Network tab) when you make a request to the exchange's API (e.g., a `tradequote` request). Paste those values into `config.py` fields: `AUTHORIZATION` and `TRADETOKEN` (or follow the variable names used in your `config.py`).

Important security notes:

- Never commit tokens to version control. Use `.gitignore` (already added) to exclude `.env` or other token files.
- Keep tokens restricted and rotate them if leaked.

Example `config.py` snippet (safe pattern — prefer environment variables):

```py
import os

AUTHORIZATION = os.getenv('AUTHORIZATION')
TRADETOKEN = os.getenv('TRADETOKEN')

# fallback for local dev only (NOT for commits)
# AUTHORIZATION = 'Bearer eyJ...'
# TRADETOKEN = 'eyJ...'
```

To set env vars in the shell before running the scanner:

```bash
export AUTHORIZATION='Bearer eyJ...'
export TRADETOKEN='eyJ...'
python3 main.py --test --once
```

### 4) Running the scanner

Development run (few symbols):

```bash
python3 main.py --test --once
```

Continuous monitoring:

```bash
python3 main.py --interval 60
```

Common CLI options:

- `--test` — use a reduced symbol set for fast iteration
- `--once` — run one scan and exit
- `--interval N` — rescan every N seconds
- `--top N` — show top N suggestions

### 5) Configuration options

Open `config.py` to tune:

- `SYMBOLS` or symbol file path (e.g., `symbols_crypto_only.json`)
- Timeframes (default: `5m`, `15m`, `1h`)
- Indicator periods (RSI length, MACD params, EMA lengths)
- Scoring weights and thresholds
- Logging preferences (enable/disable file logging)

### 6) Output and interpretation

The scanner prints a ranked table with: ticker, signal type, score, suggested entry/stop/target (if available), and timeframe alignment. Use the score and timeframe alignment to prioritize manual review.

Example output line:

```
# 1 BTC-USD  BUY  82  Entry:  95000  Stop: 94000  Target: 98000  5m↑ 15m↑ 1h↑  reason: Momentum + Volume
```

Score guidance:

- > 70: strong candidate (review first)
- 50–70: moderate — check context and risk
- < 50: informational only

### 7) Troubleshooting

- "BadRequest" or no data: tokens expired — run `python3 update_tokens.py` and re-test with `python3 test_api.py`.
- Rate limits: increase `--interval` or lower concurrent workers in `config.py`.
- Missing symbol data: verify symbol mapping files (e.g., `symbols_auto_mapped.json`).

### 8) Security & Safety

- This repository will not and should not execute trades automatically.
- Keep API credentials private and use environment variables in production.

### 9) Development notes

- The code is modular (fetch -> indicators -> scan -> display). To change scoring, edit `scanner.py`.
- To add new indicators, implement them in `indicators.py` and integrate into the scoring function.

---

If you want, I can now:

- Expand the README with sample run outputs and annotated examples, or
- Create a `requirements.txt` and a small `examples/` folder with sample outputs, or
- Archive removed docs into a zip and upload it into the repo for safekeeping.
