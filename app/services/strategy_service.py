from datetime import datetime, time, date, timedelta
import pytz
from app import db
from app.models.nifty_price import NiftyPrice
from app.models.banknifty_price import OptionChainData
from app.models.strategy_models import Strategy1Execution, Strategy1Entry, Strategy1LTPHistory
from sqlalchemy import text, func, and_, or_, desc
import math
import logging

class StrategyService:
    def __init__(self):
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.logger = logging.getLogger(__name__)
        
    def get_current_ist_time(self):
        """Get current IST time"""
        return datetime.now(self.ist_timezone)
    
    def is_market_hours(self):
        """Check if current time is within market hours (9:30 AM - 3:15 PM IST)"""
        now = self.get_current_ist_time()
        market_start = time(9, 30)
        market_end = time(15, 15)
        current_time = now.time()
        
        return market_start <= current_time <= market_end
    
    def round_to_nearest_50(self, value):
        """Round value to nearest 50"""
        return round(value / 50) * 50
    
    def get_nifty_high_low_range(self, start_time=None, end_time=None):
        """Get NIFTY high and low for specific time range (default: 9:12-9:33 AM IST)"""
        try:
            today = date.today()
            
            # Set default time range for Strategy 1 (IST)
            if start_time is None:
                start_time = time(9, 12)
            if end_time is None:
                end_time = time(9, 33)
            
            # TEMPORARY FIX: The database stores times with timezone offset issue
            # 9:12 IST is stored as 3:42, 9:33 IST is stored as 4:03
            # So we need to query for the offset times
            offset_start_hour = start_time.hour - 5
            offset_start_minute = start_time.minute - 30
            offset_end_hour = end_time.hour - 5
            offset_end_minute = end_time.minute - 30
            
            # Handle negative minutes
            if offset_start_minute < 0:
                offset_start_minute += 60
                offset_start_hour -= 1
            if offset_end_minute < 0:
                offset_end_minute += 60
                offset_end_hour -= 1
                
            offset_start_time = time(offset_start_hour, offset_start_minute)
            offset_end_time = time(offset_end_hour, offset_end_minute)
            
            # Query records and filter manually for more precise control
            all_records = db.session.query(NiftyPrice).filter(
                func.date(NiftyPrice.timestamp) == today
            ).all()
            
            # Filter records within the offset time range
            range_records = []
            for record in all_records:
                record_time = record.timestamp.time()
                # Check if time is between offset_start_time and offset_end_time
                if offset_start_time <= record_time <= offset_end_time:
                    range_records.append(record)
            
            if range_records:
                # Calculate high, low, avg from filtered records
                highs = [r.high or r.price for r in range_records if r.high or r.price]
                lows = [r.low or r.price for r in range_records if r.low or r.price]
                prices_list = [r.price for r in range_records if r.price]
                
                if highs and lows and prices_list:
                    class MockResult:
                        def __init__(self, high, low, avg_price):
                            self.high = high
                            self.low = low
                            self.avg_price = avg_price
                    
                    prices = MockResult(
                        high=max(highs),
                        low=min(lows),
                        avg_price=sum(prices_list) / len(prices_list)
                    )
                else:
                    prices = None
            else:
                prices = None
            
            if prices and prices.high and prices.low:
                # Find specific 9:12 and 9:33 prices
                price_912 = None
                price_933 = None
                
                # Look for records closest to 9:12 and 9:33 (stored as 3:42 and 4:03)
                target_912 = time(3, 42)  # 9:12 IST stored as 3:42
                target_933 = time(4, 3)   # 9:33 IST stored as 4:03
                
                for record in range_records:
                    record_time = record.timestamp.time()
                    
                    # Find 9:12 price (closest to 3:42)
                    if abs((record_time.hour * 60 + record_time.minute) - (target_912.hour * 60 + target_912.minute)) <= 2:
                        if price_912 is None or abs((record_time.hour * 60 + record_time.minute) - (target_912.hour * 60 + target_912.minute)) < abs((price_912['time'].hour * 60 + price_912['time'].minute) - (target_912.hour * 60 + target_912.minute)):
                            price_912 = {'price': record.price, 'time': record_time}
                    
                    # Find 9:33 price (closest to 4:03)  
                    if abs((record_time.hour * 60 + record_time.minute) - (target_933.hour * 60 + target_933.minute)) <= 2:
                        if price_933 is None or abs((record_time.hour * 60 + record_time.minute) - (target_933.hour * 60 + target_933.minute)) < abs((price_933['time'].hour * 60 + price_933['time'].minute) - (target_933.hour * 60 + target_933.minute)):
                            price_933 = {'price': record.price, 'time': record_time}
                
                result = {
                    'high': float(prices.high),
                    'low': float(prices.low),
                    'avg_price': float(prices.avg_price) if prices.avg_price else 0,
                    'range': float(prices.high) - float(prices.low),
                    'start_time': (start_time or time(9, 12)).strftime('%H:%M'),
                    'end_time': (end_time or time(9, 33)).strftime('%H:%M')
                }
                
                # Add specific 9:12 and 9:33 prices if found
                if price_912:
                    result['price_912'] = float(price_912['price'])
                if price_933:
                    result['price_933'] = float(price_933['price'])
                
                return result
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting NIFTY high/low range: {str(e)}")
            return None
    
    def get_current_nifty_price(self):
        """Get current NIFTY price"""
        try:
            latest_price = db.session.query(NiftyPrice).filter(
                func.date(NiftyPrice.timestamp) == date.today()
            ).order_by(NiftyPrice.timestamp.desc()).first()
            
            if latest_price:
                # Handle None values gracefully
                price = latest_price.price or 0
                high = latest_price.high or price
                low = latest_price.low or price
                
                return {
                    'price': float(price),
                    'high': float(high),
                    'low': float(low),
                    'timestamp': latest_price.timestamp
                }
            return None
        except Exception as e:
            self.logger.error(f"Error getting current NIFTY price: {str(e)}")
            return None
    
    def get_option_ltp(self, strike, option_type='CE'):
        """Get current LTP for specified strike and option type"""
        try:
            # Get latest option chain data for the strike
            option_data = db.session.query(OptionChainData).filter(
                and_(
                    OptionChainData.underlying == 'NIFTY',
                    OptionChainData.strike_price == strike,
                    func.date(OptionChainData.timestamp) == date.today()
                )
            ).order_by(OptionChainData.timestamp.desc()).first()
            
            if option_data:
                if option_type == 'CE':
                    return {
                        'ltp': float(option_data.ce_ltp) if option_data.ce_ltp else 0,
                        'timestamp': option_data.timestamp
                    }
                elif option_type == 'PE':
                    return {
                        'ltp': float(option_data.pe_ltp) if option_data.pe_ltp else 0,
                        'timestamp': option_data.timestamp
                    }
            
            return {'ltp': 0, 'timestamp': None}
        except Exception as e:
            self.logger.error(f"Error getting option LTP for strike {strike}: {str(e)}")
            return {'ltp': 0, 'timestamp': None}
    
    def calculate_strategy_1_positions(self, high, low, current_price):
        """Calculate Strategy 1 positions based on high/low breakout"""
        try:
            positions = {
                'triggered': False,
                'trigger_type': None,
                'sell_strike': None,
                'buy_strike': None,
                'sell_ltp': 0,
                'buy_ltp': 0,
                'net_premium': 0,
                'capital_used': 0,
                'current_pnl': 0,
                'lots': 3,
                'quantity_per_lot': 75
            }
            
            total_quantity = positions['lots'] * positions['quantity_per_lot']
            
            # Check if NIFTY crossed below low (bearish breakout)
            if current_price < low:
                positions['triggered'] = True
                positions['trigger_type'] = 'LOW_BREAK'
                
                # Sell CE: high + 100, rounded to nearest 50
                sell_strike = self.round_to_nearest_50(high + 100)
                # Buy CE: sell_strike + 200
                buy_strike = self.round_to_nearest_50(sell_strike + 200)
                
                positions['sell_strike'] = sell_strike
                positions['buy_strike'] = buy_strike
                
                # Get LTP for both strikes
                sell_data = self.get_option_ltp(sell_strike, 'CE')
                buy_data = self.get_option_ltp(buy_strike, 'CE')
                
                positions['sell_ltp'] = sell_data['ltp']
                positions['buy_ltp'] = buy_data['ltp']
                
                # Net premium received (sell premium - buy premium)
                positions['net_premium'] = positions['sell_ltp'] - positions['buy_ltp']
                
                # Capital used (margin requirement - approximate)
                positions['capital_used'] = (buy_strike - sell_strike) * total_quantity
                
                # Current P&L - CORRECTED CALCULATION
                # For SELL: Entry LTP - Current LTP = Profit (if price drops)
                # For BUY: Current LTP - Entry LTP = Loss (if price increases)
                current_sell_ltp = self.get_option_ltp(sell_strike, 'CE')['ltp']
                current_buy_ltp = self.get_option_ltp(buy_strike, 'CE')['ltp']
                
                sell_pnl = (positions['sell_ltp'] - current_sell_ltp) * total_quantity  # Profit if option price drops
                buy_pnl = (current_buy_ltp - positions['buy_ltp']) * total_quantity   # Loss if option price increases
                positions['current_pnl'] = sell_pnl + buy_pnl
                positions['sell_pnl'] = sell_pnl
                positions['buy_pnl'] = buy_pnl
                positions['sell_ltp_entry'] = positions['sell_ltp']
                positions['buy_ltp_entry'] = positions['buy_ltp']
                positions['net_premium_entry'] = positions['net_premium']
                positions['total_quantity'] = total_quantity
                positions['option_type'] = 'CE'
                
            # Check if NIFTY crossed above high (bullish breakout)
            elif current_price > high:
                positions['triggered'] = True
                positions['trigger_type'] = 'HIGH_BREAK'
                
                # Sell PE: low - 100, rounded to nearest 50
                sell_strike = self.round_to_nearest_50(low - 100)
                # Buy PE: sell_strike - 200
                buy_strike = self.round_to_nearest_50(sell_strike - 200)
                
                positions['sell_strike'] = sell_strike
                positions['buy_strike'] = buy_strike
                
                # Get LTP for both strikes
                sell_data = self.get_option_ltp(sell_strike, 'PE')
                buy_data = self.get_option_ltp(buy_strike, 'PE')
                
                positions['sell_ltp'] = sell_data['ltp']
                positions['buy_ltp'] = buy_data['ltp']
                
                # Net premium received
                positions['net_premium'] = positions['sell_ltp'] - positions['buy_ltp']
                
                # Capital used
                positions['capital_used'] = (sell_strike - buy_strike) * total_quantity
                
                # Current P&L - CORRECTED CALCULATION
                # For SELL: Entry LTP - Current LTP = Profit (if price drops)
                # For BUY: Current LTP - Entry LTP = Loss (if price increases)
                current_sell_ltp = self.get_option_ltp(sell_strike, 'PE')['ltp']
                current_buy_ltp = self.get_option_ltp(buy_strike, 'PE')['ltp']
                
                sell_pnl = (positions['sell_ltp'] - current_sell_ltp) * total_quantity  # Profit if option price drops
                buy_pnl = (current_buy_ltp - positions['buy_ltp']) * total_quantity   # Loss if option price increases
                positions['current_pnl'] = sell_pnl + buy_pnl
                positions['sell_pnl'] = sell_pnl
                positions['buy_pnl'] = buy_pnl
                positions['sell_ltp_entry'] = positions['sell_ltp']
                positions['buy_ltp_entry'] = positions['buy_ltp']
                positions['net_premium_entry'] = positions['net_premium']
                positions['total_quantity'] = total_quantity
                positions['option_type'] = 'PE'
                
            return positions
            
        except Exception as e:
            self.logger.error(f"Error calculating Strategy 1 positions: {str(e)}")
            return positions
    
    def get_strategy_1_data(self):
        """Get comprehensive Strategy 1 data from database"""
        try:
            # Get NIFTY high/low range (9:12 to 9:33)
            range_data = self.get_nifty_high_low_range()
            
            # Get current NIFTY price
            current_price_data = self.get_current_nifty_price()
            
            # Get active trade info
            active_trade = self.get_active_trade()
            today_trade_count = self.get_today_trade_count()
            
            # Build position data from active trade or calculate theoretical
            positions = {}
            pnl_percentage = 0
            
            if active_trade:
                # Get current LTPs for live prices
                option_type = 'CE' if active_trade.option_type == 'CE' else 'PE'
                sell_ltp_data = self.get_option_ltp(active_trade.sell_strike, option_type)
                buy_ltp_data = self.get_option_ltp(active_trade.buy_strike, option_type)
                
                current_sell_ltp = sell_ltp_data['ltp']
                current_buy_ltp = buy_ltp_data['ltp']
                current_net_premium = current_sell_ltp - current_buy_ltp
                
                # Calculate current P&L - CORRECTED CALCULATION
                entry_sell_ltp = active_trade.sell_ltp_entry or 0
                entry_buy_ltp = active_trade.buy_ltp_entry or 0
                total_quantity = active_trade.total_quantity or (active_trade.lots * active_trade.quantity_per_lot)
                
                sell_pnl = (entry_sell_ltp - current_sell_ltp) * total_quantity  # Profit if sell option price drops
                buy_pnl = (current_buy_ltp - entry_buy_ltp) * total_quantity     # Loss if buy option price increases
                current_pnl = sell_pnl + buy_pnl
                
                # Calculate individual option P&L breakdown
                entry_sell_ltp = active_trade.sell_ltp_entry or 0
                entry_buy_ltp = active_trade.buy_ltp_entry or 0
                entry_net_premium = entry_sell_ltp - entry_buy_ltp
                
                sell_pnl = (entry_sell_ltp - current_sell_ltp) * total_quantity
                buy_pnl = (current_buy_ltp - entry_buy_ltp) * total_quantity
                
                # Use actual trade data with detailed breakdown
                positions = {
                    'triggered': True,
                    'trigger_type': active_trade.trigger_type,
                    'sell_strike': active_trade.sell_strike,
                    'buy_strike': active_trade.buy_strike,
                    'sell_ltp_entry': entry_sell_ltp,
                    'buy_ltp_entry': entry_buy_ltp,
                    'sell_ltp': current_sell_ltp,
                    'buy_ltp': current_buy_ltp,
                    'net_premium_entry': entry_net_premium,
                    'net_premium': current_net_premium,
                    'sell_pnl': sell_pnl,
                    'buy_pnl': buy_pnl,
                    'capital_used': active_trade.capital_used,
                    'current_pnl': current_pnl,
                    'lots': active_trade.lots,
                    'quantity_per_lot': active_trade.quantity_per_lot,
                    'total_quantity': total_quantity,
                    'trade_status': 'CLOSED' if 'CLOSED' in (active_trade.notes or '') else 'ACTIVE',
                    'trade_id': active_trade.id,
                    'option_type': active_trade.option_type or 'CE'
                }
                pnl_percentage = active_trade.pnl_percentage
            elif range_data and current_price_data:
                # Calculate theoretical positions
                positions = self.calculate_strategy_1_positions(
                    range_data['high'],
                    range_data['low'],
                    current_price_data['price']
                )
                if positions.get('capital_used', 0) > 0:
                    pnl_percentage = (positions.get('current_pnl', 0) / positions.get('capital_used', 1)) * 100
            
            return {
                'range_data': range_data,
                'current_price': current_price_data,
                'positions': positions,
                'pnl_percentage': pnl_percentage,
                'is_market_hours': self.is_market_hours(),
                'is_trading_time': self.is_trading_time(),
                'today_trade_count': today_trade_count,
                'max_trades_per_day': 2,
                'active_trade': active_trade.to_dict() if active_trade else None,
                'last_updated': self.get_current_ist_time()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Strategy 1 data: {str(e)}")
            return {
                'error': str(e),
                'range_data': None,
                'current_price': None,
                'positions': {},
                'pnl_percentage': 0,
                'is_market_hours': self.is_market_hours(),
                'is_trading_time': False,
                'today_trade_count': 0,
                'max_trades_per_day': 2,
                'active_trade': None,
                'last_updated': self.get_current_ist_time()
            }
    
    def get_strategy_1_status(self):
        """Get current status for API endpoint"""
        return self.get_strategy_1_data()
    
    def get_strategy_1_history(self):
        """Get comprehensive execution history with detailed price tracking"""
        try:
            today = date.today()
            
            # Get all Strategy 1 executions for today
            executions = db.session.query(Strategy1Execution).filter(
                Strategy1Execution.execution_date == today
            ).order_by(Strategy1Execution.timestamp.asc()).all()
            
            # If no executions, show detailed theoretical data
            if not executions:
                return self.get_detailed_theoretical_history()
            
            history_data = []
            for execution in executions:
                # Calculate individual option P&L if entry data exists
                sell_pnl = 0
                buy_pnl = 0
                if execution.sell_ltp_entry and execution.buy_ltp_entry:
                    current_sell = execution.sell_ltp_current or execution.sell_ltp_entry
                    current_buy = execution.buy_ltp_current or execution.buy_ltp_entry
                    total_qty = execution.total_quantity or 225
                    
                    sell_pnl = (execution.sell_ltp_entry - current_sell) * total_qty
                    buy_pnl = (current_buy - execution.buy_ltp_entry) * total_qty
                
                history_data.append({
                    'timestamp': execution.timestamp.strftime('%H:%M') if execution.timestamp else '--:--',
                    'nifty_price': execution.current_nifty_price or 0,
                    'triggered': execution.triggered,
                    'trigger_type': execution.trigger_type,
                    'sell_strike': execution.sell_strike,
                    'buy_strike': execution.buy_strike,
                    'sell_ltp_entry': execution.sell_ltp_entry or 0,
                    'buy_ltp_entry': execution.buy_ltp_entry or 0,
                    'sell_ltp': execution.sell_ltp_current or execution.sell_ltp_entry or 0,
                    'buy_ltp': execution.buy_ltp_current or execution.buy_ltp_entry or 0,
                    'net_premium': execution.net_premium_current or execution.net_premium_entry or 0,
                    'sell_pnl': sell_pnl,
                    'buy_pnl': buy_pnl,
                    'current_pnl': execution.current_pnl or 0,
                    'capital_used': execution.capital_used or 0,
                    'pnl_percentage': execution.pnl_percentage or 0,
                    'trade_status': 'CLOSED' if 'CLOSED' in (execution.notes or '') else 'ACTIVE',
                    'trade_id': execution.id,
                    'option_type': execution.option_type or 'CE'
                })
            
            range_data = self.get_nifty_high_low_range()
            
            return {
                'history': history_data,
                'range_data': range_data,
                'total_records': len(history_data),
                'active_trades': len([h for h in history_data if h['trade_status'] == 'ACTIVE']),
                'closed_trades': len([h for h in history_data if h['trade_status'] == 'CLOSED'])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Strategy 1 history: {str(e)}")
            return {'history': [], 'error': str(e)}
    
    def get_detailed_theoretical_history(self):
        """Get detailed theoretical history with comprehensive price tracking"""
        try:
            today = date.today()
            
            # Get all NIFTY price records for today
            price_history = db.session.query(NiftyPrice).filter(
                func.date(NiftyPrice.timestamp) == today
            ).order_by(NiftyPrice.timestamp.asc()).all()
            
            history_data = []
            range_data = self.get_nifty_high_low_range()
            
            if not range_data:
                return {'history': [], 'range_data': None}
            
            entry_positions = None  # Track entry position for P&L calculation
            
            for price_record in price_history:
                # Calculate theoretical positions for this timestamp
                positions = self.calculate_strategy_1_positions(
                    range_data['high'],
                    range_data['low'],
                    float(price_record.price)
                )
                
                # Track entry positions when first triggered
                if positions.get('triggered') and entry_positions is None:
                    entry_positions = {
                        'sell_ltp': positions.get('sell_ltp', 0),
                        'buy_ltp': positions.get('buy_ltp', 0),
                        'trigger_type': positions.get('trigger_type'),
                        'sell_strike': positions.get('sell_strike'),
                        'buy_strike': positions.get('buy_strike')
                    }
                
                # Calculate detailed P&L with individual option breakdown
                sell_pnl = 0
                buy_pnl = 0
                total_pnl = 0
                pnl_percentage = 0
                
                if entry_positions and positions.get('triggered'):
                    total_qty = 225  # 3 lots * 75 per lot
                    sell_pnl = (entry_positions['sell_ltp'] - positions.get('sell_ltp', 0)) * total_qty
                    buy_pnl = (positions.get('buy_ltp', 0) - entry_positions['buy_ltp']) * total_qty
                    total_pnl = sell_pnl + buy_pnl
                    
                    if positions.get('capital_used', 0) > 0:
                        pnl_percentage = (total_pnl / positions.get('capital_used', 1)) * 100
                
                history_data.append({
                    'timestamp': price_record.timestamp.strftime('%H:%M'),
                    'nifty_price': float(price_record.price),
                    'triggered': positions.get('triggered', False),
                    'trigger_type': positions.get('trigger_type'),
                    'sell_strike': positions.get('sell_strike'),
                    'buy_strike': positions.get('buy_strike'),
                    'sell_ltp_entry': entry_positions['sell_ltp'] if entry_positions else 0,
                    'buy_ltp_entry': entry_positions['buy_ltp'] if entry_positions else 0,
                    'sell_ltp': positions.get('sell_ltp', 0),
                    'buy_ltp': positions.get('buy_ltp', 0),
                    'net_premium': positions.get('net_premium', 0),
                    'sell_pnl': sell_pnl,
                    'buy_pnl': buy_pnl,
                    'current_pnl': total_pnl,
                    'capital_used': positions.get('capital_used', 0),
                    'pnl_percentage': pnl_percentage,
                    'trade_status': 'THEORETICAL',
                    'trade_id': None,
                    'option_type': entry_positions['trigger_type'][-2:] if entry_positions else 'CE'
                })
            
            return {
                'history': history_data,
                'range_data': range_data,
                'total_records': len(history_data),
                'active_trades': 0,
                'closed_trades': 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting detailed theoretical history: {str(e)}")
            return {'history': [], 'error': str(e)}
    
    def execute_strategy_1(self):
        """Execute enhanced Strategy 1 logic with trade management"""
        try:
            # Get current market data
            range_data = self.get_nifty_high_low_range()
            current_price_data = self.get_current_nifty_price()
            
            if not range_data or not current_price_data:
                return {
                    'success': False,
                    'message': 'Insufficient market data for strategy execution'
                }
                
            current_price = current_price_data['price']
            
            # Check for active trade
            active_trade = self.get_active_trade()
            
            # If there's an active trade, check if it should be closed
            if active_trade:
                if self.should_close_trade(active_trade, current_price, range_data):
                    closure_result = self.close_active_trade(active_trade, current_price)
                    return {
                        'success': True,
                        'message': f'Active trade closed: {closure_result["reason"] if closure_result else "Error closing"}',
                        'action': 'TRADE_CLOSED',
                        'data': self.get_strategy_1_data()
                    }
                else:
                    # Update active trade P&L
                    self.update_active_trade_pnl(active_trade, current_price)
                    return {
                        'success': True,
                        'message': 'Active trade P&L updated',
                        'action': 'PNL_UPDATED',
                        'data': self.get_strategy_1_data()
                    }
            
            # No active trade - check if we can take new trades
            today_trade_count = self.get_today_trade_count()
            
            # Maximum 2 trades per day rule
            if today_trade_count >= 2:
                return {
                    'success': True,
                    'message': f'Daily trade limit reached ({today_trade_count}/2)',
                    'action': 'LIMIT_REACHED',
                    'data': self.get_strategy_1_data()
                }
            
            # No new trades after 12:12 PM rule
            if not self.is_trading_time():
                return {
                    'success': True,
                    'message': 'No new trades allowed after 12:12 PM',
                    'action': 'TIME_CUTOFF',
                    'data': self.get_strategy_1_data()
                }
            
            # Check for breakout conditions
            positions = self.calculate_strategy_1_positions(
                range_data['high'],
                range_data['low'],
                current_price
            )
            
            # If breakout detected, create new trade
            if positions.get('triggered'):
                new_trade = self.create_new_trade(positions, range_data, current_price)
                if new_trade:
                    return {
                        'success': True,
                        'message': f'New {positions["trigger_type"]} trade created at NIFTY {current_price}',
                        'action': 'NEW_TRADE',
                        'trade_id': new_trade.id,
                        'data': self.get_strategy_1_data()
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Failed to create new trade',
                        'action': 'TRADE_ERROR'
                    }
            
            # No action needed - monitoring
            return {
                'success': True,
                'message': 'Strategy monitoring - no action required',
                'action': 'MONITORING',
                'data': self.get_strategy_1_data()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing Strategy 1: {str(e)}")
            return {
                'success': False,
                'message': f'Error executing Strategy 1: {str(e)}',
                'action': 'ERROR'
            }
        
    def is_trading_time(self):
        """Check if current time allows new trades (before 12:12 PM IST)"""
        now = self.get_current_ist_time()
        cutoff_time = time(12, 12)
        current_time = now.time()
        
        return current_time < cutoff_time and self.is_market_hours()
    
    def get_today_trade_count(self):
        """Get number of trades taken today"""
        try:
            today = date.today()
            trade_count = db.session.query(Strategy1Execution).filter(
                and_(
                    Strategy1Execution.execution_date == today,
                    Strategy1Execution.triggered == True
                )
            ).count()
            
            return trade_count
        except Exception as e:
            self.logger.error(f"Error getting today's trade count: {str(e)}")
            return 0
    
    def get_active_trade(self):
        """Get currently active trade if any"""
        try:
            today = date.today()
            
            # First check if there's an active entry in the new Strategy1Entry table
            active_entry = db.session.query(Strategy1Entry).filter(
                and_(
                    Strategy1Entry.entry_date == today,
                    Strategy1Entry.is_active == True
                )
            ).order_by(desc(Strategy1Entry.entry_timestamp)).first()
            
            if active_entry:
                # If we have an active entry, look for the corresponding execution record
                active_trade = db.session.query(Strategy1Execution).filter(
                    and_(
                        Strategy1Execution.execution_date == today,
                        Strategy1Execution.triggered == True,
                        Strategy1Execution.notes.contains(f'Entry_ID:{active_entry.id}')
                    )
                ).order_by(desc(Strategy1Execution.timestamp)).first()
                
                if active_trade:
                    return active_trade
            
            # Fallback to legacy method
            active_trade = db.session.query(Strategy1Execution).filter(
                and_(
                    Strategy1Execution.execution_date == today,
                    Strategy1Execution.triggered == True,
                    ~Strategy1Execution.notes.contains('CLOSED')  # Not closed
                )
            ).order_by(desc(Strategy1Execution.timestamp)).first()
            
            return active_trade
        except Exception as e:
            self.logger.error(f"Error getting active trade: {str(e)}")
            return None
    
    def should_close_trade(self, active_trade, current_price, range_data):
        """Check if active trade should be closed based on opposite level crossing"""
        if not active_trade or not range_data:
            return False
            
        try:
            # For bearish trade (LOW_BREAK), close if NIFTY crosses strategy high
            if active_trade.trigger_type == 'LOW_BREAK' and current_price > range_data['high']:
                return True
                
            # For bullish trade (HIGH_BREAK), close if NIFTY crosses strategy low  
            if active_trade.trigger_type == 'HIGH_BREAK' and current_price < range_data['low']:
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking trade closure condition: {str(e)}")
            return False
    
    def close_active_trade(self, active_trade, current_price, reason="OPPOSITE_LEVEL_CROSS"):
        """Close the active trade and calculate final P&L"""
        try:
            if not active_trade:
                return None
                
            # Get current option LTPs
            option_type = 'CE' if active_trade.trigger_type == 'LOW_BREAK' else 'PE'
            
            current_sell_ltp = self.get_option_ltp(active_trade.sell_strike, option_type)['ltp']
            current_buy_ltp = self.get_option_ltp(active_trade.buy_strike, option_type)['ltp']
            
            current_net_premium = current_sell_ltp - current_buy_ltp
            
            # Calculate final P&L - CORRECTED CALCULATION
            entry_sell_ltp = active_trade.sell_ltp_entry or 0
            entry_buy_ltp = active_trade.buy_ltp_entry or 0
            
            sell_pnl = (entry_sell_ltp - current_sell_ltp) * active_trade.total_quantity  # Profit if sell option price drops
            buy_pnl = (current_buy_ltp - entry_buy_ltp) * active_trade.total_quantity     # Loss if buy option price increases
            final_pnl = sell_pnl + buy_pnl
            final_pnl_percentage = (final_pnl / active_trade.capital_used) * 100 if active_trade.capital_used > 0 else 0
            
            # Update the trade record
            active_trade.sell_ltp_current = current_sell_ltp
            active_trade.buy_ltp_current = current_buy_ltp
            active_trade.net_premium_current = current_net_premium
            active_trade.current_pnl = final_pnl
            active_trade.pnl_percentage = final_pnl_percentage
            active_trade.current_nifty_price = current_price
            active_trade.notes = f'CLOSED - {reason}'
            active_trade.timestamp = self.get_current_ist_time()
            
            db.session.commit()
            
            self.logger.info(f"Trade closed: {reason}, Final P&L: ₹{final_pnl:.2f} ({final_pnl_percentage:.2f}%)")
            
            return {
                'closed': True,
                'reason': reason,
                'final_pnl': final_pnl,
                'final_pnl_percentage': final_pnl_percentage,
                'trade_id': active_trade.id
            }
            
        except Exception as e:
            self.logger.error(f"Error closing active trade: {str(e)}")
            return None
    
    def create_new_trade(self, positions, range_data, current_price):
        """Create a new trade execution record with proper entry tracking"""
        try:
            if not positions.get('triggered'):
                return None
            
            today = date.today()
            option_type = 'CE' if positions.get('trigger_type') == 'LOW_BREAK' else 'PE'
            
            # Create Strategy1Entry record (main entry data)
            new_entry = Strategy1Entry(
                entry_date=today,
                nifty_high_912_933=range_data.get('high'),
                nifty_low_912_933=range_data.get('low'),
                nifty_price_912=range_data.get('price_912'),
                nifty_price_933=range_data.get('price_933'),
                range_size=range_data.get('range', 0),
                trigger_type=positions.get('trigger_type'),
                trigger_nifty_price=current_price,
                sell_strike=positions.get('sell_strike'),
                buy_strike=positions.get('buy_strike'),
                option_type=option_type,
                sell_ltp_entry=positions.get('sell_ltp'),
                buy_ltp_entry=positions.get('buy_ltp'),
                net_premium_entry=positions.get('net_premium'),
                lots=positions.get('lots', 3),
                quantity_per_lot=positions.get('quantity_per_lot', 75),
                total_quantity=positions.get('lots', 3) * positions.get('quantity_per_lot', 75),
                capital_used=positions.get('capital_used')
            )
            
            db.session.add(new_entry)
            db.session.flush()  # Get the ID
            
            # Create initial LTP history record
            initial_ltp_record = Strategy1LTPHistory(
                entry_id=new_entry.id,
                nifty_price=current_price,
                sell_ltp=positions.get('sell_ltp'),
                buy_ltp=positions.get('buy_ltp'),
                net_premium=positions.get('net_premium'),
                sell_pnl=0.0,  # Initial P&L is 0
                buy_pnl=0.0,   # Initial P&L is 0
                total_pnl=0.0, # Initial P&L is 0
                pnl_percentage=0.0,
                is_market_hours=self.is_market_hours(),
                notes=f"ENTRY - {positions.get('trigger_type')}"
            )
            
            db.session.add(initial_ltp_record)
            
            # Also create legacy Strategy1Execution record for compatibility
            new_trade = Strategy1Execution(
                execution_date=today,
                range_high=range_data.get('high'),
                range_low=range_data.get('low'),
                range_captured=True,
                current_nifty_price=current_price,
                triggered=True,
                trigger_type=positions.get('trigger_type'),
                sell_strike=positions.get('sell_strike'),
                buy_strike=positions.get('buy_strike'),
                option_type=option_type,
                sell_ltp_entry=positions.get('sell_ltp'),
                buy_ltp_entry=positions.get('buy_ltp'),
                net_premium_entry=positions.get('net_premium'),
                sell_ltp_current=positions.get('sell_ltp'),
                buy_ltp_current=positions.get('buy_ltp'),
                net_premium_current=positions.get('net_premium'),
                current_pnl=0.0,
                capital_used=positions.get('capital_used'),
                pnl_percentage=0.0,
                lots=positions.get('lots', 3),
                quantity_per_lot=positions.get('quantity_per_lot', 75),
                total_quantity=positions.get('lots', 3) * positions.get('quantity_per_lot', 75),
                is_market_hours=self.is_market_hours(),
                notes=f"NEW_TRADE - {positions.get('trigger_type')} - Entry_ID:{new_entry.id}"
            )
            
            db.session.add(new_trade)
            db.session.commit()
            
            self.logger.info(f"New trade created: {positions.get('trigger_type')} at NIFTY {current_price}, Entry ID: {new_entry.id}")
            
            return new_trade
            
        except Exception as e:
            self.logger.error(f"Error creating new trade: {str(e)}")
            db.session.rollback()
            return None
    
    def update_active_trade_pnl(self, active_trade, current_price):
        """Update P&L for active trade and add LTP history record"""
        try:
            if not active_trade:
                return None
                
            # Get current option LTPs
            option_type = 'CE' if active_trade.trigger_type == 'LOW_BREAK' else 'PE'
            
            current_sell_ltp = self.get_option_ltp(active_trade.sell_strike, option_type)['ltp']
            current_buy_ltp = self.get_option_ltp(active_trade.buy_strike, option_type)['ltp']
            
            current_net_premium = current_sell_ltp - current_buy_ltp
            
            # Calculate current P&L - CORRECTED CALCULATION
            entry_sell_ltp = active_trade.sell_ltp_entry or 0
            entry_buy_ltp = active_trade.buy_ltp_entry or 0
            
            sell_pnl = (entry_sell_ltp - current_sell_ltp) * active_trade.total_quantity  # Profit if sell option price drops
            buy_pnl = (current_buy_ltp - entry_buy_ltp) * active_trade.total_quantity     # Loss if buy option price increases
            current_pnl = sell_pnl + buy_pnl
            current_pnl_percentage = (current_pnl / active_trade.capital_used) * 100 if active_trade.capital_used > 0 else 0
            
            # Update the trade record
            active_trade.sell_ltp_current = current_sell_ltp
            active_trade.buy_ltp_current = current_buy_ltp
            active_trade.net_premium_current = current_net_premium
            active_trade.current_pnl = current_pnl
            active_trade.pnl_percentage = current_pnl_percentage
            active_trade.current_nifty_price = current_price
            active_trade.timestamp = self.get_current_ist_time()
            
            # Find and update LTP history for this trade
            # Extract entry_id from notes if available
            entry_id = None
            if active_trade.notes and "Entry_ID:" in active_trade.notes:
                try:
                    entry_id = int(active_trade.notes.split("Entry_ID:")[1])
                except:
                    pass
            
            if entry_id:
                # Add new LTP history record
                ltp_record = Strategy1LTPHistory(
                    entry_id=entry_id,
                    nifty_price=current_price,
                    sell_ltp=current_sell_ltp,
                    buy_ltp=current_buy_ltp,
                    net_premium=current_net_premium,
                    sell_pnl=sell_pnl,
                    buy_pnl=buy_pnl,
                    total_pnl=current_pnl,
                    pnl_percentage=current_pnl_percentage,
                    is_market_hours=self.is_market_hours(),
                    notes=f"UPDATE - {self.get_current_ist_time().strftime('%H:%M')}"
                )
                
                db.session.add(ltp_record)
            
            db.session.commit()
            
            return {
                'current_pnl': current_pnl,
                'current_pnl_percentage': current_pnl_percentage,
                'current_sell_ltp': current_sell_ltp,
                'current_buy_ltp': current_buy_ltp,
                'sell_pnl': sell_pnl,
                'buy_pnl': buy_pnl,
                'entry_id': entry_id
            }
            
        except Exception as e:
            self.logger.error(f"Error updating active trade P&L: {str(e)}")
            return None
    
    def test_pnl_calculation(self):
        """Test function to verify P&L calculation logic"""
        try:
            # Example scenario: Bearish breakout (LOW_BREAK)
            # Sell CE 24000 @ 200, Buy CE 24200 @ 50
            # Later: Sell CE now @ 190, Buy CE now @ 60
            
            entry_sell_ltp = 200
            entry_buy_ltp = 50
            current_sell_ltp = 190
            current_buy_ltp = 60
            total_quantity = 225
            
            # Correct calculation:
            sell_pnl = (entry_sell_ltp - current_sell_ltp) * total_quantity  # (200-190)*225 = +2250
            buy_pnl = (current_buy_ltp - entry_buy_ltp) * total_quantity     # (60-50)*225 = -2250
            total_pnl = sell_pnl + buy_pnl  # 2250 + (-2250) = 0
            
            self.logger.info(f"P&L Test - Sell P&L: {sell_pnl}, Buy P&L: {buy_pnl}, Total: {total_pnl}")
            
            return {
                'entry_sell': entry_sell_ltp,
                'entry_buy': entry_buy_ltp,
                'current_sell': current_sell_ltp,
                'current_buy': current_buy_ltp,
                'sell_pnl': sell_pnl,
                'buy_pnl': buy_pnl,
                'total_pnl': total_pnl
            }
            
        except Exception as e:
            self.logger.error(f"Error in P&L test: {str(e)}")
            return None
