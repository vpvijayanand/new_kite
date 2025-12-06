from flask import Blueprint, render_template, request, jsonify
from app.services.futures_oi_service import FuturesOIService
from app.services.datetime_filter_service import DateTimeFilterService
import logging

futures_oi_bp = Blueprint('futures_oi', __name__)

@futures_oi_bp.route('/futures-oi-analysis')
def futures_oi_analysis():
    """Futures OI Analysis page"""
    try:
        # Get filter parameters
        target_date = request.args.get('target_date')
        start_time = request.args.get('start_time', '09:15')
        end_time = request.args.get('end_time', '15:30')
        underlying = request.args.get('underlying', 'NIFTY')
        
        # Get today's date if no date provided
        if not target_date:
            target_date = DateTimeFilterService.get_today()
        
        return render_template('futures_oi_analysis.html',
                             target_date=target_date,
                             start_time=start_time,
                             end_time=end_time,
                             underlying=underlying)
    except Exception as e:
        logging.error(f"Error in futures_oi_analysis: {str(e)}")
        return render_template('futures_oi_analysis.html',
                             target_date=DateTimeFilterService.get_today(),
                             start_time='09:15',
                             end_time='15:30',
                             underlying='NIFTY')

@futures_oi_bp.route('/api/futures-oi-data')
def futures_oi_data_api():
    """API endpoint for futures OI analysis data"""
    try:
        # Get parameters
        target_date = request.args.get('target_date')
        start_time = request.args.get('start_time', '09:15')
        end_time = request.args.get('end_time', '15:30')
        underlying = request.args.get('underlying', 'NIFTY')
        
        if not target_date:
            target_date = DateTimeFilterService.get_today()
        
        # Get futures OI service
        service = FuturesOIService()
        
        # Get futures OI analysis data
        data = service.get_futures_oi_analysis(
            underlying=underlying,
            start_date=target_date,
            end_date=target_date,
            start_time=start_time,
            end_time=end_time
        )
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logging.error(f"Error in futures_oi_data_api: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        })
