# 🚀 STEP-BY-STEP Ubuntu Production Deployment Guide

This is a comprehensive step-by-step guide to deploy the Kite Trading Application on Ubuntu using Docker.

## 📋 Prerequisites Checklist

- [ ] Ubuntu 20.04+ server with sudo access
- [ ] Domain `newai.vijayanandpremnath.cloud` pointing to your server IP
- [ ] At least 2GB RAM and 20GB disk space
- [ ] Your Kite Connect API credentials

## 🎯 Step-by-Step Deployment

### Step 1: Connect to Your Ubuntu Server

```bash
# SSH into your server
ssh username@your-server-ip

# Update the system
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Docker and Dependencies

```bash
# Install Docker
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to docker group
sudo usermod -aG docker $USER

# Install additional tools
sudo apt install -y nginx certbot python3-certbot-nginx git curl unzip

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Log out and back in to apply group changes
exit
# SSH back in
ssh username@your-server-ip
```

### Step 3: Verify Docker Installation

```bash
# Test Docker
docker --version
docker-compose --version
docker run hello-world

# You should see "Hello from Docker!" message
```

### Step 4: Create Application Directory

```bash
# Create the application directory
sudo mkdir -p /var/www/new_aitrader
sudo chown -R $USER:$USER /var/www/new_aitrader
cd /var/www/new_aitrader
```

### Step 5: Upload Your Application Files

**Option A: Using SCP (from your local machine):**
```bash
# From your local Windows machine (use PowerShell or WSL)
scp -r c:\apps\kite_app\* username@your-server-ip:/var/www/new_aitrader/
```

**Option B: Using Git (if you have a repository):**
```bash
# Clone your repository
git clone https://github.com/yourusername/kite_app.git .
```

**Option C: Manual Upload:**
- Use SFTP client like FileZilla
- Upload all files from `c:\apps\kite_app\` to `/var/www/new_aitrader/`

### Step 6: Set File Permissions

```bash
cd /var/www/new_aitrader

# Make scripts executable
chmod +x deploy.sh
chmod +x manage.sh  
chmod +x preflight-check.sh
chmod +x docker/entrypoint.sh

# Create required directories
mkdir -p storage/logs storage/tokens logs/nginx logs/redis docker/ssl/www
```

### Step 7: Run Pre-deployment Check

```bash
# Run the preflight check
./preflight-check.sh
```

### Step 8: Configure Environment Variables

```bash
# Copy the production environment template
cp .env.production .env

# Edit the environment file
nano .env
```

**Update these critical values:**
```bash
SECRET_KEY=your-super-secret-random-key-here
KITE_API_KEY=your_actual_kite_api_key
KITE_API_SECRET=your_actual_kite_secret
SSL_EMAIL=your-email@domain.com
DOMAIN_NAME=newai.vijayanandpremnath.cloud
```

**Generate a secure secret key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 9: Run Automated Deployment

```bash
# Run the deployment script
./deploy.sh
```

**The script will:**
- Install system dependencies
- Configure Docker
- Set up Nginx
- Start the application
- Obtain SSL certificate
- Configure firewall
- Set up monitoring

### Step 10: Manual Verification Steps

```bash
# Check if containers are running
docker-compose ps

# Expected output:
# NAME               IMAGE              COMMAND             SERVICE         CREATED         STATUS                   PORTS
# kite_nginx         nginx:alpine       "/docker-entrypoint…"   nginx           2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
# kite_redis         redis:7-alpine     "docker-entrypoint.s…"   redis           2 minutes ago   Up 2 minutes (healthy)   6379/tcp
# kite_trading_app   kite_app-kite_app  "/entrypoint.sh"        kite_app        2 minutes ago   Up 2 minutes (healthy)   8000/tcp
```

### Step 11: Test the Application

```bash
# Test health endpoint
curl http://localhost/health

# Test HTTPS (after SSL setup)
curl -k https://newai.vijayanandpremnath.cloud/health

# Expected response:
# {"status":"healthy","service":"kite_trading_app","version":"1.0.0"}
```

### Step 12: Configure DNS (if not done already)

**On your domain provider (GoDaddy, Namecheap, etc.):**
```
Type: A Record
Name: newai (or @)
Value: YOUR_SERVER_IP
TTL: 300 seconds
```

**Verify DNS propagation:**
```bash
nslookup newai.vijayanandpremnath.cloud
```

### Step 13: Obtain SSL Certificate

```bash
# Get SSL certificate (if not done automatically)
sudo certbot --nginx -d newai.vijayanandpremnath.cloud --email your-email@domain.com --agree-tos --non-interactive
```

### Step 14: Final Testing

```bash
# Test the full application
curl https://newai.vijayanandpremnath.cloud/health

# Check logs
./manage.sh logs

# Check application status
./manage.sh status
```

## 🎉 Success! Your Application is Live

Your Kite Trading Application should now be accessible at:
- **Main App:** https://newai.vijayanandpremnath.cloud
- **Health Check:** https://newai.vijayanandpremnath.cloud/health

## 📱 Management Commands

```bash
# Start application
./manage.sh start

# Stop application  
./manage.sh stop

# Restart application
./manage.sh restart

# View logs
./manage.sh logs

# Check status
./manage.sh status

# Update application (from git)
./manage.sh update

# Create backup
./manage.sh backup

# Clean up Docker resources
./manage.sh clean
```

## 🔍 Troubleshooting

### Application Won't Start
```bash
# Check container logs
docker-compose logs kite_app

# Check if all required files are present
./preflight-check.sh

# Restart containers
./manage.sh restart
```

### SSL Issues
```bash
# Check certificate status
sudo certbot certificates

# Test certificate renewal
sudo certbot renew --dry-run

# Manual certificate generation
sudo certbot --nginx -d newai.vijayanandpremnath.cloud
```

### Nginx Issues
```bash
# Test Nginx configuration
sudo nginx -t

# Check Nginx status
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx
```

### Port Issues
```bash
# Check what's using port 80/443
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Stop conflicting services
sudo systemctl stop apache2  # if Apache is running
```

## 🔐 Security Checklist

- [ ] Firewall is enabled (`sudo ufw status`)
- [ ] SSL certificate is installed and valid
- [ ] Default passwords changed
- [ ] Regular backups configured
- [ ] Log monitoring set up
- [ ] Server updates automated

## 📊 Monitoring

### Check Application Health
```bash
# Application health
curl https://newai.vijayanandpremnath.cloud/health

# Container status
docker-compose ps

# System resources
htop
df -h
```

### View Logs
```bash
# Application logs
./manage.sh logs kite_app

# Nginx logs
./manage.sh logs nginx

# All logs
./manage.sh logs
```

## 🎯 Next Steps

1. **Configure API Keys:** Ensure your Kite Connect API keys are valid
2. **Test Trading Features:** Verify all trading functions work
3. **Set up Monitoring:** Configure alerts for system health
4. **Regular Backups:** Schedule automated backups
5. **Update Procedures:** Plan for application updates

## 📞 Support

If you encounter issues:
1. Run `./preflight-check.sh` to verify setup
2. Check logs: `./manage.sh logs`
3. Verify DNS settings
4. Check firewall rules: `sudo ufw status`
5. Verify domain SSL certificate

Your production Kite Trading Application is now ready! 🚀
