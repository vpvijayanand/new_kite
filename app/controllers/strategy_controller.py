from flask import Blueprint, render_template, jsonify, current_app, request
from app.services.strategy_service import StrategyService
from app.middlewares.auth_middleware import login_required
from datetime import datetime, time
import traceback

# Create Blueprint for strategy routes
strategy_bp = Blueprint('strategy', __name__, url_prefix='/strategies')

@strategy_bp.route('/')
@login_required
def strategies_dashboard():
    """Main strategies dashboard"""
    return render_template('strategies/dashboard.html')

@strategy_bp.route('/strategy-1')
@login_required
def strategy_1():
    """Strategy 1 - Nifty High Low Breakout Strategy"""
    try:
        strategy_service = StrategyService()
        
        # Get today's strategy data
        strategy_data = strategy_service.get_strategy_1_data()
        
        return render_template('strategies/strategy_1.html', **strategy_data)
    except Exception as e:
        current_app.logger.error(f"Error in strategy_1: {str(e)}")
        return render_template('strategies/strategy_1.html', error=str(e))

@strategy_bp.route('/api/strategy-1/status')
@login_required
def strategy_1_status():
    """API endpoint for Strategy 1 current status"""
    try:
        strategy_service = StrategyService()
        status_data = strategy_service.get_strategy_1_status()
        return jsonify(status_data)
    except Exception as e:
        current_app.logger.error(f"Error in strategy_1_status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@strategy_bp.route('/api/strategy-1/history')
@login_required
def strategy_1_history():
    """API endpoint for Strategy 1 minute-by-minute data"""
    try:
        strategy_service = StrategyService()
        history_data = strategy_service.get_strategy_1_history()
        return jsonify(history_data)
    except Exception as e:
        current_app.logger.error(f"Error in strategy_1_history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@strategy_bp.route('/api/strategy-1/fix-entry-data')
@login_required
def fix_entry_data():
    """Fix existing Strategy1Execution records that have 0.0 entry values"""
    try:
        from app.models.strategy_models import Strategy1Entry, Strategy1LTPHistory, Strategy1Execution
        
        today = date.today()
        
        # Find executions with missing entry data
        broken_executions = db.session.query(Strategy1Execution).filter(
            and_(
                Strategy1Execution.execution_date == today,
                Strategy1Execution.triggered == True,
                or_(
                    Strategy1Execution.sell_ltp_entry == 0.0,
                    Strategy1Execution.sell_ltp_entry == None,
                    Strategy1Execution.buy_ltp_entry == 0.0,
                    Strategy1Execution.buy_ltp_entry == None
                )
            )
        ).all()
        
        fixed_count = 0
        
        for execution in broken_executions:
            if execution.sell_ltp_current and execution.buy_ltp_current:
                # Use current LTP as entry LTP if entry is missing
                if not execution.sell_ltp_entry or execution.sell_ltp_entry == 0.0:
                    execution.sell_ltp_entry = execution.sell_ltp_current
                
                if not execution.buy_ltp_entry or execution.buy_ltp_entry == 0.0:
                    execution.buy_ltp_entry = execution.buy_ltp_current
                
                if not execution.net_premium_entry or execution.net_premium_entry == 0.0:
                    execution.net_premium_entry = execution.sell_ltp_entry - execution.buy_ltp_entry
                
                fixed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Fixed {fixed_count} execution records with missing entry data',
            'fixed_executions': fixed_count,
            'total_broken': len(broken_executions)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error fixing entry data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@strategy_bp.route('/api/strategy-1/complete-history')
@login_required
def strategy_1_complete_history():
    """Comprehensive minute-by-minute history combining all data sources"""
    try:
        from app.models.strategy_models import Strategy1Entry, Strategy1LTPHistory, Strategy1Execution
        from app.models.nifty_price import NiftyPrice
        
        today = date.today()
        
        # Get all NIFTY price records for today to build timeline
        nifty_records = db.session.query(NiftyPrice).filter(
            func.date(NiftyPrice.timestamp) == today
        ).order_by(NiftyPrice.timestamp.asc()).all()
        
        # Get today's strategy entries and executions
        entries = db.session.query(Strategy1Entry).filter(
            Strategy1Entry.entry_date == today
        ).all()
        
        executions = db.session.query(Strategy1Execution).filter(
            Strategy1Execution.execution_date == today,
            Strategy1Execution.triggered == True
        ).all()
        
        # Build comprehensive timeline
        timeline = []
        entry_data = entries[0] if entries else None
        execution_data = executions[0] if executions else None
        
        # If we have an active trade, get the range data
        range_data = None
        if execution_data:
            range_data = {
                'high': execution_data.range_high,
                'low': execution_data.range_low,
                'sell_strike': execution_data.sell_strike,
                'buy_strike': execution_data.buy_strike,
                'option_type': execution_data.option_type,
                'sell_ltp_entry': execution_data.sell_ltp_entry,
                'buy_ltp_entry': execution_data.buy_ltp_entry,
                'net_premium_entry': execution_data.net_premium_entry,
                'total_quantity': execution_data.total_quantity,
                'capital_used': execution_data.capital_used,
                'trigger_type': execution_data.trigger_type
            }
        
        # Process each NIFTY price record
        for nifty_record in nifty_records:
            record_time = nifty_record.timestamp
            nifty_price = float(nifty_record.price)
            
            # Initialize record
            history_record = {
                'timestamp': record_time.strftime('%H:%M:%S'),
                'datetime': record_time.isoformat(),
                'nifty_price': nifty_price,
                'triggered': False,
                'trigger_type': None,
                'sell_strike': None,
                'buy_strike': None,
                'option_type': None,
                'sell_ltp_entry': None,
                'buy_ltp_entry': None,
                'sell_ltp_current': None,
                'buy_ltp_current': None,
                'net_premium_entry': None,
                'net_premium_current': None,
                'sell_pnl': 0,
                'buy_pnl': 0,
                'total_pnl': 0,
                'pnl_percentage': 0,
                'capital_used': 0,
                'status': 'MONITORING'
            }
            
            # Check if this NIFTY record is after the trade trigger time
            # Since we have an active trade, mark all recent records as ACTIVE
            is_after_trigger = False
            if range_data and execution_data:
                # For simplicity, mark records from last hour as ACTIVE if we have a trade
                from datetime import timedelta
                current_time = datetime.now()
                if (current_time - record_time).total_seconds() < 3600:  # Last 1 hour
                    is_after_trigger = True
            
            # If we have active trade data and this is likely after the trigger
            if range_data and execution_data and is_after_trigger:
                history_record.update({
                    'triggered': True,
                    'trigger_type': range_data['trigger_type'],
                    'sell_strike': range_data['sell_strike'],
                    'buy_strike': range_data['buy_strike'],
                    'option_type': range_data['option_type'],
                    'sell_ltp_entry': range_data['sell_ltp_entry'],
                    'buy_ltp_entry': range_data['buy_ltp_entry'],
                    'net_premium_entry': range_data['net_premium_entry'],
                    'capital_used': range_data['capital_used'],
                    'status': 'ACTIVE'
                })
                
                # Use current execution data for LTPs (most recent available)
                current_sell_ltp = execution_data.sell_ltp_current or range_data['sell_ltp_entry']
                current_buy_ltp = execution_data.buy_ltp_current or range_data['buy_ltp_entry']
                current_net_premium = current_sell_ltp - current_buy_ltp
                
                # Calculate P&L using correct formula
                sell_pnl = (range_data['sell_ltp_entry'] - current_sell_ltp) * range_data['total_quantity']
                buy_pnl = (current_buy_ltp - range_data['buy_ltp_entry']) * range_data['total_quantity']
                total_pnl = sell_pnl + buy_pnl
                pnl_percentage = (total_pnl / range_data['capital_used']) * 100 if range_data['capital_used'] > 0 else 0
                
                history_record.update({
                    'sell_ltp_current': current_sell_ltp,
                    'buy_ltp_current': current_buy_ltp,
                    'net_premium_current': current_net_premium,
                    'sell_pnl': sell_pnl,
                    'buy_pnl': buy_pnl,
                    'total_pnl': total_pnl,
                    'pnl_percentage': pnl_percentage
                })
            
            # Check if this is the trigger point
            elif range_data and not history_record['triggered']:
                # Calculate theoretical positions for this price point
                from app.services.strategy_service import StrategyService
                strategy_service = StrategyService()
                theoretical_positions = strategy_service.calculate_strategy_1_positions(
                    range_data['high'], range_data['low'], nifty_price
                )
                
                if theoretical_positions.get('triggered'):
                    history_record['status'] = 'TRIGGER_POINT'
                    history_record.update({
                        'triggered': True,
                        'trigger_type': theoretical_positions.get('trigger_type'),
                        'sell_strike': theoretical_positions.get('sell_strike'),
                        'buy_strike': theoretical_positions.get('buy_strike'),
                        'option_type': theoretical_positions.get('option_type'),
                        'sell_ltp_entry': theoretical_positions.get('sell_ltp_entry'),
                        'buy_ltp_entry': theoretical_positions.get('buy_ltp_entry'),
                        'sell_ltp_current': theoretical_positions.get('sell_ltp'),
                        'buy_ltp_current': theoretical_positions.get('buy_ltp'),
                        'net_premium_current': theoretical_positions.get('net_premium'),
                        'sell_pnl': theoretical_positions.get('sell_pnl', 0),
                        'buy_pnl': theoretical_positions.get('buy_pnl', 0),
                        'total_pnl': theoretical_positions.get('current_pnl', 0),
                        'capital_used': theoretical_positions.get('capital_used', 0),
                        'pnl_percentage': (theoretical_positions.get('current_pnl', 0) / theoretical_positions.get('capital_used', 1)) * 100 if theoretical_positions.get('capital_used', 0) > 0 else 0
                    })
            
            timeline.append(history_record)
        
        # Get LTP history records if available
        ltp_history_records = []
        if entry_data:
            ltp_history = db.session.query(Strategy1LTPHistory).filter(
                Strategy1LTPHistory.entry_id == entry_data.id
            ).order_by(Strategy1LTPHistory.timestamp.asc()).all()
            
            ltp_history_records = [record.to_dict() for record in ltp_history]
        
        result = {
            'timeline': timeline,
            'total_records': len(timeline),
            'ltp_history': ltp_history_records,
            'ltp_history_count': len(ltp_history_records),
            'entry_data': entry_data.to_dict() if entry_data else None,
            'execution_data': execution_data.to_dict() if execution_data else None,
            'has_active_trade': execution_data is not None,
            'range_data': range_data
        }
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in strategy_1_complete_history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@strategy_bp.route('/api/strategy-1/ltp-history')
@login_required
def strategy_1_ltp_history():
    """API endpoint for detailed LTP history from new tracking tables"""
    try:
        from app.models.strategy_models import Strategy1Entry, Strategy1LTPHistory
        
        today = date.today()
        
        # Get today's entries
        entries = db.session.query(Strategy1Entry).filter(
            Strategy1Entry.entry_date == today
        ).order_by(Strategy1Entry.entry_timestamp.desc()).all()
        
        result = {
            'entries': [],
            'total_entries': len(entries)
        }
        
        for entry in entries:
            # Get LTP history for this entry
            ltp_history = db.session.query(Strategy1LTPHistory).filter(
                Strategy1LTPHistory.entry_id == entry.id
            ).order_by(Strategy1LTPHistory.timestamp.asc()).all()
            
            entry_data = entry.to_dict()
            entry_data['ltp_history'] = [record.to_dict() for record in ltp_history]
            entry_data['history_count'] = len(ltp_history)
            
            result['entries'].append(entry_data)
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in strategy_1_ltp_history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@strategy_bp.route('/api/strategy-1/execute')
@login_required
def execute_strategy_1():
    """Manual trigger for Strategy 1 execution (for testing)"""
    try:
        strategy_service = StrategyService()
        result = strategy_service.execute_strategy_1()
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in execute_strategy_1: {str(e)}")
        return jsonify({'error': str(e)}), 500

@strategy_bp.route('/api/strategy-1/create-tables')
@login_required
def create_strategy_tables():
    """Create the new strategy tracking tables"""
    try:
        from app.models.strategy_models import Strategy1Entry, Strategy1LTPHistory
        
        # Create tables
        db.create_all()
        
        return jsonify({
            'success': True,
            'message': 'Strategy1Entry and Strategy1LTPHistory tables created successfully',
            'tables': ['strategy1_entries', 'strategy1_ltp_history']
        })
    except Exception as e:
        current_app.logger.error(f"Error creating tables: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@strategy_bp.route('/api/strategy-1/test-pnl')
@login_required
def test_pnl_calculation():
    """Test P&L calculation with example values"""
    try:
        # Example: Bear Call Spread (Bearish breakout)
        # Sell 24000 CE @ 110, Buy 24200 CE @ 80
        # Later: Sell CE @ 90, Buy CE @ 70
        
        example_data = {
            'strategy_type': 'Bear Call Spread',
            'scenario': 'NIFTY fell as expected',
            'entry': {
                'sell_strike': 24000,
                'buy_strike': 24200,
                'sell_ltp': 110,
                'buy_ltp': 80,
                'net_credit': 110 - 80,  # 30
                'quantity': 225
            },
            'current': {
                'sell_ltp': 90,
                'buy_ltp': 70,
                'net_credit': 90 - 70   # 20
            },
            'pnl_calculation': {
                'sell_pnl': (110 - 90) * 225,    # +4500
                'buy_pnl': (70 - 80) * 225,      # -2250
                'total_pnl': ((110 - 90) + (70 - 80)) * 225,  # +2250
                'capital_used': (24200 - 24000) * 225,  # 45000
                'return_percent': (((110 - 90) + (70 - 80)) * 225 / (45000)) * 100  # 5%
            }
        }
        
        return jsonify({
            'success': True,
            'example': example_data,
            'explanation': {
                'sell_pnl': 'Sell P&L = (Entry LTP - Current LTP) × Quantity = (110 - 90) × 225 = +4500',
                'buy_pnl': 'Buy P&L = (Current LTP - Entry LTP) × Quantity = (70 - 80) × 225 = -2250',
                'total_pnl': 'Total P&L = Sell P&L + Buy P&L = 4500 + (-2250) = +2250',
                'logic': 'We profit when option prices decrease (favorable for credit spreads)'
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in test_pnl_calculation: {str(e)}")
        return jsonify({'error': str(e)}), 500

from flask import jsonify
from datetime import datetime, date, timedelta
import pytz
from app import db
from sqlalchemy import and_, or_, func
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
