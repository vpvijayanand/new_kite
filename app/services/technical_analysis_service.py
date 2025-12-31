import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from app import db
from app.models.nifty_price import NiftyPrice
import logging

class TechnicalAnalysisService:
    """Service for technical analysis calculations including MACD"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        return pd.Series(prices).ewm(span=period).mean()
    
    def calculate_macd(self, prices, fast_period=12, slow_period=26, signal_period=9):
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: List or Series of prices
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26) 
            signal_period: Signal line EMA period (default: 9)
            
        Returns:
            dict with macd_line, signal_line, histogram values
        """
        try:
            if len(prices) < slow_period:
                return {
                    'macd_line': 0,
                    'signal_line': 0,
                    'histogram': 0,
                    'signal': 'INSUFFICIENT_DATA'
                }
            
            # Convert to pandas Series if not already
            price_series = pd.Series(prices)
            
            # Calculate EMAs
            ema_fast = self.calculate_ema(price_series, fast_period)
            ema_slow = self.calculate_ema(price_series, slow_period)
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate Signal line (EMA of MACD line)
            signal_line = self.calculate_ema(macd_line, signal_period)
            
            # Calculate Histogram
            histogram = macd_line - signal_line
            
            # Get latest values
            latest_macd = float(macd_line.iloc[-1])
            latest_signal = float(signal_line.iloc[-1])
            latest_histogram = float(histogram.iloc[-1])
            
            # Determine signal
            signal = self.get_macd_signal(macd_line, signal_line, histogram)
            
            return {
                'macd_line': round(latest_macd, 2),
                'signal_line': round(latest_signal, 2),
                'histogram': round(latest_histogram, 2),
                'signal': signal,
                'strength': self.get_signal_strength(latest_histogram),
                'previous_macd': round(float(macd_line.iloc[-2]), 2) if len(macd_line) > 1 else latest_macd,
                'previous_signal': round(float(signal_line.iloc[-2]), 2) if len(signal_line) > 1 else latest_signal
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {str(e)}")
            return {
                'macd_line': 0,
                'signal_line': 0,
                'histogram': 0,
                'signal': 'ERROR'
            }
    
    def get_macd_signal(self, macd_line, signal_line, histogram):
        """Determine buy/sell signal from MACD values"""
        try:
            latest_macd = float(macd_line.iloc[-1])
            latest_signal = float(signal_line.iloc[-1])
            latest_histogram = float(histogram.iloc[-1])
            
            if len(macd_line) < 2:
                return 'NEUTRAL'
            
            prev_macd = float(macd_line.iloc[-2])
            prev_signal = float(signal_line.iloc[-2])
            
            # Bullish crossover: MACD crosses above signal line
            if prev_macd <= prev_signal and latest_macd > latest_signal:
                return 'BUY'
            
            # Bearish crossover: MACD crosses below signal line  
            elif prev_macd >= prev_signal and latest_macd < latest_signal:
                return 'SELL'
            
            # Current state without crossover
            elif latest_macd > latest_signal and latest_histogram > 0:
                return 'BULLISH'
            elif latest_macd < latest_signal and latest_histogram < 0:
                return 'BEARISH'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            self.logger.error(f"Error determining MACD signal: {str(e)}")
            return 'NEUTRAL'
    
    def get_signal_strength(self, histogram_value):
        """Determine signal strength based on histogram value"""
        abs_histogram = abs(histogram_value)
        
        if abs_histogram > 50:
            return 'Very Strong'
        elif abs_histogram > 30:
            return 'Strong'
        elif abs_histogram > 15:
            return 'Moderate'
        elif abs_histogram > 5:
            return 'Weak'
        else:
            return 'Very Weak'
    
    def get_nifty_30min_data(self, days_back=30):
        """Get NIFTY data for 30-minute intervals"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # Get all NIFTY price records for the period
            records = db.session.query(NiftyPrice).filter(
                db.func.date(NiftyPrice.timestamp) >= start_date,
                db.func.date(NiftyPrice.timestamp) <= end_date
            ).order_by(NiftyPrice.timestamp.asc()).all()
            
            if not records:
                return []
            
            # Convert to DataFrame for easier processing
            data = []
            for record in records:
                data.append({
                    'timestamp': record.timestamp,
                    'price': float(record.price),
                    'high': float(record.high) if record.high else float(record.price),
                    'low': float(record.low) if record.low else float(record.price)
                })
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Resample to 30-minute intervals
            resampled = df.resample('30T').agg({
                'price': 'last',  # Close price (last price in interval)
                'high': 'max',    # Highest price in interval
                'low': 'min'      # Lowest price in interval
            }).dropna()
            
            return resampled['price'].tolist()
            
        except Exception as e:
            self.logger.error(f"Error getting 30min NIFTY data: {str(e)}")
            return []
    
    def get_nifty_macd_analysis(self, timeframe_minutes=15):
        """Get complete MACD analysis for NIFTY"""
        try:
            # Get price data based on timeframe
            if timeframe_minutes == 30:
                prices = self.get_nifty_30min_data()
            else:
                # For other timeframes, use raw data (implement as needed)
                prices = self.get_nifty_30min_data()
            
            if not prices or len(prices) < 26:
                return {
                    'macd_data': {
                        'macd_line': 0,
                        'signal_line': 0,
                        'histogram': 0,
                        'signal': 'INSUFFICIENT_DATA'
                    },
                    'signal_history': [],
                    'error': 'Insufficient price data for MACD calculation'
                }
            
            # Calculate MACD
            macd_data = self.calculate_macd(prices)
            
            # Generate signal history (simulate recent signals)
            signal_history = self.generate_signal_history(prices)
            
            return {
                'macd_data': macd_data,
                'signal_history': signal_history,
                'total_prices': len(prices),
                'timeframe': f'{timeframe_minutes} minutes'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting NIFTY MACD analysis: {str(e)}")
            return {
                'macd_data': {
                    'macd_line': 0,
                    'signal_line': 0,
                    'histogram': 0,
                    'signal': 'ERROR'
                },
                'signal_history': [],
                'error': str(e)
            }
    
    def generate_signal_history(self, prices, lookback=20):
        """Generate recent MACD signal history"""
        try:
            if len(prices) < 26:
                return []
            
            signals = []
            
            # Calculate MACD for sliding window to detect signals
            for i in range(max(26, len(prices) - lookback), len(prices)):
                window_prices = prices[:i+1]
                macd_result = self.calculate_macd(window_prices)
                
                if macd_result['signal'] in ['BUY', 'SELL']:
                    # Simulate timestamp (30 minutes ago for each signal)
                    signal_time = datetime.now() - timedelta(minutes=(len(prices) - i - 1) * 30)
                    
                    signals.append({
                        'timestamp': signal_time.strftime('%H:%M:%S'),
                        'type': macd_result['signal'].lower(),
                        'price': round(window_prices[-1], 2),
                        'macd_value': macd_result['macd_line'],
                        'signal_value': macd_result['signal_line'],
                        'histogram': macd_result['histogram'],
                        'strength': macd_result.get('strength', 'Moderate')
                    })
            
            # Return most recent signals first
            return signals[-10:] if signals else []
            
        except Exception as e:
            self.logger.error(f"Error generating signal history: {str(e)}")
            return []
    
    def get_signal_stats(self):
        """Get today's signal statistics"""
        try:
            # This would typically come from a signals table
            # For now, simulate based on current analysis
            analysis = self.get_nifty_macd_analysis()
            signal_history = analysis.get('signal_history', [])
            
            buy_signals = len([s for s in signal_history if s['type'] == 'buy'])
            sell_signals = len([s for s in signal_history if s['type'] == 'sell'])
            
            return {
                'buy_signals_today': buy_signals,
                'sell_signals_today': sell_signals,
                'total_signals': buy_signals + sell_signals,
                'last_signal': signal_history[-1] if signal_history else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting signal stats: {str(e)}")
            return {
                'buy_signals_today': 0,
                'sell_signals_today': 0,
                'total_signals': 0,
                'last_signal': None
            }
