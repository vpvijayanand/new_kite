#!/bin/bash

# Health check script for Kite Trading App
LOG_FILE="/var/newai/new_kite/logs/health_check.log"
APP_URL="https://newai.vijayanandpremnath.cloud/health"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Check application health
check_app_health() {
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL)
    
    if [ "$HTTP_STATUS" -eq 200 ]; then
        log_message "✅ Application health check passed (HTTP $HTTP_STATUS)"
        return 0
    else
        log_message "❌ Application health check failed (HTTP $HTTP_STATUS)"
        return 1
    fi
}

# Check database connectivity
check_database() {
    cd /var/newai/new_kite
    source ../venv/bin/activate
    
    DB_CHECK=$(python3 -c "
from app import create_app, db
import os
os.environ['FLASK_ENV'] = 'production'
app = create_app('production')
with app.app_context():
    try:
        db.engine.execute('SELECT 1')
        print('OK')
    except Exception as e:
        print('ERROR')
" 2>/dev/null)
    
    if [ "$DB_CHECK" = "OK" ]; then
        log_message "✅ Database connectivity check passed"
        return 0
    else
        log_message "❌ Database connectivity check failed"
        return 1
    fi
}

# Main health check
main() {
    log_message "Starting health check"
    
    check_app_health
    APP_STATUS=$?
    
    check_database  
    DB_STATUS=$?
    
    if [ $APP_STATUS -eq 0 ] && [ $DB_STATUS -eq 0 ]; then
        log_message "✅ All health checks passed"
        exit 0
    else
        log_message "❌ Health check failed - Application: $APP_STATUS, Database: $DB_STATUS"
        exit 1
    fi
}

main
