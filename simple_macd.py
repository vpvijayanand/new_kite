#!/usr/bin/env python3
"""
Simple MACD Calculator for Flask App
"""
import sys
import os
sys.path.append('.')

from app import create_app, db
from app.models.nifty_price import NiftyPrice
import pandas as pd
from datetime import datetime
import pytz

def calculate_macd_signals():
    """Calculate and update MACD signals"""
    app = create_app()
    with app.app_context():
        try:
            print("Getting price data...")
            # Get recent price data
            prices = NiftyPrice.query.order_by(NiftyPrice.timestamp.asc()).limit(2000).all()
            
            if len(prices) < 100:
                print(f"Not enough data: {len(prices)} records")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'price': p.price,
                'timestamp': p.timestamp
            } for p in prices])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            print(f"Processing {len(df)} price records...")
            
            # Calculate for each timeframe
            timeframes = {'3min': 3, '6min': 6, '15min': 15, '30min': 30}
            latest_signals = {}
            
            for tf_name, tf_minutes in timeframes.items():
                print(f"Calculating {tf_name}...")
                
                # Resample data
                ohlc = df['price'].resample(tf_name).ohlc()
                ohlc.dropna(inplace=True)
                
                if len(ohlc) < 50:
                    print(f"Not enough {tf_name} data")
                    continue
                
                # Calculate MACD with EMA12-EMA27
                close = ohlc['close']
                ema_12 = close.ewm(span=12).mean()
                ema_27 = close.ewm(span=27).mean()
                macd = ema_12 - ema_27
                signal_line = macd.ewm(span=9).mean()
                
                # Find latest crossover
                for i in range(len(macd)-1, 0, -1):  # Go backwards to find latest
                    if i < 1:
                        break
                    
                    prev_macd = macd.iloc[i-1]
                    prev_sig = signal_line.iloc[i-1]
                    curr_macd = macd.iloc[i]
                    curr_sig = signal_line.iloc[i]
                    
                    if prev_macd <= prev_sig and curr_macd > curr_sig:
                        # BUY signal
                        ts = macd.index[i]
                        latest_signals[tf_name] = f"BUY {ts.strftime('%d-%m-%Y %H:%M')}"
                        break
                    elif prev_macd >= prev_sig and curr_macd < curr_sig:
                        # SELL signal
                        ts = macd.index[i]
                        latest_signals[tf_name] = f"SELL {ts.strftime('%d-%m-%Y %H:%M')}"
                        break
            
            # Update database
            if latest_signals:
                print("Updating database...")
                
                # Update all records with latest signals
                update_data = {}
                if '3min' in latest_signals:
                    update_data['macd_3m'] = latest_signals['3min']
                if '6min' in latest_signals:
                    update_data['macd_6m'] = latest_signals['6min']
                if '15min' in latest_signals:
                    update_data['macd_15m'] = latest_signals['15min']
                if '30min' in latest_signals:
                    update_data['macd_30m'] = latest_signals['30min']
                
                # Update all NIFTY 50 records
                if update_data:
                    NiftyPrice.query.filter_by(symbol='NIFTY 50').update(update_data)
                    db.session.commit()
                    
                    print("✅ Updated MACD signals:")
                    for tf, signal in latest_signals.items():
                        print(f"  {tf}: {signal}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    calculate_macd_signals()
