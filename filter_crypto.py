#!/usr/bin/env python3
"""
Quick script to run scanner with CRYPTO ONLY
"""
import json
from config import get_category

# Load all symbols
with open('symbols_auto_mapped.json') as f:
    all_symbols = json.load(f)

# Filter for crypto only
crypto_symbols = {
    sid: ticker 
    for sid, ticker in all_symbols.items() 
    if get_category(ticker) == 'crypto'
}

print(f"✅ Found {len(crypto_symbols)} crypto symbols (24/7 markets)")
print(f"⏭️  Skipping {len(all_symbols) - len(crypto_symbols)} non-crypto (markets closed)")

# Save to temp file
with open('symbols_crypto_only.json', 'w') as f:
    json.dump(crypto_symbols, f, indent=2)

print(f"\n💾 Saved to symbols_crypto_only.json")
print(f"\nTo use: Edit main.py line that loads symbols")
