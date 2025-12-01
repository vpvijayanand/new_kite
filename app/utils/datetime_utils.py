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
