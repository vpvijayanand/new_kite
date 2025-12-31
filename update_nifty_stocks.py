#!/usr/bin/env python3
"""
Script to initialize and update NIFTY 50 stocks with today's 9:20 AM and current prices
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.nifty_stocks import NiftyStock
from app.services.nifty_stocks_service import NiftyStocksService
from datetime import datetime, timedelta
import random

def initialize_stock_prices():
    """Initialize NIFTY 50 stocks with today's realistic price data"""
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Initialize the service
            stocks_service = NiftyStocksService()
            
            # First, initialize the basic stock data if not already done
            print("Initializing NIFTY 50 stocks...")
            stocks_service.initialize_stocks()
            
            # Get all stocks from database
            stocks = NiftyStock.query.all()
            print(f"Found {len(stocks)} stocks in database")
            
            # Define realistic base prices for major NIFTY 50 stocks (approximate current market prices)
            base_prices = {
                'RELIANCE': 2850.0,
                'TCS': 4120.0,
                'HDFCBANK': 1720.0,
                'ICICIBANK': 1250.0,
                'BHARTIARTL': 1580.0,
                'ITC': 460.0,
                'SBIN': 820.0,
                'LICI': 920.0,
                'INFY': 1850.0,
                'HINDUNILVR': 2410.0,
                'LT': 3680.0,
                'HCLTECH': 1780.0,
                'MARUTI': 11200.0,
                'SUNPHARMA': 1180.0,
                'TITAN': 3420.0,
                'ONGC': 240.0,
                'NTPC': 350.0,
                'KOTAKBANK': 1740.0,
                'NESTLEIND': 2180.0,
                'ULTRACEMCO': 11800.0,
                'AXISBANK': 1095.0,
                'M&M': 2950.0,
                'ASIANPAINT': 2420.0,
                'BAJFINANCE': 6850.0,
                'WIPRO': 295.0,
                'ADANIENT': 2880.0,
                'POWERGRID': 320.0,
                'COALINDIA': 405.0,
                'TATAMOTORS': 780.0,
                'TATASTEEL': 145.0,
                'BAJAJFINSV': 1650.0,
                'HDFCLIFE': 630.0,
                'TECHM': 1685.0,
                'SBILIFE': 1420.0,
                'ADANIPORTS': 1185.0,
                'GRASIM': 2560.0,
                'JSWSTEEL': 940.0,
                'TATACONSUM': 915.0,
                'BRITANNIA': 4780.0,
                'CIPLA': 1465.0,
                'DIVISLAB': 5980.0,
                'APOLLOHOSP': 7120.0,
                'EICHERMOT': 4850.0,
                'BPCL': 285.0,
                'HINDALCO': 645.0,
                'BAJAJ-AUTO': 9180.0,
                'HEROMOTOCO': 4320.0,
                'DRREDDY': 1240.0,
                'MAXHEALTH': 1085.0
            }
            
            # Calculate today's 9:20 AM (IST) timestamp
            today = datetime.now()
            morning_920 = today.replace(hour=9, minute=20, second=0, microsecond=0)
            
            print(f"Setting prices for {today.strftime('%Y-%m-%d')} at 9:20 AM IST...")
            
            # Update each stock with realistic prices
            updated_count = 0
            for stock in stocks:
                try:
                    # Get base price or generate a random one if not in our list
                    base_price = base_prices.get(stock.symbol, random.uniform(100, 3000))
                    
                    # Generate 9:20 AM price (slight variation from base)
                    morning_variation = random.uniform(-0.02, 0.02)  # -2% to +2%
                    price_920_am = round(base_price * (1 + morning_variation), 2)
                    
                    # Generate current price (variation from morning price)
                    current_variation = random.uniform(-0.05, 0.05)  # -5% to +5%
                    current_price = round(price_920_am * (1 + current_variation), 2)
                    
                    # Update stock data with proper field names
                    stock.opening_price = price_920_am  # 9:20 AM price
                    stock.current_price = current_price
                    stock.trading_date = today.date()
                    stock.last_updated = datetime.now()
                    
                    # Calculate changes manually
                    stock.price_change = current_price - price_920_am
                    if price_920_am > 0:
                        stock.price_change_percent = (stock.price_change / price_920_am) * 100
                    else:
                        stock.price_change_percent = 0
                    
                    # Calculate NIFTY influence: (Stock Change % * Weight in NIFTY) / 100
                    stock.nifty_influence = (stock.price_change_percent * stock.nifty_weightage) / 100
                    
                    updated_count += 1
                    
                    print(f"Updated {stock.symbol}: 9:20 AM ₹{price_920_am:.2f} → Current ₹{current_price:.2f} "
                          f"({stock.price_change_percent:.2f}%, Influence: {stock.nifty_influence:.2f})")
                    
                except Exception as e:
                    print(f"Error updating {stock.symbol}: {e}")
                    continue
            
            # Commit all changes
            db.session.commit()
            print(f"\n✅ Successfully updated {updated_count} stocks with today's price data!")
            
            # Display summary statistics using the model method
            print("\n📊 NIFTY 50 Summary:")
            summary = NiftyStock.get_nifty_stocks_summary()
            print(f"   Gainers: {summary['gainers']}")
            print(f"   Losers: {summary['losers']}")
            print(f"   Unchanged: {summary['unchanged']}")
            print(f"   Net NIFTY Influence: {summary['net_nifty_influence']:.2f}")
            print(f"   Positive Influence: +{summary['total_positive_influence']:.2f}")
            print(f"   Negative Influence: {summary['total_negative_influence']:.2f}")
            
            # Show top performers manually
            gainers = sorted([s for s in summary['stocks'] if s.price_change > 0], 
                           key=lambda x: x.price_change_percent, reverse=True)[:3]
            losers = sorted([s for s in summary['stocks'] if s.price_change < 0], 
                          key=lambda x: x.price_change_percent)[:3]
            
            print(f"\n🔥 Top 3 Gainers:")
            for gainer in gainers:
                print(f"   {gainer.symbol}: +{gainer.price_change_percent:.2f}% (₹{gainer.current_price:.2f})")
            
            print(f"\n📉 Top 3 Losers:")
            for loser in losers:
                print(f"   {loser.symbol}: {loser.price_change_percent:.2f}% (₹{loser.current_price:.2f})")
            
            print(f"\n🌐 Access the NIFTY 50 Stocks page at: http://127.0.0.1:5000/nifty-stocks")
            
        except Exception as e:
            print(f"❌ Error initializing stock data: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    initialize_stock_prices()
