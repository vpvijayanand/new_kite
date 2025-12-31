# Complete Kite App Environment Migration Guide

## 📦 **Pre-Migration Checklist**

### **Current Environment Assessment**
1. **Database Backup**: Export PostgreSQL database
2. **Configuration Files**: Document all settings
3. **Dependencies**: List all installed packages
4. **Cron Jobs**: Document scheduled tasks
5. **SSL Certificates**: Backup if using HTTPS
6. **Environment Variables**: Document all secrets

---

## 🔄 **Step-by-Step Migration Process**

### **Phase 1: Backup Current Environment**

#### **1.1 Database Backup**
```bash
# PostgreSQL backup
pg_dump -h localhost -U your_username -d kite_db > kite_app_backup_$(date +%Y%m%d_%H%M%S).sql

# Alternative: Full cluster backup
pg_dumpall -h localhost -U postgres > full_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -la *.sql
```

#### **1.2 Application Code Backup**
```bash
# Create complete application archive
cd /path/to/kite_app
tar -czf kite_app_complete_$(date +%Y%m%d_%H%M%S).tar.gz .

# Alternative: Git repository
git add .
git commit -m "Pre-migration backup - $(date)"
git push origin main
```

#### **1.3 Configuration Backup**
```bash
# Export environment variables
env | grep -E "(FLASK|DATABASE|KITE)" > environment_backup.txt

# Copy configuration files
cp config/config.py config/config_backup.py
cp .env .env.backup 2>/dev/null || true

# Document cron jobs
crontab -l > crontab_backup.txt
```

#### **1.4 Virtual Environment Backup**
```bash
# Export Python dependencies
source venv/bin/activate
pip freeze > requirements_current.txt
python --version > python_version.txt
```

---

### **Phase 2: Prepare New Environment**

#### **2.1 System Requirements (New Server)**
```bash
# Update system (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl wget

# For CentOS/RHEL
# sudo yum install -y python3 python3-pip postgresql postgresql-server nginx git

# Install Node.js (for any frontend dependencies)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### **2.2 PostgreSQL Setup**
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database user
sudo -u postgres createuser --interactive
# Enter: your_username, y (superuser)

# Create database
sudo -u postgres createdb kite_db -O your_username

# Set password for user
sudo -u postgres psql
ALTER USER your_username PASSWORD 'your_secure_password';
\q
```

#### **2.3 User and Directory Setup**
```bash
# Create application user (optional but recommended)
sudo useradd -m -s /bin/bash kiteapp
sudo usermod -aG sudo kiteapp

# Create application directory
sudo mkdir -p /opt/kite_app
sudo chown kiteapp:kiteapp /opt/kite_app

# Switch to application user
sudo su - kiteapp
cd /opt/kite_app
```

---

### **Phase 3: Application Migration**

#### **3.1 Code Transfer**
```bash
# Option A: From Git repository
git clone https://github.com/vpvijayanand/new_kite.git .

# Option B: From backup archive
scp kite_app_complete_*.tar.gz new_server:/opt/kite_app/
tar -xzf kite_app_complete_*.tar.gz

# Option C: Using rsync
rsync -avz --progress /old/path/kite_app/ new_server:/opt/kite_app/
```

#### **3.2 Python Environment Setup**
```bash
# Create virtual environment
cd /opt/kite_app
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# If requirements.txt doesn't exist, install key packages
pip install flask flask-sqlalchemy flask-migrate psycopg2-binary python-dotenv
pip install apscheduler requests pandas numpy
```

#### **3.3 Database Migration**
```bash
# Transfer and restore database
scp kite_app_backup_*.sql new_server:/tmp/

# Restore database
psql -h localhost -U your_username -d kite_db < /tmp/kite_app_backup_*.sql

# Run Flask migrations
export FLASK_APP=run.py
flask db upgrade

# Verify database
psql -h localhost -U your_username -d kite_db -c "\dt"
```

#### **3.4 Configuration Files**
```bash
# Create environment file
cat > .env << EOF
FLASK_ENV=production
DATABASE_URL=postgresql://your_username:your_password@localhost/kite_db
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_secret
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
EOF

# Update configuration
vim config/config.py
# Update database connection, API keys, etc.
```

---

### **Phase 4: Service Configuration**

#### **4.1 Systemd Service Setup**
```bash
# Create systemd service file
sudo tee /etc/systemd/system/kite-app.service << EOF
[Unit]
Description=Kite Trading Application
After=network.target postgresql.service

[Service]
Type=simple
User=kiteapp
Group=kiteapp
WorkingDirectory=/opt/kite_app
Environment=PATH=/opt/kite_app/venv/bin
ExecStart=/opt/kite_app/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable kite-app
sudo systemctl start kite-app
sudo systemctl status kite-app
```

#### **4.2 Nginx Configuration**
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/kite-app << EOF
server {
    listen 80;
    server_name your_domain_or_ip;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    location /static {
        alias /opt/kite_app/app/views/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/kite-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### **4.3 SSL Configuration (Optional)**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your_domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

### **Phase 5: Strategy 1 Cron Jobs**

#### **5.1 Cron Job Setup**
```bash
# Switch to application user
sudo su - kiteapp

# Make scripts executable
chmod +x /opt/kite_app/scripts/strategy1_standalone.py

# Add cron jobs
crontab -e

# Add these lines:
# Strategy 1 - NIFTY Breakout Monitoring
30-59 9 * * 1-5 cd /opt/kite_app && /opt/kite_app/venv/bin/python scripts/strategy1_standalone.py >> logs/strategy1_cron.log 2>&1
0-15 10-14 * * 1-5 cd /opt/kite_app && /opt/kite_app/venv/bin/python scripts/strategy1_standalone.py >> logs/strategy1_cron.log 2>&1
0-15 15 * * 1-5 cd /opt/kite_app && /opt/kite_app/venv/bin/python scripts/strategy1_standalone.py >> logs/strategy1_cron.log 2>&1
```

#### **5.2 Log Directory Setup**
```bash
# Create log directories
mkdir -p /opt/kite_app/logs
chmod 755 /opt/kite_app/logs

# Setup log rotation
sudo tee /etc/logrotate.d/kite-app << EOF
/opt/kite_app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 kiteapp kiteapp
}
EOF
```

---

### **Phase 6: Testing and Verification**

#### **6.1 Application Testing**
```bash
# Test database connection
cd /opt/kite_app
source venv/bin/activate
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app import db
    result = db.engine.execute('SELECT 1')
    print('Database connection: OK')
"

# Test Flask application
curl http://localhost:5000/
curl http://localhost:5000/strategies/

# Test Strategy 1 API
curl http://localhost:5000/strategies/api/strategy-1/status
```

#### **6.2 Strategy Testing**
```bash
# Manual strategy execution test
cd /opt/kite_app
source venv/bin/activate
python scripts/strategy1_standalone.py

# Check logs
tail -f logs/strategy1_cron.log
```

#### **6.3 Performance Testing**
```bash
# Check system resources
htop
df -h
free -m

# Monitor application logs
journalctl -u kite-app -f

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

### **Phase 7: Security and Monitoring**

#### **7.1 Firewall Configuration**
```bash
# Setup UFW firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw status
```

#### **7.2 Monitoring Setup**
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Setup basic monitoring script
cat > /opt/kite_app/scripts/health_check.sh << 'EOF'
#!/bin/bash
# Basic health monitoring

APP_URL="http://localhost:5000"
LOG_FILE="/opt/kite_app/logs/health_check.log"

echo "$(date): Checking application health..." >> $LOG_FILE

# Check if app is responding
if curl -f $APP_URL > /dev/null 2>&1; then
    echo "$(date): Application is healthy" >> $LOG_FILE
else
    echo "$(date): Application is DOWN - restarting" >> $LOG_FILE
    sudo systemctl restart kite-app
fi

# Check database connectivity
cd /opt/kite_app
source venv/bin/activate
python -c "
import datetime
try:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app import db
        db.engine.execute('SELECT 1')
    print(f'{datetime.datetime.now()}: Database connection OK')
except Exception as e:
    print(f'{datetime.datetime.now()}: Database connection failed: {str(e)}')
" >> $LOG_FILE
EOF

chmod +x /opt/kite_app/scripts/health_check.sh

# Add to cron for monitoring
crontab -e
# Add: */5 * * * * /opt/kite_app/scripts/health_check.sh
```

---

### **Phase 8: Backup and Recovery Setup**

#### **8.1 Automated Backups**
```bash
# Database backup script
cat > /opt/kite_app/scripts/backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/kite_app/backups"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U your_username kite_db > $BACKUP_DIR/kite_db_$(date +%Y%m%d_%H%M%S).sql

# Keep only last 7 days
find $BACKUP_DIR -name "kite_db_*.sql" -mtime +7 -delete

echo "$(date): Database backup completed"
EOF

chmod +x /opt/kite_app/scripts/backup_db.sh

# Add to cron
crontab -e
# Add: 0 2 * * * /opt/kite_app/scripts/backup_db.sh
```

---

## 🔍 **Migration Verification Checklist**

### **✅ Essential Checks**
- [ ] Application loads at http://your_server/
- [ ] Database connectivity working
- [ ] Strategy 1 dashboard accessible
- [ ] Cron jobs running (check with `crontab -l`)
- [ ] Logs being generated
- [ ] SSL certificate working (if applicable)
- [ ] All API endpoints responding
- [ ] Strategy execution working manually

### **✅ Performance Checks**
- [ ] Page load times acceptable
- [ ] Database queries performing well
- [ ] Memory usage within limits
- [ ] Disk space adequate
- [ ] Network connectivity stable

### **✅ Security Checks**
- [ ] Firewall configured
- [ ] Database passwords secure
- [ ] Application running as non-root user
- [ ] File permissions correct
- [ ] SSL/TLS configured

---

## 🚨 **Troubleshooting Common Issues**

### **Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection manually
psql -h localhost -U your_username -d kite_db

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### **Application Won't Start**
```bash
# Check service logs
journalctl -u kite-app -f

# Test manual startup
cd /opt/kite_app
source venv/bin/activate
python run.py

# Check Python dependencies
pip check
```

### **Cron Jobs Not Working**
```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog

# Test script manually
cd /opt/kite_app
source venv/bin/activate
python scripts/strategy1_standalone.py
```

---

## 📞 **Support and Maintenance**

### **Regular Maintenance Tasks**
1. **Weekly**: Check application logs
2. **Monthly**: Review database performance
3. **Quarterly**: Update dependencies
4. **As needed**: Monitor disk space and backups

### **Update Process**
```bash
# Application updates
cd /opt/kite_app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart kite-app
```

This comprehensive guide ensures a smooth migration of your complete kite_app setup to any new environment!
