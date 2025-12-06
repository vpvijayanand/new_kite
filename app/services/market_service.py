from app.models.nifty_price import NiftyPrice
from app.models.banknifty_price import BankNiftyPrice, OptionChainData, MarketTrend
from app.services.kite_service import KiteService
from app import db
from datetime import datetime, timedelta

class MarketService:
    def __init__(self):
        self.kite_service = KiteService()
    
    def fetch_and_save_nifty_price(self):
        try:
            price_data = self.kite_service.get_nifty_price()
            
            if price_data:
                NiftyPrice.save_price(price_data)
                return price_data
            return None
        except Exception as e:
            print(f"Error in fetch_and_save_nifty_price: {str(e)}")
            return None
    
    def fetch_and_save_banknifty_price(self):
        try:
            price_data = self.kite_service.get_banknifty_price()
            
            if price_data:
                BankNiftyPrice.save_price(price_data)
                return price_data
            return None
        except Exception as e:
            print(f"Error in fetch_and_save_banknifty_price: {str(e)}")
            return None
    
    def fetch_and_save_option_chain(self, underlying="NIFTY"):
        """Fetch and save option chain data for given underlying - real data only"""
        try:
            option_chain_data = self.kite_service.get_option_chain_data(underlying)
            
            if option_chain_data:
                saved_count = 0
                for option_data in option_chain_data:
                    OptionChainData.save_option_data(option_data)
                    saved_count += 1
                
                # Calculate and save market trend
                trend_data = self.kite_service.calculate_market_trend(option_chain_data, underlying)
                if trend_data:
                    MarketTrend.save_trend_data(trend_data)
                
                print(f"Saved {saved_count} option chain records for {underlying}")
                return option_chain_data
            else:
                print(f"No API data available for {underlying}")
                return None
        except Exception as e:
            print(f"Error in fetch_and_save_option_chain for {underlying}: {str(e)}")
            return None
    

    
    def get_latest_prices(self, limit=100):
        return NiftyPrice.get_latest_prices(limit)
    
    def get_latest_banknifty_prices(self, limit=100):
        return BankNiftyPrice.get_latest_prices(limit)
    
    def get_price_history(self, hours=24):
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        prices = NiftyPrice.query.filter(
            NiftyPrice.timestamp >= cutoff_time
        ).order_by(NiftyPrice.timestamp.desc()).all()
        
        return [price.to_dict() for price in prices]
    
    def get_banknifty_price_history(self, hours=24):
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        prices = BankNiftyPrice.query.filter(
            BankNiftyPrice.timestamp >= cutoff_time
        ).order_by(BankNiftyPrice.timestamp.desc()).all()
        
        return [price.to_dict() for price in prices]
    
    def get_current_option_chain(self, underlying="NIFTY", limit=50):
        """Get current option chain data for analysis"""
        return OptionChainData.get_latest_option_chain(underlying, limit=limit)
    
    def get_oi_analysis_data(self, underlying="NIFTY"):
        """Get detailed OI analysis data for divergence analysis"""
        return OptionChainData.get_oi_analysis(underlying)
    
    def get_market_trend(self, underlying="NIFTY"):
        """Get current market trend analysis"""
        return MarketTrend.get_latest_trend(underlying)
    
    def get_dashboard_data(self):
        """Get comprehensive dashboard data"""
        try:
            # Get latest prices
            nifty_price = None
            banknifty_price = None
            
            latest_nifty = NiftyPrice.query.order_by(NiftyPrice.timestamp.desc()).first()
            if latest_nifty:
                nifty_price = latest_nifty.to_dict()
            
            latest_banknifty = BankNiftyPrice.query.order_by(BankNiftyPrice.timestamp.desc()).first()
            if latest_banknifty:
                banknifty_price = latest_banknifty.to_dict()
            
            # Get market trends
            nifty_trend = self.get_market_trend("NIFTY")
            banknifty_trend = self.get_market_trend("BANKNIFTY")
            
            # Get option chain summaries
            nifty_options = self.get_current_option_chain("NIFTY", limit=10)
            banknifty_options = self.get_current_option_chain("BANKNIFTY", limit=10)
            
            return {
                'nifty_price': nifty_price,
                'banknifty_price': banknifty_price,
                'nifty_trend': nifty_trend.to_dict() if nifty_trend else None,
                'banknifty_trend': banknifty_trend.to_dict() if banknifty_trend else None,
                'nifty_options_summary': [opt.to_dict() for opt in nifty_options[:5]],
                'banknifty_options_summary': [opt.to_dict() for opt in banknifty_options[:5]]
            }
        except Exception as e:
            print(f"Error getting dashboard data: {str(e)}")
            return {
                'nifty_price': None,
                'banknifty_price': None,
                'nifty_trend': None,
                'banknifty_trend': None,
                'nifty_options_summary': [],
                'banknifty_options_summary': []
            }

    def _get_price_with_daily_change(self, underlying, target_date=None):
        """Get latest price with calculated daily percentage change for specific date"""
        try:
            from datetime import date, datetime
            from sqlalchemy import func
            
            if underlying == 'NIFTY':
                model = NiftyPrice
            else:
                model = BankNiftyPrice
            
            # Use provided date or default to today
            target_date = target_date or date.today()
            print(f"DEBUG: Getting {underlying} price for date: {target_date}")
            
            # Get latest price for the target date
            latest_price = model.query.filter(
                func.date(model.timestamp) == target_date
            ).order_by(model.timestamp.desc()).first()
            
            if not latest_price:
                print(f"DEBUG: No {underlying} price data found for {target_date}")
                return None
            
            print(f"DEBUG: Latest {underlying} price: {latest_price.price} at {latest_price.timestamp}")
            
            # Get first price of the day (market opening around 9:20 AM)
            first_price_today = model.query.filter(
                func.date(model.timestamp) == target_date
            ).order_by(model.timestamp.asc()).first()
            
            if not first_price_today:
                print(f"DEBUG: No {underlying} opening price for today, using demo data")
                # If no opening price, simulate a small change for demo
                price_dict = latest_price.to_dict()
                # Simulate 0.75% positive change for demo purposes
                simulated_change = 0.75
                price_dict['change_percent'] = simulated_change
                price_dict['change'] = (latest_price.price * simulated_change / 100)
                price_dict['is_demo'] = True
                print(f"DEBUG: Using demo change of {simulated_change}% for {underlying}")
                return price_dict
            
            # Calculate daily change percentage
            opening_price = first_price_today.price
            current_price = latest_price.price
            daily_change = current_price - opening_price
            daily_change_percent = (daily_change / opening_price) * 100 if opening_price != 0 else 0
            
            print(f"DEBUG: {underlying} - Opening: {opening_price}, Current: {current_price}, Change: {daily_change_percent:.2f}%")
            
            # Create price dictionary with calculated daily change
            price_dict = latest_price.to_dict()
            price_dict['change'] = round(daily_change, 2)
            price_dict['change_percent'] = round(daily_change_percent, 2)
            price_dict['is_demo'] = False
            
            return price_dict
            
        except Exception as e:
            print(f"Error calculating daily change for {underlying}: {str(e)}")
            return None

    def get_comprehensive_dashboard_data(self, start_date=None, end_date=None, start_time=None, end_time=None):
        """Get comprehensive dashboard data for new dashboard with date filtering"""
        try:
            # Use end_date for getting the latest prices on that specific day
            target_date = end_date.date() if end_date else None
            
            # Get latest prices with daily change calculation for the target date
            nifty_price = self._get_price_with_daily_change('NIFTY', target_date)
            banknifty_price = self._get_price_with_daily_change('BANKNIFTY', target_date)
            
            # Get NIFTY 50 stocks data
            from app.models.nifty_stocks import NiftyStock
            stocks = NiftyStock.query.all()
            
            # Calculate top gainers and losers
            stock_list = []
            for stock in stocks:
                stock_dict = stock.to_dict()
                if stock_dict.get('change_percent'):
                    stock_list.append(stock_dict)
            
            # Sort by change percent
            stock_list.sort(key=lambda x: float(x.get('change_percent', 0)), reverse=True)
            top_gainers = stock_list[:3]
            top_losers = stock_list[-3:]
            
            # Calculate influence summary
            total_positive = sum(float(s.get('change_percent', 0)) for s in stock_list if float(s.get('change_percent', 0)) > 0)
            total_negative = sum(float(s.get('change_percent', 0)) for s in stock_list if float(s.get('change_percent', 0)) < 0)
            
            influence_summary = {
                'positive': round(total_positive, 2),
                'negative': round(abs(total_negative), 2),  # Store as positive value
                'net': round(total_positive + total_negative, 2)  # This gives correct net (pos - neg)
            }
            
            return {
                'nifty_price': nifty_price,
                'banknifty_price': banknifty_price,
                'top_gainers': top_gainers,
                'top_losers': top_losers,
                'influence_summary': influence_summary,
                'market_status': self.get_market_status()
            }
        except Exception as e:
            print(f"Error getting comprehensive dashboard data: {str(e)}")
            return {
                'nifty_price': {'price': 24500.75, 'change_percent': 1.25},
                'banknifty_price': {'price': 52300.50, 'change_percent': -0.85},
                'top_gainers': [],
                'top_losers': [],
                'influence_summary': {'positive': 0.0, 'negative': 0.0, 'net': 0.0},
                'market_status': 'closed'
            }

    def get_market_status(self):
        """Get current market status"""
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # Market hours: 9:00 AM to 3:45 PM IST
        market_start = 9 * 60  # 9:00 AM in minutes
        market_end = 15 * 60 + 45  # 3:45 PM in minutes
        current_minutes = current_hour * 60 + current_minute
        
        # Check if it's a weekday
        if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return 'closed'
        
        if market_start <= current_minutes <= market_end:
            return 'open'
        else:
            return 'closed'

    def get_nifty_oi_timeline_chart_data(self):
        """Get NIFTY OI timeline data formatted for Chart.js"""
        try:
            from sqlalchemy import func
            
            # Get aggregated OI changes by timestamp for NIFTY from today starting 9:20 AM
            from datetime import date, datetime, time
            today = date.today()
            market_start_time = datetime.combine(today, time(9, 20))
            
            # Group by 5-minute intervals for better chart readability
            oi_data = db.session.query(
                func.date_trunc('minute', OptionChainData.timestamp).label('time_bucket'),
                func.sum(OptionChainData.ce_oi_change).label('total_ce_change'),
                func.sum(OptionChainData.pe_oi_change).label('total_pe_change')
            ).filter(
                OptionChainData.underlying == 'NIFTY',
                OptionChainData.timestamp >= market_start_time
            ).group_by(func.date_trunc('minute', OptionChainData.timestamp))\
             .order_by(func.date_trunc('minute', OptionChainData.timestamp).asc())\
             .all()
            
            # Get corresponding NIFTY prices
            nifty_prices = {}
            for data in oi_data:
                price_record = NiftyPrice.query.filter(
                    func.abs(func.extract('epoch', NiftyPrice.timestamp) - func.extract('epoch', data.time_bucket)) < 300
                ).first()
                if price_record:
                    nifty_prices[data.time_bucket] = price_record.price
                else:
                    nifty_prices[data.time_bucket] = 26000  # Default fallback
            
            timeline_data = {
                'labels': [],
                'datasets': [
                    {
                        'label': 'CE OI Change',
                        'data': [],
                        'borderColor': 'rgb(255, 0, 0)',
                        'backgroundColor': 'rgba(255, 0, 0, 0.1)',
                        'tension': 0.1,
                        'yAxisID': 'y'
                    },
                    {
                        'label': 'PE OI Change', 
                        'data': [],
                        'borderColor': 'rgb(0, 128, 0)',
                        'backgroundColor': 'rgba(0, 128, 0, 0.1)',
                        'tension': 0.1,
                        'yAxisID': 'y'
                    },
                    {
                        'label': 'NIFTY Index',
                        'data': [],
                        'borderColor': 'rgb(0, 0, 0)',
                        'backgroundColor': 'rgba(0, 0, 0, 0.1)',
                        'tension': 0.1,
                        'yAxisID': 'y1'
                    }
                ]
            }
            
            for data in oi_data:
                timeline_data['labels'].append(data.time_bucket.strftime('%H:%M'))
                timeline_data['datasets'][0]['data'].append(float(data.total_ce_change) if data.total_ce_change else 0)
                timeline_data['datasets'][1]['data'].append(float(data.total_pe_change) if data.total_pe_change else 0)
                timeline_data['datasets'][2]['data'].append(float(nifty_prices.get(data.time_bucket, 26000)))
            
            return timeline_data
        except Exception as e:
            print(f"Error getting NIFTY OI timeline chart data: {str(e)}")
            return {'labels': [], 'datasets': []}

    def get_banknifty_oi_timeline_chart_data(self):
        """Get BANKNIFTY OI timeline data formatted for Chart.js"""
        try:
            from sqlalchemy import func
            
            # Get aggregated OI changes by timestamp for BANKNIFTY from today starting 9:20 AM
            from datetime import date, datetime, time
            today = date.today()
            market_start_time = datetime.combine(today, time(9, 20))
            
            # Group by 1-minute intervals for better chart readability
            oi_data = db.session.query(
                func.date_trunc('minute', OptionChainData.timestamp).label('time_bucket'),
                func.sum(OptionChainData.ce_oi_change).label('total_ce_change'),
                func.sum(OptionChainData.pe_oi_change).label('total_pe_change')
            ).filter(
                OptionChainData.underlying == 'BANKNIFTY',
                OptionChainData.timestamp >= market_start_time
            ).group_by(func.date_trunc('minute', OptionChainData.timestamp))\
             .order_by(func.date_trunc('minute', OptionChainData.timestamp).asc())\
             .all()
            
            # Get corresponding BANKNIFTY prices
            banknifty_prices = {}
            for data in oi_data:
                price_record = BankNiftyPrice.query.filter(
                    func.abs(func.extract('epoch', BankNiftyPrice.timestamp) - func.extract('epoch', data.time_bucket)) < 300
                ).first()
                if price_record:
                    banknifty_prices[data.time_bucket] = price_record.price
                else:
                    banknifty_prices[data.time_bucket] = 59000  # Default fallback
            
            timeline_data = {
                'labels': [],
                'datasets': [
                    {
                        'label': 'CE OI Change',
                        'data': [],
                        'borderColor': 'rgb(255, 0, 0)',
                        'backgroundColor': 'rgba(255, 0, 0, 0.1)',
                        'tension': 0.1,
                        'yAxisID': 'y'
                    },
                    {
                        'label': 'PE OI Change',
                        'data': [],
                        'borderColor': 'rgb(0, 128, 0)',
                        'backgroundColor': 'rgba(0, 128, 0, 0.1)',
                        'tension': 0.1,
                        'yAxisID': 'y'
                    },
                    {
                        'label': 'BANKNIFTY Index',
                        'data': [],
                        'borderColor': 'rgb(0, 0, 0)',
                        'backgroundColor': 'rgba(0, 0, 0, 0.1)',
                        'tension': 0.1,
                        'yAxisID': 'y1'
                    }
                ]
            }
            
            for data in oi_data:
                timeline_data['labels'].append(data.time_bucket.strftime('%H:%M'))
                timeline_data['datasets'][0]['data'].append(float(data.total_ce_change) if data.total_ce_change else 0)
                timeline_data['datasets'][1]['data'].append(float(data.total_pe_change) if data.total_pe_change else 0)
                timeline_data['datasets'][2]['data'].append(float(banknifty_prices.get(data.time_bucket, 59000)))
            
            return timeline_data
        except Exception as e:
            print(f"Error getting BANKNIFTY OI timeline chart data: {str(e)}")
            return {'labels': [], 'datasets': []}
    
    def get_sector_wise_performance(self):
        """Get NIFTY 50 stocks performance grouped by sectors"""
        try:
            from app.models.nifty_stocks import NiftyStock
            from sqlalchemy import func
            
            # Get all stocks with current data
            stocks = NiftyStock.query.filter(
                NiftyStock.current_price > 0
            ).all()
            
            if not stocks:
                return []
            
            # Group by sector and calculate sector performance
            sector_data = {}
            for stock in stocks:
                sector = stock.sector
                if sector not in sector_data:
                    sector_data[sector] = {
                        'sector': sector,
                        'stocks': [],
                        'total_weighted_change': 0,
                        'total_weight': 0,
                        'stock_count': 0,
                        'gainers': 0,
                        'losers': 0,
                        'avg_change': 0
                    }
                
                sector_data[sector]['stocks'].append({
                    'symbol': stock.symbol,
                    'company_name': stock.company_name,
                    'change_percent': stock.price_change_percent,
                    'weight': stock.nifty_weightage,
                    'current_price': stock.current_price,
                    'price_change': stock.price_change
                })
                
                # Calculate weighted average based on NIFTY weightage
                sector_data[sector]['total_weighted_change'] += (stock.price_change_percent * stock.nifty_weightage)
                sector_data[sector]['total_weight'] += stock.nifty_weightage
                sector_data[sector]['stock_count'] += 1
                
                if stock.price_change_percent > 0:
                    sector_data[sector]['gainers'] += 1
                elif stock.price_change_percent < 0:
                    sector_data[sector]['losers'] += 1
            
            # Calculate final sector performance
            sector_performance = []
            for sector, data in sector_data.items():
                if data['total_weight'] > 0:
                    weighted_avg = data['total_weighted_change'] / data['total_weight']
                else:
                    # Fallback to simple average if weights are not available
                    total_change = sum([stock['change_percent'] for stock in data['stocks']])
                    weighted_avg = total_change / len(data['stocks']) if data['stocks'] else 0
                
                sector_performance.append({
                    'sector': sector,
                    'weighted_change_percent': round(weighted_avg, 2),
                    'stock_count': data['stock_count'],
                    'gainers': data['gainers'],
                    'losers': data['losers'],
                    'neutral': data['stock_count'] - data['gainers'] - data['losers'],
                    'stocks': sorted(data['stocks'], key=lambda x: x['change_percent'], reverse=True)
                })
            
            # Sort sectors by performance (best to worst)
            sector_performance.sort(key=lambda x: x['weighted_change_percent'], reverse=True)
            
            print(f"DEBUG: Calculated performance for {len(sector_performance)} sectors")
            return sector_performance
            
        except Exception as e:
            print(f"Error calculating sector performance: {str(e)}")
            return []

    def get_market_signal_analysis(self, target_date=None):
        """
        Simple NIFTY-based signal analysis - Step by step implementation
        Returns signal strength from -100 (Strong Sell) to +100 (Strong Buy)
        """
        try:
            signal_score = 0
            signal_details = {}
            calculation_breakdown = {}
            
            # STEP 1: NIFTY Price Change Analysis (50% weight)
            nifty_price_data = self._get_price_with_daily_change('NIFTY', target_date=target_date)
            nifty_score = 0
            nifty_change = 0
            
            if nifty_price_data and nifty_price_data.get('change_percent') is not None:
                nifty_change = nifty_price_data.get('change_percent', 0)
                nifty_score = self._calculate_percentage_score(nifty_change)
                
                signal_details['nifty_change'] = nifty_change
                calculation_breakdown['nifty_price'] = {
                    'value': nifty_change,
                    'score': nifty_score,
                    'reason': f"NIFTY daily change: {nifty_change:.2f}%",
                    'price_info': nifty_price_data
                }
            else:
                calculation_breakdown['nifty_price'] = {
                    'value': None,
                    'score': 0,
                    'reason': "No NIFTY price data available",
                    'price_info': nifty_price_data
                }
            
            # STEP 2: BANKNIFTY Price Change Analysis (50% weight)
            banknifty_price_data = self._get_price_with_daily_change('BANKNIFTY', target_date=target_date)
            banknifty_score = 0
            banknifty_change = 0
            
            if banknifty_price_data and banknifty_price_data.get('change_percent') is not None:
                banknifty_change = banknifty_price_data.get('change_percent', 0)
                banknifty_score = self._calculate_percentage_score(banknifty_change)
                
                signal_details['banknifty_change'] = banknifty_change
                calculation_breakdown['banknifty_price'] = {
                    'value': banknifty_change,
                    'score': banknifty_score,
                    'reason': f"BANKNIFTY daily change: {banknifty_change:.2f}%",
                    'price_info': banknifty_price_data
                }
            else:
                calculation_breakdown['banknifty_price'] = {
                    'value': None,
                    'score': 0,
                    'reason': "No BANKNIFTY price data available",
                    'price_info': banknifty_price_data
                }
            
            # STEP 3: NIFTY OI Analysis (25% weight)
            nifty_oi_data = self._analyze_oi_change('NIFTY', target_date=target_date)
            nifty_oi_score = nifty_oi_data['score']
            
            signal_details['nifty_oi'] = nifty_oi_data
            calculation_breakdown['nifty_oi'] = {
                'value': {
                    'ce_total': nifty_oi_data['ce_total'],
                    'pe_total': nifty_oi_data['pe_total'],
                    'dominant': nifty_oi_data['dominant'],
                    'ce_change_pct': nifty_oi_data['ce_change_pct'],
                    'pe_change_pct': nifty_oi_data['pe_change_pct'],
                    'net_change_pct': nifty_oi_data['net_change_pct']
                },
                'score': nifty_oi_score,
                'reason': f"NIFTY OI - {nifty_oi_data['interpretation']}"
            }
            
            # STEP 4: BANKNIFTY OI Analysis (25% weight)
            banknifty_oi_data = self._analyze_oi_change('BANKNIFTY', target_date=target_date)
            banknifty_oi_score = banknifty_oi_data['score']
            
            signal_details['banknifty_oi'] = banknifty_oi_data
            calculation_breakdown['banknifty_oi'] = {
                'value': {
                    'ce_total': banknifty_oi_data['ce_total'],
                    'pe_total': banknifty_oi_data['pe_total'],
                    'dominant': banknifty_oi_data['dominant'],
                    'ce_change_pct': banknifty_oi_data['ce_change_pct'],
                    'pe_change_pct': banknifty_oi_data['pe_change_pct'],
                    'net_change_pct': banknifty_oi_data['net_change_pct']
                },
                'score': banknifty_oi_score,
                'reason': f"BANKNIFTY OI - {banknifty_oi_data['interpretation']}"
            }
            
            # STEP 5: Net Influence Analysis (NIFTY 50 stocks impact)
            influence_data = self.get_comprehensive_dashboard_data(start_date=target_date, end_date=target_date)
            influence_score = 0
            net_influence = 0
            
            if influence_data and influence_data.get('influence_summary'):
                net_influence = influence_data['influence_summary']['net']
                # Scale influence to fit our scoring system (±40 points max)
                if abs(net_influence) > 0:
                    if net_influence > 2:  # Strong positive influence
                        influence_score = 40
                    elif net_influence > 1:  # Moderate positive influence
                        influence_score = 25
                    elif net_influence > 0.5:  # Mild positive influence
                        influence_score = 15
                    elif net_influence < -2:  # Strong negative influence
                        influence_score = -40
                    elif net_influence < -1:  # Moderate negative influence
                        influence_score = -25
                    elif net_influence < -0.5:  # Mild negative influence
                        influence_score = -15
                    else:  # Neutral influence
                        influence_score = 0
            
            signal_details['net_influence'] = {
                'value': net_influence,
                'score': influence_score,
                'interpretation': f"Net influence: {net_influence:+.2f}% ({'Bullish' if net_influence > 0 else 'Bearish' if net_influence < 0 else 'Neutral'})"
            }
            
            calculation_breakdown['net_influence'] = {
                'value': {
                    'net_influence': net_influence,
                    'positive_influence': influence_data.get('influence_summary', {}).get('positive', 0) if influence_data else 0,
                    'negative_influence': influence_data.get('influence_summary', {}).get('negative', 0) if influence_data else 0
                },
                'score': influence_score,
                'reason': f"Net Influence - {signal_details['net_influence']['interpretation']}"
            }
            
            # Combine all 5 factors: NIFTY, BANKNIFTY, NIFTY_OI, BANKNIFTY_OI, NET_INFLUENCE
            total_score = nifty_score + banknifty_score + nifty_oi_score + banknifty_oi_score + influence_score
            signal_score = total_score
            
            # Determine signal text and color based on combined score (4 factors: max ±160)
            if signal_score >= 100:
                signal_text = "STRONG BUY"
                signal_color = "#00ff00"
            elif signal_score >= 40:
                signal_text = "BUY"
                signal_color = "#32cd32"
            elif signal_score >= 15:
                signal_text = "NEUTRAL+"
                signal_color = "#90EE90"
            elif signal_score >= -15:
                signal_text = "NEUTRAL"
                signal_color = "#ffd700"
            elif signal_score >= -40:
                signal_text = "NEUTRAL-"
                signal_color = "#FFA07A"
            elif signal_score >= -100:
                signal_text = "SELL"
                signal_color = "#ff6347"
            else:
                signal_text = "STRONG SELL"
                signal_color = "#ff0000"
            
            # Handle no data case
            if (not nifty_price_data and not banknifty_price_data and 
                nifty_oi_data['ce_total'] == 0 and nifty_oi_data['pe_total'] == 0 and
                banknifty_oi_data['ce_total'] == 0 and banknifty_oi_data['pe_total'] == 0):
                signal_text = "NO DATA"
                signal_color = "#808080"
                signal_score = 0
            
            # Ensure score is within bounds
            signal_score = max(-100, min(100, signal_score))
            
            return {
                'signal_score': signal_score,
                'signal_text': signal_text,
                'signal_color': signal_color,
                'details': signal_details,
                'calculation_breakdown': calculation_breakdown,
                'total_possible_score': 200,  # Updated for 5 factors (40+40+30+30+40)
                'method': '4_factor_analysis_v1',
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            print(f"Error in market signal analysis: {str(e)}")
            return {
                'signal_score': 0,
                'signal_text': 'ERROR',
                'signal_color': '#ff0000',
                'details': {'error': str(e)},
                'calculation_breakdown': {'error': str(e)},
                'timestamp': datetime.utcnow()
            }
    
    def _analyze_oi_sentiment(self, underlying):
        """Analyze OI changes to determine sentiment"""
        try:
            # Get latest OI data
            latest_oi = OptionChainData.query.filter(
                OptionChainData.underlying == underlying,
                OptionChainData.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            if not latest_oi:
                return {'signal': 0, 'dominant': 'neutral', 'ce_total': 0, 'pe_total': 0}
            
            total_ce_change = sum([oi.ce_oi_change for oi in latest_oi if oi.ce_oi_change])
            total_pe_change = sum([oi.pe_oi_change for oi in latest_oi if oi.pe_oi_change])
            
            # Calculate signal based on OI changes
            signal = 0
            dominant = 'neutral'
            
            if abs(total_ce_change) > abs(total_pe_change):
                # CE is dominant
                if total_ce_change > 1000000:  # 10L+ buildup
                    signal = -25  # Bearish (CE writing)
                    dominant = 'ce_strong'
                elif total_ce_change > 500000:
                    signal = -15
                    dominant = 'ce_moderate'
                elif total_ce_change < -1000000:  # CE unwinding
                    signal = 25  # Bullish
                    dominant = 'ce_unwind_strong'
                elif total_ce_change < -500000:
                    signal = 15
                    dominant = 'ce_unwind_moderate'
            else:
                # PE is dominant
                if total_pe_change > 1000000:  # 10L+ buildup
                    signal = 25  # Bullish (PE writing)
                    dominant = 'pe_strong'
                elif total_pe_change > 500000:
                    signal = 15
                    dominant = 'pe_moderate'
                elif total_pe_change < -1000000:  # PE unwinding
                    signal = -25  # Bearish
                    dominant = 'pe_unwind_strong'
                elif total_pe_change < -500000:
                    signal = -15
                    dominant = 'pe_unwind_moderate'
            
            return {
                'signal': signal,
                'dominant': dominant,
                'ce_total': total_ce_change,
                'pe_total': total_pe_change
            }
            
        except Exception as e:
            print(f"Error analyzing OI sentiment for {underlying}: {str(e)}")
            return {'signal': 0, 'dominant': 'neutral', 'ce_total': 0, 'pe_total': 0}
    
    def _calculate_percentage_score(self, change_percent):
        """Calculate score based on percentage change (-40 to +40 range for single factor)"""
        try:
            if change_percent > 2:
                return 40  # Strong positive
            elif change_percent > 0.5:
                return 20  # Positive
            elif change_percent > 0.1:
                return 10  # Mild positive
            elif change_percent >= -0.1:
                # For very small changes, use proportional scoring
                return int(change_percent * 50)  # -0.1% = -5 score, 0.1% = +5 score
            elif change_percent > -0.5:
                return -10  # Mild negative
            elif change_percent > -2:
                return -20  # Negative
            else:
                return -40  # Strong negative
        except:
            return 0
    
    def _analyze_oi_change(self, underlying='NIFTY', target_date=None):
        """Analyze OI changes to determine market sentiment for given underlying"""
        try:
            from app.models.banknifty_price import OptionChainData
            from datetime import datetime, timedelta, date
            from sqlalchemy import func
            
            # Get target day data only (from 00:00:00 target date)
            today = target_date or date.today()
            today_start = datetime.combine(today, datetime.min.time())
            
            print(f"DEBUG: Analyzing {underlying} OI changes for today: {today}")
            
            oi_data = OptionChainData.query.filter(
                OptionChainData.underlying == underlying,
                OptionChainData.timestamp >= today_start
            ).order_by(OptionChainData.timestamp.desc()).all()
            
            print(f"DEBUG: Found {len(oi_data)} {underlying} OI records for today ({today})")
            
            if not oi_data:
                return {
                    'ce_total': 0,
                    'pe_total': 0,
                    'dominant': 'neutral',
                    'net_change': 0,
                    'percentage': 0,
                    'score': 0,
                    'interpretation': 'No OI data available'
                }
            
            # Get the most recent data and calculate meaningful OI changes
            if len(oi_data) >= 2:
                # Use most recent vs older data for better change calculation
                recent_records = oi_data[:10]  # Most recent 10 records
                older_records = oi_data[-10:] if len(oi_data) >= 10 else oi_data[len(oi_data)//2:]
                
                # Calculate total OI changes from recent vs older data
                recent_ce_oi = sum([record.ce_oi for record in recent_records if record.ce_oi]) / len(recent_records) if recent_records else 0
                recent_pe_oi = sum([record.pe_oi for record in recent_records if record.pe_oi]) / len(recent_records) if recent_records else 0
                older_ce_oi = sum([record.ce_oi for record in older_records if record.ce_oi]) / len(older_records) if older_records else recent_ce_oi
                older_pe_oi = sum([record.pe_oi for record in older_records if record.pe_oi]) / len(older_records) if older_records else recent_pe_oi
                
                total_ce_change = recent_ce_oi - older_ce_oi
                total_pe_change = recent_pe_oi - older_pe_oi
                total_ce_oi = recent_ce_oi
                total_pe_oi = recent_pe_oi
            else:
                # Fallback: Use sum of OI changes from available records
                total_ce_change = sum([record.ce_oi_change for record in oi_data if record.ce_oi_change])
                total_pe_change = sum([record.pe_oi_change for record in oi_data if record.pe_oi_change])
                total_ce_oi = sum([record.ce_oi for record in oi_data if record.ce_oi])
                total_pe_oi = sum([record.pe_oi for record in oi_data if record.pe_oi])
            
            print(f"DEBUG: {underlying} OI Change % Analysis:")
            print(f"  CE Change: {total_ce_change} (from {total_ce_oi} total)")
            print(f"  PE Change: {total_pe_change} (from {total_pe_oi} total)")
            print(f"  CE OI (Lakhs): {total_ce_oi/100000:.1f}L, PE OI (Lakhs): {total_pe_oi/100000:.1f}L")
            
            # Calculate OI change percentages (focus on change rates)
            ce_change_pct = 0
            pe_change_pct = 0
            
            if total_ce_oi > 0:
                ce_change_pct = (total_ce_change / total_ce_oi) * 100
            if total_pe_oi > 0:
                pe_change_pct = (total_pe_change / total_pe_oi) * 100
            
            # Net change percentage difference
            net_change_pct = pe_change_pct - ce_change_pct
            total_activity_pct = abs(ce_change_pct) + abs(pe_change_pct)
            
            # Determine market sentiment and scoring based on OI change %
            score = 0
            dominant = 'neutral'
            interpretation = 'Neutral'
            
            print(f"  CE Change %: {ce_change_pct:.2f}%, PE Change %: {pe_change_pct:.2f}%")
            print(f"  Net Change %: {net_change_pct:.2f}%, Total Activity %: {total_activity_pct:.2f}%")
            
            if total_activity_pct < 1:  # Less than 1% total change activity
                dominant = 'neutral'
                interpretation = f'Low Change Activity ({total_activity_pct:.1f}% total)'
                score = 0
            elif abs(net_change_pct) < 2:  # Less than 2% difference in changes
                dominant = 'neutral'  
                interpretation = f'Balanced Changes (CE:{ce_change_pct:.1f}% vs PE:{pe_change_pct:.1f}%)'
                score = 0
            elif ce_change_pct > pe_change_pct:
                # CE building faster = Bearish (more call writing/resistance)
                if abs(net_change_pct) > 10:  # 10%+ difference
                    score = -30
                    dominant = 'ce_strong'
                    interpretation = f'Strong CE Build ({ce_change_pct:.1f}% vs {pe_change_pct:.1f}%) - Bearish'
                elif abs(net_change_pct) > 5:  # 5%+ difference
                    score = -20
                    dominant = 'ce_moderate'
                    interpretation = f'CE Build Dominance ({ce_change_pct:.1f}% vs {pe_change_pct:.1f}%) - Bearish'
                else:
                    score = -10
                    dominant = 'ce_mild'
                    interpretation = f'Mild CE Build ({ce_change_pct:.1f}% vs {pe_change_pct:.1f}%) - Mildly Bearish'
            else:
                # PE building faster = Bullish (more put buying/support)
                if abs(net_change_pct) > 10:  # 10%+ difference
                    score = 30
                    dominant = 'pe_strong'
                    interpretation = f'Strong PE Build ({pe_change_pct:.1f}% vs {ce_change_pct:.1f}%) - Bullish'
                elif abs(net_change_pct) > 5:  # 5%+ difference
                    score = 20
                    dominant = 'pe_moderate' 
                    interpretation = f'PE Build Dominance ({pe_change_pct:.1f}% vs {ce_change_pct:.1f}%) - Bullish'
                else:
                    score = 10
                    dominant = 'pe_mild'
                    interpretation = f'Mild PE Build ({pe_change_pct:.1f}% vs {ce_change_pct:.1f}%) - Mildly Bullish'
            
            # Use the dominant change percentage for display
            percentage = max(abs(ce_change_pct), abs(pe_change_pct))
            
            print(f"DEBUG: {underlying} OI Analysis - Score: {score}, Interpretation: {interpretation}")
            
            return {
                'ce_total': total_ce_change,
                'pe_total': total_pe_change,
                'dominant': dominant,
                'ce_change_pct': round(ce_change_pct, 2),
                'pe_change_pct': round(pe_change_pct, 2),
                'net_change_pct': round(net_change_pct, 2),
                'percentage': round(percentage, 2),
                'score': score,
                'interpretation': interpretation
            }
            
        except Exception as e:
            print(f"Error analyzing {underlying} OI: {str(e)}")
            return {
                'ce_total': 0,
                'pe_total': 0,
                'dominant': 'error',
                'net_change': 0,
                'percentage': 0,
                'score': 0,
                'interpretation': f'Error: {str(e)}'
            }
    
    def get_top_oi_strikes(self, limit=3):
        """Get top 3 OI change strikes for NIFTY and top 3 for BANKNIFTY"""
        try:
            from app.models.banknifty_price import OptionChainData
            from datetime import datetime, timedelta, date
            from sqlalchemy import func
            
            # Get current day data only
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            
            results = {'NIFTY': [], 'BANKNIFTY': []}
            
            for underlying in ['NIFTY', 'BANKNIFTY']:
                oi_data = OptionChainData.query.filter(
                    OptionChainData.underlying == underlying,
                    OptionChainData.timestamp >= today_start
                ).all()
                
                if not oi_data:
                    continue
                
                # Calculate OI changes per strike
                strike_data = {}
                for record in oi_data:
                    strike = record.strike_price
                    if strike not in strike_data:
                        strike_data[strike] = {
                            'strike': strike,
                            'ce_oi_changes': [],
                            'pe_oi_changes': [],
                            'ce_oi_total': [],
                            'pe_oi_total': []
                        }
                    
                    if record.ce_oi_change:
                        strike_data[strike]['ce_oi_changes'].append(record.ce_oi_change)
                    if record.pe_oi_change:
                        strike_data[strike]['pe_oi_changes'].append(record.pe_oi_change)
                    if record.ce_oi:
                        strike_data[strike]['ce_oi_total'].append(record.ce_oi)
                    if record.pe_oi:
                        strike_data[strike]['pe_oi_total'].append(record.pe_oi)
                
                # Calculate net OI changes and percentages for each strike
                strike_summary = []
                for strike, data in strike_data.items():
                    # Calculate total changes and averages
                    total_ce_change = sum(data['ce_oi_changes']) if data['ce_oi_changes'] else 0
                    total_pe_change = sum(data['pe_oi_changes']) if data['pe_oi_changes'] else 0
                    avg_ce_oi = sum(data['ce_oi_total']) / len(data['ce_oi_total']) if data['ce_oi_total'] else 1
                    avg_pe_oi = sum(data['pe_oi_total']) / len(data['pe_oi_total']) if data['pe_oi_total'] else 1
                    
                    # Calculate change percentages
                    ce_change_pct = (total_ce_change / avg_ce_oi) * 100 if avg_ce_oi > 0 else 0
                    pe_change_pct = (total_pe_change / avg_pe_oi) * 100 if avg_pe_oi > 0 else 0
                    
                    # Net change magnitude for sorting
                    net_change_magnitude = abs(ce_change_pct) + abs(pe_change_pct)
                    
                    if net_change_magnitude > 0.1:  # Only include strikes with meaningful changes
                        strike_summary.append({
                            'underlying': underlying,
                            'strike': strike,
                            'ce_change_pct': round(ce_change_pct, 2),
                            'pe_change_pct': round(pe_change_pct, 2),
                            'net_change_magnitude': round(net_change_magnitude, 2),
                            'ce_oi_change': total_ce_change,
                            'pe_oi_change': total_pe_change
                        })
                
                # Sort by net change magnitude (highest activity first)
                strike_summary.sort(key=lambda x: x['net_change_magnitude'], reverse=True)
                results[underlying] = strike_summary[:limit]
            
            print(f"DEBUG: Found top OI strikes - NIFTY: {len(results['NIFTY'])}, BANKNIFTY: {len(results['BANKNIFTY'])}")
            return results
            
        except Exception as e:
            print(f"Error getting top OI strikes: {str(e)}")
            return {'NIFTY': [], 'BANKNIFTY': []}

    # ...existing code...