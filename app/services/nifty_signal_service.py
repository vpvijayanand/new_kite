import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app import db
from app.models.nifty_price import NiftyPrice
from app.models.nifty_signal import NiftySignal
import logging

class NiftySignalGenerator:
    """
    NIFTY Signal Generator based on Fast/Slow MA Crossover Strategy
    Implements Pine Script logic: Fast MA (12) crossover/crossunder Slow MA (27)
    """
    
    def __init__(self):
        self.fast_length = 12      # Fast MA Length
        self.slow_length = 27      # Slow MA Length
        self.very_slow_length = 189  # Very Slow MA Length
        self.min_data_points = 200   # Minimum data points needed for signals
        
        self.logger = logging.getLogger(__name__)
    
    def calculate_moving_averages(self, df):
        """Calculate moving averages similar to Pine Script"""
        # Simple Moving Averages (SMA) - equivalent to ta.sma() in Pine Script
        df['fast_ma'] = df['close'].rolling(window=self.fast_length).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_length).mean()
        df['very_slow_ma'] = df['close'].rolling(window=self.very_slow_length).mean()
        
        # Calculate MA differences
        df['ma_difference'] = df['fast_ma'] - df['slow_ma']
        df['ma_difference_percent'] = (df['ma_difference'] / df['close']) * 100
        
        # Trend direction based on very slow MA
        df['trend_direction'] = np.where(
            df['very_slow_ma'].diff() > 0, 'UP', 'DOWN'
        )
        
        return df
    
    def detect_crossover_signals(self, df):
        """
        Detect crossover signals equivalent to Pine Script:
        buySignal = ta.crossover(fastMA, slowMA)
        sellSignal = ta.crossunder(fastMA, slowMA)
        """
        # Previous values for crossover detection
        df['fast_ma_prev'] = df['fast_ma'].shift(1)
        df['slow_ma_prev'] = df['slow_ma'].shift(1)
        
        # Crossover logic (Fast MA crosses above Slow MA)
        df['buy_signal'] = (
            (df['fast_ma'] > df['slow_ma']) & 
            (df['fast_ma_prev'] <= df['slow_ma_prev'])
        )
        
        # Crossunder logic (Fast MA crosses below Slow MA)
        df['sell_signal'] = (
            (df['fast_ma'] < df['slow_ma']) & 
            (df['fast_ma_prev'] >= df['slow_ma_prev'])
        )
        
        return df
    
    def calculate_confidence_score(self, row):
        """Calculate confidence score for the signal (0-100)"""
        score = 50  # Base score
        
        # Increase confidence based on MA difference magnitude
        ma_diff_abs = abs(row['ma_difference_percent'])
        if ma_diff_abs > 0.5:
            score += 20
        elif ma_diff_abs > 0.2:
            score += 10
        
        # Increase confidence if signal aligns with very slow MA trend
        if row['buy_signal'] and row['trend_direction'] == 'UP':
            score += 20
        elif row['sell_signal'] and row['trend_direction'] == 'DOWN':
            score += 20
        
        # Decrease confidence if against main trend
        if row['buy_signal'] and row['trend_direction'] == 'DOWN':
            score -= 10
        elif row['sell_signal'] and row['trend_direction'] == 'UP':
            score -= 10
        
        return min(100, max(0, score))
    
    def get_nifty_data(self, start_time=None, limit=1000):
        """Get NIFTY price data from database"""
        # Try both 'NIFTY' and 'NIFTY 50' as symbols
        query = NiftyPrice.query.filter(
            (NiftyPrice.symbol == 'NIFTY') | (NiftyPrice.symbol == 'NIFTY 50')
        )
        
        if start_time:
            query = query.filter(NiftyPrice.timestamp >= start_time)
        
        # Get recent data ordered by timestamp
        nifty_data = query.order_by(NiftyPrice.timestamp.asc()).limit(limit).all()
        
        if not nifty_data:
            self.logger.warning("No NIFTY data found in database")
            return None
        
        self.logger.info(f"Found {len(nifty_data)} NIFTY price records")
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'timestamp': price.timestamp,
            'open': price.open or price.price,
            'high': price.high or price.price,
            'low': price.low or price.price,
            'close': price.close or price.price,
            'volume': getattr(price, 'volume', 0)
        } for price in nifty_data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def save_signal_to_db(self, signal_data):
        """Save generated signal to database"""
        try:
            # Check if signal already exists at this exact time
            existing_signal = NiftySignal.query.filter_by(
                signal_time=signal_data['signal_time'],
                signal_type=signal_data['signal_type']
            ).first()
            
            if existing_signal:
                self.logger.info(f"Signal already exists: {signal_data['signal_type']} at {signal_data['signal_time']}")
                return existing_signal
            
            # Create new signal
            signal = NiftySignal(
                signal_type=signal_data['signal_type'],
                signal_time=signal_data['signal_time'],
                price=signal_data['price'],
                fast_ma=signal_data['fast_ma'],
                slow_ma=signal_data['slow_ma'],
                very_slow_ma=signal_data['very_slow_ma'],
                ma_difference=signal_data['ma_difference'],
                ma_difference_percent=signal_data['ma_difference_percent'],
                trend_direction=signal_data['trend_direction'],
                confidence_score=signal_data['confidence_score'],
                is_valid=True
            )
            
            db.session.add(signal)
            db.session.commit()
            
            self.logger.info(f"Saved {signal_data['signal_type']} signal at {signal_data['signal_time']}")
            return signal
            
        except Exception as e:
            self.logger.error(f"Error saving signal: {e}")
            db.session.rollback()
            return None
    
    def generate_signals(self, lookback_hours=24):
        """Generate signals for recent data"""
        try:
            # Get recent NIFTY data
            start_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            df = self.get_nifty_data(start_time=start_time)
            
            if df is None or len(df) < self.min_data_points:
                self.logger.warning(f"Insufficient data for signal generation. Need {self.min_data_points}, got {len(df) if df is not None else 0}")
                return []
            
            # Calculate moving averages
            df = self.calculate_moving_averages(df)
            
            # Detect crossover signals
            df = self.detect_crossover_signals(df)
            
            # Find signal points
            signals_generated = []
            
            for index, row in df.iterrows():
                # Skip if we don't have enough data for MAs
                if pd.isna(row['fast_ma']) or pd.isna(row['slow_ma']):
                    continue
                
                signal_type = None
                if row['buy_signal']:
                    signal_type = 'BUY'
                elif row['sell_signal']:
                    signal_type = 'SELL'
                
                if signal_type:
                    # Calculate confidence score
                    confidence = self.calculate_confidence_score(row)
                    
                    signal_data = {
                        'signal_type': signal_type,
                        'signal_time': row['timestamp'],
                        'price': row['close'],
                        'fast_ma': row['fast_ma'],
                        'slow_ma': row['slow_ma'],
                        'very_slow_ma': row['very_slow_ma'],
                        'ma_difference': row['ma_difference'],
                        'ma_difference_percent': row['ma_difference_percent'],
                        'trend_direction': row['trend_direction'],
                        'confidence_score': confidence
                    }
                    
                    # Save to database
                    saved_signal = self.save_signal_to_db(signal_data)
                    if saved_signal:
                        signals_generated.append(saved_signal)
            
            self.logger.info(f"Generated {len(signals_generated)} new signals")
            return signals_generated
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return []
    
    def generate_signals_for_latest_data(self):
        """Generate signals for the latest data point only"""
        try:
            # Get recent data (last 500 points to calculate MAs)
            df = self.get_nifty_data(limit=500)
            
            if df is None or len(df) < self.min_data_points:
                return None
            
            # Calculate moving averages
            df = self.calculate_moving_averages(df)
            
            # Detect crossover signals
            df = self.detect_crossover_signals(df)
            
            # Check only the latest data point
            latest_row = df.iloc[-1]
            
            # Skip if we don't have enough data for MAs
            if pd.isna(latest_row['fast_ma']) or pd.isna(latest_row['slow_ma']):
                return None
            
            signal_type = None
            if latest_row['buy_signal']:
                signal_type = 'BUY'
            elif latest_row['sell_signal']:
                signal_type = 'SELL'
            
            if signal_type:
                confidence = self.calculate_confidence_score(latest_row)
                
                signal_data = {
                    'signal_type': signal_type,
                    'signal_time': latest_row['timestamp'],
                    'price': latest_row['close'],
                    'fast_ma': latest_row['fast_ma'],
                    'slow_ma': latest_row['slow_ma'],
                    'very_slow_ma': latest_row['very_slow_ma'],
                    'ma_difference': latest_row['ma_difference'],
                    'ma_difference_percent': latest_row['ma_difference_percent'],
                    'trend_direction': latest_row['trend_direction'],
                    'confidence_score': confidence
                }
                
                return self.save_signal_to_db(signal_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating signals for latest data: {e}")
            return None
    
    def get_chart_data_with_signals(self, hours=6):
        """Get chart data with signals for visualization"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get NIFTY data
            df = self.get_nifty_data(start_time=start_time)
            if df is None:
                return None
            
            # Calculate MAs
            df = self.calculate_moving_averages(df)
            df = self.detect_crossover_signals(df)
            
            # Get signals from database
            signals = NiftySignal.query.filter(
                NiftySignal.signal_time >= start_time
            ).order_by(NiftySignal.signal_time.asc()).all()
            
            return {
                'price_data': df.to_dict('records'),
                'signals': [signal.to_dict() for signal in signals]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting chart data: {e}")
            return None
