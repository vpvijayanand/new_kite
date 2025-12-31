#!/bin/bash

# Pre-deployment check script for Kite Trading Application
# This script verifies all required files and configurations are in place

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ [PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}❌ [FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  [WARN]${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️  [INFO]${NC} $1"
}

ERRORS=0
WARNINGS=0

echo "🔍 Kite Trading Application - Pre-deployment Check"
echo "=================================================="

# Check required files
echo ""
echo "📁 Checking required files..."

REQUIRED_FILES=(
    "Dockerfile"
    "docker-compose.yml" 
    "requirements.txt"
    "run.py"
    "docker/entrypoint.sh"
    "docker/nginx/nginx.conf"
    "docker/nginx/sites-available/newai.vijayanandpremnath.cloud"
    "docker/nginx/proxy_params"
    ".env.production"
    "deploy.sh"
    "manage.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_status "Found: $file"
    else
        print_error "Missing: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check required directories
echo ""
echo "📂 Checking required directories..."

REQUIRED_DIRS=(
    "app"
    "config"
    "storage"
    "logs"
    "docker/nginx"
    "docker/nginx/sites-available"
    "docker/nginx/sites-enabled"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        print_status "Found: $dir/"
    else
        print_error "Missing: $dir/"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check Python app structure
echo ""
echo "🐍 Checking Python application structure..."

PYTHON_FILES=(
    "app/__init__.py"
    "app/controllers/market_controller.py"
    "app/services/market_service.py"
    "app/models/"
    "config/config.py"
)

for file in "${PYTHON_FILES[@]}"; do
    if [ -e "$file" ]; then
        print_status "Found: $file"
    else
        print_warning "Missing: $file (may cause runtime issues)"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Check file permissions
echo ""
echo "🔒 Checking file permissions..."

EXECUTABLE_FILES=(
    "deploy.sh"
    "manage.sh"
    "docker/entrypoint.sh"
)

for file in "${EXECUTABLE_FILES[@]}"; do
    if [ -f "$file" ]; then
        if [ -x "$file" ]; then
            print_status "$file is executable"
        else
            print_warning "$file is not executable (will be fixed automatically)"
            chmod +x "$file"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
done

# Check Docker configuration
echo ""
echo "🐳 Checking Docker configuration..."

if command -v docker &> /dev/null; then
    print_status "Docker is installed"
else
    print_error "Docker is not installed"
    ERRORS=$((ERRORS + 1))
fi

if command -v docker-compose &> /dev/null; then
    print_status "Docker Compose is installed"
else
    print_error "Docker Compose is not installed"
    ERRORS=$((ERRORS + 1))
fi

# Validate docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    if docker-compose config > /dev/null 2>&1; then
        print_status "docker-compose.yml is valid"
    else
        print_error "docker-compose.yml has syntax errors"
        ERRORS=$((ERRORS + 1))
    fi
fi

# Check environment configuration
echo ""
echo "⚙️  Checking environment configuration..."

if [ -f ".env" ]; then
    print_status "Found .env file"
    
    # Check for required environment variables
    REQUIRED_ENV_VARS=(
        "SECRET_KEY"
        "KITE_API_KEY"
        "KITE_API_SECRET"
    )
    
    for var in "${REQUIRED_ENV_VARS[@]}"; do
        if grep -q "^${var}=" .env; then
            value=$(grep "^${var}=" .env | cut -d'=' -f2)
            if [ -n "$value" ] && [ "$value" != "your-" ] && [[ ! "$value" =~ ^your- ]]; then
                print_status "$var is configured"
            else
                print_warning "$var needs to be configured with actual value"
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            print_warning "$var not found in .env file"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
else
    if [ -f ".env.production" ]; then
        print_warning "Found .env.production but missing .env (will be copied during deployment)"
        WARNINGS=$((WARNINGS + 1))
    else
        print_error "No environment configuration found"
        ERRORS=$((ERRORS + 1))
    fi
fi

# Check Nginx configuration
echo ""
echo "🌐 Checking Nginx configuration..."

if [ -f "docker/nginx/nginx.conf" ]; then
    print_status "Nginx main configuration found"
else
    print_error "Missing Nginx main configuration"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "docker/nginx/sites-available/newai.vijayanandpremnath.cloud" ]; then
    print_status "Virtual host configuration found"
else
    print_error "Missing virtual host configuration"
    ERRORS=$((ERRORS + 1))
fi

# Check SSL directory structure
echo ""
echo "🔐 Checking SSL configuration..."

if [ -d "docker/ssl" ]; then
    print_status "SSL directory exists"
else
    print_warning "SSL directory will be created during deployment"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "📊 Pre-deployment Check Summary"
echo "==============================="

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        print_status "All checks passed! ✨"
        echo ""
        print_info "Your application is ready for deployment!"
        echo ""
        echo "Next steps:"
        echo "1. Copy your application to the production server"
        echo "2. Run: ./deploy.sh"
        echo "3. Configure your .env file with actual API keys"
        echo "4. Test the deployment"
    else
        print_warning "Checks passed with $WARNINGS warnings"
        echo ""
        print_info "Your application should deploy successfully, but please review the warnings above."
    fi
    exit 0
else
    print_error "Found $ERRORS critical errors and $WARNINGS warnings"
    echo ""
    echo "❗ Please fix the errors above before proceeding with deployment."
    exit 1
fi
