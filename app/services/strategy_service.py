from datetime import datetime, time, date, timedelta
import pytz
from app import db
from app.models.nifty_price import NiftyPrice
from app.models.banknifty_price import OptionChainData
from app.models.strategy_models import Strategy1Execution
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
        """Get NIFTY high and low for specified time range"""
        try:
            today = date.today()
            
            if not start_time:
                start_time = time(9, 12)
            if not end_time:
                end_time = time(9, 33)
                
            start_datetime = datetime.combine(today, start_time)
            end_datetime = datetime.combine(today, end_time)
            
            # Query for NIFTY prices in the specified range
            prices = db.session.query(
                func.max(NiftyPrice.high).label('high'),
                func.min(NiftyPrice.low).label('low'),
                func.avg(NiftyPrice.price).label('avg_price')
            ).filter(
                and_(
                    NiftyPrice.timestamp >= start_datetime,
                    NiftyPrice.timestamp <= end_datetime,
                    func.date(NiftyPrice.timestamp) == today
                )
            ).first()
            
            if prices and prices.high and prices.low:
                return {
                    'high': float(prices.high),
                    'low': float(prices.low),
                    'avg_price': float(prices.avg_price) if prices.avg_price else 0,
                    'range': float(prices.high) - float(prices.low),
                    'start_time': start_time,
                    'end_time': end_time
                }
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
                return {
                    'price': float(latest_price.price),
                    'high': float(latest_price.high),
                    'low': float(latest_price.low),
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
                    OptionChainData.strike == strike,
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
                
                # Current P&L
                current_sell_ltp = self.get_option_ltp(sell_strike, 'CE')['ltp']
                current_buy_ltp = self.get_option_ltp(buy_strike, 'CE')['ltp']
                
                current_net_premium = current_sell_ltp - current_buy_ltp
                positions['current_pnl'] = (positions['net_premium'] - current_net_premium) * total_quantity
                
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
                
                # Current P&L
                current_sell_ltp = self.get_option_ltp(sell_strike, 'PE')['ltp']
                current_buy_ltp = self.get_option_ltp(buy_strike, 'PE')['ltp']
                
                current_net_premium = current_sell_ltp - current_buy_ltp
                positions['current_pnl'] = (positions['net_premium'] - current_net_premium) * total_quantity
                
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
                # Use actual trade data
                positions = {
                    'triggered': True,
                    'trigger_type': active_trade.trigger_type,
                    'sell_strike': active_trade.sell_strike,
                    'buy_strike': active_trade.buy_strike,
                    'sell_ltp': active_trade.sell_ltp_current,
                    'buy_ltp': active_trade.buy_ltp_current,
                    'net_premium': active_trade.net_premium_current,
                    'capital_used': active_trade.capital_used,
                    'current_pnl': active_trade.current_pnl,
                    'lots': active_trade.lots,
                    'quantity_per_lot': active_trade.quantity_per_lot,
                    'trade_status': 'CLOSED' if 'CLOSED' in (active_trade.notes or '') else 'ACTIVE',
                    'trade_id': active_trade.id
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
        """Get execution history from database for today"""
        try:
            today = date.today()
            
            # Get all Strategy 1 executions for today
            executions = db.session.query(Strategy1Execution).filter(
                Strategy1Execution.execution_date == today
            ).order_by(Strategy1Execution.timestamp.asc()).all()
            
            # If no executions, show theoretical data based on NIFTY price movements
            if not executions:
                return self.get_theoretical_history()
            
            history_data = []
            for execution in executions:
                history_data.append({
                    'timestamp': execution.timestamp.strftime('%H:%M') if execution.timestamp else '--:--',
                    'nifty_price': execution.current_nifty_price or 0,
                    'triggered': execution.triggered,
                    'trigger_type': execution.trigger_type,
                    'sell_strike': execution.sell_strike,
                    'buy_strike': execution.buy_strike,
                    'sell_ltp': execution.sell_ltp_current or execution.sell_ltp_entry or 0,
                    'buy_ltp': execution.buy_ltp_current or execution.buy_ltp_entry or 0,
                    'net_premium': execution.net_premium_current or execution.net_premium_entry or 0,
                    'current_pnl': execution.current_pnl or 0,
                    'capital_used': execution.capital_used or 0,
                    'pnl_percentage': execution.pnl_percentage or 0,
                    'trade_status': 'CLOSED' if 'CLOSED' in (execution.notes or '') else 'ACTIVE',
                    'trade_id': execution.id
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
    
    def get_theoretical_history(self):
        """Get theoretical history based on NIFTY price movements (when no actual trades)"""
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
            
            for price_record in price_history:
                # Calculate theoretical positions for this timestamp
                positions = self.calculate_strategy_1_positions(
                    range_data['high'],
                    range_data['low'],
                    float(price_record.price)
                )
                
                # Calculate theoretical PnL percentage
                pnl_percentage = 0
                if positions.get('capital_used', 0) > 0:
                    pnl_percentage = (positions.get('current_pnl', 0) / positions.get('capital_used', 1)) * 100
                
                history_data.append({
                    'timestamp': price_record.timestamp.strftime('%H:%M'),
                    'nifty_price': float(price_record.price),
                    'triggered': positions.get('triggered', False),
                    'trigger_type': positions.get('trigger_type'),
                    'sell_strike': positions.get('sell_strike'),
                    'buy_strike': positions.get('buy_strike'),
                    'sell_ltp': positions.get('sell_ltp', 0),
                    'buy_ltp': positions.get('buy_ltp', 0),
                    'net_premium': positions.get('net_premium', 0),
                    'current_pnl': positions.get('current_pnl', 0),
                    'capital_used': positions.get('capital_used', 0),
                    'pnl_percentage': pnl_percentage,
                    'trade_status': 'THEORETICAL',
                    'trade_id': None
                })
            
            return {
                'history': history_data,
                'range_data': range_data,
                'total_records': len(history_data),
                'active_trades': 0,
                'closed_trades': 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting theoretical history: {str(e)}")
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
            active_trade = db.session.query(Strategy1Execution).filter(
                and_(
                    Strategy1Execution.execution_date == today,
                    Strategy1Execution.triggered == True,
                    Strategy1Execution.notes != 'CLOSED'  # Not closed
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
            
            # Calculate final P&L
            entry_premium = active_trade.net_premium_entry or 0
            final_pnl = (entry_premium - current_net_premium) * active_trade.total_quantity
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
        """Create a new trade execution record"""
        try:
            if not positions.get('triggered'):
                return None
                
            new_trade = Strategy1Execution(
                execution_date=date.today(),
                range_high=range_data.get('high'),
                range_low=range_data.get('low'),
                range_captured=True,
                current_nifty_price=current_price,
                triggered=True,
                trigger_type=positions.get('trigger_type'),
                sell_strike=positions.get('sell_strike'),
                buy_strike=positions.get('buy_strike'),
                option_type='CE' if positions.get('trigger_type') == 'LOW_BREAK' else 'PE',
                sell_ltp_entry=positions.get('sell_ltp'),
                buy_ltp_entry=positions.get('buy_ltp'),
                net_premium_entry=positions.get('net_premium'),
                sell_ltp_current=positions.get('sell_ltp'),
                buy_ltp_current=positions.get('buy_ltp'),
                net_premium_current=positions.get('net_premium'),
                current_pnl=0.0,  # Initial P&L is 0
                capital_used=positions.get('capital_used'),
                pnl_percentage=0.0,
                lots=positions.get('lots', 3),
                quantity_per_lot=positions.get('quantity_per_lot', 75),
                total_quantity=positions.get('lots', 3) * positions.get('quantity_per_lot', 75),
                is_market_hours=self.is_market_hours(),
                notes=f"NEW_TRADE - {positions.get('trigger_type')}"
            )
            
            db.session.add(new_trade)
            db.session.commit()
            
            self.logger.info(f"New trade created: {positions.get('trigger_type')} at NIFTY {current_price}")
            
            return new_trade
            
        except Exception as e:
            self.logger.error(f"Error creating new trade: {str(e)}")
            db.session.rollback()
            return None
    
    def update_active_trade_pnl(self, active_trade, current_price):
        """Update P&L for active trade"""
        try:
            if not active_trade:
                return None
                
            # Get current option LTPs
            option_type = 'CE' if active_trade.trigger_type == 'LOW_BREAK' else 'PE'
            
            current_sell_ltp = self.get_option_ltp(active_trade.sell_strike, option_type)['ltp']
            current_buy_ltp = self.get_option_ltp(active_trade.buy_strike, option_type)['ltp']
            
            current_net_premium = current_sell_ltp - current_buy_ltp
            
            # Calculate current P&L
            entry_premium = active_trade.net_premium_entry or 0
            current_pnl = (entry_premium - current_net_premium) * active_trade.total_quantity
            current_pnl_percentage = (current_pnl / active_trade.capital_used) * 100 if active_trade.capital_used > 0 else 0
            
            # Update the trade record
            active_trade.sell_ltp_current = current_sell_ltp
            active_trade.buy_ltp_current = current_buy_ltp
            active_trade.net_premium_current = current_net_premium
            active_trade.current_pnl = current_pnl
            active_trade.pnl_percentage = current_pnl_percentage
            active_trade.current_nifty_price = current_price
            active_trade.timestamp = self.get_current_ist_time()
            
            db.session.commit()
            
            return {
                'current_pnl': current_pnl,
                'current_pnl_percentage': current_pnl_percentage,
                'current_sell_ltp': current_sell_ltp,
                'current_buy_ltp': current_buy_ltp
            }
            
        except Exception as e:
            self.logger.error(f"Error updating active trade P&L: {str(e)}")
            return None
