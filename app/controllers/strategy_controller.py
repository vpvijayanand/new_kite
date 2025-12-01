from flask import jsonify
from datetime import datetime, date, timedelta
import pytz
from app import db
from app.models.nifty_price import NiftyPrice
from app.models.banknifty_price import BankNiftyPrice, OptionChainData
from sqlalchemy import text

def analyze_strategies(underlying, strike_gap, protection_gap):
    """
    Analyze sell high + buy higher strategies for both CE and PE options
    
    Strategy:
    - CE: Sell higher strike, Buy even higher strike (credit spread)
    - PE: Sell lower strike, Buy even lower strike (credit spread)
    """
    try:
        # Get current market price and context
        market_context = get_market_context(underlying)
        current_price = market_context.get('current_price', 0)
        
        if current_price == 0:
            return jsonify({
                'success': False,
                'message': 'Unable to get current market price'
            })
        
        # Analyze CE strategies (Sell higher, Buy even higher)
        ce_strategies = analyze_ce_strategies(underlying, current_price, strike_gap, protection_gap)
        
        # Analyze PE strategies (Sell lower, Buy even lower)  
        pe_strategies = analyze_pe_strategies(underlying, current_price, strike_gap, protection_gap)
        
        return jsonify({
            'success': True,
            'underlying': underlying,
            'strike_gap': strike_gap,
            'protection_gap': protection_gap,
            'market_context': market_context,
            'ce_strategies': ce_strategies[:5],  # Top 5
            'pe_strategies': pe_strategies[:5],  # Top 5
            'analysis_time': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error analyzing strategies: {str(e)}'
        }), 500

def get_market_context(underlying):
    """Get market context including open, current, high, low prices"""
    try:
        # Get today's price data
        ist_tz = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist_tz).date()
        
        # Get index prices for today using SQLAlchemy
        if underlying == 'NIFTY':
            model_class = NiftyPrice
        else:  # BANKNIFTY
            model_class = BankNiftyPrice
        
        # Get today's prices
        today_prices = db.session.execute(
            text(f'''
                SELECT 
                    MIN(price) as day_low,
                    MAX(price) as day_high,
                    (SELECT price FROM {model_class.__tablename__} 
                     WHERE DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = :today 
                     ORDER BY timestamp LIMIT 1) as open_price,
                    (SELECT price FROM {model_class.__tablename__} 
                     WHERE DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = :today 
                     ORDER BY timestamp DESC LIMIT 1) as current_price,
                    COUNT(*) as data_points
                FROM {model_class.__tablename__}
                WHERE DATE(timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') = :today
            '''), {'today': today}
        ).fetchone()
        
        if today_prices and today_prices[3]:  # current_price exists
            day_low, day_high, open_price, current_price, data_points = today_prices
            day_range = day_high - day_low if day_high and day_low else 0
            
            # Calculate simple volatility as percentage of day range vs current price
            volatility = (day_range / current_price * 100) if current_price > 0 else 0
            
            return {
                'open_price': float(open_price) if open_price else 0,
                'current_price': float(current_price),
                'day_high': float(day_high) if day_high else 0,
                'day_low': float(day_low) if day_low else 0,
                'day_range': float(day_range),
                'volatility': float(volatility),
                'data_points': data_points
            }
        else:
            return {
                'open_price': 0,
                'current_price': 0,
                'day_high': 0,
                'day_low': 0,
                'day_range': 0,
                'volatility': 0,
                'data_points': 0
            }
                
    except Exception as e:
        print(f"Error getting market context: {e}")
        return {
            'open_price': 0,
            'current_price': 0,
            'day_high': 0,
            'day_low': 0,
            'day_range': 0,
            'volatility': 0,
            'data_points': 0
        }

def analyze_ce_strategies(underlying, current_price, strike_gap, protection_gap):
    """
    Analyze CE strategies: Sell higher strike, Buy even higher strike
    Example: Market at 26000, Sell 26100 CE, Buy 26250 CE
    """
    strategies = []
    
    try:
        # Get today's date in IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist_tz).date()
        
        # Generate potential strike combinations
        # Sell strikes: current_price + strike_gap to current_price + (strike_gap * 3)
        # Buy strikes: sell_strike + protection_gap
        
        for sell_offset in range(strike_gap, strike_gap * 4, strike_gap):
            sell_strike = round_to_strike(current_price + sell_offset)
            buy_strike = sell_strike + protection_gap
            
            # Get opening and closing prices for both strikes
            sell_data = get_option_price_data(underlying, sell_strike, 'CE', today)
            buy_data = get_option_price_data(underlying, buy_strike, 'CE', today)
            
            if sell_data and buy_data:
                # Calculate strategy P&L
                # Strategy: Sell CE (receive premium) + Buy CE (pay premium)
                opening_net_premium = sell_data['open_price'] - buy_data['open_price']  # Net credit received
                closing_net_premium = sell_data['close_price'] - buy_data['close_price']  # Net credit to close
                
                # P&L = Opening net credit - Closing net cost
                pnl_today = opening_net_premium - closing_net_premium
                
                # Max profit = Net premium received (when both options expire worthless)
                max_profit = opening_net_premium
                
                # Max loss = Protection gap - Net premium received
                max_loss = protection_gap - opening_net_premium
                
                strategies.append({
                    'sell_strike': sell_strike,
                    'buy_strike': buy_strike,
                    'sell_open': round(sell_data['open_price'], 2),
                    'sell_close': round(sell_data['close_price'], 2),
                    'buy_open': round(buy_data['open_price'], 2),
                    'buy_close': round(buy_data['close_price'], 2),
                    'net_premium': round(opening_net_premium, 2),
                    'max_profit': round(max_profit, 2),
                    'max_loss': round(max_loss, 2),
                    'pnl_today': round(pnl_today, 2),
                    'profit_probability': calculate_profit_probability(current_price, sell_strike, 'CE')
                })
        
        # Sort by P&L today (descending)
        strategies.sort(key=lambda x: x['pnl_today'], reverse=True)
        
    except Exception as e:
        print(f"Error analyzing CE strategies: {e}")
    
    return strategies

def analyze_pe_strategies(underlying, current_price, strike_gap, protection_gap):
    """
    Analyze PE strategies: Sell lower strike, Buy even lower strike  
    Example: Market at 26000, Sell 25900 PE, Buy 25750 PE
    """
    strategies = []
    
    try:
        # Get today's date in IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist_tz).date()
        
        # Generate potential strike combinations
        # Sell strikes: current_price - strike_gap to current_price - (strike_gap * 3)
        # Buy strikes: sell_strike - protection_gap
        
        for sell_offset in range(strike_gap, strike_gap * 4, strike_gap):
            sell_strike = round_to_strike(current_price - sell_offset)
            buy_strike = sell_strike - protection_gap
            
            # Ensure buy strike is positive
            if buy_strike <= 0:
                continue
            
            # Get opening and closing prices for both strikes
            sell_data = get_option_price_data(underlying, sell_strike, 'PE', today)
            buy_data = get_option_price_data(underlying, buy_strike, 'PE', today)
            
            if sell_data and buy_data:
                # Calculate strategy P&L
                # Strategy: Sell PE (receive premium) + Buy PE (pay premium)
                opening_net_premium = sell_data['open_price'] - buy_data['open_price']  # Net credit received
                closing_net_premium = sell_data['close_price'] - buy_data['close_price']  # Net credit to close
                
                # P&L = Opening net credit - Closing net cost
                pnl_today = opening_net_premium - closing_net_premium
                
                # Max profit = Net premium received (when both options expire worthless)
                max_profit = opening_net_premium
                
                # Max loss = Protection gap - Net premium received  
                max_loss = protection_gap - opening_net_premium
                
                strategies.append({
                    'sell_strike': sell_strike,
                    'buy_strike': buy_strike,
                    'sell_open': round(sell_data['open_price'], 2),
                    'sell_close': round(sell_data['close_price'], 2),
                    'buy_open': round(buy_data['open_price'], 2),
                    'buy_close': round(buy_data['close_price'], 2),
                    'net_premium': round(opening_net_premium, 2),
                    'max_profit': round(max_profit, 2),
                    'max_loss': round(max_loss, 2),
                    'pnl_today': round(pnl_today, 2),
                    'profit_probability': calculate_profit_probability(current_price, sell_strike, 'PE')
                })
        
        # Sort by P&L today (descending)
        strategies.sort(key=lambda x: x['pnl_today'], reverse=True)
        
    except Exception as e:
        print(f"Error analyzing PE strategies: {e}")
    
    return strategies

def get_option_price_data(underlying, strike_price, option_type, date_filter):
    """Get opening and closing option prices for a specific strike and date using existing OptionChainData"""
    try:
        # Query option chain data for today's prices
        option_records = OptionChainData.query.filter(
            OptionChainData.underlying == underlying,
            OptionChainData.strike_price == strike_price,
            db.func.date(OptionChainData.timestamp) == date_filter
        ).order_by(OptionChainData.timestamp).all()
        
        if option_records and len(option_records) >= 2:
            # Get the appropriate price field based on option type
            if option_type == 'CE':
                prices = [record.ce_ltp for record in option_records if record.ce_ltp > 0]
            else:  # PE
                prices = [record.pe_ltp for record in option_records if record.pe_ltp > 0]
            
            if len(prices) >= 2:
                return {
                    'open_price': float(prices[0]),
                    'close_price': float(prices[-1]),
                    'data_points': len(prices)
                }
        
        # If no historical data, use current price as both open and close for demo
        current_records = OptionChainData.query.filter(
            OptionChainData.underlying == underlying,
            OptionChainData.strike_price == strike_price
        ).order_by(OptionChainData.timestamp.desc()).limit(1).all()
        
        if current_records:
            record = current_records[0]
            if option_type == 'CE' and record.ce_ltp > 0:
                price = float(record.ce_ltp)
                return {
                    'open_price': price,
                    'close_price': price,
                    'data_points': 1
                }
            elif option_type == 'PE' and record.pe_ltp > 0:
                price = float(record.pe_ltp)
                return {
                    'open_price': price,
                    'close_price': price,
                    'data_points': 1
                }
        
        return None
        
    except Exception as e:
        print(f"Error getting option price data: {e}")
        return None

def round_to_strike(price):
    """Round price to nearest strike price (usually multiples of 50)"""
    return round(price / 50) * 50

def calculate_profit_probability(current_price, strike_price, option_type):
    """
    Simple probability calculation based on how far current price is from strike
    This is a basic implementation - you might want to use more sophisticated models
    """
    distance = abs(current_price - strike_price)
    distance_percent = (distance / current_price) * 100
    
    # Basic probability based on distance
    if distance_percent > 5:
        return 85  # High probability if strike is far from current price
    elif distance_percent > 3:
        return 70  # Medium-high probability
    elif distance_percent > 1:
        return 55  # Medium probability
    else:
        return 30  # Low probability if strike is close to current price
