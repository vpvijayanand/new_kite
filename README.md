# Kite Trading Application

A comprehensive Flask-based trading application for NSE options and futures analysis with advanced charting capabilities.

## Features

- **OI Crossover Analysis**: Real-time Open Interest change analysis with dynamic visualizations
- **Futures OI Analysis**: Comprehensive futures Open Interest tracking and analytics
- **Market Data Integration**: Seamless integration with Zerodha Kite Connect API
- **Advanced Charting**: Interactive charts with Chart.js including dynamic opacity and grid lines
- **Real-time Monitoring**: Automated strategy execution during market hours
- **User Authentication**: Secure login system with session management
- **Responsive UI**: Modern Bootstrap 5 interface with organized navigation

## Production Deployment Guide for Ubuntu Server

### Prerequisites

- Ubuntu 20.04 LTS or higher
- Root or sudo access
- Domain name (optional but recommended)
- SSL certificate (for production)

### Step 1: System Updates and Dependencies

```bash
# Update the system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y software-properties-common curl wget git unzip

# Install Python 3.10+ and development tools
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib postgresql-server-dev-all

# Install Apache and required modules
sudo apt install -y apache2 apache2-dev

# Install additional system dependencies for Python packages
sudo apt install -y pkg-config libxml2-dev libxmlsec1-dev libffi-dev libjpeg-dev libpng-dev
```

### Step 2: PostgreSQL Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell, create database and user
CREATE DATABASE kite_db;
CREATE USER kite_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE kite_db TO kite_user;
ALTER USER kite_user CREATEDB;
\q

# Configure PostgreSQL for local connections
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Add this line before other rules:
# local   kite_db         kite_user                               md5

# Restart PostgreSQL
sudo systemctl restart postgresql
sudo systemctl enable postgresql
```

### Step 3: Create Application User and Directory

```bash
# Create application user
sudo useradd -m -s /bin/bash kite_app
sudo usermod -aG www-data kite_app

# Create application directory
sudo mkdir -p /var/www/kite_app
sudo chown -R kite_app:www-data /var/www/kite_app
sudo chmod -R 755 /var/www/kite_app
```

### Step 4: Clone and Setup Application

```bash
# Switch to application user
sudo su - kite_app

# Navigate to application directory
cd /var/www/kite_app

# Clone the repository (replace with your repo URL)
git clone https://github.com/vpvijayanand/new_kite.git .

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install wheel
pip install --upgrade pip wheel setuptools

# Install Python dependencies from requirements.txt
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn mod_wsgi
```

### Step 5: Environment Configuration

```bash
# Create .env file
nano .env
```

Add the following content to `.env`:

```env
# Flask Configuration
SECRET_KEY=your_very_long_random_secret_key_here_min_32_chars
FLASK_ENV=production

# Database Configuration
DATABASE_URL=postgresql://kite_user:your_secure_password@localhost/kite_db

# Kite API Configuration
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret
KITE_REDIRECT_URL=https://yourdomain.com/auth/callback

# Token Storage Path
TOKEN_FILE_PATH=/var/www/kite_app/storage/tokens/access_token.json

# Logging
LOG_LEVEL=INFO
```

### Step 6: Create Required Directories and Set Permissions

```bash
# Create necessary directories
mkdir -p logs storage/tokens migrations

# Set proper permissions
chmod 755 logs storage storage/tokens migrations
chmod 664 storage/tokens/access_token.json 2>/dev/null || true

# Create log files
touch logs/app.log
chmod 664 logs/app.log
```

### Step 7: Database Initialization

```bash
# Activate virtual environment
source venv/bin/activate

# Set Flask app
export FLASK_APP=run.py

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Test the application
python run.py
# Press Ctrl+C after confirming it starts without errors
```

### Step 8: Create WSGI Entry Point

```bash
# Create WSGI file
nano /var/www/kite_app/kite_app.wsgi
```

Add the following content:

```python
#!/usr/bin/python3
import sys
import os

# Add the application directory to Python path
sys.path.insert(0, "/var/www/kite_app/")

# Activate virtual environment
activate_this = '/var/www/kite_app/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import the Flask application
from run import app as application

if __name__ == "__main__":
    application.run()
```

### Step 9: Apache Virtual Host Configuration

```bash
# Exit from kite_app user
exit

# Create Apache virtual host configuration
sudo nano /etc/apache2/sites-available/kite_app.conf
```

Add the following configuration:

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com
    DocumentRoot /var/www/kite_app
    
    WSGIDaemonProcess kite_app python-path=/var/www/kite_app python-home=/var/www/kite_app/venv
    WSGIProcessGroup kite_app
    WSGIScriptAlias / /var/www/kite_app/kite_app.wsgi
    
    <Directory /var/www/kite_app>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    # Serve static files directly with Apache
    Alias /static /var/www/kite_app/app/views/static
    <Directory /var/www/kite_app/app/views/static>
        Require all granted
    </Directory>
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/kite_app_error.log
    CustomLog ${APACHE_LOG_DIR}/kite_app_access.log combined
    LogLevel info
</VirtualHost>
```

### Step 10: Enable Apache Modules and Site

```bash
# Enable required Apache modules
sudo a2enmod wsgi
sudo a2enmod rewrite
sudo a2enmod headers

# Enable the site
sudo a2ensite kite_app.conf

# Disable default Apache site (optional)
sudo a2dissite 000-default.conf

# Test Apache configuration
sudo apache2ctl configtest

# Restart Apache
sudo systemctl restart apache2
sudo systemctl enable apache2
```

### Step 11: SSL Configuration (Recommended for Production)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-apache

# Obtain SSL certificate (replace with your domain)
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com

# Test SSL renewal
sudo certbot renew --dry-run
```

### Step 12: Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH (adjust port if different)
sudo ufw allow 22

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Check firewall status
sudo ufw status
```

### Step 13: Setup Automated Trading Cron Jobs

```bash
# Switch to application user
sudo su - kite_app

# Create crontab for automated execution
crontab -e

# Add the following lines for market hours execution (9:15 AM to 3:30 PM, Monday-Friday)
# Strategy execution during market hours
30-59 9 * * 1-5 cd /var/www/kite_app && /var/www/kite_app/venv/bin/python /var/www/kite_app/scripts/strategy1_standalone.py >> /var/www/kite_app/logs/strategy1.log 2>&1
0-15 10-14 * * 1-5 cd /var/www/kite_app && /var/www/kite_app/venv/bin/python /var/www/kite_app/scripts/strategy1_standalone.py >> /var/www/kite_app/logs/strategy1.log 2>&1
0-15 15 * * 1-5 cd /var/www/kite_app && /var/www/kite_app/venv/bin/python /var/www/kite_app/scripts/strategy1_standalone.py >> /var/www/kite_app/logs/strategy1.log 2>&1

# Log rotation at midnight
0 0 * * * cd /var/www/kite_app && find logs/ -name "*.log" -size +100M -exec gzip {} \; 2>/dev/null

# Exit from kite_app user
exit
```

### Step 14: Log Rotation Setup

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/kite_app
```

Add the following content:

```
/var/www/kite_app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 664 kite_app www-data
    postrotate
        sudo systemctl reload apache2 > /dev/null 2>&1 || true
    endscript
}
```

### Step 15: System Service for Background Tasks (Optional)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/kite_app_scheduler.service
```

Add the following content:

```ini
[Unit]
Description=Kite App Scheduler Service
After=network.target postgresql.service

[Service]
Type=simple
User=kite_app
WorkingDirectory=/var/www/kite_app
Environment=PATH=/var/www/kite_app/venv/bin
ExecStart=/var/www/kite_app/venv/bin/python -c "from app.services.scheduler_service import start_scheduler; start_scheduler()"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable kite_app_scheduler
sudo systemctl start kite_app_scheduler
```

### Step 16: Final Verification and Testing

```bash
# Check Apache status
sudo systemctl status apache2

# Check PostgreSQL status
sudo systemctl status postgresql

# Check application logs
sudo tail -f /var/log/apache2/kite_app_error.log

# Test database connection
sudo su - kite_app
cd /var/www/kite_app
source venv/bin/activate
python -c "from app.database.db import db; print('Database connection successful')"

# Check if application is accessible
curl -I http://localhost
```

### Step 17: Monitoring and Maintenance

```bash
# Create monitoring script
sudo nano /usr/local/bin/kite_app_monitor.sh
```

Add the following content:

```bash
#!/bin/bash
# Kite App Monitoring Script

LOG_FILE="/var/log/kite_app_monitor.log"

# Check Apache
if ! systemctl is-active --quiet apache2; then
    echo "$(date): Apache2 is not running. Restarting..." >> $LOG_FILE
    systemctl restart apache2
fi

# Check PostgreSQL
if ! systemctl is-active --quiet postgresql; then
    echo "$(date): PostgreSQL is not running. Restarting..." >> $LOG_FILE
    systemctl restart postgresql
fi

# Check disk space
DISK_USAGE=$(df /var/www/kite_app | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): High disk usage: ${DISK_USAGE}%" >> $LOG_FILE
fi

# Check log file sizes
find /var/www/kite_app/logs -name "*.log" -size +500M -exec echo "$(date): Large log file found: {}" \; >> $LOG_FILE
```

```bash
# Make script executable
sudo chmod +x /usr/local/bin/kite_app_monitor.sh

# Add to crontab
echo "*/5 * * * * /usr/local/bin/kite_app_monitor.sh" | sudo crontab -
```

## Post-Deployment Configuration

### 1. Initial Login Setup
- Access your application at `https://yourdomain.com`
- Complete Kite Connect authentication
- Verify market data connectivity

### 2. Performance Optimization
```bash
# Apache performance tuning
sudo nano /etc/apache2/mods-available/mpm_prefork.conf

# Add or modify:
<IfModule mpm_prefork_module>
    StartServers 5
    MinSpareServers 5
    MaxSpareServers 10
    MaxRequestWorkers 150
    MaxConnectionsPerChild 0
</IfModule>
```

### 3. Security Hardening
```bash
# Hide Apache version
echo "ServerTokens Prod" | sudo tee -a /etc/apache2/apache2.conf
echo "ServerSignature Off" | sudo tee -a /etc/apache2/apache2.conf

# Restart Apache
sudo systemctl restart apache2
```

## Troubleshooting

### Common Issues and Solutions

1. **Database Connection Issues**
   ```bash
   # Check PostgreSQL logs
   sudo tail -f /var/log/postgresql/postgresql-*-main.log
   
   # Test connection
   sudo -u kite_app psql -h localhost -U kite_user kite_db
   ```

2. **Apache WSGI Issues**
   ```bash
   # Check Apache error logs
   sudo tail -f /var/log/apache2/kite_app_error.log
   
   # Test WSGI configuration
   sudo apache2ctl configtest
   ```

3. **Permission Issues**
   ```bash
   # Fix permissions
   sudo chown -R kite_app:www-data /var/www/kite_app
   sudo chmod -R 755 /var/www/kite_app
   sudo chmod 664 /var/www/kite_app/logs/*.log
   ```

4. **Python Package Issues**
   ```bash
   # Reinstall packages
   sudo su - kite_app
   cd /var/www/kite_app
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

## Backup and Recovery

### Database Backup
```bash
# Create backup script
sudo nano /usr/local/bin/backup_kite_db.sh

#!/bin/bash
BACKUP_DIR="/var/backups/kite_app"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
sudo -u postgres pg_dump kite_db > $BACKUP_DIR/kite_db_$DATE.sql

# Application backup
tar -czf $BACKUP_DIR/kite_app_$DATE.tar.gz /var/www/kite_app --exclude=/var/www/kite_app/venv

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete
```

### Automated Backups
```bash
# Make script executable
sudo chmod +x /usr/local/bin/backup_kite_db.sh

# Add to daily cron
echo "0 2 * * * /usr/local/bin/backup_kite_db.sh" | sudo crontab -
```

## Development vs Production

### Development Setup (Local)
```bash
# Quick development setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install all Python dependencies from requirements.txt
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run the application
python run.py
```

### Key Differences
- **Database**: SQLite for dev, PostgreSQL for production
- **Web Server**: Flask dev server vs Apache + WSGI
- **SSL**: Not required for dev, mandatory for production
- **Logging**: Console for dev, file-based for production
- **Debug Mode**: Enabled for dev, disabled for production

## Support and Maintenance

- **Logs Location**: `/var/www/kite_app/logs/`
- **Configuration**: `/var/www/kite_app/.env`
- **Database**: PostgreSQL on localhost
- **Web Server**: Apache with mod_wsgi
- **SSL Certificates**: Auto-renewal via certbot

For issues or questions, check the application logs and ensure all services are running properly.
