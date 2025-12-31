# 🚀 NIFTY Signals Production Deployment Guide

## 📋 **Prerequisites**
- Ubuntu server with Nginx + Gunicorn
- Flask app already running
- Database (PostgreSQL/MySQL) configured
- SSH access to production server

---

## 🛠️ **Step 1: Upload Files to Production Server**

### **Method A: Using SCP/SFTP**
```bash
# Upload new files to your production server
scp -r app/models/nifty_signal.py user@your-server:/path/to/your/app/app/models/
scp -r app/services/nifty_signal_service.py user@your-server:/path/to/your/app/app/services/
scp -r app/services/signal_scheduler.py user@your-server:/path/to/your/app/app/services/
scp -r app/controllers/signal_controller.py user@your-server:/path/to/your/app/app/controllers/
scp -r app/views/templates/signals_dashboard.html user@your-server:/path/to/your/app/app/views/templates/
scp -r app/views/templates/nifty_signals_chart.html user@your-server:/path/to/your/app/app/views/templates/
scp setup_nifty_signals.py user@your-server:/path/to/your/app/
```

### **Method B: Using Git (Recommended)**
```bash
# On your production server
cd /path/to/your/app
git pull origin main  # or your branch name
```

---

## 🔧 **Step 2: SSH to Production Server and Setup**

```bash
# SSH to your production server
ssh user@your-server

# Navigate to your app directory
cd /path/to/your/app

# Activate virtual environment (if using)
source venv/bin/activate  # or source env/bin/activate

# Install required Python packages
pip install pandas apscheduler
```

---

## 🗄️ **Step 3: Database Setup**

```bash
# Run the setup script to create tables and initial signals
python setup_nifty_signals.py
```

**Expected Output:**
```
🚀 Starting NIFTY Trading Signals Production Setup...
============================================================
📊 Creating database tables...
✅ Database tables created successfully
🔍 Checking NIFTY price data availability...
📈 Found XXXX NIFTY price records
🎯 Generating initial trading signals...
✅ Successfully generated XX signals
📈 Buy signals: X
📉 Sell signals: X
✅ Validating signal generation...
📊 Total signals in database: XX
🎉 Production setup completed successfully!
```

---

## ⚙️ **Step 4: Update Flask App Initialization**

Make sure your main app file (`app/__init__.py`) includes signal blueprint registration:

```python
# Verify this exists in app/__init__.py
from app.controllers.signal_controller import signal_bp
app.register_blueprint(signal_bp, url_prefix='/signals')
```

---

## 🔄 **Step 5: Restart Production Services**

### **Restart Gunicorn**
```bash
# Find Gunicorn process
sudo ps aux | grep gunicorn

# Method A: Using systemctl (if configured as service)
sudo systemctl restart your-flask-app.service

# Method B: Kill and restart manually
sudo pkill -f gunicorn
cd /path/to/your/app
gunicorn --bind 0.0.0.0:5000 run:app --daemon

# Method C: Using supervisor (if configured)
sudo supervisorctl restart your-flask-app
```

### **Restart Nginx (if needed)**
```bash
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

---

## 🧪 **Step 6: Test the Deployment**

### **Check if services are running**
```bash
# Check Gunicorn
sudo ps aux | grep gunicorn

# Check if app is responding
curl -I http://localhost:5000/signals/

# Check logs
tail -f /path/to/your/logs/app.log
```

### **Test the endpoints**
```bash
# Test signals dashboard
curl http://your-domain.com/signals/

# Test API endpoint
curl http://your-domain.com/api/signals

# Test chart page
curl http://your-domain.com/signals/chart
```

---

## 📊 **Step 7: Verify Background Scheduler**

Check if the signal generation scheduler is running:

```bash
# Check app logs for scheduler messages
tail -f /path/to/your/logs/app.log | grep -i "signal\|scheduler"
```

**Expected log messages:**
```
✅ Signal generation scheduler initialized successfully
📊 Real-time signal detection started for market hours
🎯 Generated signal: BUY at ₹26500.50 (Confidence: 85%)
```

---

## 🌐 **Step 8: Update Nginx Configuration (if needed)**

If you need to add specific routing for signals:

```nginx
# Add to your existing Nginx config
location /signals/ {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

location /api/signals {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

---

## 📱 **Step 9: Access Your Dashboard**

Once deployed, access your NIFTY signals system:

- **📊 Main Dashboard**: `https://your-domain.com/signals/`
- **📈 Chart View**: `https://your-domain.com/signals/chart`
- **🔗 API Data**: `https://your-domain.com/api/signals`

---

## 🔍 **Troubleshooting**

### **If setup script fails:**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Check database connection
python -c "from app import create_app; app = create_app(); print('DB connected')"

# Check required packages
pip list | grep -E "pandas|apscheduler|flask"
```

### **If signals don't generate:**
```bash
# Test signal generation manually
python -c "
from app import create_app
from app.services.nifty_signal_service import NiftySignalGenerator
app = create_app()
with app.app_context():
    gen = NiftySignalGenerator()
    result = gen.generate_current_signal()
    print(result)
"
```

### **If scheduler doesn't start:**
```bash
# Check for scheduler errors in logs
grep -i "scheduler\|error" /path/to/your/logs/app.log

# Restart with verbose logging
export FLASK_DEBUG=1
python run.py
```

---

## ✅ **Production Deployment Checklist**

- [ ] ✅ Files uploaded to production server
- [ ] ✅ Virtual environment activated
- [ ] ✅ Required packages installed (`pandas`, `apscheduler`)
- [ ] ✅ Database setup script executed successfully
- [ ] ✅ Flask app includes signal blueprint
- [ ] ✅ Gunicorn restarted
- [ ] ✅ Nginx configuration updated (if needed)
- [ ] ✅ Services are running correctly
- [ ] ✅ Dashboard accessible at `/signals/`
- [ ] ✅ Chart view accessible at `/signals/chart`
- [ ] ✅ API endpoint responsive at `/api/signals`
- [ ] ✅ Background scheduler generating signals
- [ ] ✅ Logs showing signal generation during market hours

---

## 🎯 **Expected Results After Deployment**

1. **Real-time signal generation** every minute during market hours (9:15 AM - 3:30 PM IST)
2. **Dashboard updates** with latest BUY/SELL signals
3. **Chart visualization** with candlesticks and signal markers
4. **API endpoints** returning JSON data for integration
5. **Background processing** running automatically

Your NIFTY trading signals system is now ready for production! 🚀📈
