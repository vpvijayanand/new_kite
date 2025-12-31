from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.nifty_signal_service import NiftySignalGenerator
from app import create_app
import logging
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalScheduler:
    """
    Background scheduler for automatic signal generation
    Runs during market hours to detect buy/sell signals
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.app = None
        self.signal_generator = NiftySignalGenerator()
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self.start_scheduler()
        
        # Ensure graceful shutdown
        atexit.register(lambda: self.scheduler.shutdown())
    
    def generate_signals_job(self):
        """Job to generate signals for latest data"""
        if not self.app:
            logger.error("Flask app not initialized")
            return
            
        with self.app.app_context():
            try:
                logger.info("🔄 Running scheduled signal generation...")
                
                # Generate signals for latest data point only
                new_signal = self.signal_generator.generate_signals_for_latest_data()
                
                if new_signal:
                    logger.info(f"🔥 New {new_signal.signal_type} signal detected at ₹{new_signal.price:.2f}")
                    logger.info(f"   Confidence: {new_signal.confidence_score:.1f}%")
                    logger.info(f"   MA Difference: {new_signal.ma_difference:.2f}")
                else:
                    logger.info("📊 No new signals detected")
                
            except Exception as e:
                logger.error(f"❌ Error in signal generation job: {e}")
    
    def bulk_signal_generation_job(self):
        """Job to run bulk signal generation (runs less frequently)"""
        if not self.app:
            return
            
        with self.app.app_context():
            try:
                logger.info("🔄 Running bulk signal generation...")
                
                # Generate signals for last 6 hours of data
                signals = self.signal_generator.generate_signals(lookback_hours=6)
                
                if signals:
                    logger.info(f"✅ Bulk generation completed: {len(signals)} signals")
                else:
                    logger.info("📊 No new signals in bulk generation")
                
            except Exception as e:
                logger.error(f"❌ Error in bulk signal generation: {e}")
    
    def start_scheduler(self):
        """Start the background scheduler with market hours timing"""
        try:
            # Real-time signal detection every minute during market hours (9:15 AM - 3:30 PM)
            self.scheduler.add_job(
                func=self.generate_signals_job,
                trigger=CronTrigger(
                    day_of_week='mon-fri',  # Monday to Friday
                    hour='9-15',            # 9 AM to 3 PM
                    minute='*',             # Every minute
                    timezone='Asia/Kolkata'
                ),
                id='realtime_signal_generation',
                name='Real-time Signal Generation',
                replace_existing=True,
                max_instances=1
            )
            
            # Bulk signal generation every 30 minutes during market hours
            self.scheduler.add_job(
                func=self.bulk_signal_generation_job,
                trigger=CronTrigger(
                    day_of_week='mon-fri',
                    hour='9-15',
                    minute='*/30',          # Every 30 minutes
                    timezone='Asia/Kolkata'
                ),
                id='bulk_signal_generation',
                name='Bulk Signal Generation',
                replace_existing=True,
                max_instances=1
            )
            
            # Pre-market analysis (9:00 AM)
            self.scheduler.add_job(
                func=self.bulk_signal_generation_job,
                trigger=CronTrigger(
                    day_of_week='mon-fri',
                    hour=9,
                    minute=0,
                    timezone='Asia/Kolkata'
                ),
                id='premarket_analysis',
                name='Pre-market Signal Analysis',
                replace_existing=True
            )
            
            # Post-market analysis (4:00 PM)
            self.scheduler.add_job(
                func=self.bulk_signal_generation_job,
                trigger=CronTrigger(
                    day_of_week='mon-fri',
                    hour=16,
                    minute=0,
                    timezone='Asia/Kolkata'
                ),
                id='postmarket_analysis',
                name='Post-market Signal Analysis',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("✅ Signal generation scheduler started")
            logger.info("📅 Scheduled jobs:")
            for job in self.scheduler.get_jobs():
                logger.info(f"   - {job.name}: {job.next_run_time}")
            
        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {e}")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Signal generation scheduler stopped")

# Global scheduler instance
signal_scheduler = SignalScheduler()

def init_signal_scheduler(app):
    """Initialize signal scheduler with Flask app"""
    signal_scheduler.init_app(app)
