import os
from app import create_app
from flask import jsonify

app = create_app(os.getenv('FLASK_ENV', 'development'))

# Health check endpoint for Docker
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'kite_trading_app',
        'version': '1.0.0'
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)