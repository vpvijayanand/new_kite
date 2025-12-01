from flask import render_template, jsonify, Blueprint
from app.services.nifty_stocks_service import NiftyStocksService
from datetime import datetime
from app.utils.datetime_utils import utc_to_ist

nifty_stocks_bp = Blueprint('nifty_stocks', __name__)

def nifty_stocks_page():
    """Display NIFTY 50 stocks analysis page"""
    try:
        stocks_service = NiftyStocksService()
        
        # Initialize stocks if not already done
        stocks_service.initialize_stocks()
        
        # Get current stocks data
        stocks_data = stocks_service.get_nifty_stocks_data()
        
        return render_template('nifty_stocks.html',
                             stocks_data=stocks_data,
                             current_time=datetime.utcnow())
    except Exception as e:
        print(f"Error in nifty_stocks_page: {e}")
        return render_template('nifty_stocks.html',
                             stocks_data={'stocks': [], 'total_positive_influence': 0,
                                        'total_negative_influence': 0, 'net_nifty_influence': 0,
                                        'total_stocks': 0, 'gainers': 0, 'losers': 0, 'unchanged': 0},
                             error="Error loading NIFTY 50 stocks data")

def nifty_stocks_api():
    """API endpoint for NIFTY 50 stocks data"""
    try:
        stocks_service = NiftyStocksService()
        stocks_data = stocks_service.get_nifty_stocks_data()
        
        # Convert stocks to dictionary format
        stocks_dict = []
        for stock in stocks_data['stocks']:
            stocks_dict.append(stock.to_dict())
        
        return jsonify({
            'success': True,
            'stocks': stocks_dict,
            'summary': {
                'total_positive_influence': stocks_data['total_positive_influence'],
                'total_negative_influence': stocks_data['total_negative_influence'],
                'net_nifty_influence': stocks_data['net_nifty_influence'],
                'total_stocks': stocks_data['total_stocks'],
                'gainers': stocks_data['gainers'],
                'losers': stocks_data['losers'],
                'unchanged': stocks_data['unchanged']
            },
            'last_updated': utc_to_ist(datetime.utcnow()).isoformat()
        })
    except Exception as e:
        print(f"Error in nifty_stocks_api: {e}")
        return jsonify({
            'success': False,
            'error': f'Error loading NIFTY 50 stocks: {str(e)}'
        }), 500

def update_nifty_stocks_api():
    """API endpoint to update all NIFTY 50 stock prices"""
    try:
        stocks_service = NiftyStocksService()
        updated_count = stocks_service.update_all_stock_prices()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'message': f'Updated {updated_count} stocks successfully'
        })
    except Exception as e:
        print(f"Error in update_nifty_stocks_api: {e}")
        return jsonify({
            'success': False,
            'error': f'Error updating stocks: {str(e)}'
        }), 500

def nifty_top_performers_api():
    """API endpoint for top performing stocks"""
    try:
        stocks_service = NiftyStocksService()
        performers = stocks_service.get_top_performers(limit=5)
        
        return jsonify({
            'success': True,
            'data': performers
        })
    except Exception as e:
        print(f"Error in nifty_top_performers_api: {e}")
        return jsonify({
            'success': False,
            'error': f'Error loading top performers: {str(e)}'
        }), 500

def nifty_sector_performance_api():
    """API endpoint for sector performance"""
    try:
        stocks_service = NiftyStocksService()
        sectors = stocks_service.get_sector_performance()
        
        return jsonify({
            'success': True,
            'sectors': sectors
        })
    except Exception as e:
        print(f"Error in nifty_sector_performance_api: {e}")
        return jsonify({
            'success': False,
            'error': f'Error loading sector performance: {str(e)}'
        }), 500
