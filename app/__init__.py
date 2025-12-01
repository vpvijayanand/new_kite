from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config.config import config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__, 
                template_folder='views/templates',
                static_folder='views/static')
    
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.market_controller import market_bp, init_scheduler
    from app.controllers.admin_controller import admin_bp
    from app.api.routes import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Import models to ensure they're registered with SQLAlchemy
    from app.models import nifty_price, banknifty_price, expiry_settings
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Add datetime utilities to Jinja2 globals
    from app.utils.datetime_utils import format_ist_time, format_ist_time_only, utc_to_ist
    app.jinja_env.globals.update(
        format_ist_time=format_ist_time,
        format_ist_time_only=format_ist_time_only,
        utc_to_ist=utc_to_ist
    )
    
    # Initialize scheduler after app context is available
    init_scheduler(app)
    
    return app