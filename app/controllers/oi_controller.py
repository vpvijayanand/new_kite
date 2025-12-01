from flask import render_template, jsonify, request, has_request_context
from app.models.banknifty_price import OptionChainData
from datetime import datetime
from app.utils.datetime_utils import utc_to_ist
from app import db
from sqlalchemy import distinct
from app import db


def oi_changes():
    """Display OI changes analysis page"""
    try:
        # Get top OI changes data
        oi_data = OptionChainData.get_top_oi_changes(underlying="NIFTY", limit=10)
        
        return render_template('oi_changes.html', 
                             oi_data=oi_data,
                             current_time=datetime.utcnow())
    except Exception as e:
        print(f"Error in oi_changes: {e}")
        return render_template('oi_changes.html', 
                             oi_data={},
                             error="Error loading OI changes data")


def oi_changes_api():
    """API endpoint for OI changes data"""
    try:
        limit = request.args.get('limit', 10, type=int) if has_request_context() else 10
        oi_data = OptionChainData.get_top_oi_changes(underlying="NIFTY", limit=limit)
        
        # Format data for JSON response
        response_data = {
            'ce_increases': [
                {
                    'strike': record.strike_price,
                    'oi_change': record.ce_oi_change,
                    'oi': record.ce_oi,
                    'ltp': record.ce_ltp,
                    'timestamp': utc_to_ist(record.timestamp).isoformat()
                } for record in oi_data['ce_increases']
            ],
            'ce_decreases': [
                {
                    'strike': record.strike_price,
                    'oi_change': record.ce_oi_change,
                    'oi': record.ce_oi,
                    'ltp': record.ce_ltp,
                    'timestamp': utc_to_ist(record.timestamp).isoformat()
                } for record in oi_data['ce_decreases']
            ],
            'pe_increases': [
                {
                    'strike': record.strike_price,
                    'oi_change': record.pe_oi_change,
                    'oi': record.pe_oi,
                    'ltp': record.pe_ltp,
                    'timestamp': utc_to_ist(record.timestamp).isoformat()
                } for record in oi_data['pe_increases']
            ],
            'pe_decreases': [
                {
                    'strike': record.strike_price,
                    'oi_change': record.pe_oi_change,
                    'oi': record.pe_oi,
                    'ltp': record.pe_ltp,
                    'timestamp': utc_to_ist(record.timestamp).isoformat()
                } for record in oi_data['pe_decreases']
            ],
            'last_updated': utc_to_ist(datetime.utcnow()).isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in oi_changes_api: {e}")
        return jsonify({'error': 'Error loading OI changes data'}), 500


def oi_history():
    """Display OI history analysis page"""
    try:
        # Get available strikes for dropdown
        available_strikes = db.session.query(
            distinct(OptionChainData.strike_price)
        ).filter(
            OptionChainData.underlying == "NIFTY"
        ).order_by(OptionChainData.strike_price).all()
        
        strikes = [float(strike[0]) for strike in available_strikes]
        
        return render_template('oi_history.html', 
                             available_strikes=strikes,
                             current_time=datetime.utcnow())
    except Exception as e:
        print(f"Error in oi_history: {e}")
        return render_template('oi_history.html', 
                             available_strikes=[],
                             error="Error loading OI history page")


def get_oi_history_data(strike_price, option_type):
    """API endpoint for OI history data for specific strike and option type"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import and_
        
        strike = float(strike_price)
        
        # Get today's date (start of day in IST)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get all records for this strike from today
        records = db.session.query(OptionChainData).filter(
            and_(
                OptionChainData.underlying == "NIFTY",
                OptionChainData.strike_price == strike,
                OptionChainData.timestamp >= today_start
            )
        ).order_by(OptionChainData.timestamp.asc()).all()
        
        if not records:
            return jsonify({
                'success': False,
                'message': 'No data found for this strike price'
            })
        
        # Get first and latest records for summary
        first_record = records[0]
        latest_record = records[-1]
        
        # Calculate summary based on option type
        if option_type.upper() == 'CE':
            first_oi = first_record.ce_oi
            latest_oi = latest_record.ce_oi
            first_ltp = first_record.ce_ltp
            latest_ltp = latest_record.ce_ltp
        else:  # PE
            first_oi = first_record.pe_oi
            latest_oi = latest_record.pe_oi
            first_ltp = first_record.pe_ltp
            latest_ltp = latest_record.pe_ltp
        
        # Calculate totals
        total_oi_change = latest_oi - first_oi
        total_oi_change_percent = (total_oi_change / first_oi * 100) if first_oi > 0 else 0
        total_price_change = latest_ltp - first_ltp
        total_price_change_percent = (total_price_change / first_ltp * 100) if first_ltp > 0 else 0
        
        # Build history data (only records with changes)
        history_data = []
        prev_oi = first_oi
        
        for i, record in enumerate(records):
            if option_type.upper() == 'CE':
                current_oi = record.ce_oi
                current_ltp = record.ce_ltp
                oi_change = record.ce_oi_change
            else:
                current_oi = record.pe_oi
                current_ltp = record.pe_ltp
                oi_change = record.pe_oi_change
            
            # Only include records where there's a meaningful change
            if i == 0 or abs(oi_change) > 0:
                change_from_start = current_oi - first_oi
                change_percent_from_start = (change_from_start / first_oi * 100) if first_oi > 0 else 0
                
                history_data.append({
                    'timestamp': utc_to_ist(record.timestamp).strftime('%H:%M:%S'),
                    'oi': current_oi,
                    'oi_change': oi_change,
                    'oi_change_from_start': change_from_start,
                    'oi_change_percent_from_start': round(change_percent_from_start, 2),
                    'ltp': current_ltp
                })
        
        response_data = {
            'success': True,
            'strike_price': strike,
            'option_type': option_type.upper(),
            'summary': {
                'first_oi': first_oi,
                'latest_oi': latest_oi,
                'total_oi_change': total_oi_change,
                'total_oi_change_percent': round(total_oi_change_percent, 2),
                'first_ltp': first_ltp,
                'latest_ltp': latest_ltp,
                'total_price_change': round(total_price_change, 4),
                'total_price_change_percent': round(total_price_change_percent, 2),
                'first_time': utc_to_ist(first_record.timestamp).strftime('%H:%M:%S'),
                'latest_time': utc_to_ist(latest_record.timestamp).strftime('%H:%M:%S')
            },
            'history': history_data
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in get_oi_history_data: {e}")
        return jsonify({
            'success': False,
            'message': f'Error loading OI history: {str(e)}'
        }), 500
