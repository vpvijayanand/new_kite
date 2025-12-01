from flask import jsonify
from datetime import datetime, timedelta
import pytz
from app import db
from app.models.nifty_price import NiftyPrice
from app.models.banknifty_price import BankNiftyPrice, OptionChainData
from sqlalchemy import text, desc, func

def get_all_oi_data(underlying):
    """
    Get complete OI analysis for all strikes of the specified underlying
    Returns CE OI, CE Change %, Strike Price, PE Change %, PE OI for all available strikes
    """
    try:
        # Get current index price
        current_index_price = get_current_index_price(underlying)
        
        # Get all OI data for the underlying
        strike_data = get_complete_strike_data(underlying)
        
        if not strike_data:
            return jsonify({
                'success': False,
                'message': f'No OI data found for {underlying}'
            })
        
        # Calculate summary statistics
        summary_stats = calculate_summary_stats(strike_data, current_index_price)
        
        return jsonify({
            'success': True,
            'underlying': underlying,
            'summary': summary_stats,
            'strikes': strike_data,
            'total_strikes': len(strike_data),
            'analysis_time': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error analyzing OI data: {str(e)}'
        }), 500

def get_current_index_price(underlying):
    """Get the current index price for the underlying"""
    try:
        if underlying == 'NIFTY':
            latest_price = NiftyPrice.query.order_by(desc(NiftyPrice.timestamp)).first()
            return float(latest_price.price) if latest_price else 0
        else:  # BANKNIFTY
            latest_price = BankNiftyPrice.query.order_by(desc(BankNiftyPrice.timestamp)).first()
            return float(latest_price.price) if latest_price else 0
    except Exception as e:
        print(f"Error getting current index price: {e}")
        return 0

def get_complete_strike_data(underlying):
    """Get complete OI data for all strikes"""
    try:
        # Get the latest OI data for each strike
        # We need the most recent data and also historical data to calculate changes
        
        # First, get all unique strikes for the underlying
        unique_strikes = db.session.query(
            OptionChainData.strike_price
        ).filter(
            OptionChainData.underlying == underlying
        ).distinct().order_by(OptionChainData.strike_price).all()
        
        strike_data = []
        
        for strike_tuple in unique_strikes:
            strike_price = strike_tuple[0]
            
            # Get latest data for this strike
            latest_data = OptionChainData.query.filter(
                OptionChainData.underlying == underlying,
                OptionChainData.strike_price == strike_price
            ).order_by(desc(OptionChainData.timestamp)).first()
            
            if not latest_data:
                continue
            
            # Get first data from today for change calculation (start of day)
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            first_today_data = OptionChainData.query.filter(
                OptionChainData.underlying == underlying,
                OptionChainData.strike_price == strike_price,
                OptionChainData.timestamp >= today_start
            ).order_by(OptionChainData.timestamp.asc()).first()
            
            # Calculate OI changes from start of day
            ce_oi_change_percent = 0
            pe_oi_change_percent = 0
            
            if first_today_data and first_today_data.id != latest_data.id:
                # Calculate CE OI change percentage from start of day
                if first_today_data.ce_oi and first_today_data.ce_oi > 0:
                    ce_oi_change_percent = ((latest_data.ce_oi - first_today_data.ce_oi) / first_today_data.ce_oi) * 100
                
                # Calculate PE OI change percentage from start of day
                if first_today_data.pe_oi and first_today_data.pe_oi > 0:
                    pe_oi_change_percent = ((latest_data.pe_oi - first_today_data.pe_oi) / first_today_data.pe_oi) * 100
            
            # Create strike data entry
            strike_info = {
                'strike_price': float(strike_price),
                'ce_oi': latest_data.ce_oi or 0,
                'pe_oi': latest_data.pe_oi or 0,
                'ce_oi_change_percent': round(ce_oi_change_percent, 1) if ce_oi_change_percent != 0 else 0,
                'pe_oi_change_percent': round(pe_oi_change_percent, 1) if pe_oi_change_percent != 0 else 0,
                'ce_ltp': latest_data.ce_ltp or 0,
                'pe_ltp': latest_data.pe_ltp or 0,
                'ce_volume': latest_data.ce_volume or 0,
                'pe_volume': latest_data.pe_volume or 0,
                'timestamp': latest_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            strike_data.append(strike_info)
        
        # Sort by strike price
        strike_data.sort(key=lambda x: x['strike_price'])
        
        return strike_data
        
    except Exception as e:
        print(f"Error getting complete strike data: {e}")
        return []

def calculate_summary_stats(strike_data, current_index_price):
    """Calculate summary statistics for the OI data"""
    try:
        total_ce_oi = sum(strike['ce_oi'] for strike in strike_data)
        total_pe_oi = sum(strike['pe_oi'] for strike in strike_data)
        
        # Calculate PCR (Put-Call Ratio)
        pcr_ratio = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 0
        
        # Find ATM strike (closest to current price)
        atm_strike = min(strike_data, key=lambda x: abs(x['strike_price'] - current_index_price)) if strike_data else None
        
        # Calculate max pain (strike with highest total OI)
        max_pain_strike = max(strike_data, key=lambda x: x['ce_oi'] + x['pe_oi']) if strike_data else None
        
        return {
            'total_ce_oi': int(total_ce_oi),
            'total_pe_oi': int(total_pe_oi),
            'current_index_price': current_index_price,
            'pcr_ratio': pcr_ratio,
            'atm_strike': atm_strike['strike_price'] if atm_strike else 0,
            'max_pain_strike': max_pain_strike['strike_price'] if max_pain_strike else 0,
            'total_strikes': len(strike_data)
        }
        
    except Exception as e:
        print(f"Error calculating summary stats: {e}")
        return {
            'total_ce_oi': 0,
            'total_pe_oi': 0,
            'current_index_price': current_index_price,
            'pcr_ratio': 0,
            'atm_strike': 0,
            'max_pain_strike': 0,
            'total_strikes': 0
        }

def get_oi_changes_for_strike(underlying, strike_price, hours=24):
    """Get OI change history for a specific strike (helper function)"""
    try:
        # Get OI data for the last N hours
        records = OptionChainData.query.filter(
            OptionChainData.underlying == underlying,
            OptionChainData.strike_price == strike_price,
            OptionChainData.timestamp >= datetime.utcnow() - timedelta(hours=hours)
        ).order_by(OptionChainData.timestamp).all()
        
        changes = []
        for i, record in enumerate(records):
            if i == 0:
                continue  # Skip first record as we need previous for change calculation
            
            prev_record = records[i-1]
            
            ce_change = record.ce_oi - prev_record.ce_oi if record.ce_oi and prev_record.ce_oi else 0
            pe_change = record.pe_oi - prev_record.pe_oi if record.pe_oi and prev_record.pe_oi else 0
            
            changes.append({
                'timestamp': record.timestamp.strftime('%H:%M:%S'),
                'ce_oi': record.ce_oi,
                'pe_oi': record.pe_oi,
                'ce_change': ce_change,
                'pe_change': pe_change
            })
        
        return changes
        
    except Exception as e:
        print(f"Error getting OI changes for strike {strike_price}: {e}")
        return []
