# Gunicorn configuration file
bind = "127.0.0.1:8001"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "kite_trading_app"

# Server mechanics
daemon = False
pidfile = "gunicorn.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# Worker processes
worker_tmp_dir = "/dev/shm"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
