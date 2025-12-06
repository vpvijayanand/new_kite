# NIFTY Chart & MACD Technical Analysis

## Overview
Advanced NIFTY Index charting system with real-time MACD (Moving Average Convergence Divergence) analysis for generating buy/sell signals.

## Features

### 📊 Interactive Chart
- **TradingView Integration**: Professional-grade candlestick charts
- **Multiple Timeframes**: 15min, 30min, 1hour, Daily
- **MACD Indicator**: Built-in MACD overlay with signal detection
- **Real-time Updates**: Auto-refresh every 30 seconds
- **IST Timezone**: All data in Indian Standard Time

### 📈 MACD Analysis
- **Technical Parameters**:
  - Fast EMA: 12 periods
  - Slow EMA: 26 periods  
  - Signal EMA: 9 periods
- **Signal Generation**:
  - **BUY**: MACD line crosses above Signal line
  - **SELL**: MACD line crosses below Signal line
  - **Signal Strength**: Very Strong, Strong, Moderate, Weak
- **Real-time Values**: Live MACD Line, Signal Line, Histogram

### 🎯 Signal Dashboard
- **Current Signal Status**: BUY/SELL/NEUTRAL with color coding
- **Signal History**: Recent crossovers with timestamps
- **Daily Statistics**: Count of buy/sell signals today
- **Price Tracking**: Current NIFTY price with change percentage

## Technical Implementation

### Backend Components
1. **TechnicalAnalysisService** (`app/services/technical_analysis_service.py`)
   - EMA calculations using pandas
   - MACD computation with crossover detection
   - 30-minute data aggregation
   - Signal strength analysis

2. **API Endpoints**:
   - `/market/api/current-nifty` - Real-time NIFTY price
   - `/market/api/macd-analysis` - MACD calculations
   - `/market/api/signal-stats` - Daily signal statistics

3. **Database Integration**:
   - Uses existing NiftyPrice table
   - Resamples minute data to 30-minute intervals
   - Historical signal tracking

### Frontend Features
1. **TradingView Chart**:
   - Professional charting library
   - Customizable timeframes
   - Built-in MACD indicator
   - Dark theme optimized

2. **Real-time Dashboard**:
   - Live price updates
   - Signal status cards
   - MACD value display
   - Signal history panel

## Dependencies Added

### Python Packages
```
pandas>=2.1.1          # Data manipulation and analysis
numpy>=1.25.2           # Numerical computations
ta-lib>=0.4.28          # Technical Analysis Library (optional)
scikit-learn>=1.3.0     # Machine Learning (future enhancements)
```

### JavaScript Libraries
```
TradingView Charting Library (CDN)
Bootstrap 5.3.0
Font Awesome 6.4.0
```

## Usage Guide

### Accessing the Chart
1. **Via Navigation**: Charts & Technical Analysis → NIFTY Chart & MACD
2. **Quick Access**: Dashboard → Quick Access → NIFTY Chart & MACD
3. **Direct URL**: `http://localhost:5000/market/nifty-chart`

### Reading MACD Signals

#### Buy Signals 📈
- MACD line crosses **above** Signal line
- Histogram turns **positive** 
- Signal strength indicates momentum
- Best in **uptrending** markets

#### Sell Signals 📉  
- MACD line crosses **below** Signal line
- Histogram turns **negative**
- Signal strength indicates momentum
- Best in **downtrending** markets

#### Signal Strength Levels
- **Very Strong**: |Histogram| > 50
- **Strong**: |Histogram| > 30  
- **Moderate**: |Histogram| > 15
- **Weak**: |Histogram| > 5
- **Very Weak**: |Histogram| ≤ 5

### Best Practices
1. **Combine with Price Action**: Don't rely on MACD alone
2. **Consider Market Trend**: MACD works best in trending markets
3. **Watch for Divergence**: Price vs MACD divergence signals
4. **Use Multiple Timeframes**: Confirm signals across timeframes
5. **Risk Management**: Always use stop losses

## Configuration

### Timeframe Settings
- **Default**: 30 minutes (optimal for intraday)
- **Available**: 15min, 30min, 1hour, Daily
- **Data Source**: NSE NIFTY real-time data

### Auto-Refresh Settings
- **Interval**: 30 seconds
- **Toggleable**: Can be disabled via UI
- **Market Hours**: Respects trading session times

### Signal Parameters
```python
# MACD Parameters (customizable in service)
FAST_PERIOD = 12    # Fast EMA period
SLOW_PERIOD = 26    # Slow EMA period  
SIGNAL_PERIOD = 9   # Signal line EMA period
```

## Future Enhancements

### Planned Features
- **BANKNIFTY Chart**: Similar analysis for BANKNIFTY
- **RSI Integration**: Additional momentum indicator
- **Bollinger Bands**: Volatility-based signals
- **Multi-Indicator Signals**: Combined indicator analysis
- **Alert System**: Email/SMS notifications for signals
- **Backtesting**: Historical performance analysis

### Advanced Features
- **Pattern Recognition**: Chart pattern detection
- **Machine Learning**: AI-based signal prediction
- **Portfolio Integration**: Link with trading positions
- **Risk Metrics**: Sharpe ratio, max drawdown analysis

## Troubleshooting

### Common Issues
1. **No MACD Data**: Insufficient price history (need 26+ periods)
2. **Chart Not Loading**: TradingView API connection issue
3. **Signal Delays**: Database lag or calculation errors
4. **Timeframe Issues**: Data availability for selected timeframe

### Performance Optimization
- Data caching for faster MACD calculations
- Efficient pandas operations
- Minimal API calls during market hours
- Optimized database queries

## Support
For technical issues or feature requests, refer to the main application documentation or contact the development team.

---
*Last Updated: December 4, 2025*
*Version: 1.0.0*
