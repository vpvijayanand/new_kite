#!/bin/bash

# Production Deployment Script for Kite Trading Application
# Usage: ./deploy.sh

set -e

echo "🚀 Deploying Kite Trading Application to Production..."

# Configuration
DOMAIN="newai.vijayanandpremnath.cloud"
EMAIL="your-email@domain.com"
APP_DIR="/var/www/new_aitrader"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Step 1: System Prerequisites
print_status "Installing system prerequisites..."
sudo apt update
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx git curl

# Step 2: Setup Docker
print_status "Setting up Docker..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Step 3: Create application directory
print_status "Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR
cd $APP_DIR

# Step 4: Clone or copy application code
print_status "Setting up application code..."
# If you're using git (recommended):
# git clone https://github.com/yourusername/kite_app.git .
# For now, we'll assume the code is already here

# Step 5: Create necessary directories
print_status "Creating storage directories..."
mkdir -p storage/logs storage/tokens logs/nginx logs/redis docker/ssl/www

# Step 6: Set up environment variables
print_status "Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.production .env
    print_warning "Please edit .env file with your actual API keys and secrets"
    print_warning "Current .env file has placeholder values"
fi

# Step 7: Enable nginx site
print_status "Setting up Nginx configuration..."
sudo ln -sf $APP_DIR/docker/nginx/sites-available/newai.vijayanandpremnath.cloud /etc/nginx/sites-available/
sudo ln -sf $APP_DIR/docker/nginx/sites-available/newai.vijayanandpremnath.cloud /etc/nginx/sites-enabled/

# Step 8: Create nginx proxy_params
sudo cp docker/nginx/proxy_params /etc/nginx/

# Step 9: Test nginx configuration
print_status "Testing Nginx configuration..."
sudo nginx -t

# Step 10: Start the application
print_status "Starting the application..."
docker-compose down || true
docker-compose build
docker-compose up -d

# Step 11: Wait for application to be ready
print_status "Waiting for application to be ready..."
sleep 30

# Step 12: Obtain SSL certificate
print_status "Obtaining SSL certificate..."
sudo certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive --redirect

# Step 13: Setup certificate auto-renewal
print_status "Setting up SSL certificate auto-renewal..."
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Step 14: Final nginx reload
sudo systemctl reload nginx

# Step 15: Setup log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/kite_app > /dev/null <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f $APP_DIR/docker-compose.yml restart nginx
    endscript
}
EOF

# Step 16: Setup monitoring and health checks
print_status "Setting up health check monitoring..."
cat > /tmp/healthcheck.sh << 'EOF'
#!/bin/bash
HEALTH_URL="https://newai.vijayanandpremnath.cloud/health"
if ! curl -f -s $HEALTH_URL > /dev/null; then
    echo "$(date): Health check failed - restarting application"
    cd /var/www/new_aitrader && docker-compose restart kite_app
fi
EOF

sudo mv /tmp/healthcheck.sh /usr/local/bin/kite_healthcheck.sh
sudo chmod +x /usr/local/bin/kite_healthcheck.sh
echo "*/5 * * * * /usr/local/bin/kite_healthcheck.sh" | sudo crontab -u $USER -

# Step 17: Setup firewall
print_status "Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

print_status "✅ Deployment completed successfully!"
print_status ""
print_status "🌐 Your application should now be available at: https://$DOMAIN"
print_status "📊 Health check endpoint: https://$DOMAIN/health"
print_status "📝 Application logs: $APP_DIR/logs/"
print_status "🐳 Docker logs: docker-compose logs -f"
print_status ""
print_warning "⚠️  Don't forget to:"
print_warning "   1. Update .env file with your actual API keys"
print_warning "   2. Configure your DNS to point $DOMAIN to this server"
print_warning "   3. Test all functionality after deployment"
print_warning "   4. Setup monitoring and backups"
