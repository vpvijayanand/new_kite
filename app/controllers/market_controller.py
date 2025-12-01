from flask import Blueprint, render_template, jsonify, current_app, request
from app.services.market_service import MarketService
from app.middlewares.auth_middleware import login_required
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.controllers.oi_controller import oi_changes

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
                
                print(f"Market data fetched at {datetime.now()}")
    except Exception as e:
        print(f"Error in scheduled job: {str(e)}")

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
        scheduler.start()
        
        # Store reference to app for context
        fetch_price_job.app = app

@market_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        market_service = MarketService()
        dashboard_data = market_service.get_dashboard_data()
        return render_template('dashboard.html', **dashboard_data)
    except Exception as e:
        print(f"Error loading dashboard: {str(e)}")
        return render_template('dashboard.html')

@market_bp.route('/nifty-prices')
@login_required
def nifty_prices():
    return render_template('nifty_prices.html')

@market_bp.route('/option-chain')
@login_required
def option_chain():
    """Option chain analysis page"""
    underlying = request.args.get('underlying', 'NIFTY')
    return render_template('option_chain.html', underlying=underlying)

@market_bp.route('/oi-analysis')
@login_required
def oi_analysis():
    """Detailed OI analysis page"""
    underlying = request.args.get('underlying', 'NIFTY')
    return render_template('oi_analysis.html', underlying=underlying)

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