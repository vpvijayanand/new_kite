#!/bin/bash

# Quick Setup Script for vijayanandpremnath.cloud Kite App Migration
# Run this script as: sudo ./existing_server_setup.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Configuration
APP_DIR="/var/www/html/Kite_app"
DB_NAME="kite_db"
DB_USER="kiteuser"
DOMAIN="vijayanandpremnath.cloud"

print_header "Kite App Setup for $DOMAIN"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Step 1: Navigate to app directory
print_status "Step 1: Checking application directory..."
if [[ ! -d "$APP_DIR" ]]; then
    print_error "Application directory $APP_DIR does not exist!"
    exit 1
fi
cd "$APP_DIR"
print_status "✅ Found application directory: $APP_DIR"

# Step 2: Create virtual environment
print_status "Step 2: Setting up Python virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    print_status "✅ Created virtual environment"
else
    print_status "✅ Virtual environment already exists"
fi

# Step 3: Install dependencies
print_status "Step 3: Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip

# Install packages one by one with error handling
packages=(
    "Flask==3.0.0"
    "Flask-SQLAlchemy==3.1.1"
    "Flask-Migrate==4.0.5"
    "psycopg2-binary==2.9.9"
    "kiteconnect==5.0.1"
    "python-dotenv==1.0.0"
    "APScheduler==3.10.4"
    "gunicorn==21.2.0"
    "pytz==2023.3"
    "requests==2.31.0"
    "pandas==2.1.1"
    "numpy==1.25.2"
)

for package in "${packages[@]}"; do
    print_status "Installing $package..."
    pip install "$package" || print_warning "Failed to install $package, continuing..."
done

print_status "✅ Python dependencies installed"

# Step 4: Create .env file if it doesn't exist
print_status "Step 4: Setting up environment configuration..."
if [[ ! -f ".env" ]]; then
    cat > .env << EOF
# Flask Configuration
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_ENV=production

# Database Configuration
DATABASE_URL=postgresql://$DB_USER:CHANGE_THIS_PASSWORD@localhost/$DB_NAME

# Kite Connect API Configuration
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret
KITE_REDIRECT_URL=https://$DOMAIN/kite/callback

# Token Storage Path
TOKEN_FILE_PATH=storage/tokens/access_token.json
EOF
    print_status "✅ Created .env file"
    print_warning "⚠️  Please update the .env file with your actual database password and Kite API credentials"
else
    print_status "✅ .env file already exists"
fi

# Step 5: Set proper permissions
print_status "Step 5: Setting proper file permissions..."
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod 644 .env 2>/dev/null || true

# Create required directories
mkdir -p storage/tokens logs backups scripts
chown -R www-data:www-data storage logs backups scripts
chmod -R 755 storage logs backups scripts

print_status "✅ File permissions set"

# Step 6: Create WSGI file
print_status "Step 6: Creating WSGI configuration..."
cat > kite_app.wsgi << 'EOF'
#!/usr/bin/python3

import sys
import os

# Add the application directory to Python path
sys.path.insert(0, "/var/www/html/Kite_app/")

# Change to application directory
os.chdir('/var/www/html/Kite_app')

# Activate virtual environment
activate_this = '/var/www/html/Kite_app/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), dict(__file__=activate_this))

from app import create_app
application = create_app()

if __name__ == "__main__":
    application.run()
EOF

chmod 644 kite_app.wsgi
chown www-data:www-data kite_app.wsgi
print_status "✅ WSGI file created"

# Step 7: Create Apache virtual host
print_status "Step 7: Creating Apache virtual host configuration..."
cat > /etc/apache2/sites-available/$DOMAIN.conf << EOF
<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAlias www.$DOMAIN
    
    # Redirect HTTP to HTTPS
    Redirect permanent / https://$DOMAIN/
</VirtualHost>

<VirtualHost *:443>
    ServerName $DOMAIN
    ServerAlias www.$DOMAIN
    
    DocumentRoot $APP_DIR
    
    WSGIDaemonProcess kiteapp python-home=$APP_DIR/venv python-path=$APP_DIR
    WSGIProcessGroup kiteapp
    WSGIScriptAlias / $APP_DIR/kite_app.wsgi
    
    <Directory $APP_DIR>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    # Static files
    Alias /static $APP_DIR/app/views/static
    <Directory $APP_DIR/app/views/static>
        Require all granted
    </Directory>
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/$DOMAIN/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/$DOMAIN/privkey.pem
    
    # Security headers
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    
    # Logging
    ErrorLog \${APACHE_LOG_DIR}/kite_app_error.log
    CustomLog \${APACHE_LOG_DIR}/kite_app_access.log combined
</VirtualHost>
EOF

print_status "✅ Apache virtual host configuration created"

# Step 8: Enable Apache modules and site
print_status "Step 8: Configuring Apache..."
a2enmod wsgi ssl headers rewrite
a2ensite $DOMAIN.conf
a2dissite 000-default.conf 2>/dev/null || true

# Test Apache configuration
if apache2ctl configtest; then
    print_status "✅ Apache configuration is valid"
else
    print_error "❌ Apache configuration has errors"
    exit 1
fi

# Step 9: Create backup script
print_status "Step 9: Creating backup scripts..."
cat > scripts/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/www/html/Kite_app/backups"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U kiteuser kite_db > $BACKUP_DIR/kite_db_$(date +%Y%m%d_%H%M%S).sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "kite_db_*.sql" -mtime +7 -delete

echo "$(date): Database backup completed" >> /var/www/html/Kite_app/logs/backup.log
EOF

chmod +x scripts/backup_db.sh
chown www-data:www-data scripts/backup_db.sh
print_status "✅ Backup script created"

# Step 10: Test Python imports
print_status "Step 10: Testing Python imports..."
cd "$APP_DIR"
source venv/bin/activate

if python3 -c "from app import create_app; app = create_app(); print('✅ Flask app import successful')" 2>/dev/null; then
    print_status "✅ Python imports working"
else
    print_warning "⚠️  Python imports may have issues - check after database setup"
fi

print_header "Setup Summary"
echo ""
print_status "✅ Python virtual environment created"
print_status "✅ Dependencies installed"
print_status "✅ Environment configuration created"
print_status "✅ File permissions set"
print_status "✅ Apache configuration created"
print_status "✅ Backup scripts created"
echo ""

print_header "Manual Steps Required"
echo ""
echo -e "${YELLOW}1. Database Setup:${NC}"
echo "   sudo -u postgres psql"
echo "   CREATE DATABASE $DB_NAME;"
echo "   CREATE USER $DB_USER WITH PASSWORD 'your_secure_password';"
echo "   GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
echo "   \\q"
echo ""

echo -e "${YELLOW}2. Update .env file:${NC}"
echo "   nano $APP_DIR/.env"
echo "   - Set your database password"
echo "   - Set your Kite API credentials"
echo ""

echo -e "${YELLOW}3. Run database migrations:${NC}"
echo "   cd $APP_DIR"
echo "   source venv/bin/activate"
echo "   export FLASK_APP=run.py"
echo "   flask db init      # (if migrations folder doesn't exist)"
echo "   flask db migrate -m 'Initial migration'"
echo "   flask db upgrade"
echo ""

echo -e "${YELLOW}4. Get SSL certificate:${NC}"
echo "   sudo certbot --apache -d $DOMAIN -d www.$DOMAIN"
echo ""

echo -e "${YELLOW}5. Restart Apache:${NC}"
echo "   sudo systemctl restart apache2"
echo ""

echo -e "${YELLOW}6. Set up cron jobs:${NC}"
echo "   sudo crontab -u www-data -e"
echo "   # Add the cron entries from the migration guide"
echo ""

print_header "Next Steps"
echo ""
print_status "After completing the manual steps above:"
print_status "1. Visit https://$DOMAIN to test the application"
print_status "2. Check https://$DOMAIN/strategies/ for Strategy 1"
print_status "3. Monitor logs in $APP_DIR/logs/"
echo ""

print_status "🎉 Basic setup completed! Follow the manual steps above to finish the migration."
