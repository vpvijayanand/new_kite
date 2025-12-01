from flask import Blueprint, render_template, redirect, request, url_for, flash
from app.services.kite_service import KiteService
from app.middlewares.auth_middleware import guest_only, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
@auth_bp.route('/login')
@guest_only
def login():
    return render_template('login.html')

@auth_bp.route('/kite/login')
@guest_only
def kite_login():
    kite_service = KiteService()
    login_url = kite_service.get_login_url()
    return redirect(login_url)

@auth_bp.route('/kite/callback')
def kite_callback():
    request_token = request.args.get('request_token')
    
    if not request_token:
        flash('Login failed. No request token received.', 'danger')
        return redirect(url_for('auth.login'))
    
    try:
        kite_service = KiteService()
        access_token = kite_service.generate_session(request_token)
        
        flash('Successfully logged in with Kite!', 'success')
        return redirect(url_for('market.dashboard'))
    except Exception as e:
        flash(f'Login error: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    kite_service = KiteService()
    kite_service.logout()
    flash('Successfully logged out.', 'info')
    return redirect(url_for('auth.login'))