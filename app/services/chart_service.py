"""
Custom Chart Service for NIFTY Index
Create            # Define resampling rules
            timeframe_map = {
                '1min': '1T',
                '5min': '5T', 
                '15min': '15T',
                '30min': '30T',
                '1hour': '1H',
                '4hour': '4H',
                '1day': '1D'
            }
            
            resample_rule = timeframe_map.get(timeframe, '30T')ive charts using matplotlib and plotly without external dependencies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
import json
from app.models.nifty_price import NiftyPrice
from app.services.technical_analysis_service import TechnicalAnalysisService


class ChartService:
    def __init__(self):
        self.ta_service = TechnicalAnalysisService()
    
    def get_nifty_chart_data(self, timeframe='30min', days_back=30):
        """Get NIFTY data for charting with specified timeframe"""
        try:
            # Get raw data from database
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Query NIFTY prices
            prices = NiftyPrice.query.filter(
                NiftyPrice.timestamp >= start_date,
                NiftyPrice.timestamp <= end_date
            ).order_by(NiftyPrice.timestamp.asc()).all()
            
            if not prices:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': price.timestamp,
                'open': price.open or price.price,
                'high': price.high or price.price,
                'low': price.low or price.price,
                'close': price.close or price.price,
                'price': price.price
            } for price in prices])
            
            # Resample based on timeframe
            df.set_index('timestamp', inplace=True)
            
            # Define resampling rules
            timeframe_map = {
                '1min': '1min',
                '5min': '5min',
                '15min': '15min',
                '30min': '30min',
                '1hour': '1H',
                '4hour': '4H',
                '1day': '1D'
            }
            
            resample_rule = timeframe_map.get(timeframe, '30T')
            
            # Resample OHLC data
            ohlc_df = df.resample(resample_rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'price': 'last'
            }).dropna()
            
            print(f"DEBUG: Chart data generated - {len(ohlc_df)} candles, timeframe: {timeframe}, rule: {resample_rule}")
            if len(ohlc_df) > 0:
                print(f"DEBUG: Data range: {ohlc_df.index.min()} to {ohlc_df.index.max()}")
            
            return ohlc_df
            
        except Exception as e:
            print(f"Error getting chart data: {e}")
            return None
    
    def calculate_macd_for_chart(self, df):
        """Calculate MACD values for the chart data"""
        try:
            if df is None or len(df) < 26:
                return None
            
            # Calculate MACD using close prices
            close_prices = df['close'].values
            
            # Calculate EMAs
            ema_12 = self._calculate_ema(close_prices, 12)
            ema_26 = self._calculate_ema(close_prices, 26)
            
            # MACD line = EMA12 - EMA26
            macd_line = ema_12 - ema_26
            
            # Signal line = EMA9 of MACD line
            signal_line = self._calculate_ema(macd_line, 9)
            
            # Histogram = MACD - Signal
            histogram = macd_line - signal_line
            
            # Create MACD DataFrame
            macd_df = pd.DataFrame({
                'macd_line': macd_line,
                'signal_line': signal_line,
                'histogram': histogram
            }, index=df.index)
            
            return macd_df
            
        except Exception as e:
            print(f"Error calculating MACD for chart: {e}")
            return None
    
    def _calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    def generate_interactive_chart(self, timeframe='30min', days_back=30):
        """Generate interactive NIFTY chart with MACD"""
        try:
            # Get chart data
            ohlc_df = self.get_nifty_chart_data(timeframe, days_back)
            if ohlc_df is None or len(ohlc_df) == 0:
                return self._generate_no_data_chart()
            
            return self._create_chart_from_data(ohlc_df, timeframe, days_back)
            
        except Exception as e:
            print(f"Error generating interactive chart: {e}")
            return {
                'success': False,
                'error': str(e),
                'chart_html': self._generate_error_chart()
            }
    
    def generate_interactive_chart_with_date_filter(self, timeframe='30min', days_back=30, start_datetime=None, end_datetime=None):
        """Generate interactive NIFTY chart with MACD using date filter"""
        try:
            # Get chart data with date filter
            if start_datetime and end_datetime:
                ohlc_df = self.get_nifty_chart_data_with_date_filter(timeframe, start_datetime, end_datetime)
            else:
                ohlc_df = self.get_nifty_chart_data(timeframe, days_back)
                
            if ohlc_df is None or len(ohlc_df) == 0:
                return self._generate_no_data_chart()
            
            return self._create_chart_from_data(ohlc_df, timeframe, days_back)
            
        except Exception as e:
            print(f"Error generating interactive chart with date filter: {e}")
            return {
                'success': False,
                'error': str(e),
                'chart_html': self._generate_error_chart()
            }
    
    def get_nifty_chart_data_with_date_filter(self, timeframe='30min', start_datetime=None, end_datetime=None):
        """Get NIFTY data for charting with date filter"""
        try:
            # Query NIFTY prices within date range
            query = NiftyPrice.query
            
            if start_datetime:
                query = query.filter(NiftyPrice.timestamp >= start_datetime)
            if end_datetime:
                query = query.filter(NiftyPrice.timestamp <= end_datetime)
                
            prices = query.order_by(NiftyPrice.timestamp.asc()).all()
            
            if not prices:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': price.timestamp,
                'open': price.open or price.price,
                'high': price.high or price.price,
                'low': price.low or price.price,
                'close': price.close or price.price,
                'price': price.price
            } for price in prices])
            
            # Resample based on timeframe
            df.set_index('timestamp', inplace=True)
            
            # Define resampling rules  
            timeframe_map = {
                '1min': '1T',
                '5min': '5T',
                '15min': '15T',
                '30min': '30T', 
                '1hour': '1H',
                '4hour': '4H',
                '1day': '1D'
            }
            
            resample_rule = timeframe_map.get(timeframe, '30T')
            
            # Resample OHLC data
            ohlc_df = df.resample(resample_rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'price': 'last'
            }).dropna()
            
            return ohlc_df
            
        except Exception as e:
            print(f"Error getting chart data with date filter: {e}")
            return None
    
    def _create_chart_from_data(self, ohlc_df, timeframe, days_back):
        """Create chart from OHLC data"""
        try:
            # Calculate MACD
            macd_df = self.calculate_macd_for_chart(ohlc_df)
            
            # Create subplot figure
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.15,
                subplot_titles=('NIFTY 50 Index - Candlestick Chart', 'MACD Indicator'),
                row_heights=[0.7, 0.3]
            )
            
            # Add candlestick chart
            candlestick = go.Candlestick(
                x=ohlc_df.index,
                open=ohlc_df['open'],
                high=ohlc_df['high'],
                low=ohlc_df['low'],
                close=ohlc_df['close'],
                name='NIFTY 50',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            )
            
            fig.add_trace(candlestick, row=1, col=1)
            
            # Add MACD if available
            if macd_df is not None:
                # MACD Line
                fig.add_trace(go.Scatter(
                    x=macd_df.index,
                    y=macd_df['macd_line'],
                    mode='lines',
                    name='MACD Line',
                    line=dict(color='#2196F3', width=2)
                ), row=2, col=1)
                
                # Signal Line
                fig.add_trace(go.Scatter(
                    x=macd_df.index,
                    y=macd_df['signal_line'],
                    mode='lines',
                    name='Signal Line',
                    line=dict(color='#FF9800', width=2)
                ), row=2, col=1)
                
                # Histogram
                colors = ['#26a69a' if h >= 0 else '#ef5350' for h in macd_df['histogram']]
                fig.add_trace(go.Bar(
                    x=macd_df.index,
                    y=macd_df['histogram'],
                    name='Histogram',
                    marker_color=colors,
                    opacity=0.7
                ), row=2, col=1)
            
            # Update layout
            fig.update_layout(
                title=f'NIFTY 50 Index - {timeframe.upper()} Chart with MACD',
                xaxis_title='Time',
                yaxis_title='Price (₹)',
                template='plotly_dark',
                showlegend=True,
                height=450,
                margin=dict(l=40, r=40, t=60, b=40),
                hovermode='x unified'
            )
            
            # Update x-axes with proper datetime formatting
            fig.update_xaxes(
                rangeslider_visible=False,
                showgrid=True,
                gridcolor='rgba(128,128,128,0.3)',
                tickformat='%H:%M<br>%d/%m',  # Show time and date
                showticklabels=True,
                tickangle=0
            )
            
            # Update y-axes
            fig.update_yaxes(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.3)',
                title_text="Price (₹)",
                row=1, col=1
            )
            
            fig.update_yaxes(
                title_text="MACD",
                row=2, col=1
            )
            
            # Convert to HTML
            chart_html = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')
            
            # Get current market data
            current_data = self._get_current_market_data()
            
            # Get latest MACD signal
            latest_signal = self.get_signal_analysis(timeframe)
            
            return {
                'success': True,
                'chart_html': chart_html,
                'current_data': current_data,
                'latest_signal': latest_signal,
                'data_points': len(ohlc_df),
                'timeframe': timeframe
            }
            
        except Exception as e:
            print(f"Error creating chart from data: {e}")
            return {
                'success': False,
                'error': str(e),
                'chart_html': self._generate_error_chart()
            }
    
    def _generate_no_data_chart(self):
        """Generate a placeholder chart when no data is available"""
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="No NIFTY data available<br>Please ensure data collection is running",
            showarrow=False,
            font=dict(size=20, color="white"),
            xref="paper", yref="paper"
        )
        fig.update_layout(
            template='plotly_dark',
            height=450,
            title="NIFTY 50 Chart - No Data Available"
        )
        
        chart_html = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')
        
        return {
            'success': False,
            'chart_html': chart_html,
            'current_data': {},
            'latest_signal': {},
            'data_points': 0,
            'timeframe': '30min'
        }
    
    def _generate_error_chart(self):
        """Generate an error chart"""
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text="Error loading chart data<br>Please try refreshing the page",
            showarrow=False,
            font=dict(size=20, color="red"),
            xref="paper", yref="paper"
        )
        fig.update_layout(
            template='plotly_dark',
            height=450,
            title="Chart Error"
        )
        
        chart_html = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')
        
        return {
            'success': False,
            'chart_html': chart_html,
            'current_data': {},
            'latest_signal': {},
            'data_points': 0,
            'timeframe': '30min'
        }
    
    def _get_current_market_data(self):
        """Get current NIFTY market data"""
        try:
            latest_price = NiftyPrice.query.order_by(NiftyPrice.timestamp.desc()).first()
            if latest_price:
                return {
                    'price': latest_price.price,
                    'change': latest_price.change or 0,
                    'change_percent': latest_price.change_percent or 0,
                    'timestamp': latest_price.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'high': latest_price.high,
                    'low': latest_price.low,
                    'open': latest_price.open
                }
            return None
        except Exception as e:
            print(f"Error getting current market data: {e}")
            return None
    
    def get_signal_analysis(self, timeframe='30min'):
        """Get MACD signal analysis with strength"""
        try:
            # Get MACD data
            ohlc_df = self.get_nifty_chart_data(timeframe, days_back=100)
            if ohlc_df is None:
                return None
            
            macd_df = self.calculate_macd_for_chart(ohlc_df)
            if macd_df is None:
                return None
            
            # Get latest values
            latest = macd_df.iloc[-1]
            prev = macd_df.iloc[-2] if len(macd_df) > 1 else latest
            
            # Determine signal
            signal = 'NEUTRAL'
            strength = 'Weak'
            
            macd_line = latest['macd_line']
            signal_line = latest['signal_line']
            histogram = latest['histogram']
            
            prev_histogram = prev['histogram']
            
            # Signal logic
            if macd_line > signal_line and histogram > prev_histogram:
                signal = 'BUY'
                strength = 'Strong' if histogram > 0.5 else 'Moderate'
            elif macd_line < signal_line and histogram < prev_histogram:
                signal = 'SELL'
                strength = 'Strong' if histogram < -0.5 else 'Moderate'
            elif macd_line > signal_line:
                signal = 'BULLISH'
                strength = 'Weak'
            elif macd_line < signal_line:
                signal = 'BEARISH'
                strength = 'Weak'
            
            return {
                'signal': signal,
                'strength': strength,
                'macd_line': round(macd_line, 2),
                'signal_line': round(signal_line, 2),
                'histogram': round(histogram, 2),
                'timestamp': ohlc_df.index[-1].strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"Error in signal analysis: {e}")
            return None
        
    def get_nifty_chart_with_macd(self, symbol='NIFTY', timeframe_minutes=15):
        """
        Get NIFTY chart data with MACD for Plotly.js rendering
        Returns JSON-serializable data for frontend charting
        """
        try:
            # Convert timeframe minutes to string format
            if timeframe_minutes <= 1:
                timeframe = '1min'
                days_back = 2
            elif timeframe_minutes <= 5:
                timeframe = '5min'
                days_back = 5
            elif timeframe_minutes <= 15:
                timeframe = '15min'
                days_back = 10
            elif timeframe_minutes <= 30:
                timeframe = '30min'
                days_back = 15
            elif timeframe_minutes <= 60:
                timeframe = '1hour'
                days_back = 30
            elif timeframe_minutes <= 240:
                timeframe = '4hour'
                days_back = 90
            else:
                timeframe = '1day'
                days_back = 180
            
            # Get OHLC data
            ohlc_df = self.get_nifty_chart_data(timeframe, days_back)
            
            if ohlc_df is None or len(ohlc_df) == 0:
                # Return sample data if no real data available
                return self._generate_sample_chart_data()
            
            # Calculate MACD
            macd_df = self.calculate_macd_for_chart(ohlc_df)
            
            if macd_df is None:
                # Create empty MACD data
                macd_df = pd.DataFrame({
                    'macd_line': [0] * len(ohlc_df),
                    'signal_line': [0] * len(ohlc_df),
                    'histogram': [0] * len(ohlc_df)
                }, index=ohlc_df.index)
            
            # Prepare data for frontend
            chart_data = {
                'timestamps': [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in ohlc_df.index],
                'open': ohlc_df['open'].round(2).fillna(method='ffill').tolist(),
                'high': ohlc_df['high'].round(2).fillna(method='ffill').tolist(),
                'low': ohlc_df['low'].round(2).fillna(method='ffill').tolist(),
                'close': ohlc_df['close'].round(2).fillna(method='ffill').tolist(),
                'macd_line': macd_df['macd_line'].round(4).fillna(0).tolist(),
                'signal_line': macd_df['signal_line'].round(4).fillna(0).tolist(),
                'histogram': macd_df['histogram'].round(4).fillna(0).tolist(),
                'current_price': float(ohlc_df['close'].iloc[-1]),
                'current_signal': self._determine_current_signal(macd_df)
            }
            
            return chart_data
            
        except Exception as e:
            print(f"Error generating chart data with MACD: {e}")
            return self._generate_sample_chart_data()
    
    def _determine_current_signal(self, macd_df):
        """Determine current MACD signal from dataframe"""
        try:
            if len(macd_df) < 2:
                return 'NEUTRAL'
            
            current = macd_df.iloc[-1]
            prev = macd_df.iloc[-2]
            
            macd_line = current['macd_line']
            signal_line = current['signal_line']
            prev_macd = prev['macd_line']
            prev_signal = prev['signal_line']
            
            # Check for crossovers
            if prev_macd <= prev_signal and macd_line > signal_line:
                return 'BUY'
            elif prev_macd >= prev_signal and macd_line < signal_line:
                return 'SELL'
            elif macd_line > signal_line:
                return 'BULLISH'
            elif macd_line < signal_line:
                return 'BEARISH'
            else:
                return 'NEUTRAL'
                
        except Exception as e:
            print(f"Error determining signal: {e}")
            return 'NEUTRAL'
    
    def _generate_sample_chart_data(self):
        """Generate sample chart data when real data is unavailable"""
        import numpy as np
        from datetime import datetime, timedelta
        
        # Generate 100 sample candles
        np.random.seed(42)
        base_price = 24000
        n_candles = 100
        
        # Generate timestamps
        timestamps = []
        current_time = datetime.now() - timedelta(hours=n_candles//4)
        for i in range(n_candles):
            timestamps.append((current_time + timedelta(minutes=15*i)).strftime('%Y-%m-%d %H:%M:%S'))
        
        # Generate realistic price data
        price_changes = np.random.normal(0, 50, n_candles).cumsum()
        closes = base_price + price_changes
        
        opens = closes + np.random.normal(0, 10, n_candles)
        highs = np.maximum(opens, closes) + np.abs(np.random.normal(0, 15, n_candles))
        lows = np.minimum(opens, closes) - np.abs(np.random.normal(0, 15, n_candles))
        
        # Generate MACD data
        macd_line = np.sin(np.arange(n_candles) * 0.1) * 20 + np.random.normal(0, 5, n_candles)
        signal_line = np.sin(np.arange(n_candles) * 0.08) * 18 + np.random.normal(0, 3, n_candles)
        histogram = macd_line - signal_line
        
        return {
            'timestamps': timestamps,
            'open': opens.round(2).tolist(),
            'high': highs.round(2).tolist(),
            'low': lows.round(2).tolist(),
            'close': closes.round(2).tolist(),
            'macd_line': macd_line.round(4).tolist(),
            'signal_line': signal_line.round(4).tolist(),
            'histogram': histogram.round(4).tolist(),
            'current_price': float(closes[-1]),
            'current_signal': 'NEUTRAL'
        }
