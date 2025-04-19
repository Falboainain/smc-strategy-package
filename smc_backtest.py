"""
SMC Backtest Module

This module provides functions for backtesting the Smart Money Concept (SMC) strategy
with proper risk management and performance tracking.
"""

import pandas as pd
import numpy as np

def run_backtest(data, risk_per_trade=0.5, take_profit_ratio=2.0, 
                initial_balance=10000, commission=0.0001, slippage=0.0001, spread=0.0003):
    """
    Run a backtest on the provided data with proper risk management.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLC columns and signals
    risk_per_trade : float
        Risk percentage per trade (0.5 = 0.5% of account balance)
    take_profit_ratio : float
        Risk-reward ratio for take profit (2.0 = 2:1 reward-to-risk)
    initial_balance : float
        Initial account balance in USD
    commission : float
        Commission per trade as a percentage of trade value
    slippage : float
        Slippage per trade as a percentage of trade value
    spread : float
        Spread as a percentage of price
        
    Returns:
    --------
    tuple
        (data, trades, equity_curve, performance_metrics)
    """
    print("Starting backtest...")
    
    # Make a copy of the data
    data = data.copy()
    
    # Initialize variables
    balance = initial_balance
    position = None
    entry_price = None
    entry_date = None
    stop_loss = None
    take_profit = None
    trade_size = None
    trades = []
    equity_curve = [{'date': data.index[0], 'equity': balance}]
    
    # Add columns for tracking
    data['position'] = None
    data['equity'] = initial_balance
    
    # Convert risk_per_trade to decimal
    risk_per_trade = risk_per_trade / 100
    
    # Iterate through data
    for i in range(1, len(data)):
        current_candle = data.iloc[i]
        prev_candle = data.iloc[i-1]
        
        # Update equity curve
        equity_curve.append({
            'date': current_candle.name,
            'equity': balance
        })
        data.loc[data.index[i], 'equity'] = balance
        
        # Check for exit if in a position
        if position is not None:
            # Check for stop loss hit
            stop_hit = False
            if position == 'long' and current_candle['low'] <= stop_loss:
                # Stop loss hit for long position
                exit_price = stop_loss
                exit_date = current_candle.name
                exit_type = 'stop_loss'
                stop_hit = True
            elif position == 'short' and current_candle['high'] >= stop_loss:
                # Stop loss hit for short position
                exit_price = stop_loss
                exit_date = current_candle.name
                exit_type = 'stop_loss'
                stop_hit = True
            
            # Check for take profit hit
            tp_hit = False
            if position == 'long' and current_candle['high'] >= take_profit:
                # Take profit hit for long position
                exit_price = take_profit
                exit_date = current_candle.name
                exit_type = 'take_profit'
                tp_hit = True
            elif position == 'short' and current_candle['low'] <= take_profit:
                # Take profit hit for short position
                exit_price = take_profit
                exit_date = current_candle.name
                exit_type = 'take_profit'
                tp_hit = True
            
            # Exit trade if stop loss or take profit hit
            if stop_hit or tp_hit:
                # Calculate profit/loss
                if position == 'long':
                    profit = (exit_price - entry_price) * trade_size
                else:  # short
                    profit = (entry_price - exit_price) * trade_size
                
                # Apply commission and slippage
                commission_cost = exit_price * trade_size * commission
                slippage_cost = exit_price * trade_size * slippage
                profit -= (commission_cost + slippage_cost)
                
                # Update balance
                balance += profit
                
                # Record trade
                trades.append({
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'exit_date': exit_date,
                    'exit_price': exit_price,
                    'position': position,
                    'trade_size': trade_size,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'profit': profit,
                    'profit_pct': profit / (entry_price * trade_size) * 100,
                    'exit_type': exit_type,
                    'balance_after': balance
                })
                
                # Reset position
                position = None
                entry_price = None
                entry_date = None
                stop_loss = None
                take_profit = None
                trade_size = None
        
        # Check for entry signals
        if position is None:  # Only enter if not already in a position
            # Long signal
            if prev_candle['long_signal']:
                position = 'long'
                entry_price = current_candle['open']  # Use open price for realistic simulation
                entry_date = current_candle.name
                stop_loss = prev_candle['stop_loss']
                take_profit = prev_candle['take_profit']
                
                # Apply spread for more realistic simulation
                entry_price = entry_price * (1 + spread)
                
                # Calculate risk amount
                risk_amount = balance * risk_per_trade
                
                # Calculate trade size based on risk
                price_risk = entry_price - stop_loss
                trade_size = risk_amount / price_risk if price_risk > 0 else 0
                
                # Apply commission and slippage
                commission_cost = entry_price * trade_size * commission
                slippage_cost = entry_price * trade_size * slippage
                balance -= (commission_cost + slippage_cost)
                
                # Record position
                data.loc[data.index[i], 'position'] = 'long'
            
            # Short signal
            elif prev_candle['short_signal']:
                position = 'short'
                entry_price = current_candle['open']  # Use open price for realistic simulation
                entry_date = current_candle.name
                stop_loss = prev_candle['stop_loss']
                take_profit = prev_candle['take_profit']
                
                # Apply spread for more realistic simulation
                entry_price = entry_price * (1 - spread)
                
                # Calculate risk amount
                risk_amount = balance * risk_per_trade
                
                # Calculate trade size based on risk
                price_risk = stop_loss - entry_price
                trade_size = risk_amount / price_risk if price_risk > 0 else 0
                
                # Apply commission and slippage
                commission_cost = entry_price * trade_size * commission
                slippage_cost = entry_price * trade_size * slippage
                balance -= (commission_cost + slippage_cost)
                
                # Record position
                data.loc[data.index[i], 'position'] = 'short'
        
        # Record current position
        if position is not None:
            data.loc[data.index[i], 'position'] = position
    
    # Close any open position at the end of the backtest
    if position is not None:
        # Get last candle
        last_candle = data.iloc[-1]
        exit_price = last_candle['close']
        exit_date = last_candle.name
        exit_type = 'end_of_data'
        
        # Calculate profit/loss
        if position == 'long':
            profit = (exit_price - entry_price) * trade_size
        else:  # short
            profit = (entry_price - exit_price) * trade_size
        
        # Apply commission and slippage
        commission_cost = exit_price * trade_size * commission
        slippage_cost = exit_price * trade_size * slippage
        profit -= (commission_cost + slippage_cost)
        
        # Update balance
        balance += profit
        
        # Record trade
        trades.append({
            'entry_date': entry_date,
            'entry_price': entry_price,
            'exit_date': exit_date,
            'exit_price': exit_price,
            'position': position,
            'trade_size': trade_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit': profit,
            'profit_pct': profit / (entry_price * trade_size) * 100,
            'exit_type': exit_type,
            'balance_after': balance
        })
        
        # Update final equity
        equity_curve[-1]['equity'] = balance
        data.loc[data.index[-1], 'equity'] = balance
    
    # Calculate performance metrics
    performance_metrics = calculate_performance_metrics(trades, equity_curve, initial_balance)
    
    print(f"Backtest completed with {len(trades)} trades")
    print(f"Final balance: ${balance:.2f}, Return: {(balance - initial_balance) / initial_balance:.2%}")
    
    return data, trades, equity_curve, performance_metrics

def calculate_performance_metrics(trades, equity_curve, initial_balance):
    """
    Calculate performance metrics based on the trades.
    
    Parameters:
    -----------
    trades : list
        List of trade dictionaries
    equity_curve : list
        List of equity dictionaries
    initial_balance : float
        Initial account balance
        
    Returns:
    --------
    dict
        Performance metrics
    """
    if not trades:
        print("No trades to calculate performance metrics")
        return {
            'total_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'final_balance': initial_balance,
            'return': 0,
            'sharpe_ratio': 0
        }
    
    # Calculate basic metrics
    total_trades = len(trades)
    winning_trades = [t for t in trades if t['profit'] > 0]
    losing_trades = [t for t in trades if t['profit'] <= 0]
    
    win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
    
    gross_profit = sum(t['profit'] for t in winning_trades)
    gross_loss = abs(sum(t['profit'] for t in losing_trades))
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    avg_win = gross_profit / len(winning_trades) if winning_trades else 0
    avg_loss = gross_loss / len(losing_trades) if losing_trades else 0
    
    # Calculate drawdown
    equity_values = [initial_balance] + [t['balance_after'] for t in trades]
    max_equity = initial_balance
    max_drawdown = 0
    max_drawdown_pct = 0
    
    for equity in equity_values:
        if equity > max_equity:
            max_equity = equity
        
        drawdown = max_equity - equity
        drawdown_pct = drawdown / max_equity if max_equity > 0 else 0
        
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_drawdown_pct = drawdown_pct
    
    # Calculate returns
    final_balance = trades[-1]['balance_after'] if trades else initial_balance
    total_return = (final_balance - initial_balance) / initial_balance
    
    # Store metrics
    metrics = {
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_drawdown': max_drawdown,
        'max_drawdown_pct': max_drawdown_pct,
        'final_balance': final_balance,
        'return': total_return
    }
    
    return metrics
