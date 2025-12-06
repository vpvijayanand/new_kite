from flask import Blueprint, render_template, request, jsonify
from app.services.datetime_filter_service import DateTimeFilterService
from app.services.oi_crossover_service import OICrossoverService
from app.middlewares.auth_middleware import login_required

oi_crossover_bp = Blueprint('oi_crossover', __name__)

@oi_crossover_bp.route('/oi-crossover')
@login_required
def oi_crossover():
    """OI Change Crossover analysis page"""
    try:
        # Initialize services
        date_filter = DateTimeFilterService()
        
        # Parse simplified parameters
        target_date_str = request.args.get('target_date')
        start_time_str = request.args.get('start_time', '09:15')
        end_time_str = request.args.get('end_time', '15:30')
        underlying = request.args.get('underlying', 'NIFTY')
        
        # Use target_date for both start and end date
        if target_date_str:
            target_date = date_filter.parse_date(target_date_str)
        else:
            target_date = date_filter.get_today()
        
        # Parse times
        start_time = date_filter.parse_time(start_time_str) if start_time_str else date_filter.parse_time('09:15')
        end_time = date_filter.parse_time(end_time_str) if end_time_str else date_filter.parse_time('15:30')
        
        # Get initial summary data
        oi_service = OICrossoverService()
        summary_data = oi_service.get_oi_crossover_summary(
            start_date=target_date,
            end_date=target_date, 
            start_time=start_time,
            end_time=end_time,
            underlying=underlying
        )
        
        return render_template('oi_crossover.html',
                             summary_data=summary_data,
                             target_date=target_date.strftime('%Y-%m-%d') if target_date else '',
                             start_time=start_time.strftime('%H:%M') if start_time else '09:15',
                             end_time=end_time.strftime('%H:%M') if end_time else '15:30',
                             underlying=underlying)
    
    except Exception as e:
        print(f"Error in OI crossover page: {str(e)}")
        return render_template('oi_crossover.html',
                             summary_data={
                                 'total_pe_change_percent': 0,
                                 'total_ce_change_percent': 0, 
                                 'total_difference_percent': 0,
                                 'error': str(e)
                             },
                             target_date='',
                             start_time='09:15',
                             end_time='15:30',
                             underlying='NIFTY')

@oi_crossover_bp.route('/api/oi-crossover-summary')
def api_oi_crossover_summary():
    """API endpoint for OI crossover summary data"""
    try:
        # Initialize services
        date_filter = DateTimeFilterService()
        
        # Parse simplified parameters
        target_date_str = request.args.get('target_date')
        start_time_str = request.args.get('start_time', '09:15')
        end_time_str = request.args.get('end_time', '15:30')
        underlying = request.args.get('underlying', 'NIFTY')
        
        # Use target_date for both start and end date
        if target_date_str:
            target_date = date_filter.parse_date(target_date_str)
        else:
            target_date = date_filter.get_today()
            
        # Parse times
        start_time = date_filter.parse_time(start_time_str) if start_time_str else date_filter.parse_time('09:15')
        end_time = date_filter.parse_time(end_time_str) if end_time_str else date_filter.parse_time('15:30')
        
        # Get summary data
        oi_service = OICrossoverService()
        summary_data = oi_service.get_oi_crossover_summary(
            start_date=target_date,
            end_date=target_date,
            start_time=start_time, 
            end_time=end_time,
            underlying=underlying
        )
        
        return jsonify({
            'success': True,
            'data': summary_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'total_pe_change_percent': 0,
                'total_ce_change_percent': 0,
                'total_difference_percent': 0
            }
        })

@oi_crossover_bp.route('/api/oi-crossover-chart')
def api_oi_crossover_chart():
    """API endpoint for OI crossover chart data"""
    try:
        # Initialize services
        date_filter = DateTimeFilterService()
        
        # Parse simplified parameters
        target_date_str = request.args.get('target_date')
        start_time_str = request.args.get('start_time', '09:15')
        end_time_str = request.args.get('end_time', '15:30')
        underlying = request.args.get('underlying', 'NIFTY').upper()
        
        # Use target_date for both start and end date
        if target_date_str:
            target_date = date_filter.parse_date(target_date_str)
        else:
            target_date = date_filter.get_today()
            
        # Parse times
        start_time = date_filter.parse_time(start_time_str) if start_time_str else date_filter.parse_time('09:15')
        end_time = date_filter.parse_time(end_time_str) if end_time_str else date_filter.parse_time('15:30')
        
        # Get chart data
        oi_service = OICrossoverService()
        chart_data = oi_service.get_oi_crossover_chart_data(
            underlying=underlying,
            start_date=target_date,
            end_date=target_date,
            start_time=start_time,
            end_time=end_time
        )
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'labels': [],
                'pe_changes': [],
                'ce_changes': [], 
                'index_prices': []
            }
        })
