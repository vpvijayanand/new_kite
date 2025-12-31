# wsgi.py
import os
from app import create_app

# Use FLASK_ENV if set (e.g. "production" or "development"); default to "development"
env = os.getenv("FLASK_ENV", "development")

# create the Flask app (this variable name MUST be `app` for gunicorn: wsgi:app)
app = create_app(env)

# Optional: simple health endpoint in case you want it available under gunicorn too.
# If you already add /health elsewhere, you can remove this block.
from flask import jsonify

@app.route("/health")
def _health_check():
    return jsonify({
        "status": "healthy",
        "service": "kite_trading_app",
        "version": "1.0.0"
    }), 200

