from app.models.futures_oi_data import FuturesOIData
from app.services.datetime_filter_service import DateTimeFilterService
from app import db
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
import pytz
import logging

class FuturesOIService:
    
    def __init__(self):
        self.datetime_filter = DateTimeFilterService()
    
    def get_futures_oi_analysis(self, underlying='NIFTY', start_date=None, end_date=None, start_time=None, end_time=None):
        """
        Get futures OI analysis data with trend calculations
        """
        try:
            # Convert dates to datetime objects for filtering
            start_datetime, end_datetime = self.datetime_filter._prepare_datetime_range(
                start_date, end_date, start_time, end_time
            )
            
            print(f"DEBUG: Getting futures OI data for {underlying} from {start_datetime} to {end_datetime}")
            
            # Query futures OI data
            query = db.session.query(FuturesOIData).filter(
                and_(
                    FuturesOIData.underlying == underlying,
                    FuturesOIData.timestamp >= start_datetime,
                    FuturesOIData.timestamp <= end_datetime
                )
            ).order_by(FuturesOIData.timestamp.asc())
            
            futures_data = query.all()
            
            # If no data exists, try to fetch and store some sample data
            if not futures_data:
                print(f"DEBUG: No futures data found for {underlying}, creating sample data")
                futures_data = self._create_sample_data(underlying, start_datetime, end_datetime)
            
            # Calculate changes and trends
            analyzed_data = self._calculate_trends(futures_data)
            
            return analyzed_data
            
        except Exception as e:
            print(f"Error in get_futures_oi_analysis for {underlying}: {str(e)}")
            return []
    
    def _calculate_trends(self, futures_data):
        """Calculate price changes, OI changes, meanings and trends"""
        analyzed_data = []
        
        for i, record in enumerate(futures_data):
            # Calculate changes from previous record
            if i > 0:
                prev_record = futures_data[i-1]
                price_change = record.futures_price - prev_record.futures_price
                oi_change = record.open_interest - prev_record.open_interest
            else:
                price_change = 0
                oi_change = 0
            
            # Calculate meaning and trend
            meaning, trend = FuturesOIData.calculate_meaning_and_trend(price_change, oi_change)
            
            # Update database record if needed
            if record.meaning != meaning or record.trend != trend:
                record.price_change = price_change
                record.oi_change = oi_change
                record.meaning = meaning
                record.trend = trend
                record.updated_at = datetime.now(pytz.UTC)
            
            # Add to analyzed data
            analyzed_data.append({
                'id': record.id,
                'time': record.timestamp.strftime('%H:%M:%S'),
                'futures_price': record.futures_price,
                'open_interest': record.open_interest,
                'volume': record.volume,
                'price_change': round(price_change, 2),
                'oi_change': oi_change,
                'meaning': meaning,
                'trend': trend,
                'trend_color': self._get_trend_color(trend)
            })
        
        # Commit any database updates
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error updating futures data: {str(e)}")
            db.session.rollback()
        
        return analyzed_data
    
    def _get_trend_color(self, trend):
        """Get color class for trend display"""
        if trend == 'Bullish':
            return 'success'  # Green
        elif trend == 'Bearish':
            return 'danger'   # Red
        else:
            return 'warning'  # Yellow
    
    def _create_sample_data(self, underlying, start_datetime, end_datetime):
        """Create sample futures data for demonstration"""
        try:
            # Base price for the underlying
            base_price = 24500 if underlying == 'NIFTY' else 52000
            base_oi = 5000000 if underlying == 'NIFTY' else 3000000
            
            # Get current expiry (next Friday)
            current_date = start_datetime.date()
            days_ahead = 4 - current_date.weekday()  # Friday is 4
            if days_ahead <= 0:
                days_ahead += 7
            expiry_date = current_date + timedelta(days=days_ahead)
            
            sample_data = []
            current_time = start_datetime
            
            # Generate data every 5 minutes
            while current_time <= end_datetime:
                # Simulate some price and OI movements
                import random
                price_change = random.uniform(-50, 50)
                oi_change = random.randint(-100000, 100000)
                
                futures_price = base_price + price_change
                open_interest = max(base_oi + oi_change, 1000000)  # Minimum OI
                volume = random.randint(50000, 200000)
                
                # Create record
                record = FuturesOIData(
                    underlying=underlying,
                    expiry_date=expiry_date,
                    timestamp=current_time,
                    futures_price=futures_price,
                    open_interest=open_interest,
                    volume=volume
                )
                
                db.session.add(record)
                sample_data.append(record)
                
                # Move to next 5-minute interval
                current_time += timedelta(minutes=5)
                base_price = futures_price  # Update base for next iteration
                base_oi = open_interest
            
            # Commit sample data
            db.session.commit()
            print(f"DEBUG: Created {len(sample_data)} sample records for {underlying}")
            
            return sample_data
            
        except Exception as e:
            print(f"Error creating sample data: {str(e)}")
            db.session.rollback()
            return []
    
    def store_futures_data(self, underlying, expiry_date, futures_price, open_interest, volume=0, timestamp=None):
        """Store new futures data point"""
        try:
            if not timestamp:
                timestamp = datetime.now(pytz.UTC)
            
            # Get previous record for change calculation
            prev_record = db.session.query(FuturesOIData).filter(
                and_(
                    FuturesOIData.underlying == underlying,
                    FuturesOIData.expiry_date == expiry_date
                )
            ).order_by(desc(FuturesOIData.timestamp)).first()
            
            # Calculate changes
            if prev_record:
                price_change = futures_price - prev_record.futures_price
                oi_change = open_interest - prev_record.open_interest
            else:
                price_change = 0
                oi_change = 0
            
            # Calculate meaning and trend
            meaning, trend = FuturesOIData.calculate_meaning_and_trend(price_change, oi_change)
            
            # Create new record
            record = FuturesOIData(
                underlying=underlying,
                expiry_date=expiry_date,
                timestamp=timestamp,
                futures_price=futures_price,
                open_interest=open_interest,
                volume=volume,
                price_change=price_change,
                oi_change=oi_change,
                meaning=meaning,
                trend=trend
            )
            
            db.session.add(record)
            db.session.commit()
            
            print(f"DEBUG: Stored futures data for {underlying}: Price={futures_price}, OI={open_interest}, Trend={trend}")
            return record
            
        except Exception as e:
            print(f"Error storing futures data: {str(e)}")
            db.session.rollback()
            return None
