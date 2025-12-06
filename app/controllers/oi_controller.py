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


def oi_changes_timeline_api():
    """API endpoint for OI changes timeline data for chart"""
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta, time
        from flask import request
        from app.services.datetime_filter_service import DateTimeFilterService
        
        # Get underlying parameter (default to NIFTY)
        underlying = request.args.get('underlying', 'NIFTY').upper()
        
        # Initialize date filter service
        date_filter = DateTimeFilterService()
        
        # Parse date/time parameters with today as default
        start_date, end_date, start_time, end_time = date_filter.parse_date_params(
            request.args, default_today=True
        )
        
        # Use the filter service to get the target date
        target_date = DateTimeFilterService.get_target_date(start_date, end_date)
        
        # Get market hours for the target date: 9:20 AM to 15:30 IST and convert to UTC
        from datetime import timezone, timedelta
        today = target_date
        
        # Create IST timezone
        ist_timezone = timezone(timedelta(hours=5, minutes=30))
        
        # Create 9:20 AM IST time
        market_start_ist = datetime.combine(today, time(9, 20)).replace(tzinfo=ist_timezone)
        
        # Create 15:30 IST time (market close)
        market_end_ist = datetime.combine(today, time(15, 30)).replace(tzinfo=ist_timezone)
        
        # Convert to UTC for database query
        market_start_utc = market_start_ist.astimezone(timezone.utc).replace(tzinfo=None)
        market_end_utc = market_end_ist.astimezone(timezone.utc).replace(tzinfo=None)
        
        # Get all records from 9:20 AM today grouped by minute for better readability
        timeline_data = db.session.query(
            func.date_trunc('minute', OptionChainData.timestamp).label('time_bucket'),
            func.sum(OptionChainData.ce_oi_change).label('total_ce_change'),
            func.sum(OptionChainData.pe_oi_change).label('total_pe_change')
        ).filter(
            OptionChainData.timestamp >= market_start_utc,
            OptionChainData.timestamp <= market_end_utc,
            OptionChainData.underlying == underlying
        ).group_by(func.date_trunc('minute', OptionChainData.timestamp)).order_by(func.date_trunc('minute', OptionChainData.timestamp)).all()
        
        # Get corresponding index prices for the timeline
        if underlying == 'NIFTY':
            from app.models.nifty_price import NiftyPrice
            price_model = NiftyPrice
        else:
            from app.models.banknifty_price import BankNiftyPrice
            price_model = BankNiftyPrice
        
        # Format data for chart
        chart_data = {
            'labels': [],
            'ce_changes': [],
            'pe_changes': [],
            'index_prices': []
        }
        
        cumulative_ce_change = 0
        cumulative_pe_change = 0
        
        for record in timeline_data:
            # Convert timestamp to IST and format for display
            ist_time = utc_to_ist(record.time_bucket)
            time_label = ist_time.strftime('%H:%M')
            
            # Calculate cumulative changes
            cumulative_ce_change += (record.total_ce_change or 0)
            cumulative_pe_change += (record.total_pe_change or 0)
            
            # Get corresponding index price (within 5 minutes of the OI timestamp)
            price_record = price_model.query.filter(
                func.abs(func.extract('epoch', price_model.timestamp) - func.extract('epoch', record.time_bucket)) < 300
            ).order_by(func.abs(func.extract('epoch', price_model.timestamp) - func.extract('epoch', record.time_bucket))).first()
            
            index_price = price_record.price if price_record else (26000 if underlying == 'NIFTY' else 59000)
            
            chart_data['labels'].append(time_label)
            chart_data['ce_changes'].append(cumulative_ce_change)
            chart_data['pe_changes'].append(cumulative_pe_change)
            chart_data['index_prices'].append(float(index_price))
        
        return jsonify({
            'success': True,
            'data': chart_data,
            'last_updated': utc_to_ist(datetime.utcnow()).isoformat()
        })
        
    except Exception as e:
        print(f"Error in oi_changes_timeline_api: {e}")
        return jsonify({
            'success': False,
            'error': 'Error loading timeline data'
        }), 500


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
        return render_template('oi_history.html', 
                             current_time=datetime.utcnow())
    except Exception as e:
        print(f"Error in oi_history: {e}")
        return render_template('oi_history.html', 
                             error="Error loading OI history page")


def get_strikes_api(underlying):
    """API endpoint for getting available strikes for underlying"""
    try:
        from sqlalchemy import distinct
        available_strikes = db.session.query(
            distinct(OptionChainData.strike_price)
        ).filter(
            OptionChainData.underlying == underlying.upper()
        ).order_by(OptionChainData.strike_price).all()
        
        strikes = [float(strike[0]) for strike in available_strikes]
        
        return jsonify({
            'success': True,
            'strikes': strikes
        })
        
    except Exception as e:
        print(f"Error in get_strikes_api: {e}")
        return jsonify({
            'success': False,
            'message': f'Error loading strikes: {str(e)}'
        }), 500


def get_oi_history_data(underlying, strike_price, option_type):
    """API endpoint for OI history data for specific underlying, strike and option type"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import and_
        
        strike = float(strike_price)
        
        # Get today's date (start of day in IST)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get all records for this strike from today
        records = db.session.query(OptionChainData).filter(
            and_(
                OptionChainData.underlying == underlying.upper(),
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
                
                # Calculate divergence (OI vs Price movement)
                divergence = 'neutral'
                divergence_symbol = '—'
                
                if i > 0:  # Need previous record to calculate price change
                    prev_record = records[i-1]
                    if option_type.upper() == 'CE':
                        prev_ltp = prev_record.ce_ltp
                    else:
                        prev_ltp = prev_record.pe_ltp
                    
                    price_change = current_ltp - prev_ltp
                    
                    # Divergence logic:
                    # Bullish Divergence: OI decreasing while price increasing
                    # Bearish Divergence: OI increasing while price decreasing
                    # Confluence: OI and price moving in same direction
                    
                    # Only calculate divergence for significant changes (avoid noise)
                    if abs(oi_change) > 100 and abs(price_change) > 0.01:  # Minimum thresholds
                        if oi_change > 0 and price_change < 0:
                            divergence = 'bearish'
                            divergence_symbol = '🔻'  # Bearish divergence
                        elif oi_change < 0 and price_change > 0:
                            divergence = 'bullish' 
                            divergence_symbol = '▲'  # Bullish divergence
                        elif (oi_change > 0 and price_change > 0) or (oi_change < 0 and price_change < 0):
                            divergence = 'confluence'
                            divergence_symbol = '⚡'  # Confluence (same direction)
                        else:
                            divergence_symbol = '—'
                    elif abs(oi_change) > 1000:  # Significant OI change without price change
                        divergence = 'volume_spike'
                        divergence_symbol = '📊'  # Volume spike
                    else:
                        divergence_symbol = '—'
                
                # Get index price for this timestamp
                index_price = get_index_price_for_timestamp(underlying.upper(), record.timestamp)
                
                history_data.append({
                    'timestamp': utc_to_ist(record.timestamp).strftime('%H:%M:%S'),
                    'oi': current_oi,
                    'oi_change': oi_change,
                    'oi_change_from_start': change_from_start,
                    'oi_change_percent_from_start': round(change_percent_from_start, 2),
                    'ltp': current_ltp,
                    'index_price': index_price,
                    'divergence': divergence,
                    'divergence_symbol': divergence_symbol
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


def get_index_price_for_timestamp(underlying, timestamp):
    """Get index price for specific underlying at given timestamp"""
    try:
        from app.models.nifty_price import NiftyPrice
        from app.models.banknifty_price import BankNiftyPrice
        from datetime import timedelta
        from sqlalchemy import and_
        
        # Create a time window around the timestamp (±2 minutes)
        start_time = timestamp - timedelta(minutes=2)
        end_time = timestamp + timedelta(minutes=2)
        
        if underlying == "NIFTY":
            price_record = db.session.query(NiftyPrice).filter(
                and_(
                    NiftyPrice.timestamp >= start_time,
                    NiftyPrice.timestamp <= end_time
                )
            ).order_by(NiftyPrice.timestamp.desc()).first()
        elif underlying == "BANKNIFTY":
            price_record = db.session.query(BankNiftyPrice).filter(
                and_(
                    BankNiftyPrice.timestamp >= start_time,
                    BankNiftyPrice.timestamp <= end_time
                )
            ).order_by(BankNiftyPrice.timestamp.desc()).first()
        else:
            return None
            
        return price_record.price if price_record else None
        
    except Exception as e:
        print(f"Error getting index price for {underlying} at {timestamp}: {e}")
        return None
