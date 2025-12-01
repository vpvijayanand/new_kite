from datetime import datetime, timezone, timedelta

def utc_to_ist(utc_datetime):
    """Convert UTC datetime to IST (Indian Standard Time)"""
    if utc_datetime is None:
        return None
    
    # If the datetime is naive (no timezone), assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    # IST is UTC+5:30
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return utc_datetime.astimezone(ist_timezone)

def format_ist_time(utc_datetime, format_str='%Y-%m-%d %H:%M:%S'):
    """Format UTC datetime as IST string"""
    if utc_datetime is None:
        return "N/A"
    
    ist_time = utc_to_ist(utc_datetime)
    return ist_time.strftime(format_str) + " IST"

def format_ist_time_only(utc_datetime):
    """Format UTC datetime as IST time only (HH:MM)"""
    if utc_datetime is None:
        return "N/A"
    
    ist_time = utc_to_ist(utc_datetime)
    return ist_time.strftime('%H:%M')


def is_market_hours(check_datetime=None):
    """
    Check if the given datetime (or current time) is within market hours.
    Market hours: 9:00 AM IST to 3:45 PM IST (15:45)
    
    Args:
        check_datetime: datetime object to check (UTC or IST). If None, uses current time.
    
    Returns:
        bool: True if within market hours, False otherwise
    """
    if check_datetime is None:
        check_datetime = datetime.utcnow()
    
    # Convert to IST if it's a UTC datetime
    if check_datetime.tzinfo is None:
        # Assume UTC if no timezone
        check_datetime = check_datetime.replace(tzinfo=timezone.utc)
    
    # Convert to IST
    ist_time = utc_to_ist(check_datetime)
    
    # Market hours: 9:00 AM to 3:45 PM IST (Monday to Friday)
    market_start_hour = 9
    market_start_minute = 0
    market_end_hour = 15
    market_end_minute = 45
    
    # Check if it's a weekday (0=Monday, 6=Sunday)
    if ist_time.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    # Create market start and end times for today
    market_start = ist_time.replace(hour=market_start_hour, minute=market_start_minute, second=0, microsecond=0)
    market_end = ist_time.replace(hour=market_end_hour, minute=market_end_minute, second=0, microsecond=0)
    
    # Check if current time is within market hours
    return market_start <= ist_time <= market_end


def get_next_market_open():
    """
    Get the next market opening time in IST
    
    Returns:
        datetime: Next market opening datetime in IST timezone
    """
    now_ist = utc_to_ist(datetime.utcnow())
    
    # Market opens at 9:00 AM IST
    market_open_time = now_ist.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # If market hasn't opened today, return today's opening
    if now_ist < market_open_time and now_ist.weekday() < 5:
        return market_open_time
    
    # Otherwise, find next weekday
    days_to_add = 1
    next_day = now_ist + timedelta(days=days_to_add)
    
    # Skip weekends
    while next_day.weekday() >= 5:
        days_to_add += 1
        next_day = now_ist + timedelta(days=days_to_add)
    
    return next_day.replace(hour=9, minute=0, second=0, microsecond=0)
