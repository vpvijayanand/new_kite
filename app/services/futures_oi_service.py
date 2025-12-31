from app.models.futures_oi_data import FuturesOIData
from app.services.datetime_filter_service import DateTimeFilterService
from app.utils.datetime_utils import format_ist_time_only
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
            from datetime import datetime
            import pytz
            
            # Parse date strings
            if isinstance(start_date, str):
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date_obj = start_date
            
            if isinstance(end_date, str):
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date_obj = end_date
                
            # Parse time strings  
            if start_time:
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            else:
                start_time_obj = datetime.strptime('09:15', '%H:%M').time()
                
            if end_time:
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            else:
                end_time_obj = datetime.strptime('15:30', '%H:%M').time()
            
            # For date filtering, use market hours to avoid previous day data
            # If time range spans full day (00:00-23:59), use market hours instead
            if (start_time_obj.hour == 0 and start_time_obj.minute == 0 and 
                end_time_obj.hour == 23 and end_time_obj.minute == 59):
                start_time_obj = datetime.strptime('09:15', '%H:%M').time()
                end_time_obj = datetime.strptime('15:30', '%H:%M').time()
            
            # Combine date and time
            start_datetime = datetime.combine(start_date_obj, start_time_obj)
            end_datetime = datetime.combine(end_date_obj, end_time_obj)
            
            # Convert to UTC (assuming IST input)
            ist_tz = pytz.timezone('Asia/Kolkata')
            start_datetime_utc = ist_tz.localize(start_datetime).astimezone(pytz.UTC)
            end_datetime_utc = ist_tz.localize(end_datetime).astimezone(pytz.UTC)
            
            # Convert to naive UTC for database comparison (database stores naive UTC timestamps)
            start_datetime_naive = start_datetime_utc.replace(tzinfo=None)
            end_datetime_naive = end_datetime_utc.replace(tzinfo=None)
            
            print(f"DEBUG: Getting futures OI data for {underlying} from {start_datetime_naive} to {end_datetime_naive} UTC")
            
            # Query futures OI data
            query = db.session.query(FuturesOIData).filter(
                and_(
                    FuturesOIData.underlying == underlying,
                    FuturesOIData.timestamp >= start_datetime_naive,
                    FuturesOIData.timestamp <= end_datetime_naive
                )
            ).order_by(FuturesOIData.timestamp.desc())
            
            futures_data = query.all()
            
            # If no data exists, return empty list (live data only)
            if not futures_data:
                print(f"DEBUG: No futures data found for {underlying}. Live data will be collected during market hours.")
                return []
            
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
                'time': format_ist_time_only(record.timestamp),
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
    
    # Sample data creation removed - using live data only
    
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
