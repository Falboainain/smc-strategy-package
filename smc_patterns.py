"""
SMC Patterns Module

This module provides functions for identifying Smart Money Concept (SMC) patterns
such as Fair Value Gaps and Liquidity Sweeps in price data.
"""

def identify_fair_value_gaps(data, threshold=0.0005):
    """
    Identify Fair Value Gaps (FVGs) in the data.
    
    A Fair Value Gap occurs when price moves so quickly that it leaves a gap
    in the "fair value" of the asset. In candlestick terms:
    - Bullish FVG: Low of current candle > High of previous candle
    - Bearish FVG: High of current candle < Low of previous candle
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLC columns
    threshold : float
        Minimum gap size as a percentage of price
        
    Returns:
    --------
    tuple
        (bullish_fvgs, bearish_fvgs) as lists of dictionaries
    """
    bullish_fvgs = []
    bearish_fvgs = []
    
    # Iterate through data to find FVGs (starting from 3rd candle)
    for i in range(2, len(data)):
        # Get candles
        first_candle = data.iloc[i-2]
        second_candle = data.iloc[i-1]
        third_candle = data.iloc[i]
        
        # Check for bullish FVG (low of 3rd candle > high of 1st candle)
        if third_candle['low'] > first_candle['high']:
            gap_size = (third_candle['low'] - first_candle['high']) / first_candle['high']
            if gap_size >= threshold:
                bullish_fvgs.append({
                    'index': i,
                    'time': data.index[i],
                    'gap_top': third_candle['low'],
                    'gap_bottom': first_candle['high'],
                    'gap_size': gap_size,
                    'filled': False,
                    'fill_time': None
                })
        
        # Check for bearish FVG (high of 3rd candle < low of 1st candle)
        if third_candle['high'] < first_candle['low']:
            gap_size = (first_candle['low'] - third_candle['high']) / third_candle['high']
            if gap_size >= threshold:
                bearish_fvgs.append({
                    'index': i,
                    'time': data.index[i],
                    'gap_top': first_candle['low'],
                    'gap_bottom': third_candle['high'],
                    'gap_size': gap_size,
                    'filled': False,
                    'fill_time': None
                })
    
    print(f"Found {len(bullish_fvgs)} bullish FVGs and {len(bearish_fvgs)} bearish FVGs")
    return bullish_fvgs, bearish_fvgs

def identify_liquidity_sweeps(data, lookback=10, threshold=0.0002):
    """
    Identify liquidity sweeps (stop hunts) in the data.
    
    A liquidity sweep occurs when price briefly breaks above a significant high
    or below a significant low, triggering stop losses, before reversing direction.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLC columns
    lookback : int
        Number of candles to look back for swing highs/lows
    threshold : float
        Minimum sweep size as a percentage of price
        
    Returns:
    --------
    tuple
        (high_sweeps, low_sweeps) as lists of dictionaries
    """
    high_sweeps = []
    low_sweeps = []
    
    # Iterate through data to find liquidity sweeps
    for i in range(lookback, len(data) - 1):
        # Get current and next candle
        curr_candle = data.iloc[i]
        next_candle = data.iloc[i+1]
        
        # Find local high in lookback period
        local_high = max(data.iloc[i-lookback:i]['high'])
        local_high_idx = data.iloc[i-lookback:i]['high'].idxmax()
        
        # Find local low in lookback period
        local_low = min(data.iloc[i-lookback:i]['low'])
        local_low_idx = data.iloc[i-lookback:i]['low'].idxmin()
        
        # Check for high sweep (price breaks above local high then reverses)
        if curr_candle['high'] > local_high and next_candle['close'] < curr_candle['close']:
            sweep_size = (curr_candle['high'] - local_high) / local_high
            if sweep_size >= threshold:
                high_sweeps.append({
                    'index': i,
                    'time': data.index[i],
                    'sweep_level': local_high,
                    'sweep_high': curr_candle['high'],
                    'sweep_size': sweep_size,
                    'reference_time': local_high_idx,
                    'confirmed': next_candle['close'] < local_high
                })
        
        # Check for low sweep (price breaks below local low then reverses)
        if curr_candle['low'] < local_low and next_candle['close'] > curr_candle['close']:
            sweep_size = (local_low - curr_candle['low']) / local_low
            if sweep_size >= threshold:
                low_sweeps.append({
                    'index': i,
                    'time': data.index[i],
                    'sweep_level': local_low,
                    'sweep_low': curr_candle['low'],
                    'sweep_size': sweep_size,
                    'reference_time': local_low_idx,
                    'confirmed': next_candle['close'] > local_low
                })
    
    print(f"Found {len(high_sweeps)} high sweeps and {len(low_sweeps)} low sweeps")
    return high_sweeps, low_sweeps

def identify_order_blocks(data, threshold=0.0005, confirmation_candles=3):
    """
    Identify order blocks in the data.
    
    An order block is the last opposing candle before a strong move in the opposite direction.
    - Bullish order block: Last bearish candle before a strong bullish move
    - Bearish order block: Last bullish candle before a strong bearish move
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLC columns
    threshold : float
        Minimum move size as a percentage of price
    confirmation_candles : int
        Number of candles required to confirm the move
        
    Returns:
    --------
    tuple
        (bullish_obs, bearish_obs) as lists of dictionaries
    """
    bullish_obs = []
    bearish_obs = []
    
    # Iterate through data to find order blocks
    for i in range(1, len(data) - confirmation_candles):
        # Get candles
        curr_candle = data.iloc[i]
        prev_candle = data.iloc[i-1]
        
        # Check if current candle is bearish (potential bullish order block)
        is_bearish = curr_candle['close'] < curr_candle['open']
        
        # Check if current candle is bullish (potential bearish order block)
        is_bullish = curr_candle['close'] > curr_candle['open']
        
        # Check for bullish order block (bearish candle followed by strong bullish move)
        if is_bearish:
            # Calculate move after this candle
            move_size = 0
            for j in range(1, confirmation_candles + 1):
                if i + j < len(data):
                    next_candle = data.iloc[i+j]
                    move_size += (next_candle['close'] - next_candle['open']) / next_candle['open']
            
            # If strong bullish move after, mark as bullish order block
            if move_size >= threshold:
                bullish_obs.append({
                    'index': i,
                    'time': data.index[i],
                    'ob_top': curr_candle['high'],
                    'ob_bottom': curr_candle['low'],
                    'ob_mid': (curr_candle['high'] + curr_candle['low']) / 2,
                    'move_size': move_size,
                    'touched': False,
                    'touch_time': None
                })
        
        # Check for bearish order block (bullish candle followed by strong bearish move)
        if is_bullish:
            # Calculate move after this candle
            move_size = 0
            for j in range(1, confirmation_candles + 1):
                if i + j < len(data):
                    next_candle = data.iloc[i+j]
                    move_size += (next_candle['open'] - next_candle['close']) / next_candle['open']
            
            # If strong bearish move after, mark as bearish order block
            if move_size >= threshold:
                bearish_obs.append({
                    'index': i,
                    'time': data.index[i],
                    'ob_top': curr_candle['high'],
                    'ob_bottom': curr_candle['low'],
                    'ob_mid': (curr_candle['high'] + curr_candle['low']) / 2,
                    'move_size': move_size,
                    'touched': False,
                    'touch_time': None
                })
    
    print(f"Found {len(bullish_obs)} bullish order blocks and {len(bearish_obs)} bearish order blocks")
    return bullish_obs, bearish_obs
