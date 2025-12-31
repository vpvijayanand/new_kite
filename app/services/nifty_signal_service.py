"""
NIFTY Signal Generation Service

Service to generate trading signals based on Pine Script MA crossover strategy.
Converts Pine Script logic to Python for Flask application.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sqlalchemy import desc
from app import db
from app.models.nifty_price import NiftyPrice
from app.models.nifty_signal import NiftySignal

class NiftySignalGenerator:
    """
    NIFTY Trading Signal Generator
    
    Implements Pine Script MA Crossover Strategy:
    - Fast MA: 12 periods
    - Slow MA: 27 periods  
    - Very Slow MA: 189 periods (trend filter)
    
    Signal Logic:
    - BUY: Fast MA crosses above Slow MA
    - SELL: Fast MA crosses below Slow MA
    """
    
    def __init__(self):
        self.fast_ma_period = 12
        self.slow_ma_period = 27
        self.very_slow_ma_period = 189
        self.min_data_points = max(self.fast_ma_period, self.slow_ma_period, self.very_slow_ma_period) + 10
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def calculate_moving_averages(self, df):
        """Calculate moving averages for the dataframe"""
        df = df.copy()
        
        # Calculate Simple Moving Averages
        df['fast_ma'] = df['close'].rolling(window=self.fast_ma_period, min_periods=self.fast_ma_period).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_ma_period, min_periods=self.slow_ma_period).mean()
        df['very_slow_ma'] = df['close'].rolling(window=self.very_slow_ma_period, min_periods=self.very_slow_ma_period).mean()
        
        # Calculate MA difference for trend analysis
        df['ma_difference'] = df['fast_ma'] - df['slow_ma']
        
        # Determine trend direction based on very slow MA
        df['trend_direction'] = 'SIDEWAYS'
        df.loc[df['close'] > df['very_slow_ma'], 'trend_direction'] = 'UP'
        df.loc[df['close'] < df['very_slow_ma'], 'trend_direction'] = 'DOWN'
        
        return df
    
    def detect_crossover_signals(self, df):
        """Detect MA crossover signals (Pine Script logic)"""
        df = df.copy()
        
        # Initialize signal columns
        df['buy_signal'] = False
        df['sell_signal'] = False
        
        # Calculate previous MA values for crossover detection
        df['prev_fast_ma'] = df['fast_ma'].shift(1)
        df['prev_slow_ma'] = df['slow_ma'].shift(1)
        
        # Detect crossovers (Pine Script: crossover and crossunder functions)
        # BUY signal: Fast MA crosses above Slow MA
        df['buy_signal'] = (
            (df['fast_ma'] > df['slow_ma']) & 
            (df['prev_fast_ma'] <= df['prev_slow_ma'])
        )
        
        # SELL signal: Fast MA crosses below Slow MA  
        df['sell_signal'] = (
            (df['fast_ma'] < df['slow_ma']) & 
            (df['prev_fast_ma'] >= df['prev_slow_ma'])
        )
        
        return df
    
    def calculate_confidence_score(self, row):
        """Calculate confidence score for a signal (0-100)"""
        score = 50  # Base score
        
        # Increase confidence based on MA separation
        ma_separation = abs(row['ma_difference'])
        if ma_separation > 50:
            score += 30
        elif ma_separation > 20:
            score += 20
        elif ma_separation > 10:
            score += 10
        
        # Increase confidence if aligned with main trend
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
        query = NiftyPrice.query.filter_by(symbol='NIFTY')
        
        if start_time:
            query = query.filter(NiftyPrice.timestamp >= start_time)
        
        # Get recent data ordered by timestamp
        nifty_data = query.order_by(NiftyPrice.timestamp.asc()).limit(limit).all()
        
        if not nifty_data:
            self.logger.warning("No NIFTY data found in database")
            return None
        
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
            signal = NiftySignal(
                timestamp=signal_data['signal_time'],
                signal_type=signal_data['signal_type'],
                price=signal_data['price'],
                fast_ma=signal_data.get('fast_ma'),
                slow_ma=signal_data.get('slow_ma'),
                very_slow_ma=signal_data.get('very_slow_ma'),
                confidence=signal_data.get('confidence', 50),
                volume=signal_data.get('volume', 0),
                trend_direction=signal_data.get('trend_direction'),
                ma_difference=signal_data.get('ma_difference'),
                signal_strength=signal_data.get('signal_strength', 'MEDIUM'),
                market_condition=signal_data.get('market_condition', 'NORMAL')
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
                        'confidence': confidence,
                        'volume': row.get('volume', 0),
                        'trend_direction': row['trend_direction'],
                        'signal_strength': 'STRONG' if confidence > 80 else 'MEDIUM' if confidence > 60 else 'WEAK'
                    }
                    
                    # Check if signal already exists
                    existing_signal = NiftySignal.query.filter(
                        NiftySignal.timestamp == row['timestamp'],
                        NiftySignal.signal_type == signal_type
                    ).first()
                    
                    if not existing_signal:
                        saved_signal = self.save_signal_to_db(signal_data)
                        if saved_signal:
                            signals_generated.append(saved_signal)
            
            self.logger.info(f"Generated {len(signals_generated)} new signals from {lookback_hours} hours of data")
            return signals_generated
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return []
    
    def generate_signals_for_latest_data(self):
        """Generate signals for the most recent data"""
        try:
            # Get the last 500 data points to ensure we have enough for MA calculation
            nifty_data = NiftyPrice.query.filter_by(symbol='NIFTY').order_by(
                desc(NiftyPrice.timestamp)
            ).limit(500).all()
            
            if not nifty_data or len(nifty_data) < self.min_data_points:
                self.logger.warning(f"Insufficient data for signal generation. Need {self.min_data_points}, got {len(nifty_data) if nifty_data else 0}")
                return []
            
            # Reverse order to have chronological data
            nifty_data = list(reversed(nifty_data))
            
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
            
            # Calculate moving averages
            df = self.calculate_moving_averages(df)
            
            # Detect crossover signals
            df = self.detect_crossover_signals(df)
            
            # Look only at the last few rows for new signals
            recent_df = df.tail(10)
            signals_generated = []
            
            for index, row in recent_df.iterrows():
                # Skip if we don't have enough data for MAs
                if pd.isna(row['fast_ma']) or pd.isna(row['slow_ma']):
                    continue
                
                signal_type = None
                if row['buy_signal']:
                    signal_type = 'BUY'
                elif row['sell_signal']:
                    signal_type = 'SELL'
                
                if signal_type:
                    # Check if signal already exists
                    existing_signal = NiftySignal.query.filter(
                        NiftySignal.timestamp == row['timestamp'],
                        NiftySignal.signal_type == signal_type
                    ).first()
                    
                    if not existing_signal:
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
                            'confidence': confidence,
                            'volume': row.get('volume', 0),
                            'trend_direction': row['trend_direction'],
                            'signal_strength': 'STRONG' if confidence > 80 else 'MEDIUM' if confidence > 60 else 'WEAK'
                        }
                        
                        saved_signal = self.save_signal_to_db(signal_data)
                        if saved_signal:
                            signals_generated.append(saved_signal)
            
            if signals_generated:
                self.logger.info(f"Generated {len(signals_generated)} new signals from latest data")
            
            return signals_generated
            
        except Exception as e:
            self.logger.error(f"Error generating signals for latest data: {e}")
            return []
    
    def get_chart_data_with_signals(self, hours=6):
        """Get chart data with signals for visualization"""
        try:
            # Get NIFTY price data
            start_time = datetime.utcnow() - timedelta(hours=hours)
            df = self.get_nifty_data(start_time=start_time)
            
            if df is None:
                return None
            
            # Calculate moving averages
            df = self.calculate_moving_averages(df)
            
            # Get signals for the same time period
            signals = NiftySignal.query.filter(
                NiftySignal.timestamp >= start_time
            ).order_by(NiftySignal.timestamp.asc()).all()
            
            chart_data = {
                'timestamps': df['timestamp'].dt.strftime('%H:%M').tolist(),
                'prices': df['close'].tolist(),
                'fast_ma': df['fast_ma'].tolist(),
                'slow_ma': df['slow_ma'].tolist(),
                'very_slow_ma': df['very_slow_ma'].tolist(),
                'signals': [signal.to_dict() for signal in signals]
            }
            
            return chart_data
            
        except Exception as e:
            self.logger.error(f"Error getting chart data: {e}")
            return None
