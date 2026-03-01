"""
Configuration module for trading competition system
"""
import json
import os
from pathlib import Path

# Project paths
PROJECT_DIR = Path(__file__).parent
SYMBOLS_FILE = PROJECT_DIR / "symbols_auto_mapped.json"

# API Configuration
API_BASE_URL = "https://wikitrade.interface002.com:32377/forexpayweb-v1/invoke-v3/tradequote"

# Headers for API requests
API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
    'Authorization': 'Bearer Ut3Yk8D87EMMbzuXkh4BQtQO1GKMVUwo',
    'tradetoken': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk0MTgzNDEsImlhdCI6MTc2OTMzMTk0MSwidXNlcklkIjoiMzkxNzU2NjQ2OCJ9.pVoL2lzNqrRNSFFOiPsNh0w6kTf07Vcz1qp5blH8RzQ',
    'wikibrokercode': '3837527770',
    'CountryCode': '356',
    'LanguageCode': 'en',
    'PreferredLanguageCode': 'en',
    'web-version': '5',
    'BasicData': '999,0,100,0,0,4435bbe86d160fd824938a1d1fc85a58,0',
    'Routes': 'simulationtradetemp$klines',
    'Origin': 'https://wttplay.worldtradingtournament.com',
    'Referer': 'https://wttplay.worldtradingtournament.com/',
}

# Timeframe configurations
TIMEFRAMES = {
    '1m': {'period': '1m', 'limit': 300},
    '5m': {'period': '5m', 'limit': 300},
    '15m': {'period': '15m', 'limit': 300},
    '30m': {'period': '30m', 'limit': 300},
    '1h': {'period': '1h', 'limit': 300},
}

# Trading strategy configuration
STRATEGY_CONFIG = {
    'scan_timeframe': '5m',      # Primary scanning timeframe
    'confirm_timeframe': '15m',   # Confirmation timeframe
    'trend_timeframe': '1h',      # Bigger trend context
    'scan_interval': 60,          # Seconds between scans
    'top_n_signals': 20,          # Show top N opportunities
}

# Risk management
RISK_CONFIG = {
    'max_risk_per_trade': 0.02,   # 2% per trade
    'stop_loss_atr_multiplier': 2.0,
    'take_profit_ratio': 2.0,     # 2:1 reward:risk
}

# Indicator parameters
INDICATOR_CONFIG = {
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'ema_fast': 9,
    'ema_slow': 21,
    'volume_ma_period': 20,
    'atr_period': 14,
}

# Load symbols
def load_symbols():
    """Load symbol mappings from JSON file"""
    try:
        with open(SYMBOLS_FILE, 'r') as f:
            symbols = json.load(f)
        print(f"✓ Loaded {len(symbols)} symbols")
        return symbols
    except Exception as e:
        print(f"✗ Error loading symbols: {e}")
        return {}

# Symbol categories (for filtering/analysis)
SYMBOL_CATEGORIES = {
    'indices': ['DJIUSD', 'SPXUSD', 'NDXUSD', 'DAXEUR', 'FTSGBP', 'NIKJPY', 'HSIHKD', 'ESXEUR', 'F40EUR', 'IBXEUR', 'ASXAUD', 'XINUSD'],
    'forex': ['EURUSD', 'GBPUSD', 'USDJPY'],
    'commodities': ['BRNUSD', 'WTIUSD', 'NGCUSD', 'CUCUSD'],
    'metals': ['XAUUSD', 'XAGUSD', 'XPTUSD', 'XPDUSD', 'XAUEUR', 'XAUGBP', 'XAUAUD', 'XAUCHF', 'XAGEUR', 'XAGGBP', 'XAGAUD', 'XAGCHF'],
    'crypto': []  # Everything else is crypto
}

def get_category(ticker):
    """Get category for a ticker"""
    for category, tickers in SYMBOL_CATEGORIES.items():
        if ticker in tickers:
            return category
    return 'crypto'

# Parallel fetching configuration
PARALLEL_CONFIG = {
    'max_workers': 10,            # Number of parallel requests (reduced to avoid rate limits)
    'batch_size': 30,             # Fetch symbols in batches of 30
    'batch_delay': 2.0,           # Delay between batches (seconds)
    'request_delay': 0.1,         # Small delay between individual requests
    'timeout': 10,                # Request timeout in seconds
    'retry_attempts': 2,          # Number of retries on failure
}

# Smart refresh intervals (in seconds)
# Different timeframes need different update frequencies
REFRESH_INTERVALS = {
    '1m': 60,      # Update 1m data every 60 seconds
    '5m': 120,     # Update 5m data every 2 minutes
    '15m': 300,    # Update 15m data every 5 minutes
    '1h': 900,     # Update 1h data every 15 minutes
}

if __name__ == "__main__":
    symbols = load_symbols()
    print(f"\nTotal symbols: {len(symbols)}")
    print(f"Sample: {list(symbols.items())[:5]}")
    
    # Count categories
    categories_count = {}
    for symbol_id, ticker in symbols.items():
        cat = get_category(ticker)
        categories_count[cat] = categories_count.get(cat, 0) + 1
    
    print("\nSymbols by category:")
    for cat, count in categories_count.items():
        print(f"  {cat}: {count}")
