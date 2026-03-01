"""
Multi-timeframe Scanner - Identifies trading opportunities
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time

from data_fetcher import DataFetcher, get_latest_price
from indicators import (
    calculate_rsi, calculate_macd, calculate_ema, 
    calculate_atr, calculate_volume_ratio, 
    identify_trend, calculate_momentum_score
)
from config import load_symbols, STRATEGY_CONFIG, INDICATOR_CONFIG


@dataclass
class TradingSignal:
    """Trading signal with all relevant information"""
    symbol_id: str
    ticker: str
    signal_type: str  # 'BUY', 'SELL', or 'NEUTRAL'
    score: float  # 0-100
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframe_alignment: str  # '5m+15m+1h' etc
    reason: List[str]  # List of reasons for the signal
    timestamp: str
    
    def __str__(self):
        return f"{self.ticker} {self.signal_type} @ {self.entry_price:.4f} (Score: {self.score:.1f})"


class MultiTimeframeScanner:
    """Scans multiple symbols across multiple timeframes with smart caching"""
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.symbols = load_symbols()
        
        # Cache for multi-timeframe data
        self.multi_tf_cache = {}
        self.cache_timestamps = {}  # Track when each timeframe was last fetched
        
        # Timeframes to analyze
        self.scan_tf = STRATEGY_CONFIG['scan_timeframe']
        self.confirm_tf = STRATEGY_CONFIG['confirm_timeframe']
        self.trend_tf = STRATEGY_CONFIG['trend_timeframe']
        
    def analyze_single_timeframe(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """
        Analyze a single timeframe and return signal components
        
        Returns dict with:
        - trend: UPTREND, DOWNTREND, NEUTRAL
        - rsi: RSI value
        - macd_signal: bullish/bearish/neutral
        - volume_signal: high/normal/low
        - momentum_score: 0-100
        """
        if df is None or len(df) < 50:
            return None
        
        # Calculate indicators
        rsi = calculate_rsi(df)
        macd_line, macd_signal, macd_hist = calculate_macd(df)
        ema_9 = calculate_ema(df, 9)
        ema_21 = calculate_ema(df, 21)
        volume_ratio = calculate_volume_ratio(df)
        trend = identify_trend(df)
        momentum = calculate_momentum_score(df)
        
        # Get latest values
        latest_rsi = rsi.iloc[-1] if not rsi.empty else 50
        latest_macd_hist = macd_hist.iloc[-1] if not macd_hist.empty else 0
        latest_volume_ratio = volume_ratio.iloc[-1] if not volume_ratio.empty else 1
        latest_ema_9 = ema_9.iloc[-1] if not ema_9.empty else 0
        latest_ema_21 = ema_21.iloc[-1] if not ema_21.empty else 0
        
        # Determine signals
        macd_signal_type = 'bullish' if latest_macd_hist > 0 else 'bearish'
        volume_signal_type = 'high' if latest_volume_ratio > 1.5 else 'normal' if latest_volume_ratio > 0.5 else 'low'
        
        return {
            'trend': trend,
            'rsi': latest_rsi,
            'macd_signal': macd_signal_type,
            'macd_hist': latest_macd_hist,
            'volume_signal': volume_signal_type,
            'volume_ratio': latest_volume_ratio,
            'ema_9': latest_ema_9,
            'ema_21': latest_ema_21,
            'momentum_score': momentum,
            'price': df['close'].iloc[-1]
        }
    
    def generate_signal(self, symbol_id: str, multi_tf_data: Dict[str, pd.DataFrame]) -> Optional[TradingSignal]:
        """
        Generate trading signal based on multi-timeframe analysis
        
        Args:
            symbol_id: Symbol ID
            multi_tf_data: Dict mapping timeframe to DataFrame
            
        Returns:
            TradingSignal or None
        """
        ticker = self.symbols.get(symbol_id, symbol_id)
        
        # Analyze each timeframe
        scan_analysis = self.analyze_single_timeframe(multi_tf_data.get(self.scan_tf), self.scan_tf)
        confirm_analysis = self.analyze_single_timeframe(multi_tf_data.get(self.confirm_tf), self.confirm_tf)
        trend_analysis = self.analyze_single_timeframe(multi_tf_data.get(self.trend_tf), self.trend_tf)
        
        if not all([scan_analysis, confirm_analysis, trend_analysis]):
            return None
        
        # Decision logic
        reasons = []
        score = 0
        signal_type = 'NEUTRAL'
        
        # 1. Trend alignment (30 points)
        trend_score = 0
        if trend_analysis['trend'] == 'UPTREND':
            trend_score += 15
            reasons.append(f"1h uptrend")
        elif trend_analysis['trend'] == 'DOWNTREND':
            trend_score -= 15
            reasons.append(f"1h downtrend")
        
        if confirm_analysis['trend'] == 'UPTREND':
            trend_score += 15
            reasons.append(f"15m uptrend")
        elif confirm_analysis['trend'] == 'DOWNTREND':
            trend_score -= 15
            reasons.append(f"15m downtrend")
        
        score += abs(trend_score)
        
        # 2. Momentum (30 points)
        momentum_score = scan_analysis['momentum_score']
        if momentum_score > 60:
            score += 30
            reasons.append(f"Strong momentum ({momentum_score:.0f})")
        elif momentum_score < 40:
            score += 30
            reasons.append(f"Strong bearish momentum ({momentum_score:.0f})")
        else:
            score += (abs(momentum_score - 50) / 10) * 30  # Partial credit
        
        # 3. RSI conditions (20 points)
        rsi = scan_analysis['rsi']
        if rsi < 30:
            score += 20
            reasons.append(f"RSI oversold ({rsi:.0f})")
        elif rsi > 70:
            score += 20
            reasons.append(f"RSI overbought ({rsi:.0f})")
        elif 40 < rsi < 60:
            score += 5  # Neutral RSI is less interesting
        else:
            score += 10  # Moderate RSI
        
        # 4. Volume confirmation (20 points)
        if scan_analysis['volume_ratio'] > 1.5:
            score += 20
            reasons.append(f"High volume ({scan_analysis['volume_ratio']:.1f}x)")
        elif scan_analysis['volume_ratio'] > 1.0:
            score += 10
        
        # Determine signal type
        if trend_score > 20 and momentum_score > 55:
            signal_type = 'BUY'
        elif trend_score < -20 and momentum_score < 45:
            signal_type = 'SELL'
        elif abs(trend_score) > 20:
            signal_type = 'BUY' if trend_score > 0 else 'SELL'
        
        # Calculate entry, stop-loss, take-profit
        entry_price = scan_analysis['price']
        
        # Use ATR for stop-loss
        atr = calculate_atr(multi_tf_data[self.scan_tf])
        latest_atr = atr.iloc[-1] if not atr.empty else entry_price * 0.02
        
        if signal_type == 'BUY':
            stop_loss = entry_price - (latest_atr * 2)
            take_profit = entry_price + (latest_atr * 4)  # 2:1 reward:risk
        elif signal_type == 'SELL':
            stop_loss = entry_price + (latest_atr * 2)
            take_profit = entry_price - (latest_atr * 4)
        else:
            stop_loss = entry_price - (latest_atr * 2)
            take_profit = entry_price + (latest_atr * 2)
        
        # Timeframe alignment
        alignment_parts = []
        for tf, analysis in [(self.scan_tf, scan_analysis), (self.confirm_tf, confirm_analysis), (self.trend_tf, trend_analysis)]:
            if analysis['trend'] == 'UPTREND':
                alignment_parts.append(f"{tf}↑")
            elif analysis['trend'] == 'DOWNTREND':
                alignment_parts.append(f"{tf}↓")
            else:
                alignment_parts.append(f"{tf}→")
        
        timeframe_alignment = " ".join(alignment_parts)
        
        return TradingSignal(
            symbol_id=symbol_id,
            ticker=ticker,
            signal_type=signal_type,
            score=min(100, score),
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timeframe_alignment=timeframe_alignment,
            reason=reasons,
            timestamp=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def scan_all(self, max_symbols: Optional[int] = None, force_refresh: bool = False) -> List[TradingSignal]:
        """
        Scan all symbols and return ranked signals with smart caching
        
        Args:
            max_symbols: Limit number of symbols to scan (for testing)
            force_refresh: Force refresh all timeframes (ignore cache)
            
        Returns:
            List of TradingSignals, sorted by score (highest first)
        """
        from config import REFRESH_INTERVALS
        
        print(f"\n{'='*60}")
        print(f"🔍 MULTI-TIMEFRAME SCANNER")
        print(f"{'='*60}")
        
        symbol_ids = list(self.symbols.keys())
        if max_symbols:
            symbol_ids = symbol_ids[:max_symbols]
        
        print(f"Scanning {len(symbol_ids)} symbols across {self.scan_tf}, {self.confirm_tf}, {self.trend_tf}...")
        
        all_signals = []
        current_time = time.time()
        
        # Fetch data for all symbols on all timeframes (with smart refresh)
        timeframes = [self.scan_tf, self.confirm_tf, self.trend_tf]
        
        for tf in timeframes:
            # Check if we need to refresh this timeframe
            last_fetch = self.cache_timestamps.get(tf, 0)
            time_since_fetch = current_time - last_fetch
            refresh_interval = REFRESH_INTERVALS.get(tf, 120)  # Default 2 min
            
            should_fetch = force_refresh or (time_since_fetch >= refresh_interval)
            
            if should_fetch:
                print(f"\n📊 Fetching {tf} data (last update: {time_since_fetch:.0f}s ago)...")
                tf_data = self.fetcher.fetch_multiple_parallel(symbol_ids, period=tf, limit=100)
                
                # Update cache
                for symbol_id, df in tf_data.items():
                    if symbol_id not in self.multi_tf_cache:
                        self.multi_tf_cache[symbol_id] = {}
                    self.multi_tf_cache[symbol_id][tf] = df
                
                self.cache_timestamps[tf] = current_time
            else:
                print(f"\n♻️  Using cached {tf} data (age: {time_since_fetch:.0f}s, refresh in: {refresh_interval - time_since_fetch:.0f}s)")
        
        # Generate signals for each symbol
        print(f"\n🔬 Analyzing signals...")
        for symbol_id in symbol_ids:
            if symbol_id in self.multi_tf_cache:
                signal = self.generate_signal(symbol_id, self.multi_tf_cache[symbol_id])
                if signal and signal.score > 30:  # Only include signals above threshold
                    all_signals.append(signal)
        
        # Sort by score
        all_signals.sort(key=lambda s: s.score, reverse=True)
        
        print(f"\n✓ Found {len(all_signals)} signals (score > 30)")
        
        return all_signals
    
    def get_top_opportunities(self, n: int = 20) -> List[TradingSignal]:
        """Get top N trading opportunities"""
        signals = self.scan_all()
        return signals[:n]


if __name__ == "__main__":
    print("Testing Multi-Timeframe Scanner...")
    print("NOTE: This will fail if API token is expired. Test with fresh token during competition.")
    
    scanner = MultiTimeframeScanner()
    
    # Test with just 5 symbols
    print("\n=== Testing with 5 symbols ===")
    signals = scanner.scan_all(max_symbols=5)
    
    if signals:
        print(f"\n{'='*80}")
        print(f"🎯 TOP OPPORTUNITIES")
        print(f"{'='*80}")
        
        for i, signal in enumerate(signals[:10], 1):
            print(f"\n{i}. {signal.ticker} - {signal.signal_type} (Score: {signal.score:.1f})")
            print(f"   Entry: {signal.entry_price:.4f}")
            print(f"   Stop:  {signal.stop_loss:.4f} ({((signal.stop_loss/signal.entry_price-1)*100):+.2f}%)")
            print(f"   Target: {signal.take_profit:.4f} ({((signal.take_profit/signal.entry_price-1)*100):+.2f}%)")
            print(f"   Timeframes: {signal.timeframe_alignment}")
            print(f"   Reasons: {', '.join(signal.reason)}")
    else:
        print("\n✗ No signals generated (likely due to expired token)")
