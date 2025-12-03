#!/usr/bin/env python3
"""
Strategy 1 Standalone Execution Script
This script can be run independently or via cron job to execute Strategy 1 monitoring
"""

import os
import sys
import logging
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.strategy_service import StrategyService

def setup_logging():
    """Setup logging for the script"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, 'strategy1_cron.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def main():
    """Main execution function"""
    logger = setup_logging()
    
    try:
        logger.info("Starting Strategy 1 execution")
        
        # Create Flask app with proper environment
        app = create_app(os.getenv('FLASK_ENV', 'production'))
        
        with app.app_context():
            # Initialize strategy service
            strategy_service = StrategyService()
            
            # Check if it's market hours
            if not strategy_service.is_market_hours():
                logger.info("Outside market hours, skipping execution")
                return
            
            # Execute strategy
            result = strategy_service.execute_strategy_1()
            
            if result.get('success'):
                logger.info(f"Strategy execution successful: {result.get('message', 'Unknown')}")
                logger.info(f"Action taken: {result.get('action', 'NONE')}")
                
                if result.get('trade_id'):
                    logger.info(f"Trade ID: {result.get('trade_id')}")
                    
            else:
                logger.error(f"Strategy execution failed: {result.get('message', 'Unknown error')}")
                
    except Exception as e:
        logger.error(f"Error in strategy execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
