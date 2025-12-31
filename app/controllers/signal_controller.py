from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, timedelta
from app.models.nifty_signal import NiftySignal
from app.services.nifty_signal_service import NiftySignalGenerator
from app.utils.datetime_utils import utc_to_ist, format_ist_time
import logging

# Create blueprint
signal_bp = Blueprint('signals', __name__, url_prefix='/signals')

logger = logging.getLogger(__name__)

@signal_bp.route('/')
def signals_dashboard():
    """Main signals dashboard page"""
    return render_template('signals_dashboard.html')

@signal_bp.route('/chart')
def signals_chart():
    """NIFTY chart with signals page"""
    return render_template('nifty_signals_chart.html')

@signal_bp.route('/api/signals')
def api_get_signals():
    """API endpoint to get signals data"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        date_str = request.args.get('date')
        signal_type = request.args.get('type')  # 'BUY' or 'SELL'
        
        # Build query
        query = NiftySignal.query
        
        # Filter by date if provided
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                start_date = datetime.combine(date, datetime.min.time())
                end_date = datetime.combine(date, datetime.max.time())
                query = query.filter(
                    NiftySignal.signal_time >= start_date,
                    NiftySignal.signal_time <= end_date
                )
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        
        # Filter by signal type if provided
        if signal_type and signal_type in ['BUY', 'SELL']:
            query = query.filter(NiftySignal.signal_type == signal_type)
        
        # Get signals with limit
        signals = query.order_by(NiftySignal.signal_time.desc()).limit(limit).all()
        
        # Convert to IST and format for response
        signals_data = []
        for signal in signals:
            signal_dict = signal.to_dict()
            # Convert UTC to IST for display
            if signal_dict['signal_time']:
                signal_dict['signal_time_ist'] = format_ist_time(
                    datetime.fromisoformat(signal_dict['signal_time'].replace('Z', '+00:00'))
                )
            signals_data.append(signal_dict)
        
        # Get performance summary
        performance = NiftySignal.get_performance_summary()
        
        return jsonify({
            'success': True,
            'data': signals_data,
            'performance': performance,
            'count': len(signals_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@signal_bp.route('/api/chart-data')
def api_get_chart_data():
    """API endpoint to get chart data with signals"""
    try:
        # Get query parameters
        hours = request.args.get('hours', 6, type=int)
        
        # Initialize signal generator
        signal_generator = NiftySignalGenerator()
        
        # Get chart data
        chart_data = signal_generator.get_chart_data_with_signals(hours=hours)
        
        if chart_data is None:
            return jsonify({
                'success': False,
                'error': 'No data available'
            }), 404
        
        # Convert timestamps to IST for display
        price_data = chart_data['price_data']
        for item in price_data:
            if item.get('timestamp'):
                item['timestamp_ist'] = format_ist_time(item['timestamp'])
        
        signals_data = chart_data['signals']
        for signal in signals_data:
            if signal.get('signal_time'):
                signal['signal_time_ist'] = format_ist_time(
                    datetime.fromisoformat(signal['signal_time'].replace('Z', '+00:00'))
                )
        
        return jsonify({
            'success': True,
            'data': {
                'price_data': price_data,
                'signals': signals_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@signal_bp.route('/api/generate-signals', methods=['POST'])
def api_generate_signals():
    """API endpoint to manually trigger signal generation"""
    try:
        # Get parameters
        lookback_hours = request.json.get('lookback_hours', 24) if request.is_json else 24
        
        # Initialize signal generator
        signal_generator = NiftySignalGenerator()
        
        # Generate signals
        new_signals = signal_generator.generate_signals(lookback_hours=lookback_hours)
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(new_signals)} new signals',
            'signals_generated': len(new_signals),
            'signals': [signal.to_dict() for signal in new_signals]
        })
        
    except Exception as e:
        logger.error(f"Error generating signals: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@signal_bp.route('/api/latest-signal')
def api_get_latest_signal():
    """API endpoint to get the latest signal"""
    try:
        latest_signal = NiftySignal.query.order_by(NiftySignal.signal_time.desc()).first()
        
        if not latest_signal:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No signals found'
            })
        
        signal_data = latest_signal.to_dict()
        if signal_data['signal_time']:
            signal_data['signal_time_ist'] = format_ist_time(
                datetime.fromisoformat(signal_data['signal_time'].replace('Z', '+00:00'))
            )
        
        return jsonify({
            'success': True,
            'data': signal_data
        })
        
    except Exception as e:
        logger.error(f"Error getting latest signal: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@signal_bp.route('/api/performance')
def api_get_performance():
    """API endpoint to get signal performance summary"""
    try:
        performance = NiftySignal.get_performance_summary()
        
        # Get recent signals for additional stats
        recent_signals = NiftySignal.query.filter(
            NiftySignal.signal_time >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        performance['recent_signals_count'] = len(recent_signals)
        performance['recent_buy_signals'] = len([s for s in recent_signals if s.signal_type == 'BUY'])
        performance['recent_sell_signals'] = len([s for s in recent_signals if s.signal_type == 'SELL'])
        
        return jsonify({
            'success': True,
            'data': performance
        })
        
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@signal_bp.route('/api/signals/<int:signal_id>')
def api_get_signal_details(signal_id):
    """API endpoint to get specific signal details"""
    try:
        signal = NiftySignal.query.get(signal_id)
        
        if not signal:
            return jsonify({
                'success': False,
                'error': 'Signal not found'
            }), 404
        
        signal_data = signal.to_dict()
        if signal_data['signal_time']:
            signal_data['signal_time_ist'] = format_ist_time(
                datetime.fromisoformat(signal_data['signal_time'].replace('Z', '+00:00'))
            )
        
        return jsonify({
            'success': True,
            'data': signal_data
        })
        
    except Exception as e:
        logger.error(f"Error getting signal details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@signal_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404

@signal_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
