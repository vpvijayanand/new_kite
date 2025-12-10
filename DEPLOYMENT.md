# 🚀 Kite Trading Application - Production Deployment

This guide provides step-by-step instructions to deploy the Kite Trading Application to production with Docker, Nginx, and SSL certificates.

## 📋 Prerequisites

- Ubuntu 20.04+ server
- Domain name pointed to your server: `newai.vijayanandpremnath.cloud`
- Non-root user with sudo privileges
- At least 2GB RAM and 20GB storage

## 🏗️ Architecture

```
Internet -> Nginx (SSL/Reverse Proxy) -> Flask App (Gunicorn) -> SQLite/Redis
```

## 🚀 Quick Deployment

1. **Upload your application code to the server:**
   ```bash
   sudo mkdir -p /var/www/new_aitrader
   sudo chown -R $USER:$USER /var/www/new_aitrader
   cd /var/www/new_aitrader
   # Upload your application files here
   ```

2. **Make deployment script executable and run:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Configure environment variables:**
   ```bash
   nano .env
   # Update with your actual API keys and secrets
   ```

4. **Restart the application:**
   ```bash
   ./manage.sh restart
   ```

## 🔧 Manual Deployment Steps

### Step 1: Install Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx git curl
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### Step 2: Setup Application Directory
```bash
sudo mkdir -p /var/www/new_aitrader
sudo chown -R $USER:$USER /var/www/new_aitrader
cd /var/www/new_aitrader
```

### Step 3: Configure Environment
```bash
cp .env.production .env
nano .env  # Update with your actual values
```

### Step 4: Start Services
```bash
docker-compose build
docker-compose up -d
```

### Step 5: Configure Nginx
```bash
sudo ln -sf /var/www/new_aitrader/docker/nginx/sites-available/newai.vijayanandpremnath.cloud /etc/nginx/sites-enabled/
sudo cp docker/nginx/proxy_params /etc/nginx/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Obtain SSL Certificate
```bash
sudo certbot --nginx -d newai.vijayanandpremnath.cloud --email your-email@domain.com --agree-tos --non-interactive
```

## 🛠️ Management Commands

Use the `manage.sh` script for common operations:

```bash
# Start the application
./manage.sh start

# Stop the application
./manage.sh stop

# Restart the application
./manage.sh restart

# View logs
./manage.sh logs

# Check status
./manage.sh status

# Update application
./manage.sh update

# Create backup
./manage.sh backup

# Clean Docker resources
./manage.sh clean
```

## 📊 Monitoring

### Health Check
```bash
curl https://newai.vijayanandpremnath.cloud/health
```

### View Logs
```bash
# Application logs
docker-compose logs -f kite_app

# Nginx logs
docker-compose logs -f nginx

# All logs
docker-compose logs -f
```

### System Status
```bash
docker-compose ps
systemctl status nginx
```

## 🔒 Security Features

- ✅ SSL/TLS encryption with Let's Encrypt
- ✅ HTTP to HTTPS redirect
- ✅ Security headers (HSTS, XSS Protection, etc.)
- ✅ Rate limiting for API endpoints
- ✅ Firewall configuration
- ✅ Non-root user in containers
- ✅ Secrets management via environment variables

## 📁 Directory Structure

```
/var/www/new_aitrader/
├── app/                    # Flask application
├── docker/                 # Docker configuration
│   ├── nginx/             # Nginx configuration
│   └── ssl/               # SSL certificates
├── storage/               # Application data
│   ├── logs/             # Application logs
│   └── tokens/           # API tokens
├── logs/                 # Service logs
├── docker-compose.yml    # Docker services
├── Dockerfile           # Application container
├── .env                # Environment variables
├── deploy.sh           # Deployment script
└── manage.sh          # Management script
```

## 🚨 Troubleshooting

### Application not starting
```bash
docker-compose logs kite_app
```

### SSL issues
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

### Nginx issues
```bash
sudo nginx -t
sudo systemctl status nginx
```

### Database issues
```bash
docker-compose exec kite_app python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

## 🔄 Maintenance

### Regular Updates
```bash
./manage.sh update
```

### Backup Schedule
Set up automated backups with cron:
```bash
# Add to crontab
0 2 * * * cd /var/www/new_aitrader && ./manage.sh backup
```

### Log Rotation
Logs are automatically rotated using logrotate configuration.

### Certificate Renewal
Certificates are automatically renewed via cron job.

## 🌐 DNS Configuration

Point your domain to the server IP:
```
A Record: newai.vijayanandpremnath.cloud -> YOUR_SERVER_IP
```

## 📞 Support

For issues or questions:
1. Check logs: `./manage.sh logs`
2. Verify status: `./manage.sh status`
3. Review configuration files
4. Check Docker containers: `docker-compose ps`

## 🔐 Environment Variables

Required environment variables in `.env`:
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key`
- `KITE_API_KEY=your-api-key`
- `KITE_API_SECRET=your-api-secret`
- `DATABASE_URL=sqlite:///storage/kite_app.db`
