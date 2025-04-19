"""
SMC Indicators Module

This module provides functions for calculating technical indicators
used in the Smart Money Concept (SMC) strategy.
"""

def calculate_indicators(data):
    """
    Calculate technical indicators for the strategy.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLC columns
        
    Returns:
    --------
    pandas.DataFrame
        Data with added indicators
    """
    # Make a copy of the data
    data = data.copy()
    
    # Calculate EMAs
    data['ema20'] = _calculate_ema(data['close'], 20)
    data['ema50'] = _calculate_ema(data['close'], 50)
    data['ema200'] = _calculate_ema(data['close'], 200)
    
    # Calculate RSI
    data['rsi'] = _calculate_rsi(data['close'], 14)
    
    # Calculate ATR
    data['atr'] = _calculate_atr(data, 14)
    data['atr_ma'] = _calculate_ema(data['atr'], 20)
    
    # Add dummy volume data if not available
    if 'volume' not in data.columns:
        data['volume'] = 1000
        data['volume_ma'] = 1000
        data['volume_ratio'] = 1.0
    else:
        data['volume_ma'] = _calculate_ema(data['volume'], 20)
        data['volume_ratio'] = data['volume'] / data['volume_ma']
    
    print("Technical indicators calculated successfully")
    return data

def _calculate_ema(series, period):
    """
    Calculate Exponential Moving Average.
    
    Parameters:
    -----------
    series : pandas.Series
        Price series
    period : int
        EMA period
        
    Returns:
    --------
    pandas.Series
        EMA values
    """
    return series.ewm(span=period, adjust=False).mean()

def _calculate_rsi(series, period):
    """
    Calculate Relative Strength Index.
    
    Parameters:
    -----------
    series : pandas.Series
        Price series
    period : int
        RSI period
        
    Returns:
    --------
    pandas.Series
        RSI values
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def _calculate_atr(data, period):
    """
    Calculate Average True Range.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLC columns
    period : int
        ATR period
        
    Returns:
    --------
    pandas.Series
        ATR values
    """
    high = data['high']
    low = data['low']
    close = data['close']
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    import pandas as pd
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate ATR
    atr = tr.rolling(window=period).mean()
    
    return atr
