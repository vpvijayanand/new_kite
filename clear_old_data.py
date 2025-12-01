#!/usr/bin/env python3

from app import create_app, db
from app.models.nifty_price import NiftyPrice
from app.models.banknifty_price import BankNiftyPrice, OptionChainData, MarketTrend

def clear_old_data():
    """Clear all old data from database tables"""
    app = create_app()
    with app.app_context():
        print('🗑️  Starting database cleanup...')
        
        try:
            # Clear option chain data completely
            deleted_options = OptionChainData.query.delete()
            print(f'✅ Deleted {deleted_options} option chain records')
            
            # Clear market trends completely
            deleted_trends = MarketTrend.query.delete()
            print(f'✅ Deleted {deleted_trends} market trend records')
            
            # Clear ALL Nifty price data for fresh start
            deleted_nifty = NiftyPrice.query.delete()
            print(f'✅ Deleted {deleted_nifty} Nifty price records')
            
            # Clear ALL BankNifty price data for fresh start
            deleted_banknifty = BankNiftyPrice.query.delete()
            print(f'✅ Deleted {deleted_banknifty} BankNifty price records')
            
            # Commit all changes
            db.session.commit()
            print('🎉 Database cleared successfully! Ready for fresh API data.')
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f'❌ Error clearing database: {str(e)}')
            return False

if __name__ == "__main__":
    clear_old_data()
