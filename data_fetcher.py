"""
Data fetcher module with parallel request capability
"""
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

from config import (
    API_BASE_URL, 
    API_HEADERS, 
    TIMEFRAMES,
    PARALLEL_CONFIG,
    load_symbols
)


class DataFetcher:
    """Fetches OHLC data from WikiTrade API with parallel request support"""
    
    def __init__(self):
        self.symbols = load_symbols()
        self.base_url = API_BASE_URL
        self.headers = API_HEADERS.copy()
        self.cache = {}  # Simple cache: {(symbol_id, period): dataframe}
        self.cache_timeout = 30  # Cache validity in seconds
        self.cache_timestamps = {}
        
    def fetch_klines(self, symbol_id: str, period: str = '5m', limit: int = 300) -> Optional[pd.DataFrame]:
        """
        Fetch OHLC candlestick data for a single symbol
        
        Args:
            symbol_id: Symbol ID (e.g., "619557173490693")
            period: Timeframe (1m, 5m, 15m, 30m, 1h)
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, code
        """
        # Check cache first
        cache_key = (symbol_id, period)
        if cache_key in self.cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if time.time() - cache_time < self.cache_timeout:
                return self.cache[cache_key]
        
        # Small delay to avoid overwhelming API
        time.sleep(PARALLEL_CONFIG.get('request_delay', 0.05))
        
        # Get current timestamp in milliseconds
        import datetime
        end_timestamp = int(time.time() * 1000)
        
        payload = {
            "symbol": symbol_id,
            "period": period,
            "limit": limit,
            "end_timestamp": end_timestamp
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=PARALLEL_CONFIG['timeout']
            )
            
            if response.status_code != 200:
                print(f"✗ Error fetching {symbol_id}: HTTP {response.status_code}")
                return None
            
            # Parse JSON response (requests handles decompression automatically)
            try:
                data = response.json()
            except Exception as json_err:
                print(f"✗ JSON error for {symbol_id}: {json_err}")
                print(f"   Response text (first 200 chars): {response.text[:200]}")
                return None
            
            # Navigate the nested JSON structure
            klines_data = data.get('data', {}).get('simulationtradetemp', {}).get('klines', {}).get('data', {})
            
            if klines_data is None or not isinstance(klines_data, dict):
                # API returned error
                error_msg = data.get('data', {}).get('simulationtradetemp', {}).get('klines', {}).get('debug', 'Unknown error')
                if 'BadRequest' in str(error_msg):
                    return None  # Silent fail for BadRequest (common with expired/inactive symbols)
                return None
            
            klines_list = klines_data.get('list', [])
            
            if not klines_list:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(klines_list)
            
            # Rename columns for consistency
            df = df.rename(columns={
                'open_price': 'open',
                'close_price': 'close',
                'high_price': 'high',
                'low_price': 'low',
            })
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Add volume if available (might not be in response)
            if 'volume' not in df.columns:
                df['volume'] = 0
            
            # Sort by timestamp (oldest first)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Cache the result
            self.cache[cache_key] = df
            self.cache_timestamps[cache_key] = time.time()
            
            return df
            
        except requests.exceptions.Timeout:
            print(f"✗ Timeout fetching {symbol_id}")
            return None
        except Exception as e:
            print(f"✗ Error fetching {symbol_id}: {e}")
            return None
    
    def fetch_multiple_parallel(self, symbol_ids: List[str], period: str = '5m', limit: int = 300) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols in parallel with rate limiting
        
        Args:
            symbol_ids: List of symbol IDs to fetch
            period: Timeframe
            limit: Number of candles
            
        Returns:
            Dictionary mapping symbol_id to DataFrame
        """
        results = {}
        max_workers = PARALLEL_CONFIG['max_workers']
        batch_size = PARALLEL_CONFIG['batch_size']
        batch_delay = PARALLEL_CONFIG['batch_delay']
        
        total_symbols = len(symbol_ids)
        
        print(f"📊 Fetching {total_symbols} symbols on {period} timeframe...")
        print(f"   Strategy: {batch_size} symbols/batch, {batch_delay}s delay between batches")
        start_time = time.time()
        
        # Process in batches to avoid rate limits
        for batch_num, i in enumerate(range(0, total_symbols, batch_size), 1):
            batch_symbols = symbol_ids[i:i + batch_size]
            batch_results = {}
            
            print(f"\n   Batch {batch_num}/{(total_symbols-1)//batch_size + 1} ({len(batch_symbols)} symbols)...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit batch tasks
                future_to_symbol = {
                    executor.submit(self.fetch_klines, symbol_id, period, limit): symbol_id 
                    for symbol_id in batch_symbols
                }
                
                # Collect results
                for future in as_completed(future_to_symbol):
                    symbol_id = future_to_symbol[future]
                    ticker = self.symbols.get(symbol_id, symbol_id)
                    
                    try:
                        df = future.result()
                        if df is not None and not df.empty:
                            batch_results[symbol_id] = df
                            # Don't print every single one to reduce clutter
                        else:
                            pass  # Silently skip failed symbols
                    except Exception as e:
                        pass  # Silently handle errors
            
            results.update(batch_results)
            print(f"   ✓ Batch {batch_num}: {len(batch_results)}/{len(batch_symbols)} successful")
            
            # Delay before next batch (except for last batch)
            if i + batch_size < total_symbols:
                print(f"   ⏳ Waiting {batch_delay}s before next batch...")
                time.sleep(batch_delay)
        
        elapsed = time.time() - start_time
        success_rate = (len(results) / total_symbols * 100) if total_symbols > 0 else 0
        print(f"\n✓ Total: {len(results)}/{total_symbols} symbols ({success_rate:.1f}%) in {elapsed:.2f}s")
        
        return results
    
    def fetch_all_symbols(self, period: str = '5m', limit: int = 300, category: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for all symbols (or filtered by category)
        
        Args:
            period: Timeframe
            limit: Number of candles
            category: Optional category filter (crypto, forex, indices, commodities, metals)
            
        Returns:
            Dictionary mapping symbol_id to DataFrame
        """
        symbol_ids = list(self.symbols.keys())
        
        # Filter by category if specified
        if category:
            from config import get_category
            symbol_ids = [
                sid for sid in symbol_ids 
                if get_category(self.symbols[sid]) == category
            ]
            print(f"Filtering to {category}: {len(symbol_ids)} symbols")
        
        return self.fetch_multiple_parallel(symbol_ids, period, limit)
    
    def fetch_multi_timeframe(self, symbol_id: str, timeframes: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch multiple timeframes for a single symbol
        
        Args:
            symbol_id: Symbol ID
            timeframes: List of timeframes (default: ['5m', '15m', '1h'])
            
        Returns:
            Dictionary mapping timeframe to DataFrame
        """
        if timeframes is None:
            timeframes = ['5m', '15m', '1h']
        
        results = {}
        ticker = self.symbols.get(symbol_id, symbol_id)
        
        print(f"📊 Fetching {ticker} on {len(timeframes)} timeframes...")
        
        for tf in timeframes:
            df = self.fetch_klines(symbol_id, tf)
            if df is not None:
                results[tf] = df
                print(f"  ✓ {tf}: {len(df)} candles")
        
        return results
    
    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
        self.cache_timestamps.clear()
        print("✓ Cache cleared")


# Utility functions
def get_latest_price(df: pd.DataFrame) -> float:
    """Get the most recent close price from dataframe"""
    if df is None or df.empty:
        return 0.0
    return float(df.iloc[-1]['close'])


def get_price_change_pct(df: pd.DataFrame, periods: int = 20) -> float:
    """Calculate percentage price change over N periods"""
    if df is None or len(df) < periods:
        return 0.0
    
    old_price = float(df.iloc[-periods]['close'])
    new_price = float(df.iloc[-1]['close'])
    
    if old_price == 0:
        return 0.0
    
    return ((new_price - old_price) / old_price) * 100


if __name__ == "__main__":
    # Test the data fetcher
    fetcher = DataFetcher()
    
    print("\n=== Testing Single Symbol Fetch ===")
    # Test with SXPUSD (from your sample)
    test_symbol_id = "619557173490693"
    df = fetcher.fetch_klines(test_symbol_id, period='1h', limit=300)
    
    if df is not None:
        print(f"\n✓ Fetched {len(df)} candles")
        print(f"\nFirst candle:")
        print(df.head(1))
        print(f"\nLast candle:")
        print(df.tail(1))
        print(f"\nLatest price: {get_latest_price(df):.4f}")
        print(f"Price change (20 periods): {get_price_change_pct(df, 20):.2f}%")
    
    print("\n=== Testing Parallel Fetch (10 symbols) ===")
    # Test parallel fetch with first 10 symbols
    test_symbols = list(fetcher.symbols.keys())[:10]
    results = fetcher.fetch_multiple_parallel(test_symbols, period='5m')
    
    print(f"\n✓ Successfully fetched {len(results)} symbols")
    for symbol_id, df in results.items():
        ticker = fetcher.symbols[symbol_id]
        latest = get_latest_price(df)
        change = get_price_change_pct(df, 20)
        print(f"  {ticker}: ${latest:.4f} ({change:+.2f}%)")
