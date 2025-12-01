from functools import wraps
from flask import redirect, url_for, session, flash
from app.services.kite_service import KiteService

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        kite_service = KiteService()
        if not kite_service.is_authenticated():
            flash('Please login with Kite to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def guest_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        kite_service = KiteService()
        if kite_service.is_authenticated():
            return redirect(url_for('market.dashboard'))
        return f(*args, **kwargs)
    return decorated_function