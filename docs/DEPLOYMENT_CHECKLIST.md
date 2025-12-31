# Kite App Deployment Checklist

## Pre-Migration Preparation

### Source Environment (Current)
- [ ] **Backup Database**
  ```bash
  pg_dump -h localhost -U your_user kite_db > kite_db_backup_$(date +%Y%m%d).sql
  ```

- [ ] **Export Environment Variables**
  - [ ] Copy `.env` file
  - [ ] Document Kite API credentials
  - [ ] Note database connection details

- [ ] **Archive Application Code**
  ```bash
  tar -czf kite_app_$(date +%Y%m%d).tar.gz /path/to/kite_app
  ```

- [ ] **Document Current Configuration**
  - [ ] Python version: `python --version`
  - [ ] Installed packages: `pip freeze > requirements.txt`
  - [ ] System services status
  - [ ] Cron jobs: `crontab -l`

---

## Target Environment Setup

### System Requirements
- [ ] **Operating System**
  - [ ] Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
  - [ ] Minimum 2GB RAM, 10GB storage
  - [ ] Network access to Kite Connect APIs

- [ ] **Install Base Software**
  - [ ] Python 3.8+ 
  - [ ] PostgreSQL 12+
  - [ ] Git (optional)
  - [ ] Nginx (Linux) / IIS (Windows)

### Quick Setup Scripts
- [ ] **Linux/Ubuntu**
  ```bash
  chmod +x scripts/quick_migration_setup.sh
  ./scripts/quick_migration_setup.sh
  ```

- [ ] **Windows**
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  .\scripts\quick_migration_setup.ps1
  ```

---

## Application Deployment

### 1. Code Transfer
- [ ] **Copy Files**
  ```bash
  # Linux
  scp -r kite_app/ user@target-server:/opt/kite_app/
  
  # Windows
  # Use WinSCP or copy via RDP
  ```

- [ ] **Set Permissions (Linux)**
  ```bash
  sudo chown -R kiteapp:kiteapp /opt/kite_app
  sudo chmod +x /opt/kite_app/scripts/*.sh
  ```

### 2. Environment Configuration
- [ ] **Create Environment File**
  ```bash
  cp .env.template .env
  nano .env  # Update with actual values
  ```

- [ ] **Required Environment Variables**
  ```env
  SECRET_KEY=generate_random_key_here
  DATABASE_URL=postgresql://user:pass@localhost/kite_db
  KITE_API_KEY=your_api_key
  KITE_API_SECRET=your_api_secret
  ```

### 3. Database Setup
- [ ] **Create Database**
  ```sql
  CREATE DATABASE kite_db;
  CREATE USER kiteuser WITH PASSWORD 'secure_password';
  GRANT ALL PRIVILEGES ON DATABASE kite_db TO kiteuser;
  ```

- [ ] **Restore Data**
  ```bash
  psql -h localhost -U kiteuser -d kite_db < kite_db_backup.sql
  ```

- [ ] **Run Migrations**
  ```bash
  cd /opt/kite_app
  source venv/bin/activate
  export FLASK_APP=run.py
  flask db upgrade
  ```

### 4. Python Environment
- [ ] **Create Virtual Environment**
  ```bash
  cd /opt/kite_app
  python3 -m venv venv
  source venv/bin/activate
  ```

- [ ] **Install Dependencies**
  ```bash
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

---

## Service Configuration

### Linux - SystemD Service
- [ ] **Create Service File**
  ```bash
  sudo systemctl enable kite-app
  sudo systemctl start kite-app
  sudo systemctl status kite-app
  ```

### Windows - Windows Service
- [ ] **Install Service**
  ```powershell
  pip install pywin32
  python kite_service.py install
  python kite_service.py start
  ```

### Web Server Setup
- [ ] **Nginx (Linux)**
  ```bash
  sudo systemctl enable nginx
  sudo systemctl start nginx
  sudo systemctl status nginx
  ```

- [ ] **Test Reverse Proxy**
  - [ ] Visit: `http://your-server-ip/`
  - [ ] Check: `http://your-server-ip/strategies/`

---

## Automation Setup

### Cron Jobs (Linux)
- [ ] **Edit Crontab**
  ```bash
  sudo -u kiteapp crontab -e
  ```

- [ ] **Add Strategy 1 Jobs**
  ```cron
  # Strategy 1 execution at market hours
  30-59 9 * * 1-5 /opt/kite_app/scripts/strategy1_cron.sh
  0-29 10,11,12,13,14,15 * * 1-5 /opt/kite_app/scripts/strategy1_cron.sh
  
  # Health check every 5 minutes
  */5 * * * * /opt/kite_app/scripts/health_check.sh
  
  # Daily backup at 6 AM
  0 6 * * * /opt/kite_app/scripts/backup_db.sh
  ```

### Scheduled Tasks (Windows)
- [ ] **Create Tasks**
  ```powershell
  .\scripts\create_scheduled_task.ps1
  ```

---

## Testing & Verification

### Functional Testing
- [ ] **Application Access**
  - [ ] Login page loads: `/`
  - [ ] Dashboard accessible: `/dashboard`
  - [ ] Strategies menu: `/strategies/`
  - [ ] Strategy 1 page: `/strategies/strategy-1`

- [ ] **API Endpoints**
  - [ ] Health check: `/api/health`
  - [ ] Strategy status: `/api/strategies/strategy-1/status`
  - [ ] Market data: `/api/market/nifty-price`

- [ ] **Database Operations**
  - [ ] Strategy executions logging
  - [ ] User authentication
  - [ ] Market data storage

### Performance Testing
- [ ] **Resource Usage**
  - [ ] Memory usage < 1GB under normal load
  - [ ] CPU usage < 50% during trading hours
  - [ ] Disk space sufficient for logs

- [ ] **Response Times**
  - [ ] Page load times < 3 seconds
  - [ ] API responses < 1 second
  - [ ] Strategy execution < 30 seconds

---

## Security Configuration

### Firewall Rules
- [ ] **Linux (UFW)**
  ```bash
  sudo ufw allow ssh
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw --force enable
  ```

- [ ] **Windows Firewall**
  - [ ] Allow inbound HTTP (80)
  - [ ] Allow inbound HTTPS (443)
  - [ ] Restrict PostgreSQL (5432) to localhost

### SSL Certificate (Production)
- [ ] **Let's Encrypt (Linux)**
  ```bash
  sudo apt install certbot python3-certbot-nginx
  sudo certbot --nginx -d yourdomain.com
  ```

- [ ] **Update Nginx Configuration**
  - [ ] Force HTTPS redirects
  - [ ] Security headers
  - [ ] Rate limiting

---

## Monitoring Setup

### Log Files Monitoring
- [ ] **Application Logs**
  - [ ] `/opt/kite_app/logs/app.log`
  - [ ] `/opt/kite_app/logs/strategy1.log`
  - [ ] `/opt/kite_app/logs/health_check.log`

- [ ] **System Logs**
  - [ ] `/var/log/nginx/access.log`
  - [ ] `journalctl -u kite-app -f`

### Health Monitoring
- [ ] **Automated Checks**
  - [ ] Application uptime monitoring
  - [ ] Database connectivity
  - [ ] API response times
  - [ ] Disk space alerts

---

## Post-Deployment Tasks

### Documentation
- [ ] **Update Documentation**
  - [ ] Server details (IP, credentials)
  - [ ] Service management commands
  - [ ] Troubleshooting procedures
  - [ ] Backup/restore procedures

### Team Training
- [ ] **Operations Team**
  - [ ] How to restart services
  - [ ] How to check logs
  - [ ] How to perform backups
  - [ ] Emergency procedures

### Maintenance Schedule
- [ ] **Regular Tasks**
  - [ ] Weekly: Review logs and performance
  - [ ] Monthly: Update dependencies
  - [ ] Quarterly: Security updates
  - [ ] Annually: Renew SSL certificates

---

## Rollback Plan

### Emergency Procedures
- [ ] **Service Issues**
  ```bash
  # Restart services
  sudo systemctl restart kite-app
  sudo systemctl restart nginx
  
  # Check status
  sudo systemctl status kite-app
  ```

- [ ] **Database Issues**
  ```bash
  # Restore from backup
  psql -h localhost -U kiteuser -d kite_db < latest_backup.sql
  ```

- [ ] **Complete Rollback**
  - [ ] Restore previous application version
  - [ ] Restore database backup
  - [ ] Update DNS if needed
  - [ ] Verify functionality

---

## Success Criteria

### Deployment Complete When:
- [ ] ✅ Application accessible via web browser
- [ ] ✅ All strategies functioning correctly
- [ ] ✅ Database operations working
- [ ] ✅ Automated jobs running
- [ ] ✅ Monitoring in place
- [ ] ✅ Backups configured
- [ ] ✅ Documentation updated
- [ ] ✅ Team trained on operations

---

## Support Contacts

### Technical Issues
- **Application**: Check logs in `/opt/kite_app/logs/`
- **Database**: PostgreSQL admin
- **System**: Infrastructure team
- **API**: Kite Connect support

### Emergency Contacts
- **Primary**: [Your contact info]
- **Secondary**: [Backup contact]
- **Infrastructure**: [Infrastructure team]

---

*Last Updated: $(date)*
*Migration Guide Version: 1.0*
