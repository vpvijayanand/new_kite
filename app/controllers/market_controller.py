from flask import Blueprint, render_template, jsonify, current_app, request, redirect, url_for, send_from_directory
from app.services.market_service import MarketService
from app.services.chart_service import ChartService
from app.services.datetime_filter_service import DateTimeFilterService
from app.middlewares.auth_middleware import login_required
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, date
from app.controllers.oi_controller import oi_changes
from app import db

market_bp = Blueprint('market', __name__)

# Initialize scheduler
scheduler = BackgroundScheduler()

def fetch_price_job():
    """Background job to fetch prices and option data every minute"""
    try:
        # Use stored app reference if available, otherwise try current_app
        app = getattr(fetch_price_job, 'app', None)
        if app:
            with app.app_context():
                market_service = MarketService()
                
                # Fetch Nifty price
                market_service.fetch_and_save_nifty_price()
                
                # Fetch BankNifty price
                market_service.fetch_and_save_banknifty_price()
                
                # Fetch option chain data (every 2 minutes to avoid rate limits)
                current_minute = datetime.now().minute
                if current_minute % 2 == 0:  # Every 2 minutes
                    market_service.fetch_and_save_option_chain("NIFTY")
                    market_service.fetch_and_save_option_chain("BANKNIFTY")
                
                # Fetch futures data (every 5 minutes to avoid rate limits)
                if current_minute % 5 == 0:  # Every 5 minutes
                    market_service.fetch_and_save_futures_data("NIFTY")
                    market_service.fetch_and_save_futures_data("BANKNIFTY")
                
                print(f"Market data fetched at {datetime.now()}")
        else:
            with current_app.app_context():
                market_service = MarketService()
                market_service.fetch_and_save_nifty_price()
                market_service.fetch_and_save_banknifty_price()
                
                # Fetch option chain data every 2 minutes
                current_minute = datetime.now().minute
                if current_minute % 2 == 0:
                    market_service.fetch_and_save_option_chain("NIFTY")
                    market_service.fetch_and_save_option_chain("BANKNIFTY")
                
                # Fetch futures data every 5 minutes
                if current_minute % 5 == 0:
                    market_service.fetch_and_save_futures_data("NIFTY")
                    market_service.fetch_and_save_futures_data("BANKNIFTY")
                
                print(f"Market data fetched at {datetime.now()}")
    except Exception as e:
        print(f"Error in scheduled job: {str(e)}")

def strategy_1_monitor_job():
    """Background job to monitor Strategy 1 every minute during market hours"""
    try:
        # Import here to avoid circular imports
        from app.services.strategy_service import StrategyService
        
        app = getattr(strategy_1_monitor_job, 'app', None)
        if app:
            with app.app_context():
                strategy_service = StrategyService()
                
                # Only run during market hours (9:30 AM - 3:15 PM IST)
                if strategy_service.is_market_hours():
                    # Execute strategy logic
                    result = strategy_service.execute_strategy_1()
                    if result.get('success'):
                        print(f"Strategy 1 monitoring completed at {datetime.now()}")
                    else:
                        print(f"Strategy 1 monitoring error: {result.get('message', 'Unknown error')}")
                else:
                    print(f"Strategy 1 monitoring skipped - outside market hours at {datetime.now()}")
        else:
            print("Strategy 1 monitoring failed - no app context")
    except ImportError as ie:
        print(f"Strategy service not available: {str(ie)}")
    except Exception as e:
        print(f"Error in Strategy 1 monitoring job: {str(e)}")

# Initialize scheduler after app context is available
def init_scheduler(app):
    """Initialize the background scheduler"""
    if not scheduler.running:
        scheduler.add_job(
            func=fetch_price_job,
            trigger="interval",
            minutes=1,
            id='fetch_nifty_price',
            replace_existing=True
        )
        
        # Add Strategy 1 monitoring job (every minute during market hours)
        try:
            scheduler.add_job(
                func=strategy_1_monitor_job,
                trigger="interval",
                minutes=1,
                id='strategy_1_monitor',
                replace_existing=True
            )
            print("Strategy 1 monitoring job added successfully")
        except Exception as e:
            print(f"Failed to add Strategy 1 monitoring job: {str(e)}")
        
        scheduler.start()
        
        # Store reference to app for context
        fetch_price_job.app = app
        try:
            strategy_1_monitor_job.app = app
        except:
            pass  # Ignore if strategy job function is not available
    
    # Initialize signal generation scheduler
    try:
        from app.services.signal_scheduler import init_signal_scheduler
        init_signal_scheduler(app)
        print("✅ Signal generation scheduler initialized successfully")
    except ImportError as ie:
        print(f"⚠️ Signal scheduler not available: {str(ie)}")
    except Exception as e:
        print(f"⚠️ Signal scheduler initialization warning: {str(e)}")

@market_bp.route('/')
def index():
    return redirect(url_for('market.dashboard_new'))

@market_bp.route('/test-dashboard')
def test_dashboard():
    return send_from_directory('.', 'test_dashboard.html')

@market_bp.route('/dashboard')
# @login_required  # Temporarily disabled for testing
def dashboard():
    try:
        # Try to get the dashboard data
        market_service = MarketService()
        dashboard_data = market_service.get_dashboard_data()
        print(f"Dashboard data loaded successfully: {dashboard_data}")
        return render_template('dashboard.html', **dashboard_data)
    except Exception as e:
        print(f"Error loading dashboard data: {str(e)}")
        # If data loading fails, provide fallback data for dashboard template
        fallback_data = {
            'nifty_price': {'price': 26134.75, 'change_percent': 0.81},
            'banknifty_price': {'price': 59605.8, 'change_percent': 0.53}
        }
        return render_template('dashboard.html', **fallback_data)

@market_bp.route('/dashboard-new')
# @login_required  # Temporarily disabled for testing
def dashboard_new():
    try:
        # Initialize services
        market_service = MarketService()
        date_filter = DateTimeFilterService()
        
        # Parse date/time parameters with today as default
        start_date, end_date, start_time, end_time = date_filter.parse_date_params(
            request.args, default_today=True
        )
        
        # Get comprehensive dashboard data
        dashboard_data = market_service.get_comprehensive_dashboard_data()
        
        # Add date filter parameters for template
        dashboard_data.update({
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
            'start_time': start_time.strftime('%H:%M') if start_time else None,
            'end_time': end_time.strftime('%H:%M') if end_time else None,
            'today_date': date.today().strftime('%Y-%m-%d')
        })
        
        return render_template('dashboard_new.html', **dashboard_data)
    except Exception as e:
        print(f"Error loading new dashboard data: {str(e)}")
        # Fallback data for new dashboard with current market values
        fallback_data = {
            'nifty_price': {'price': 26134.75, 'change_percent': 0.81},
            'banknifty_price': {'price': 59605.8, 'change_percent': 0.53},
            'top_gainers': [],
            'top_losers': [],
            'influence_summary': {'positive': 0.0, 'negative': 0.0, 'net': 0.0},
            'start_date': date.today().strftime('%Y-%m-%d'),
            'end_date': date.today().strftime('%Y-%m-%d'),
            'start_time': '09:00',
            'end_time': '15:30',
            'today_date': date.today().strftime('%Y-%m-%d')
        }
        return render_template('dashboard_new.html', **fallback_data)

@market_bp.route('/nifty-prices')
@login_required
def nifty_prices():
    # Initialize date filter service
    date_filter = DateTimeFilterService()
    
    # Parse date/time parameters with today as default
    start_date, end_date, start_time, end_time = date_filter.parse_date_params(
        request.args, default_today=True
    )
    
    return render_template('nifty_prices.html',
                         start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
                         end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
                         start_time=start_time.strftime('%H:%M') if start_time else None,
                         end_time=end_time.strftime('%H:%M') if end_time else None)

@market_bp.route('/nifty-chart')
@login_required
def nifty_chart():
    """NIFTY Index Chart with 30-min MACD Analysis"""
    # Initialize date filter service
    date_filter = DateTimeFilterService()
    
    # Parse date/time parameters with today as default
    start_date, end_date, start_time, end_time = date_filter.parse_date_params(
        request.args, default_today=True
    )
    
    # Get timeframe from query params
    timeframe = request.args.get('timeframe', '30min')
    days_back = int(request.args.get('days', 30))
    
    # Create start and end datetime for chart service
    start_datetime = datetime.combine(start_date, start_time) if start_date else None
    end_datetime = datetime.combine(end_date, end_time) if end_date else None
    
    # Generate chart using our custom service with date filter
    chart_service = ChartService()
    chart_data = chart_service.generate_interactive_chart_with_date_filter(
        timeframe=timeframe, 
        days_back=days_back,
        start_datetime=start_datetime,
        end_datetime=end_datetime
    )
    
    # Add date filter parameters for template
    if isinstance(chart_data, dict):
        chart_data.update({
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
            'start_time': start_time.strftime('%H:%M') if start_time else None,
            'end_time': end_time.strftime('%H:%M') if end_time else None,
            'today_date': date.today().strftime('%Y-%m-%d'),
            'timeframe': timeframe,
            'days_back': days_back
        })
    
    return render_template('nifty_chart_custom.html', **chart_data)

@market_bp.route('/option-chain')
@login_required
def option_chain():
    """Option chain analysis page"""
    underlying = request.args.get('underlying', 'NIFTY')
    
    # Initialize date filter service
    date_filter = DateTimeFilterService()
    
    # Parse date/time parameters with today as default
    start_date, end_date, start_time, end_time = date_filter.parse_date_params(
        request.args, default_today=True
    )
    
    return render_template('option_chain.html', 
                         underlying=underlying,
                         start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
                         end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
                         start_time=start_time.strftime('%H:%M') if start_time else None,
                         end_time=end_time.strftime('%H:%M') if end_time else None)

@market_bp.route('/oi-analysis')
@login_required
def oi_analysis():
    """Detailed OI analysis page"""
    underlying = request.args.get('underlying', 'NIFTY')
    
    # Initialize date filter service
    date_filter = DateTimeFilterService()
    
    # Parse date/time parameters with today as default
    start_date, end_date, start_time, end_time = date_filter.parse_date_params(
        request.args, default_today=True
    )
    
    return render_template('oi_analysis.html', 
                         underlying=underlying,
                         start_date=start_date.strftime('%Y-%m-%d') if start_date else None,
                         end_date=end_date.strftime('%Y-%m-%d') if end_date else None,
                         start_time=start_time.strftime('%H:%M') if start_time else None,
                         end_time=end_time.strftime('%H:%M') if end_time else None)

@market_bp.route('/fetch-now')
@login_required
def fetch_now():
    """Manual trigger to fetch current prices and option data"""
    try:
        market_service = MarketService()
        
        # Fetch both prices
        nifty_data = market_service.fetch_and_save_nifty_price()
        banknifty_data = market_service.fetch_and_save_banknifty_price()
        
        # Fetch option chains
        nifty_options = market_service.fetch_and_save_option_chain("NIFTY")
        banknifty_options = market_service.fetch_and_save_option_chain("BANKNIFTY")
        
        return jsonify({
            'success': True,
            'data': {
                'nifty': nifty_data,
                'banknifty': banknifty_data,
                'nifty_options_count': len(nifty_options) if nifty_options else 0,
                'banknifty_options_count': len(banknifty_options) if banknifty_options else 0
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@market_bp.route('/api/current-nifty')
@login_required
def api_current_nifty():
    """API endpoint for current NIFTY price data"""
    try:
        market_service = MarketService()
        
        # Get current and previous NIFTY price
        current_price = market_service.get_current_nifty_price()
        
        if not current_price:
            return jsonify({
                'success': False,
                'message': 'No NIFTY data available'
            }), 404
        
        # Get previous day's closing price for change calculation
        from app.models.nifty_price import NiftyPrice
        from datetime import date, timedelta
        import pytz
        
        ist = pytz.timezone('Asia/Kolkata')
        yesterday = date.today() - timedelta(days=1)
        
        previous_close = db.session.query(NiftyPrice).filter(
            db.func.date(NiftyPrice.timestamp) == yesterday
        ).order_by(NiftyPrice.timestamp.desc()).first()
        
        # Calculate change
        change = 0
        change_percent = 0
        if previous_close:
            prev_price = float(previous_close.price)
            curr_price = float(current_price['price'])
            change = curr_price - prev_price
            change_percent = (change / prev_price) * 100
        
        return jsonify({
            'success': True,
            'price': float(current_price['price']),
            'high': float(current_price.get('high', 0)),
            'low': float(current_price.get('low', 0)),
            'change': change,
            'change_percent': change_percent,
            'timestamp': current_price['timestamp'].isoformat() if current_price.get('timestamp') else None,
            'last_updated': datetime.now(ist).isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting current NIFTY data: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@market_bp.route('/api/macd-analysis')
@login_required  
def api_macd_analysis():
    """API endpoint for NIFTY MACD analysis"""
    try:
        from app.services.technical_analysis_service import TechnicalAnalysisService
        
        timeframe = request.args.get('timeframe', 30, type=int)
        
        ta_service = TechnicalAnalysisService()
        analysis = ta_service.get_nifty_macd_analysis(timeframe)
        
        return jsonify({
            'success': True,
            'macd_data': analysis['macd_data'],
            'signal_history': analysis['signal_history'],
            'timeframe': f'{timeframe} minutes',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting MACD analysis: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@market_bp.route('/api/signal-stats')
@login_required
def api_signal_stats():
    """API endpoint for signal statistics"""
    try:
        from app.services.technical_analysis_service import TechnicalAnalysisService
        
        ta_service = TechnicalAnalysisService()
        stats = ta_service.get_signal_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting signal stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@market_bp.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API endpoint for dashboard data - real data only"""
    try:
        market_service = MarketService()
        data = market_service.get_dashboard_data()
        
        # Return only real data - no demo fallbacks
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@market_bp.route('/api/option-chain/<underlying>')
@login_required
def api_option_chain(underlying):
    """API endpoint for option chain data - real data only"""
    try:
        # Check if we have custom expiry settings
        from app.models.expiry_settings import ExpirySettings
        custom_expiry = None
        try:
            setting = ExpirySettings.query.filter_by(underlying=underlying.upper()).first()
            if setting:
                custom_expiry = setting.current_expiry
        except:
            pass
        
        # Get market service - only real database data
        market_service = MarketService()
        option_data = market_service.get_current_option_chain(underlying.upper())
        trend_data = market_service.get_market_trend(underlying.upper())
        
        # Convert SQLAlchemy objects to dictionaries
        option_data_dicts = []
        if option_data:
            option_data_dicts = [opt.to_dict() for opt in option_data]
        
        # Return only real database data - no demo fallbacks
        return jsonify({
            'success': True,
            'data': {
                'option_chain': option_data_dicts,
                'trend': trend_data.to_dict() if trend_data else None,
                'demo_mode': False,
                'using_custom_expiry': bool(custom_expiry),
                'custom_expiry_date': custom_expiry.isoformat() if custom_expiry else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@market_bp.route('/api/oi-analysis/<underlying>')
@login_required  
def api_oi_analysis(underlying):
    """API endpoint for detailed OI analysis - real data only"""
    try:
        market_service = MarketService()
        oi_data = market_service.get_oi_analysis_data(underlying.upper())
        
        # Return only real data - no demo fallbacks
        return jsonify({
            'success': True,
            'data': [opt.to_dict() for opt in oi_data] if oi_data else []
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@market_bp.route('/oi-changes')
@login_required
def oi_changes_page():
    """Display OI changes analysis page"""
    from app.controllers.oi_controller import oi_changes
    return oi_changes()

@market_bp.route('/oi-history')
@login_required
def oi_history_page():
    """Display OI history analysis page"""
    from app.controllers.oi_controller import oi_history
    return oi_history()

@market_bp.route('/strategy-analysis')
@login_required
def strategy_analysis_page():
    """Display strategy analysis page"""
    return render_template('strategy_analysis.html', 
                         current_time=datetime.now())

@market_bp.route('/all-oi-analysis')
@login_required
def all_oi_analysis_page():
    """Display all OI analysis page"""
    return render_template('all_oi_analysis.html', 
                         current_time=datetime.now())

@market_bp.route('/nifty-stocks')
@login_required
def nifty_stocks_page():
    """Display NIFTY 50 stocks analysis page"""
    from app.controllers.nifty_stocks_controller import nifty_stocks_page
    return nifty_stocks_page()

@market_bp.route('/api/dashboard-comprehensive')
def dashboard_comprehensive_api():
    """API endpoint for comprehensive dashboard data with date filtering"""
    try:
        # Initialize services
        market_service = MarketService()
        date_filter = DateTimeFilterService()
        
        # Parse date/time parameters with today as default
        start_date, end_date, start_time, end_time = date_filter.parse_date_params(
            request.args, default_today=True
        )
        
        # Get comprehensive dashboard data with date filters
        dashboard_data = market_service.get_comprehensive_dashboard_data(
            start_date=start_date, 
            end_date=end_date,
            start_time=start_time,
            end_time=end_time
        )
        return jsonify(dashboard_data)
    except Exception as e:
        print(f"Error in comprehensive dashboard data API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@market_bp.route('/api/oi-timeline')
def oi_timeline_api():
    """API endpoint for OI timeline data for charts"""
    try:
        instrument_type = request.args.get('type', 'NIFTY').upper()
        market_service = MarketService()
        
        # Get OI timeline data for the specified instrument
        if instrument_type == 'NIFTY':
            timeline_data = market_service.get_nifty_oi_timeline_chart_data()
        elif instrument_type == 'BANKNIFTY':
            timeline_data = market_service.get_banknifty_oi_timeline_chart_data()
        else:
            return jsonify({'error': 'Invalid instrument type'}), 400
            
        return jsonify(timeline_data)
    except Exception as e:
        print(f"Error in OI timeline API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@market_bp.route('/api/market-signal')
def api_market_signal():
    """API endpoint for market signal analysis with date filtering"""
    try:
        # Initialize services
        market_service = MarketService()
        date_filter = DateTimeFilterService()
        
        # Parse date/time parameters with today as default
        start_date, end_date, start_time, end_time = date_filter.parse_date_params(
            request.args, default_today=True
        )
        
        # Get market signal analysis for the specified date
        signal_data = market_service.get_market_signal_analysis(
            target_date=end_date if end_date else None
        )
        return jsonify({
            'success': True,
            'data': signal_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'signal_score': 0,
                'signal_text': 'NEUTRAL',
                'signal_color': '#ffd700',
                'details': {}
            }
        })

@market_bp.route('/api/market-signal-debug')
def api_market_signal_debug():
    """Debug API endpoint for detailed market signal analysis"""
    try:
        market_service = MarketService()
        signal_data = market_service.get_market_signal_analysis()
        
        # Add additional debug information
        debug_info = {
            'current_time_utc': datetime.utcnow().isoformat(),
            'current_time_ist': (datetime.utcnow() + timedelta(hours=5, minutes=30)).isoformat(),
            'market_hours_check': '9:00 AM - 3:45 PM IST',
        }
        
        # Get raw data counts for verification
        from app.models.nifty_price import NiftyPrice
        from app.models.banknifty_price import BankNiftyPrice, OptionChainData
        
        # Count of recent data
        recent_time = datetime.utcnow() - timedelta(hours=24)
        debug_info['data_counts'] = {
            'nifty_prices_24h': NiftyPrice.query.filter(NiftyPrice.timestamp >= recent_time).count(),
            'banknifty_prices_24h': BankNiftyPrice.query.filter(BankNiftyPrice.timestamp >= recent_time).count(),
            'nifty_options_24h': OptionChainData.query.filter(
                OptionChainData.timestamp >= recent_time,
                OptionChainData.underlying == 'NIFTY'
            ).count(),
            'banknifty_options_24h': OptionChainData.query.filter(
                OptionChainData.timestamp >= recent_time,
                OptionChainData.underlying == 'BANKNIFTY'
            ).count()
        }
        
        # Get latest prices for verification
        latest_nifty = NiftyPrice.query.order_by(NiftyPrice.timestamp.desc()).first()
        latest_banknifty = BankNiftyPrice.query.order_by(BankNiftyPrice.timestamp.desc()).first()
        
        debug_info['latest_data'] = {
            'nifty': {
                'price': latest_nifty.price if latest_nifty else None,
                'timestamp': latest_nifty.timestamp.isoformat() if latest_nifty else None
            },
            'banknifty': {
                'price': latest_banknifty.price if latest_banknifty else None,
                'timestamp': latest_banknifty.timestamp.isoformat() if latest_banknifty else None
            }
        }
        
        return jsonify({
            'success': True,
            'signal_data': signal_data,
            'debug_info': debug_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'signal_data': {
                'signal_score': 0,
                'signal_text': 'ERROR',
                'signal_color': '#ff0000'
            }
        })

@market_bp.route('/api/sector-performance')
def get_sector_performance():
    """Get NIFTY 50 sector-wise performance data"""
    try:
        market_service = MarketService()
        sector_data = market_service.get_sector_wise_performance()
        
        return jsonify({
            'success': True,
            'data': sector_data,
            'total_sectors': len(sector_data),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500

@market_bp.route('/api/top-oi-strikes')
def get_top_oi_strikes():
    """Get top OI change strikes for NIFTY and BANKNIFTY"""
    try:
        market_service = MarketService()
        strikes_data = market_service.get_top_oi_strikes()
        
        return jsonify({
            'success': True,
            'data': strikes_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {'NIFTY': [], 'BANKNIFTY': []}
        }), 500

@market_bp.route('/api/chart-data')
def get_chart_data():
    """Get NIFTY chart data with MACD"""
    try:
        timeframe = request.args.get('timeframe', '30min')
        days_back = int(request.args.get('days', 30))
        
        chart_service = ChartService()
        chart_data = chart_service.generate_interactive_chart(timeframe, days_back)
        
        return jsonify(chart_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@market_bp.route('/api/macd-signal')
def get_macd_signal():
    """Get current MACD signal analysis"""
    try:
        timeframe = request.args.get('timeframe', '30min')
        
        chart_service = ChartService()
        signal_data = chart_service.get_signal_analysis(timeframe)
        
        if signal_data:
            return jsonify({
                'success': True,
                'signal_data': signal_data,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No MACD data available'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500