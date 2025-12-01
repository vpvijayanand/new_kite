from flask import Blueprint, jsonify, request
from app.services.market_service import MarketService
from app.services.kite_service import KiteService

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