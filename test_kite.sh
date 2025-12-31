#!/bin/bash

# Kite Connect Quick Test Script
# =============================
# This script provides a quick way to test Kite Connect integration
# Run this on your production server to verify everything is working

echo "🔍 KITE CONNECT QUICK TEST"
echo "=========================="
echo "Date: $(date)"
echo "Server: $(hostname)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Set your application path here (adjust as needed)
APP_PATH="/var/newai/new_kite"  # Change this to your actual path
VENV_PATH="$APP_PATH/../venv"
TOKEN_PATH="$APP_PATH/storage/tokens/access_token.json"

echo "🔍 Step 1: Basic System Check"
echo "------------------------------"

# Check if application directory exists
if [ -d "$APP_PATH" ]; then
    print_success "Application directory exists: $APP_PATH"
else
    print_error "Application directory not found: $APP_PATH"
    print_info "Please update APP_PATH in this script to match your installation"
    exit 1
fi

# Check if virtual environment exists
if [ -d "$VENV_PATH" ]; then
    print_success "Virtual environment found"
else
    print_error "Virtual environment not found at: $VENV_PATH"
fi

# Check if .env file exists
if [ -f "$APP_PATH/.env" ]; then
    print_success ".env file exists"
else
    print_error ".env file not found"
fi

echo ""
echo "🔍 Step 2: Service Status Check"
echo "-------------------------------"

# Check if application service is running
if systemctl is-active --quiet kite-app.service; then
    print_success "Kite app service is running"
else
    print_error "Kite app service is not running"
    print_info "Try: sudo systemctl start kite-app.service"
fi

# Check if Nginx is running
if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx is not running"
fi

# Check if PostgreSQL is running
if systemctl is-active --quiet postgresql; then
    print_success "PostgreSQL is running"
else
    print_error "PostgreSQL is not running"
fi

echo ""
echo "🔍 Step 3: Network Connectivity"
echo "-------------------------------"

# Test if application port is listening
if netstat -tlnp 2>/dev/null | grep -q ":8001"; then
    print_success "Application port 8000 is listening"
else
    print_error "Application port 8000 is not listening"
fi

# Test health endpoint
print_info "Testing health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://newai.vijayanandpremnath.cloud/health 2>/dev/null)
if [ "$HEALTH_STATUS" = "200" ]; then
    print_success "Health endpoint responding (HTTP $HEALTH_STATUS)"
else
    print_error "Health endpoint not responding (HTTP $HEALTH_STATUS)"
fi

echo ""
echo "🔍 Step 4: Environment Configuration"
echo "-----------------------------------"

if [ -f "$APP_PATH/.env" ]; then
    # Check for required environment variables
    if grep -q "KITE_API_KEY=" "$APP_PATH/.env" && [ -n "$(grep "KITE_API_KEY=" "$APP_PATH/.env" | cut -d'=' -f2)" ]; then
        print_success "KITE_API_KEY is configured"
    else
        print_error "KITE_API_KEY is missing or empty"
    fi
    
    if grep -q "KITE_API_SECRET=" "$APP_PATH/.env" && [ -n "$(grep "KITE_API_SECRET=" "$APP_PATH/.env" | cut -d'=' -f2)" ]; then
        print_success "KITE_API_SECRET is configured"
    else
        print_error "KITE_API_SECRET is missing or empty"
    fi
    
    if grep -q "DATABASE_URL=" "$APP_PATH/.env" && [ -n "$(grep "DATABASE_URL=" "$APP_PATH/.env" | cut -d'=' -f2)" ]; then
        print_success "DATABASE_URL is configured"
    else
        print_error "DATABASE_URL is missing or empty"
    fi
fi

echo ""
echo "🔍 Step 5: Token File Check"
echo "---------------------------"

if [ -f "$TOKEN_PATH" ]; then
    print_success "Token file exists: $TOKEN_PATH"
    
    # Check token file size
    TOKEN_SIZE=$(wc -c < "$TOKEN_PATH" 2>/dev/null)
    if [ "$TOKEN_SIZE" -gt 10 ]; then
        print_success "Token file has content ($TOKEN_SIZE bytes)"
        
        # Check if it's valid JSON
        if python3 -c "import json; json.load(open('$TOKEN_PATH'))" 2>/dev/null; then
            print_success "Token file contains valid JSON"
        else
            print_error "Token file contains invalid JSON"
        fi
    else
        print_error "Token file is too small (may be empty)"
    fi
else
    print_error "Token file not found: $TOKEN_PATH"
    print_info "You need to authenticate via: https://newai.vijayanandpremnath.cloud/auth/login"
fi

echo ""
echo "🔍 Step 6: Database Connection Test"
echo "----------------------------------"

# Extract database credentials from .env
if [ -f "$APP_PATH/.env" ]; then
    DB_URL=$(grep "DATABASE_URL=" "$APP_PATH/.env" | cut -d'=' -f2- | tr -d '"')
    
    if [ -n "$DB_URL" ]; then
        print_info "Testing database connection..."
        
        # Extract database details from URL
        # Format: postgresql://user:password@host:port/database
        DB_USER=$(echo "$DB_URL" | sed -n 's|postgresql://\([^:]*\):.*|\1|p')
        DB_PASS=$(echo "$DB_URL" | sed -n 's|postgresql://[^:]*:\([^@]*\)@.*|\1|p')
        DB_HOST=$(echo "$DB_URL" | sed -n 's|postgresql://[^@]*@\([^:]*\):.*|\1|p')
        DB_PORT=$(echo "$DB_URL" | sed -n 's|postgresql://[^@]*@[^:]*:\([^/]*\)/.*|\1|p')
        DB_NAME=$(echo "$DB_URL" | sed -n 's|postgresql://[^/]*/\(.*\)|\1|p')
        
        # Test database connection
        if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "Database connection successful"
            
            # Check if main tables exist
            TABLES=("nifty_prices" "banknifty_prices" "futures_oi_data")
            for table in "${TABLES[@]}"; do
                COUNT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d ' ')
                if [ $? -eq 0 ]; then
                    print_success "Table '$table' exists with $COUNT records"
                else
                    print_error "Table '$table' not found or not accessible"
                fi
            done
        else
            print_error "Database connection failed"
        fi
    else
        print_error "Could not extract database URL"
    fi
fi

echo ""
echo "🔍 Step 7: Market Hours Check"
echo "----------------------------"

# Check current time in IST
IST_TIME=$(TZ="Asia/Kolkata" date '+%H%M')
DAY_OF_WEEK=$(date '+%u')  # 1=Monday, 7=Sunday

print_info "Current IST time: $(TZ='Asia/Kolkata' date '+%Y-%m-%d %H:%M:%S')"
print_info "Day of week: $DAY_OF_WEEK (1=Mon, 7=Sun)"

# Check if in market hours (9:15 AM to 3:30 PM, Monday to Friday)
if [ "$DAY_OF_WEEK" -le 5 ] && [ "$IST_TIME" -ge 915 ] && [ "$IST_TIME" -le 1530 ]; then
    print_success "Currently in market hours (9:15 AM - 3:30 PM IST, Mon-Fri)"
    print_info "Real-time market data should be flowing"
elif [ "$DAY_OF_WEEK" -le 5 ]; then
    print_warning "Market day but outside trading hours"
    print_info "Market hours: 9:15 AM - 3:30 PM IST"
else
    print_warning "Weekend - Market is closed"
fi

echo ""
echo "🔍 Step 8: Application Logs Check"
echo "---------------------------------"

# Check recent application logs
if [ -f "$APP_PATH/logs/app.log" ]; then
    print_success "Application log file exists"
    
    # Check for recent errors
    RECENT_ERRORS=$(tail -100 "$APP_PATH/logs/app.log" | grep -i "error\|exception\|failed" | wc -l)
    if [ "$RECENT_ERRORS" -eq 0 ]; then
        print_success "No recent errors in application logs"
    else
        print_warning "Found $RECENT_ERRORS recent error entries in logs"
        print_info "Check: tail -50 $APP_PATH/logs/app.log"
    fi
    
    # Check for recent Kite API activity
    KITE_ACTIVITY=$(tail -100 "$APP_PATH/logs/app.log" | grep -i "kite\|api\|token" | wc -l)
    if [ "$KITE_ACTIVITY" -gt 0 ]; then
        print_success "Recent Kite API activity found in logs"
    else
        print_warning "No recent Kite API activity in logs"
    fi
else
    print_error "Application log file not found: $APP_PATH/logs/app.log"
fi

# Check Gunicorn logs
if [ -f "$APP_PATH/logs/gunicorn_error.log" ]; then
    GUNICORN_ERRORS=$(tail -50 "$APP_PATH/logs/gunicorn_error.log" | grep -i "error\|exception" | wc -l)
    if [ "$GUNICORN_ERRORS" -eq 0 ]; then
        print_success "No recent Gunicorn errors"
    else
        print_warning "Found $GUNICORN_ERRORS recent Gunicorn errors"
    fi
fi

echo ""
echo "🔍 Step 9: Quick Kite Test (Python)"
echo "-----------------------------------"

if [ -d "$VENV_PATH" ] && [ -f "$TOKEN_PATH" ]; then
    print_info "Running Python-based Kite API test..."
    
    # Activate virtual environment and run test
    cd "$APP_PATH"
    source "$VENV_PATH/bin/activate"
    
    python3 -c "
import sys, os
sys.path.insert(0, '.')
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    from app import create_app
    os.environ['FLASK_ENV'] = 'production'
    app = create_app('production')
    
    with app.app_context():
        from app.services.kite_service import KiteService
        import json
        
        # Load token
        with open('$TOKEN_PATH', 'r') as f:
            token_data = json.load(f)
        
        kite_service = KiteService()
        kite_service.kite.set_access_token(token_data['access_token'])
        
        # Test profile
        profile = kite_service.kite.profile()
        print('✅ Kite API connection successful')
        print(f'✅ User: {profile.get(\"user_name\", \"Unknown\")}')
        
        # Test quote
        quote = kite_service.kite.quote(['NSE:NIFTY 50'])
        nifty_price = quote['NSE:NIFTY 50']['last_price']
        print(f'✅ NIFTY 50 price: {nifty_price}')
        
except Exception as e:
    print(f'❌ Kite API test failed: {str(e)}')
    if 'token' in str(e).lower():
        print('ℹ️  Authentication issue - visit: https://newai.vijayanandpremnath.cloud/auth/login')
" 2>/dev/null
else
    print_warning "Skipping Python test - missing virtual environment or token file"
fi

echo ""
echo "📊 SUMMARY & RECOMMENDATIONS"
echo "============================"

print_info "Test completed at: $(date)"

# Provide recommendations based on findings
if [ ! -f "$TOKEN_PATH" ]; then
    print_warning "AUTHENTICATION REQUIRED:"
    print_info "1. Visit: https://newai.vijayanandpremnath.cloud/auth/login"
    print_info "2. Complete Kite Connect authentication"
    print_info "3. Re-run this test script"
    echo ""
fi

print_info "TO MONITOR YOUR APPLICATION:"
print_info "1. Check health: curl https://newai.vijayanandpremnath.cloud/health"
print_info "2. View logs: tail -f $APP_PATH/logs/app.log"
print_info "3. Check service: sudo systemctl status kite-app.service"
print_info "4. Visit dashboard: https://newai.vijayanandpremnath.cloud/dashboard"

echo ""
print_info "FOR DETAILED TESTING, RUN:"
print_info "cd $APP_PATH && source venv/bin/activate && python3 test_kite_connection.py"

echo ""
echo "🎯 Test completed successfully!"

