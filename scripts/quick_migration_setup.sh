#!/bin/bash

# Kite App Quick Migration Script
# This script automates the basic setup for migrating kite_app to a new environment

set -e  # Exit on any error

echo "🚀 Starting Kite App Migration Setup..."
echo "========================================"

# Configuration
APP_USER="kiteapp"
APP_DIR="/opt/kite_app"
DB_NAME="kite_db"
DB_USER="kiteuser"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Update system packages
update_system() {
    print_status "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    
    print_status "Installing required system packages..."
    sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib \
                       nginx git curl wget htop unzip
}

# Setup PostgreSQL
setup_database() {
    print_status "Setting up PostgreSQL database..."
    
    # Start PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Create database user
    print_status "Creating database user: $DB_USER"
    sudo -u postgres createuser --interactive --pwprompt $DB_USER
    
    # Create database
    print_status "Creating database: $DB_NAME"
    sudo -u postgres createdb $DB_NAME -O $DB_USER
    
    print_status "Database setup completed"
}

# Create application user and directories
setup_user() {
    print_status "Creating application user: $APP_USER"
    
    if ! id "$APP_USER" &>/dev/null; then
        sudo useradd -m -s /bin/bash $APP_USER
        sudo usermod -aG sudo $APP_USER
    else
        print_warning "User $APP_USER already exists"
    fi
    
    print_status "Creating application directory: $APP_DIR"
    sudo mkdir -p $APP_DIR
    sudo chown $APP_USER:$APP_USER $APP_DIR
    
    # Create log directory
    sudo mkdir -p $APP_DIR/logs
    sudo chown $APP_USER:$APP_USER $APP_DIR/logs
}

# Setup Python environment
setup_python() {
    print_status "Setting up Python environment..."
    
    cd $APP_DIR
    
    # Create virtual environment
    sudo -u $APP_USER python3 -m venv venv
    
    # Activate and upgrade pip
    sudo -u $APP_USER bash -c "source venv/bin/activate && pip install --upgrade pip"
    
    print_status "Python environment setup completed"
}

# Install application dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    cd $APP_DIR
    
    # Create basic requirements.txt if it doesn't exist
    if [ ! -f requirements.txt ]; then
        print_status "Creating basic requirements.txt..."
        cat > requirements.txt << EOF
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
psycopg2-binary==2.9.7
python-dotenv==1.0.0
APScheduler==3.10.4
requests==2.31.0
pandas==2.1.1
numpy==1.25.2
pytz==2023.3
EOF
        sudo chown $APP_USER:$APP_USER requirements.txt
    fi
    
    # Install dependencies
    sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && pip install -r requirements.txt"
}

# Setup systemd service
setup_service() {
    print_status "Creating systemd service..."
    
    sudo tee /etc/systemd/system/kite-app.service > /dev/null << EOF
[Unit]
Description=Kite Trading Application
After=network.target postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable kite-app
    
    print_status "Systemd service created (not started yet)"
}

# Setup Nginx
setup_nginx() {
    print_status "Setting up Nginx configuration..."
    
    sudo tee /etc/nginx/sites-available/kite-app > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    location /static {
        alias $APP_DIR/app/views/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/kite-app /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    
    print_status "Nginx configuration completed"
}

# Create environment file template
create_env_template() {
    print_status "Creating environment file template..."
    
    sudo -u $APP_USER tee $APP_DIR/.env.template > /dev/null << EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your_secret_key_here

# Database Configuration
DATABASE_URL=postgresql://$DB_USER:your_db_password@localhost/$DB_NAME

# Kite Connect API Configuration
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret

# Optional: Redis for caching (if using)
# REDIS_URL=redis://localhost:6379/0
EOF

    print_warning "Please update $APP_DIR/.env with your actual configuration values"
}

# Setup log rotation
setup_logrotate() {
    print_status "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/kite-app > /dev/null << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
}
EOF

    print_status "Log rotation configured"
}

# Setup firewall
setup_firewall() {
    print_status "Configuring firewall..."
    
    # Check if ufw is available
    if command_exists ufw; then
        sudo ufw --force enable
        sudo ufw allow ssh
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        print_status "Firewall configured (SSH, HTTP, HTTPS allowed)"
    else
        print_warning "UFW not available, please configure firewall manually"
    fi
}

# Create helper scripts
create_scripts() {
    print_status "Creating helper scripts..."
    
    # Create scripts directory
    sudo -u $APP_USER mkdir -p $APP_DIR/scripts
    
    # Database backup script
    sudo -u $APP_USER tee $APP_DIR/scripts/backup_db.sh > /dev/null << EOF
#!/bin/bash
BACKUP_DIR="$APP_DIR/backups"
mkdir -p \$BACKUP_DIR

pg_dump -h localhost -U $DB_USER $DB_NAME > \$BACKUP_DIR/${DB_NAME}_\$(date +%Y%m%d_%H%M%S).sql

# Keep only last 7 days
find \$BACKUP_DIR -name "${DB_NAME}_*.sql" -mtime +7 -delete

echo "\$(date): Database backup completed"
EOF

    # Health check script
    sudo -u $APP_USER tee $APP_DIR/scripts/health_check.sh > /dev/null << EOF
#!/bin/bash
APP_URL="http://localhost:5000"
LOG_FILE="$APP_DIR/logs/health_check.log"

echo "\$(date): Checking application health..." >> \$LOG_FILE

if curl -f \$APP_URL > /dev/null 2>&1; then
    echo "\$(date): Application is healthy" >> \$LOG_FILE
else
    echo "\$(date): Application is DOWN - restarting" >> \$LOG_FILE
    sudo systemctl restart kite-app
fi
EOF

    # Make scripts executable
    sudo -u $APP_USER chmod +x $APP_DIR/scripts/*.sh
    
    print_status "Helper scripts created"
}

# Print final instructions
print_final_instructions() {
    echo ""
    echo "🎉 Basic setup completed!"
    echo "======================="
    echo ""
    echo "Next steps to complete the migration:"
    echo ""
    echo "1. Transfer your application code:"
    echo "   - Copy your kite_app files to: $APP_DIR"
    echo "   - Or clone from git: cd $APP_DIR && git clone <your-repo> ."
    echo ""
    echo "2. Update configuration:"
    echo "   - Edit: $APP_DIR/.env with your actual values"
    echo "   - Update: $APP_DIR/config/config.py if needed"
    echo ""
    echo "3. Restore database:"
    echo "   - psql -h localhost -U $DB_USER -d $DB_NAME < your_backup.sql"
    echo ""
    echo "4. Install Python dependencies:"
    echo "   - cd $APP_DIR && sudo -u $APP_USER bash -c 'source venv/bin/activate && pip install -r requirements.txt'"
    echo ""
    echo "5. Run database migrations:"
    echo "   - cd $APP_DIR && sudo -u $APP_USER bash -c 'source venv/bin/activate && export FLASK_APP=run.py && flask db upgrade'"
    echo ""
    echo "6. Start the application:"
    echo "   - sudo systemctl start kite-app"
    echo "   - sudo systemctl status kite-app"
    echo ""
    echo "7. Setup cron jobs for Strategy 1:"
    echo "   - sudo -u $APP_USER crontab -e"
    echo "   - Add the cron entries from the documentation"
    echo ""
    echo "8. Test the application:"
    echo "   - Visit: http://your-server-ip/"
    echo "   - Check: http://your-server-ip/strategies/"
    echo ""
    echo "For detailed instructions, see: $APP_DIR/docs/MIGRATION_GUIDE.md"
}

# Main execution
main() {
    print_status "Starting automated setup for Kite App migration..."
    
    # Prompt for confirmation
    echo ""
    read -p "This will install packages and create users. Continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Setup cancelled by user"
        exit 0
    fi
    
    # Run setup functions
    update_system
    setup_database
    setup_user
    setup_python
    install_dependencies
    setup_service
    setup_nginx
    create_env_template
    setup_logrotate
    setup_firewall
    create_scripts
    
    print_final_instructions
}

# Run main function
main "$@"
