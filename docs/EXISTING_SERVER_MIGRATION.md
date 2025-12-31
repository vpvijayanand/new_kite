# Kite App Migration for vijayanandpremnath.cloud

## 🎯 **Current Environment Setup**
- **Domain**: vijayanandpremnath.cloud
- **Server**: Ubuntu with Apache Web Server
- **Web Server**: Apache with WSGI configured
- **App Location**: /var/www/html/Kite_app
- **Database**: PostgreSQL installed and running
- **Code Status**: New code already pulled to Kite_app folder

---

## 🚀 **Step-by-Step Migration Process**

### **Step 1: Navigate to Application Directory**
```bash
cd /var/www/html/Kite_app
```

### **Step 2: Create Python Virtual Environment**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### **Step 3: Install Python Dependencies**
```bash
# Install all required packages
pip install Flask==3.0.0
pip install Flask-SQLAlchemy==3.1.1
pip install Flask-Migrate==4.0.5
pip install psycopg2-binary==2.9.9
pip install kiteconnect==5.0.1
pip install python-dotenv==1.0.0
pip install APScheduler==3.10.4
pip install gunicorn==21.2.0
pip install pytz==2023.3
pip install requests==2.31.0
pip install pandas==2.1.1
pip install numpy==1.25.2

# Or install from requirements.txt if available
# pip install -r requirements.txt
```

### **Step 4: PostgreSQL Database Setup**
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user (run these SQL commands)
CREATE DATABASE kite_db;
CREATE USER kiteuser WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE kite_db TO kiteuser;
\q
```

### **Step 5: Environment Configuration**
```bash
# Create .env file in /var/www/html/Kite_app/
cat > .env << 'EOF'
# Flask Configuration
SECRET_KEY=your_secret_key_here
FLASK_ENV=production

# Database Configuration
DATABASE_URL=postgresql://kiteuser:your_secure_password@localhost/kite_db

# Kite Connect API Configuration
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret
KITE_REDIRECT_URL=https://vijayanandpremnath.cloud/kite/callback

# Token Storage Path
TOKEN_FILE_PATH=storage/tokens/access_token.json
EOF

# Generate a secure secret key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env.temp
# Copy the generated key to replace 'your_secret_key_here' in .env
```

### **Step 6: Set Proper Permissions**
```bash
# Set ownership to Apache user (usually www-data)
sudo chown -R www-data:www-data /var/www/html/Kite_app

# Set proper permissions
sudo chmod -R 755 /var/www/html/Kite_app
sudo chmod -R 644 /var/www/html/Kite_app/.env

# Make sure storage and logs directories exist and are writable
mkdir -p /var/www/html/Kite_app/storage/tokens
mkdir -p /var/www/html/Kite_app/logs
sudo chown -R www-data:www-data /var/www/html/Kite_app/storage
sudo chown -R www-data:www-data /var/www/html/Kite_app/logs
sudo chmod -R 755 /var/www/html/Kite_app/storage
sudo chmod -R 755 /var/www/html/Kite_app/logs
```

### **Step 7: Database Migration**
```bash
# Navigate to app directory and activate virtual environment
cd /var/www/html/Kite_app
source venv/bin/activate

# Set Flask app
export FLASK_APP=run.py

# Initialize database migrations (if migrations folder doesn't exist)
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migrations
flask db upgrade
```

### **Step 8: Apache WSGI Configuration**
```bash
# Create WSGI file for the application
sudo tee /var/www/html/Kite_app/kite_app.wsgi << 'EOF'
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
```

### **Step 9: Apache Virtual Host Configuration**
```bash
# Create or update Apache virtual host configuration
sudo tee /etc/apache2/sites-available/vijayanandpremnath.cloud.conf << 'EOF'
<VirtualHost *:80>
    ServerName vijayanandpremnath.cloud
    ServerAlias www.vijayanandpremnath.cloud
    
    # Redirect HTTP to HTTPS
    Redirect permanent / https://vijayanandpremnath.cloud/
</VirtualHost>

<VirtualHost *:443>
    ServerName vijayanandpremnath.cloud
    ServerAlias www.vijayanandpremnath.cloud
    
    DocumentRoot /var/www/html/Kite_app
    
    WSGIDaemonProcess kiteapp python-home=/var/www/html/Kite_app/venv python-path=/var/www/html/Kite_app
    WSGIProcessGroup kiteapp
    WSGIScriptAlias / /var/www/html/Kite_app/kite_app.wsgi
    
    <Directory /var/www/html/Kite_app>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>
    
    # Static files
    Alias /static /var/www/html/Kite_app/app/views/static
    <Directory /var/www/html/Kite_app/app/views/static>
        Require all granted
    </Directory>
    
    # SSL Configuration (if you have SSL certificates)
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/vijayanandpremnath.cloud.crt
    SSLCertificateKeyFile /etc/ssl/private/vijayanandpremnath.cloud.key
    # SSLCertificateChainFile /etc/ssl/certs/vijayanandpremnath.cloud-chain.crt
    
    # Security headers
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/kite_app_error.log
    CustomLog ${APACHE_LOG_DIR}/kite_app_access.log combined
</VirtualHost>
EOF
```

### **Step 10: Enable Required Apache Modules**
```bash
# Enable required Apache modules
sudo a2enmod wsgi
sudo a2enmod ssl
sudo a2enmod headers
sudo a2enmod rewrite

# Enable the site
sudo a2ensite vijayanandpremnath.cloud.conf

# Disable default site if needed
sudo a2dissite 000-default.conf

# Test Apache configuration
sudo apache2ctl configtest

# Restart Apache
sudo systemctl restart apache2
sudo systemctl status apache2
```

### **Step 11: SSL Certificate Setup (Let's Encrypt)**
```bash
# Install Certbot for Apache
sudo apt update
sudo apt install certbot python3-certbot-apache -y

# Get SSL certificate
sudo certbot --apache -d vijayanandpremnath.cloud -d www.vijayanandpremnath.cloud

# Test automatic renewal
sudo certbot renew --dry-run
```

### **Step 12: Strategy 1 Cron Jobs Setup**
```bash
# Switch to www-data user for cron jobs
sudo crontab -u www-data -e

# Add these cron job entries:
# Strategy 1 - NIFTY Breakout Monitoring (Market Hours: 9:30 AM - 3:30 PM IST)
30-59 9 * * 1-5 cd /var/www/html/Kite_app && /var/www/html/Kite_app/venv/bin/python scripts/strategy1_standalone.py >> logs/strategy1_cron.log 2>&1
0-15 10-14 * * 1-5 cd /var/www/html/Kite_app && /var/www/html/Kite_app/venv/bin/python scripts/strategy1_standalone.py >> logs/strategy1_cron.log 2>&1
0-15 15 * * 1-5 cd /var/www/html/Kite_app && /var/www/html/Kite_app/venv/bin/python scripts/strategy1_standalone.py >> logs/strategy1_cron.log 2>&1

# Health check every 5 minutes
*/5 * * * * curl -f https://vijayanandpremnath.cloud/api/health >> /var/www/html/Kite_app/logs/health_check.log 2>&1

# Daily database backup at 2 AM
0 2 * * * pg_dump -h localhost -U kiteuser kite_db > /var/www/html/Kite_app/backups/kite_db_$(date +\%Y\%m\%d_\%H\%M\%S).sql
```

### **Step 13: Create Backup Directory and Scripts**
```bash
# Create backup directory
mkdir -p /var/www/html/Kite_app/backups
sudo chown www-data:www-data /var/www/html/Kite_app/backups

# Create backup script
cat > /var/www/html/Kite_app/scripts/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/www/html/Kite_app/backups"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U kiteuser kite_db > $BACKUP_DIR/kite_db_$(date +%Y%m%d_%H%M%S).sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "kite_db_*.sql" -mtime +7 -delete

echo "$(date): Database backup completed" >> /var/www/html/Kite_app/logs/backup.log
EOF

chmod +x /var/www/html/Kite_app/scripts/backup_db.sh
sudo chown www-data:www-data /var/www/html/Kite_app/scripts/backup_db.sh
```

### **Step 14: Testing and Verification**
```bash
# Test database connection
cd /var/www/html/Kite_app
source venv/bin/activate
python3 -c "
from app import create_app
app = create_app()
with app.app_context():
    from app import db
    print('Database connection: OK')
"

# Test Apache restart
sudo systemctl restart apache2

# Check Apache status
sudo systemctl status apache2

# Test website access
curl -I https://vijayanandpremnath.cloud/

# Test Strategy 1 API
curl https://vijayanandpremnath.cloud/strategies/api/strategy-1/status
```

---

## 🔍 **Verification Checklist**

### **✅ Essential Checks**
- [ ] Website loads: https://vijayanandpremnath.cloud/
- [ ] SSL certificate working (green padlock)
- [ ] Database connection successful
- [ ] Strategy 1 dashboard accessible: https://vijayanandpremnath.cloud/strategies/
- [ ] API endpoints responding: https://vijayanandpremnath.cloud/api/health
- [ ] Virtual environment activated and dependencies installed
- [ ] Apache configuration valid (`sudo apache2ctl configtest`)
- [ ] Cron jobs scheduled (`sudo crontab -u www-data -l`)
- [ ] Log files being created in logs/ directory
- [ ] File permissions correct (www-data ownership)

### **✅ Performance Checks**
- [ ] Page load times < 3 seconds
- [ ] Apache error logs clean (`sudo tail -f /var/log/apache2/kite_app_error.log`)
- [ ] No Python import errors
- [ ] Database queries responding quickly

---

## 🚨 **Troubleshooting**

### **Apache Issues**
```bash
# Check Apache error logs
sudo tail -f /var/log/apache2/error.log
sudo tail -f /var/log/apache2/kite_app_error.log

# Check Apache status
sudo systemctl status apache2

# Test Apache configuration
sudo apache2ctl configtest

# Restart Apache
sudo systemctl restart apache2
```

### **Python/WSGI Issues**
```bash
# Check WSGI application directly
cd /var/www/html/Kite_app
source venv/bin/activate
python3 kite_app.wsgi

# Check Python path and imports
python3 -c "import sys; print(sys.path)"
python3 -c "from app import create_app; print('Import successful')"
```

### **Database Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -h localhost -U kiteuser -d kite_db

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### **Permission Issues**
```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/html/Kite_app

# Fix permissions
sudo chmod -R 755 /var/www/html/Kite_app
sudo chmod 644 /var/www/html/Kite_app/.env
```

---

## 📝 **Post-Migration Tasks**

### **1. Update DNS (if needed)**
- Ensure vijayanandpremnath.cloud points to your server IP
- Add www.vijayanandpremnath.cloud CNAME record

### **2. Configure Monitoring**
```bash
# Set up log monitoring
sudo apt install logwatch
sudo logwatch --detail Med --mailto your-email@domain.com --service apache --range today
```

### **3. Security Hardening**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### **4. Backup Strategy**
- Automated daily database backups (already configured)
- Weekly full application backup
- Monthly off-site backup

---

## 🎉 **Success!**

Your Kite App should now be running at:
- **Main Site**: https://vijayanandpremnath.cloud/
- **Strategies**: https://vijayanandpremnath.cloud/strategies/
- **Strategy 1**: https://vijayanandpremnath.cloud/strategies/strategy-1

The application will:
- ✅ Run automatically via Apache WSGI
- ✅ Execute Strategy 1 during market hours via cron
- ✅ Backup database daily
- ✅ Monitor health automatically
- ✅ Serve over HTTPS with SSL

**Next Steps**: Configure your Kite Connect API credentials in the `.env` file and test the trading strategies!
