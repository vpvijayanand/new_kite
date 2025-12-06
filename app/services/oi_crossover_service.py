from app import db
from app.models.banknifty_price import OptionChainData
from app.models.nifty_price import NiftyPrice
from app.models.banknifty_price import BankNiftyPrice
from datetime import datetime, timedelta, time, timezone
from sqlalchemy import func
import pytz

class OICrossoverService:
    """Service for OI Change Crossover analysis"""
    
    def __init__(self):
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        
    def get_oi_crossover_summary(self, start_date=None, end_date=None, start_time=None, end_time=None):
        """
        Get OI crossover summary with total PE change %, CE change % and difference %
        """
        try:
            # Convert dates to datetime objects for filtering
            start_datetime, end_datetime = self._prepare_datetime_range(
                start_date, end_date, start_time, end_time
            )
            
            print(f"DEBUG: Getting OI summary from {start_datetime} to {end_datetime}")
            
            # Get all OI data for the time range for both NIFTY and BANKNIFTY
            nifty_summary = self._calculate_oi_summary('NIFTY', start_datetime, end_datetime)
            banknifty_summary = self._calculate_oi_summary('BANKNIFTY', start_datetime, end_datetime)
            
            # Combine summaries
            total_pe_change_percent = (nifty_summary['pe_change_percent'] + banknifty_summary['pe_change_percent']) / 2
            total_ce_change_percent = (nifty_summary['ce_change_percent'] + banknifty_summary['ce_change_percent']) / 2
            total_difference_percent = total_ce_change_percent - total_pe_change_percent
            
            return {
                'total_pe_change_percent': round(total_pe_change_percent, 2),
                'total_ce_change_percent': round(total_ce_change_percent, 2), 
                'total_difference_percent': round(total_difference_percent, 2),
                'nifty_summary': nifty_summary,
                'banknifty_summary': banknifty_summary,
                'time_range': {
                    'start': start_datetime.isoformat() if start_datetime else None,
                    'end': end_datetime.isoformat() if end_datetime else None
                }
            }
            
        except Exception as e:
            print(f"Error in get_oi_crossover_summary: {str(e)}")
            return {
                'total_pe_change_percent': 0,
                'total_ce_change_percent': 0,
                'total_difference_percent': 0,
                'error': str(e)
            }
    
    def _calculate_oi_summary(self, underlying, start_datetime, end_datetime):
        """Calculate OI change summary for a specific underlying"""
        try:
            # Get OI data for the time range
            oi_data = OptionChainData.query.filter(
                OptionChainData.underlying == underlying,
                OptionChainData.timestamp >= start_datetime,
                OptionChainData.timestamp <= end_datetime
            ).order_by(OptionChainData.timestamp).all()
            
            if not oi_data:
                return {
                    'pe_change_percent': 0,
                    'ce_change_percent': 0,
                    'total_pe_oi': 0,
                    'total_ce_oi': 0,
                    'records_count': 0
                }
            
            print(f"DEBUG: Found {len(oi_data)} {underlying} OI records")
            
            # Calculate total OI changes
            total_pe_change = sum([record.pe_oi_change for record in oi_data if record.pe_oi_change])
            total_ce_change = sum([record.ce_oi_change for record in oi_data if record.ce_oi_change])
            
            # Calculate average total OI to compute percentage
            total_pe_oi = sum([record.pe_oi for record in oi_data if record.pe_oi]) / len(oi_data) if oi_data else 0
            total_ce_oi = sum([record.ce_oi for record in oi_data if record.ce_oi]) / len(oi_data) if oi_data else 0
            
            # Calculate percentage changes
            pe_change_percent = (total_pe_change / total_pe_oi * 100) if total_pe_oi > 0 else 0
            ce_change_percent = (total_ce_change / total_ce_oi * 100) if total_ce_oi > 0 else 0
            
            return {
                'pe_change_percent': round(pe_change_percent, 2),
                'ce_change_percent': round(ce_change_percent, 2),
                'total_pe_oi': total_pe_oi,
                'total_ce_oi': total_ce_oi,
                'total_pe_change': total_pe_change,
                'total_ce_change': total_ce_change,
                'records_count': len(oi_data)
            }
            
        except Exception as e:
            print(f"Error calculating OI summary for {underlying}: {str(e)}")
            return {
                'pe_change_percent': 0,
                'ce_change_percent': 0,
                'total_pe_oi': 0,
                'total_ce_oi': 0,
                'records_count': 0,
                'error': str(e)
            }
    
    def get_oi_crossover_chart_data(self, underlying='NIFTY', start_date=None, end_date=None, start_time=None, end_time=None):
        """
        Get time-series chart data for OI changes and index prices for both NIFTY and BANKNIFTY
        """
        try:
            # Convert dates to datetime objects for filtering
            start_datetime, end_datetime = self._prepare_datetime_range(
                start_date, end_date, start_time, end_time
            )
            
            print(f"DEBUG: Getting chart data for {underlying} (primary) from {start_datetime} to {end_datetime}")
            
            # Always get data for both underlyings
            nifty_data = self._get_single_underlying_chart_data('NIFTY', start_datetime, end_datetime)
            banknifty_data = self._get_single_underlying_chart_data('BANKNIFTY', start_datetime, end_datetime)
            
            # Use the selected underlying as primary
            if underlying == 'NIFTY':
                primary_data = nifty_data
                secondary_data = banknifty_data
                secondary_prefix = 'banknifty'
                nifty_prefix = 'nifty'
            else:
                primary_data = banknifty_data
                secondary_data = nifty_data
                secondary_prefix = 'nifty'
                nifty_prefix = 'nifty'
            
            # Build chart data with primary underlying as main datasets
            chart_data = primary_data.copy()
            
            # Add secondary underlying data with appropriate naming
            if underlying == 'NIFTY':
                # Primary is NIFTY, secondary is BankNifty
                chart_data['banknifty_pe_changes'] = secondary_data['pe_changes']
                chart_data['banknifty_ce_changes'] = secondary_data['ce_changes']
                chart_data['banknifty_prices'] = secondary_data['index_prices']
                # Also keep nifty data for when BankNifty is selected
                chart_data['nifty_pe_changes'] = primary_data['pe_changes']
                chart_data['nifty_ce_changes'] = primary_data['ce_changes']
            else:
                # Primary is BankNifty, secondary is NIFTY
                chart_data['nifty_pe_changes'] = secondary_data['pe_changes']
                chart_data['nifty_ce_changes'] = secondary_data['ce_changes']
                chart_data['nifty_prices'] = secondary_data['index_prices']
                # Also keep banknifty data
                chart_data['banknifty_pe_changes'] = primary_data['pe_changes']
                chart_data['banknifty_ce_changes'] = primary_data['ce_changes']
            
            return chart_data
            
        except Exception as e:
            print(f"Error in get_oi_crossover_chart_data for {underlying}: {str(e)}")
            return {
                'labels': [],
                'pe_changes': [],
                'ce_changes': [],
                'index_prices': [],
                'pe_change_percentages': [],
                'ce_change_percentages': [],
                'banknifty_pe_changes': [],
                'banknifty_ce_changes': [],
                'banknifty_prices': [],
                'error': str(e)
            }

    def _get_single_underlying_chart_data(self, underlying, start_datetime, end_datetime):
        """
        Get chart data for a single underlying
        """
        # Get OI data grouped by time intervals (5-minute intervals)
        timeline_data = db.session.query(
            func.date_trunc('minute', OptionChainData.timestamp).label('time_bucket'),
            func.sum(OptionChainData.ce_oi_change).label('total_ce_change'),
            func.sum(OptionChainData.pe_oi_change).label('total_pe_change'),
            func.avg(OptionChainData.ce_oi).label('avg_ce_oi'),
            func.avg(OptionChainData.pe_oi).label('avg_pe_oi')
        ).filter(
            OptionChainData.timestamp >= start_datetime,
            OptionChainData.timestamp <= end_datetime,
            OptionChainData.underlying == underlying
        ).group_by(
            func.date_trunc('minute', OptionChainData.timestamp)
        ).order_by(
            func.date_trunc('minute', OptionChainData.timestamp)
        ).all()
        
        # Get corresponding index prices
        if underlying == 'NIFTY':
            price_model = NiftyPrice
        else:
            price_model = BankNiftyPrice
        
        # Format data for chart
        chart_data = {
            'labels': [],
            'pe_changes': [],
            'ce_changes': [],
            'index_prices': [],
            'pe_change_percentages': [],
            'ce_change_percentages': []
        }
        
        cumulative_pe_change = 0
        cumulative_ce_change = 0
        
        for record in timeline_data:
            # Convert timestamp to IST and format for display
            ist_time = self._utc_to_ist(record.time_bucket)
            time_label = ist_time.strftime('%H:%M')
            
            # Calculate percentage changes
            pe_change_pct = (record.total_pe_change / record.avg_pe_oi * 100) if record.avg_pe_oi and record.avg_pe_oi > 0 else 0
            ce_change_pct = (record.total_ce_change / record.avg_ce_oi * 100) if record.avg_ce_oi and record.avg_ce_oi > 0 else 0
            
            # Calculate cumulative changes
            cumulative_pe_change += (record.total_pe_change or 0)
            cumulative_ce_change += (record.total_ce_change or 0)
            
            # Get corresponding index price (within 5 minutes of the OI timestamp)
            price_record = price_model.query.filter(
                func.abs(func.extract('epoch', price_model.timestamp) - func.extract('epoch', record.time_bucket)) < 300
            ).order_by(
                func.abs(func.extract('epoch', price_model.timestamp) - func.extract('epoch', record.time_bucket))
            ).first()
            
            index_price = price_record.price if price_record else (26000 if underlying == 'NIFTY' else 59000)
            
            chart_data['labels'].append(time_label)
            chart_data['pe_changes'].append(cumulative_pe_change)
            chart_data['ce_changes'].append(cumulative_ce_change)
            chart_data['pe_change_percentages'].append(round(pe_change_pct, 2))
            chart_data['ce_change_percentages'].append(round(ce_change_pct, 2))
            chart_data['index_prices'].append(float(index_price))
        
        return chart_data
    
    def _prepare_datetime_range(self, start_date, end_date, start_time, end_time):
        """Convert date/time parameters to UTC datetime objects for database queries"""
        try:
            # Use provided dates or default to today
            if not start_date:
                start_date = datetime.now().date()
            if not end_date:
                end_date = start_date
                
            # Use provided times or default to market hours
            if not start_time:
                start_time = time(9, 0)  # 9:00 AM
            if not end_time:
                end_time = time(15, 30)  # 3:30 PM
                
            # Create IST datetime objects
            start_datetime_ist = datetime.combine(start_date, start_time)
            end_datetime_ist = datetime.combine(end_date, end_time)
            
            # Add IST timezone info
            start_datetime_ist = self.ist_timezone.localize(start_datetime_ist)
            end_datetime_ist = self.ist_timezone.localize(end_datetime_ist)
            
            # Convert to UTC for database query
            start_datetime_utc = start_datetime_ist.astimezone(timezone.utc).replace(tzinfo=None)
            end_datetime_utc = end_datetime_ist.astimezone(timezone.utc).replace(tzinfo=None)
            
            return start_datetime_utc, end_datetime_utc
            
        except Exception as e:
            print(f"Error preparing datetime range: {str(e)}")
            # Fallback to today's market hours
            today = datetime.now().date()
            start_dt = self.ist_timezone.localize(datetime.combine(today, time(9, 0)))
            end_dt = self.ist_timezone.localize(datetime.combine(today, time(15, 30)))
            
            return (start_dt.astimezone(timezone.utc).replace(tzinfo=None),
                    end_dt.astimezone(timezone.utc).replace(tzinfo=None))
    
    def _utc_to_ist(self, utc_datetime):
        """Convert UTC datetime to IST"""
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
        return utc_datetime.astimezone(self.ist_timezone)
