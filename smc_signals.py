"""
SMC Signals Module

This module provides functions for generating trade signals based on
Smart Money Concept (SMC) patterns in price data.
"""

import numpy as np

def generate_trade_signals(data, patterns, risk_per_trade=0.5, 
                          take_profit_ratio=2.0, atr_multiplier=1.2, 
                          max_trades_per_day=3):
    """
    Generate trade signals based on SMC patterns.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLC columns and indicators
    patterns : dict
        Dictionary containing identified patterns
    risk_per_trade : float
        Risk percentage per trade (0.5 = 0.5% of account balance)
    take_profit_ratio : float
        Risk-reward ratio for take profit (2.0 = 2:1 reward-to-risk)
    atr_multiplier : float
        Multiplier for ATR to determine stop loss distance
    max_trades_per_day : int
        Maximum number of trades per day
        
    Returns:
    --------
    pandas.DataFrame
        Data with trade signals
    """
    # Make a copy of the data
    data = data.copy()
    
    # Add signal columns
    data['long_signal'] = False
    data['short_signal'] = False
    data['stop_loss'] = np.nan
    data['take_profit'] = np.nan
    
    # Extract patterns
    bullish_fvgs = patterns.get('bullish_fvgs', [])
    bearish_fvgs = patterns.get('bearish_fvgs', [])
    high_sweeps = patterns.get('high_sweeps', [])
    low_sweeps = patterns.get('low_sweeps', [])
    
    # Track active trades to avoid overlapping signals
    active_trade = False
    active_trade_direction = None
    trades_today = 0
    current_date = None
    
    # Iterate through data to generate signals
    for i in range(50, len(data)):  # Start after indicators are calculated
        current_candle = data.iloc[i]
        
        # Reset trades_today counter on new day
        if current_date is None or current_candle.name.date() != current_date:
            current_date = current_candle.name.date()
            trades_today = 0
        
        # Skip if maximum trades per day reached
        if trades_today >= max_trades_per_day:
            continue
        
        # Check if active trade has hit stop loss or take profit
        if active_trade:
            # Check for long trade
            if active_trade_direction == 'long':
                if current_candle['low'] <= data.iloc[i-1]['stop_loss']:
                    # Stop loss hit
                    active_trade = False
                    active_trade_direction = None
                elif current_candle['high'] >= data.iloc[i-1]['take_profit']:
                    # Take profit hit
                    active_trade = False
                    active_trade_direction = None
            
            # Check for short trade
            elif active_trade_direction == 'short':
                if current_candle['high'] >= data.iloc[i-1]['stop_loss']:
                    # Stop loss hit
                    active_trade = False
                    active_trade_direction = None
                elif current_candle['low'] <= data.iloc[i-1]['take_profit']:
                    # Take profit hit
                    active_trade = False
                    active_trade_direction = None
        
        # Skip if already in a trade
        if active_trade:
            continue
        
        # Get ATR for stop loss calculation
        atr = current_candle['atr']
        
        # === Long Signal Conditions ===
        
        # Condition: Bullish FVG with liquidity sweep
        bullish_fvg_signal = False
        for fvg in bullish_fvgs:
            if fvg['index'] < i - 20:  # Only consider recent FVGs
                continue
                
            # Check if price is near the FVG
            if (current_candle['low'] <= fvg['gap_bottom'] * 1.001 and 
                current_candle['close'] > current_candle['open']):
                
                # Check for recent low sweep
                for sweep in low_sweeps:
                    if sweep['index'] > fvg['index'] and sweep['index'] <= i - 1:
                        # Found a low sweep after the FVG
                        bullish_fvg_signal = True
                        break
                
                if bullish_fvg_signal:
                    break
        
        # Combined long signal
        long_signal = bullish_fvg_signal
        
        # Additional filters for long signal
        if long_signal:
            # Trend filter
            trend_aligned = current_candle['ema20'] > current_candle['ema50']
            
            # RSI filter (not oversold)
            rsi_ok = current_candle['rsi'] > 40
            
            # Final long signal
            long_signal = long_signal and trend_aligned and rsi_ok
        
        # === Short Signal Conditions ===
        
        # Condition: Bearish FVG with liquidity sweep
        bearish_fvg_signal = False
        for fvg in bearish_fvgs:
            if fvg['index'] < i - 20:  # Only consider recent FVGs
                continue
                
            # Check if price is near the FVG
            if (current_candle['high'] >= fvg['gap_bottom'] * 0.999 and 
                current_candle['close'] < current_candle['open']):
                
                # Check for recent high sweep
                for sweep in high_sweeps:
                    if sweep['index'] > fvg['index'] and sweep['index'] <= i - 1:
                        # Found a high sweep after the FVG
                        bearish_fvg_signal = True
                        break
                
                if bearish_fvg_signal:
                    break
        
        # Combined short signal
        short_signal = bearish_fvg_signal
        
        # Additional filters for short signal
        if short_signal:
            # Trend filter
            trend_aligned = current_candle['ema20'] < current_candle['ema50']
            
            # RSI filter (not overbought)
            rsi_ok = current_candle['rsi'] < 60
            
            # Final short signal
            short_signal = short_signal and trend_aligned and rsi_ok
        
        # Set signals and calculate stop loss / take profit
        if long_signal:
            data.loc[data.index[i], 'long_signal'] = True
            
            # Calculate stop loss and take profit
            stop_loss = current_candle['low'] - (atr * atr_multiplier)
            risk_per_unit = current_candle['close'] - stop_loss
            take_profit = current_candle['close'] + (risk_per_unit * take_profit_ratio)
            
            data.loc[data.index[i], 'stop_loss'] = stop_loss
            data.loc[data.index[i], 'take_profit'] = take_profit
            
            # Update active trade tracking
            active_trade = True
            active_trade_direction = 'long'
            trades_today += 1
            
        elif short_signal:
            data.loc[data.index[i], 'short_signal'] = True
            
            # Calculate stop loss and take profit
            stop_loss = current_candle['high'] + (atr * atr_multiplier)
            risk_per_unit = stop_loss - current_candle['close']
            take_profit = current_candle['close'] - (risk_per_unit * take_profit_ratio)
            
            data.loc[data.index[i], 'stop_loss'] = stop_loss
            data.loc[data.index[i], 'take_profit'] = take_profit
            
            # Update active trade tracking
            active_trade = True
            active_trade_direction = 'short'
            trades_today += 1
    
    print(f"Generated {data['long_signal'].sum()} long signals and {data['short_signal'].sum()} short signals")
    return data
