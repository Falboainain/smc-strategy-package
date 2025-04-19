"""
SMC Strategy Core Module

This file contains the main SMCStrategy class that integrates all components
of the Smart Money Concept strategy for XAUUSD trading.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# Import modules
from smc_indicators import calculate_indicators
from smc_patterns import identify_fair_value_gaps, identify_liquidity_sweeps
from smc_signals import generate_trade_signals
from smc_backtest import run_backtest

class SMCStrategy:
    """Smart Money Concept (SMC) strategy implementation."""
    
    def __init__(self, risk_per_trade=0.5, take_profit_ratio=2.0, 
                 atr_multiplier=1.2, max_trades_per_day=3):
        """Initialize the SMC strategy."""
        self.risk_per_trade = risk_per_trade / 100  # Convert to decimal
        self.take_profit_ratio = take_profit_ratio
        self.atr_multiplier = atr_multiplier
        self.max_trades_per_day = max_trades_per_day
    
    def prepare_data(self, data):
        """Prepare data by calculating indicators."""
        return calculate_indicators(data)
    
    def find_patterns(self, data):
        """Identify SMC patterns in the data."""
        patterns = {}
        patterns['bullish_fvgs'], patterns['bearish_fvgs'] = identify_fair_value_gaps(data)
        patterns['high_sweeps'], patterns['low_sweeps'] = identify_liquidity_sweeps(data)
        return patterns
    
    def generate_signals(self, data, patterns=None):
        """Generate trade signals based on SMC patterns."""
        if patterns is None:
            patterns = self.find_patterns(data)
        
        return generate_trade_signals(
            data, 
            patterns, 
            self.risk_per_trade, 
            self.take_profit_ratio, 
            self.atr_multiplier, 
            self.max_trades_per_day
        )
    
    def backtest(self, data, initial_balance=10000, commission=0.0001, 
                slippage=0.0001, spread=0.0003):
        """Run a backtest on the provided data."""
        # Calculate indicators if not already calculated
        if 'ema20' not in data.columns:
            data = self.prepare_data(data)
        
        # Generate trade signals if not already generated
        if 'long_signal' not in data.columns:
            data = self.generate_signals(data)
        
        # Run backtest
        return run_backtest(
            data, 
            self.risk_per_trade, 
            self.take_profit_ratio, 
            initial_balance, 
            commission, 
            slippage, 
            spread
        )

def load_data(file_path):
    """Load data from CSV file."""
    try:
        # Load data
        data = pd.read_csv(file_path)
        
        # Convert time column to datetime if it exists
        if 'time' in data.columns:
            data['time'] = pd.to_datetime(data['time'])
            data.set_index('time', inplace=True)
        elif 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data.set_index('date', inplace=True)
        
        # Ensure column names are lowercase
        data.columns = [col.lower() for col in data.columns]
        
        # Check for required columns
        required_columns = ['open', 'high', 'low', 'close']
        for col in required_columns:
            if col not in data.columns:
                print(f"Required column '{col}' not found in data")
                return None
        
        print(f"Loaded {len(data)} rows of data")
        return data
    
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return None

def main():
    """Main function to demonstrate the SMC strategy."""
    print("Starting SMC strategy demonstration...")
    
    # Load data
    data_file = 'xauusd_1min_data.csv'  # Replace with your data file
    if os.path.exists(data_file):
        data = load_data(data_file)
        if data is not None:
            # Create strategy
            strategy = SMCStrategy(risk_per_trade=0.5, take_profit_ratio=2.0, atr_multiplier=1.2)
            
            # Run backtest
            data, trades, equity_curve, metrics = strategy.backtest(data)
            
            # Print performance summary
            print("\nPerformance Summary:")
            print(f"Total Trades: {metrics['total_trades']}")
            print(f"Win Rate: {metrics['win_rate']:.2%}")
            print(f"Return: {metrics['return']:.2%}")
            
            print("Demonstration completed successfully")
    else:
        print(f"Data file '{data_file}' not found")
        print("Please download XAUUSD data from TradingView and save as CSV")

if __name__ == "__main__":
    main()
