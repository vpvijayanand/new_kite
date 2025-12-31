from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.models.expiry_settings import ExpirySettings
from app.middlewares.auth_middleware import login_required
from datetime import datetime, date
from app import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def admin_dashboard():
    """Admin dashboard for managing expiry settings"""
    expiry_settings = ExpirySettings.get_all_expiry_settings()
    return render_template('admin/expiry_settings.html', expiry_settings=expiry_settings)

@admin_bp.route('/set-expiry', methods=['POST'])
@login_required
def set_expiry():
    """Set or update expiry dates for underlyings"""
    try:
        data = request.get_json()
        
        underlying = data.get('underlying', '').upper()
        current_expiry_str = data.get('current_expiry')
        next_expiry_str = data.get('next_expiry')
        
        if not underlying or not current_expiry_str:
            return jsonify({
                'success': False,
                'message': 'Underlying and current expiry are required'
            }), 400
        
        # Parse dates
        current_expiry = datetime.strptime(current_expiry_str, '%Y-%m-%d').date()
        next_expiry = None
        if next_expiry_str:
            next_expiry = datetime.strptime(next_expiry_str, '%Y-%m-%d').date()
        
        # Validate that current expiry is not in the past
        if current_expiry < date.today():
            return jsonify({
                'success': False,
                'message': 'Current expiry cannot be in the past'
            }), 400
        
        # Save expiry settings
        setting = ExpirySettings.set_expiry_dates(underlying, current_expiry, next_expiry)
        
        return jsonify({
            'success': True,
            'message': f'Expiry dates updated for {underlying}',
            'data': setting.to_dict()
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': 'Invalid date format. Use YYYY-MM-DD'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating expiry: {str(e)}'
        }), 500

@admin_bp.route('/get-expiry/<underlying>')
@login_required
def get_expiry(underlying):
    """Get current expiry setting for an underlying"""
    try:
        setting = ExpirySettings.query.filter_by(underlying=underlying.upper()).first()
        if setting:
            return jsonify({
                'success': True,
                'data': setting.to_dict()
            })
        else:
            # Return calculated default
            current_expiry = ExpirySettings.get_current_expiry(underlying)
            return jsonify({
                'success': True,
                'data': {
                    'underlying': underlying.upper(),
                    'current_expiry': current_expiry.isoformat(),
                    'next_expiry': None,
                    'is_default': True
                }
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/bulk-set-expiry', methods=['POST'])
@login_required  
def bulk_set_expiry():
    """Set expiry dates for both NIFTY and BankNifty at once"""
    try:
        data = request.get_json()
        
        nifty_expiry_str = data.get('nifty_expiry')
        banknifty_expiry_str = data.get('banknifty_expiry')
        nifty_next_str = data.get('nifty_next_expiry')
        banknifty_next_str = data.get('banknifty_next_expiry')
        
        results = []
        
        # Update NIFTY expiry
        if nifty_expiry_str:
            nifty_expiry = datetime.strptime(nifty_expiry_str, '%Y-%m-%d').date()
            nifty_next = None
            if nifty_next_str:
                nifty_next = datetime.strptime(nifty_next_str, '%Y-%m-%d').date()
                
            nifty_setting = ExpirySettings.set_expiry_dates('NIFTY', nifty_expiry, nifty_next)
            results.append({
                'underlying': 'NIFTY',
                'success': True,
                'data': nifty_setting.to_dict()
            })
        
        # Update BankNifty expiry
        if banknifty_expiry_str:
            banknifty_expiry = datetime.strptime(banknifty_expiry_str, '%Y-%m-%d').date()
            banknifty_next = None
            if banknifty_next_str:
                banknifty_next = datetime.strptime(banknifty_next_str, '%Y-%m-%d').date()
                
            banknifty_setting = ExpirySettings.set_expiry_dates('BANKNIFTY', banknifty_expiry, banknifty_next)
            results.append({
                'underlying': 'BANKNIFTY', 
                'success': True,
                'data': banknifty_setting.to_dict()
            })
        
        return jsonify({
            'success': True,
            'message': 'Expiry dates updated successfully',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating expiry dates: {str(e)}'
        }), 500

@admin_bp.route('/reset-expiry/<underlying>', methods=['POST'])
@login_required
def reset_expiry(underlying):
    """Reset expiry to auto-calculated default"""
    try:
        setting = ExpirySettings.query.filter_by(underlying=underlying.upper()).first()
        if setting:
            db.session.delete(setting)
            db.session.commit()
        
        # Get new default expiry
        new_expiry = ExpirySettings.get_current_expiry(underlying)
        
        return jsonify({
            'success': True,
            'message': f'Expiry reset to default for {underlying.upper()}',
            'data': {
                'underlying': underlying.upper(),
                'current_expiry': new_expiry.isoformat(),
                'is_default': True
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error resetting expiry: {str(e)}'
        }), 500
