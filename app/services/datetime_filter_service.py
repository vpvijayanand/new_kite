"""
Date/Time Filter Utility Service
Provides standardized date/time filtering across all pages
"""

from datetime import datetime, date, timedelta
import pytz

class DateTimeFilterService:
    """Service for handling date/time filters across the application"""
    
    def __init__(self):
        self.ist_tz = pytz.timezone('Asia/Kolkata')
    
    def get_default_date_range(self):
        """Get default date range (today)"""
        today = date.today()
        return {
            'start_date': today,
            'end_date': today,
            'start_datetime': datetime.combine(today, datetime.min.time()),
            'end_datetime': datetime.combine(today, datetime.max.time())
        }
    
    def parse_date_params(self, request_args, default_today=True):
        """Parse date parameters from request"""
        try:
            # Get date parameters
            start_date_str = request_args.get('start_date')
            end_date_str = request_args.get('end_date')
            
            # Get time parameters (optional)
            start_time_str = request_args.get('start_time', '09:00')
            end_time_str = request_args.get('end_time', '15:30')
            
            # Parse dates or use defaults
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            else:
                start_date = date.today() if default_today else None
                
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                end_date = start_date if start_date else date.today()
            
            # Parse times
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Return tuple format for easy unpacking
            return start_date, end_date, start_time, end_time
            
        except (ValueError, TypeError) as e:
            print(f"Error parsing date parameters: {e}")
            # Return tuple format for consistency
            today = date.today()
            return today, today, datetime.strptime('09:00', '%H:%M').time(), datetime.strptime('15:30', '%H:%M').time()
    
    def format_date_for_display(self, dt):
        """Format date for display in templates"""
        if isinstance(dt, str):
            return dt
        elif isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d')
        elif isinstance(dt, date):
            return dt.strftime('%Y-%m-%d')
        return str(dt)
    
    def format_time_for_display(self, time_str):
        """Format time for display in templates"""
        return time_str if time_str else '09:00'
    
    def get_market_hours_filter(self, target_date=None):
        """Get market hours filter for a specific date"""
        if target_date is None:
            target_date = date.today()
            
        # Market hours: 9:00 AM to 3:30 PM IST
        start_datetime = datetime.combine(target_date, datetime.strptime('09:00', '%H:%M').time())
        end_datetime = datetime.combine(target_date, datetime.strptime('15:30', '%H:%M').time())
        
        return {
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'start_date': target_date,
            'end_date': target_date
        }
    
    def is_within_date_range(self, timestamp, start_datetime, end_datetime):
        """Check if timestamp is within the specified date range"""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
        return start_datetime <= timestamp <= end_datetime
    
    def get_quick_date_options(self):
        """Get quick date selection options"""
        today = date.today()
        return {
            'today': {
                'label': 'Today',
                'start_date': today,
                'end_date': today
            },
            'yesterday': {
                'label': 'Yesterday', 
                'start_date': today - timedelta(days=1),
                'end_date': today - timedelta(days=1)
            },
            'last_3_days': {
                'label': 'Last 3 Days',
                'start_date': today - timedelta(days=2),
                'end_date': today
            },
            'last_week': {
                'label': 'Last 7 Days',
                'start_date': today - timedelta(days=6),
                'end_date': today
            },
            'last_month': {
                'label': 'Last 30 Days',
                'start_date': today - timedelta(days=29),
                'end_date': today
            }
        }
    
    def apply_date_filter_to_query(self, query, model_timestamp_field, start_datetime, end_datetime):
        """Apply date filter to SQLAlchemy query"""
        return query.filter(
            model_timestamp_field >= start_datetime,
            model_timestamp_field <= end_datetime
        )
    
    def parse_date(self, date_str):
        """Parse date string to date object"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            # Try alternative formats
            for fmt in ['%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {date_str}")
    
    def parse_time(self, time_str):
        """Parse time string to time object"""
        if not time_str:
            return None
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            # Try alternative formats
            for fmt in ['%H:%M:%S', '%I:%M %p', '%I:%M:%S %p']:
                try:
                    return datetime.strptime(time_str, fmt).time()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse time: {time_str}")
    
    @staticmethod
    def get_today():
        """Get today's date"""
        return date.today()
    
    @staticmethod
    def get_target_date(start_date, end_date):
        """Get target date from start and end dates, preferring start_date"""
        if start_date:
            return start_date
        elif end_date:
            return end_date
        else:
            return date.today()
