"""
Technical Indicators Calculator
"""
import pandas as pd
import numpy as np
from typing import Optional


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index
    
    Args:
        df: DataFrame with 'close' column
        period: RSI period (default 14)
        
    Returns:
        Series with RSI values (0-100)
    """
    if 'close' not in df.columns or len(df) < period:
        return pd.Series([50] * len(df), index=df.index)
    
    # Calculate price changes
    delta = df['close'].diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate average gains and losses
    avg_gains = gains.rolling(window=period, min_periods=period).mean()
    avg_losses = losses.rolling(window=period, min_periods=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    Args:
        df: DataFrame with 'close' column
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    if 'close' not in df.columns or len(df) < slow:
        zeros = pd.Series([0] * len(df), index=df.index)
        return zeros, zeros, zeros
    
    # Calculate EMAs
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    
    # MACD line
    macd_line = ema_fast - ema_slow
    
    # Signal line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # Histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average
    
    Args:
        df: DataFrame with 'close' column
        period: EMA period
        
    Returns:
        Series with EMA values
    """
    if 'close' not in df.columns or len(df) < period:
        return df['close']
    
    return df['close'].ewm(span=period, adjust=False).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (for volatility and stop-loss)
    
    Args:
        df: DataFrame with 'high', 'low', 'close'
        period: ATR period
        
    Returns:
        Series with ATR values
    """
    required_cols = ['high', 'low', 'close']
    if not all(col in df.columns for col in required_cols) or len(df) < period:
        return pd.Series([0] * len(df), index=df.index)
    
    # True Range = max of:
    # 1. Current high - current low
    # 2. Abs(current high - previous close)
    # 3. Abs(current low - previous close)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # ATR is the moving average of true range
    atr = true_range.rolling(window=period, min_periods=period).mean()
    
    return atr


def calculate_volume_ratio(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    Calculate volume ratio (current volume vs average volume)
    
    Args:
        df: DataFrame with 'volume' column
        period: Period for average volume
        
    Returns:
        Series with volume ratio (1.0 = average, >1.0 = above average)
    """
    if 'volume' not in df.columns or len(df) < period:
        return pd.Series([1.0] * len(df), index=df.index)
    
    avg_volume = df['volume'].rolling(window=period, min_periods=period).mean()
    
    # Avoid division by zero
    volume_ratio = df['volume'] / avg_volume.replace(0, 1)
    
    return volume_ratio


def identify_trend(df: pd.DataFrame, fast_period: int = 9, slow_period: int = 21) -> str:
    """
    Identify overall trend using EMAs
    
    Args:
        df: DataFrame with 'close' column
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        
    Returns:
        'UPTREND', 'DOWNTREND', or 'NEUTRAL'
    """
    if len(df) < slow_period:
        return 'NEUTRAL'
    
    ema_fast = calculate_ema(df, fast_period)
    ema_slow = calculate_ema(df, slow_period)
    
    # Get latest values
    fast_val = ema_fast.iloc[-1]
    slow_val = ema_slow.iloc[-1]
    
    # Also check if price is trending
    price_now = df['close'].iloc[-1]
    price_old = df['close'].iloc[-slow_period]
    
    if fast_val > slow_val and price_now > price_old:
        return 'UPTREND'
    elif fast_val < slow_val and price_now < price_old:
        return 'DOWNTREND'
    else:
        return 'NEUTRAL'


def calculate_momentum_score(df: pd.DataFrame) -> float:
    """
    Calculate overall momentum score (0-100)
    Combines RSI, MACD, and price momentum
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        Momentum score (0-100, where >60 is strong bullish, <40 is strong bearish)
    """
    if len(df) < 30:
        return 50.0
    
    scores = []
    
    # RSI component (0-100)
    rsi = calculate_rsi(df)
    if not rsi.empty:
        scores.append(rsi.iloc[-1])
    
    # MACD component
    macd_line, signal_line, histogram = calculate_macd(df)
    if not histogram.empty:
        # MACD histogram positive = bullish, negative = bearish
        # Normalize to 0-100
        if histogram.iloc[-1] > 0:
            macd_score = 50 + min(50, histogram.iloc[-1] * 1000)  # Scale histogram
        else:
            macd_score = 50 + max(-50, histogram.iloc[-1] * 1000)
        scores.append(macd_score)
    
    # Price momentum component
    price_change_pct = ((df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]) * 100
    # Normalize: +5% change = 75, -5% change = 25
    price_score = 50 + (price_change_pct * 5)
    price_score = max(0, min(100, price_score))
    scores.append(price_score)
    
    # Average all components
    if scores:
        return sum(scores) / len(scores)
    return 50.0


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators to a dataframe
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with added indicator columns
    """
    df = df.copy()
    
    # RSI
    df['rsi'] = calculate_rsi(df, 14)
    
    # MACD
    macd_line, signal_line, histogram = calculate_macd(df)
    df['macd'] = macd_line
    df['macd_signal'] = signal_line
    df['macd_histogram'] = histogram
    
    # EMAs
    df['ema_9'] = calculate_ema(df, 9)
    df['ema_21'] = calculate_ema(df, 21)
    df['ema_50'] = calculate_ema(df, 50)
    
    # ATR
    df['atr'] = calculate_atr(df, 14)
    
    # Volume ratio
    df['volume_ratio'] = calculate_volume_ratio(df, 20)
    
    # Momentum score
    df['momentum_score'] = calculate_momentum_score(df)
    
    return df


if __name__ == "__main__":
    # Test with sample data
    print("Testing indicators with sample data...")
    
    # Create sample OHLC data
    dates = pd.date_range('2024-01-01', periods=100, freq='5min')
    np.random.seed(42)
    
    # Generate sample price data (random walk)
    close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    high_prices = close_prices + np.random.rand(100) * 2
    low_prices = close_prices - np.random.rand(100) * 2
    open_prices = close_prices + np.random.randn(100) * 0.3
    volumes = np.random.randint(1000, 10000, 100)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })
    
    # Add indicators
    df_with_indicators = add_all_indicators(df)
    
    print("\n✓ Sample data with indicators:")
    print(df_with_indicators.tail(5)[['timestamp', 'close', 'rsi', 'macd', 'ema_9', 'ema_21', 'volume_ratio']])
    
    # Test individual functions
    print(f"\n✓ Latest RSI: {calculate_rsi(df).iloc[-1]:.2f}")
    print(f"✓ Latest Momentum Score: {calculate_momentum_score(df):.2f}")
    print(f"✓ Trend: {identify_trend(df)}")
    print(f"✓ Latest ATR: {calculate_atr(df).iloc[-1]:.4f}")
