#!/bin/bash

# Kite App Management Script
# Usage: ./manage.sh [start|stop|restart|logs|status|update|backup]

APP_DIR="/var/www/new_aitrader"
BACKUP_DIR="/var/backups/kite_app"

cd $APP_DIR

case "$1" in
    start)
        echo "🚀 Starting Kite Trading Application..."
        docker-compose up -d
        sleep 10
        docker-compose ps
        ;;
    
    stop)
        echo "🛑 Stopping Kite Trading Application..."
        docker-compose down
        ;;
    
    restart)
        echo "🔄 Restarting Kite Trading Application..."
        docker-compose down
        docker-compose up -d
        sleep 10
        docker-compose ps
        ;;
    
    logs)
        echo "📝 Showing application logs..."
        if [ -n "$2" ]; then
            docker-compose logs -f "$2"
        else
            docker-compose logs -f
        fi
        ;;
    
    status)
        echo "📊 Application Status:"
        docker-compose ps
        echo ""
        echo "🌐 Health Check:"
        curl -s https://newai.vijayanandpremnath.cloud/health | python3 -m json.tool || echo "Health check failed"
        ;;
    
    update)
        echo "🔄 Updating application..."
        git pull origin main
        docker-compose build --no-cache
        docker-compose down
        docker-compose up -d
        ;;
    
    backup)
        echo "💾 Creating backup..."
        mkdir -p $BACKUP_DIR
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        
        # Backup database
        cp storage/kite_app.db "$BACKUP_DIR/kite_app_${TIMESTAMP}.db"
        
        # Backup logs
        tar -czf "$BACKUP_DIR/logs_${TIMESTAMP}.tar.gz" logs/
        
        # Backup configuration
        tar -czf "$BACKUP_DIR/config_${TIMESTAMP}.tar.gz" .env docker/
        
        echo "✅ Backup created at $BACKUP_DIR/"
        ls -la $BACKUP_DIR/
        ;;
    
    clean)
        echo "🧹 Cleaning up Docker resources..."
        docker system prune -f
        docker volume prune -f
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|update|backup|clean}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the application"
        echo "  stop     - Stop the application"
        echo "  restart  - Restart the application"
        echo "  logs     - Show logs (optionally specify service: logs nginx)"
        echo "  status   - Show application status and health"
        echo "  update   - Update application from git and rebuild"
        echo "  backup   - Create backup of database and logs"
        echo "  clean    - Clean up Docker resources"
        exit 1
        ;;
esac
