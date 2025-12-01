from flask import Blueprint, render_template, jsonify, current_app
from app.services.market_service import MarketService
from app.middlewares.auth_middleware import login_required
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

market_bp = Blueprint('market', __name__)

# Initialize scheduler
scheduler = BackgroundScheduler()

def fetch_price_job():
    """Background job to fetch Nifty price every minute"""
    try:
        # Use stored app reference if available, otherwise try current_app
        app = getattr(fetch_price_job, 'app', None)
        if app:
            with app.app_context():
                market_service = MarketService()
                market_service.fetch_and_save_nifty_price()
                print(f"Price fetched at {datetime.now()}")
        else:
            with current_app.app_context():
                market_service = MarketService()
                market_service.fetch_and_save_nifty_price()
                print(f"Price fetched at {datetime.now()}")
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
    return render_template('dashboard.html')

@market_bp.route('/nifty-prices')
@login_required
def nifty_prices():
    return render_template('nifty_prices.html')

@market_bp.route('/fetch-now')
@login_required
def fetch_now():
    """Manual trigger to fetch current price"""
    try:
        market_service = MarketService()
        price_data = market_service.fetch_and_save_nifty_price()
        if price_data:
            return jsonify({
                'success': True,
                'data': price_data
            })
        return jsonify({
            'success': False,
            'message': 'Failed to fetch price'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500