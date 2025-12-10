#!/bin/bash

# Quick Start Script for Kite Trading Application
# Run this after uploading files to Ubuntu server

set -e

echo "🚀 Kite Trading Application - Quick Start"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the application directory."
    exit 1
fi

# Make scripts executable
echo "📋 Setting file permissions..."
chmod +x deploy.sh manage.sh preflight-check.sh docker/entrypoint.sh

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p storage/logs storage/tokens logs/nginx logs/redis docker/ssl/www

# Run preflight check
echo "🔍 Running pre-deployment check..."
./preflight-check.sh

echo ""
echo "✅ Quick setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Configure environment: nano .env"
echo "2. Run deployment: ./deploy.sh"
echo "3. Test application: ./manage.sh status"
echo ""
echo "🌐 Your app will be available at: https://newai.vijayanandpremnath.cloud"
