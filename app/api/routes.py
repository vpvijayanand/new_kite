from flask import Blueprint, jsonify, request
from app.services.market_service import MarketService
from app.services.kite_service import KiteService
from app.controllers.oi_controller import oi_changes_api

api_bp = Blueprint('api', __name__)

@api_bp.route('/prices/latest', methods=['GET'])
def get_latest_prices():
    """API endpoint to get latest prices"""
    try:
        limit = request.args.get('limit', 100, type=int)
        market_service = MarketService()
        prices = market_service.get_latest_prices(limit)
        
        return jsonify({
            'success': True,
            'data': [price.to_dict() for price in prices]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/prices/history', methods=['GET'])
def get_price_history():
    """API endpoint to get price history"""
    try:
        hours = request.args.get('hours', 24, type=int)
        market_service = MarketService()
        prices = market_service.get_price_history(hours)
        
        return jsonify({
            'success': True,
            'data': prices
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/price/current', methods=['GET'])
def get_current_price():
    """API endpoint to get current price from Kite"""
    try:
        kite_service = KiteService()
        price_data = kite_service.get_nifty_price()
        
        return jsonify({
            'success': True,
            'data': price_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/status', methods=['GET'])
def api_status():
    """API health check"""
    return jsonify({
        'success': True,
        'message': 'API is running',
        'version': '1.0.0'
    })

@api_bp.route('/oi-changes', methods=['GET'])
def get_oi_changes():
    """API endpoint to get OI changes data"""
    return oi_changes_api()

@api_bp.route('/strikes/<underlying>', methods=['GET'])
def get_strikes(underlying):
    """API endpoint to get available strikes for underlying"""
    from app.controllers.oi_controller import get_strikes_api
    return get_strikes_api(underlying)

@api_bp.route('/oi-history/<underlying>/<strike_price>/<option_type>', methods=['GET'])
def get_oi_history(underlying, strike_price, option_type):
    """API endpoint to get OI history for specific underlying, strike and option type"""
    from app.controllers.oi_controller import get_oi_history_data
    return get_oi_history_data(underlying, strike_price, option_type)

@api_bp.route('/strategy-analysis/<underlying>/<int:strike_gap>/<int:protection_gap>', methods=['GET'])
def get_strategy_analysis(underlying, strike_gap, protection_gap):
    """API endpoint to get strategy analysis for sell high + buy higher strategy"""
    from app.controllers.strategy_controller import analyze_strategies
    return analyze_strategies(underlying, strike_gap, protection_gap)