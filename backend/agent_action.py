# live_agent.py (formerly agent_action.py)

import pandas as pd
import pandas_ta as ta
import numpy as np
from sklearn.linear_model import LinearRegression
import logging
from datetime import datetime, timedelta
import configparser
from kiteconnect import KiteConnect, KiteTicker
import time
import warnings
import google.generativeai as genai
from itertools import combinations

# Import the DeterministicPatternDetector and AdvancedPatternAnalyzer from detector.py
from detector import DeterministicPatternDetector, MathematicalIndicators, AdvancedPatternAnalyzer
from business_analyzer import generate_business_analysis_for_symbol
from current_market_analyzer import generate_current_market_analysis
from volume_fibonacci_analyzer import generate_enhanced_current_market_analysis
from comprehensive_market_analyzer import generate_comprehensive_market_analysis

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


################################################################################
# COMPONENT 1: The Core Pivot Engine (Simplified for MTA's needs)
# Keeping this for the MultiTimeframeAnalyzer's general trendline detection,
# but AdvancedPatternAnalyzer will handle detailed pattern pivots.
################################################################################
class PivotEngine:
    """A purely mathematical engine to identify swing points for general trendline context."""
    @staticmethod
    def find_pivots(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        df['is_swing_high'] = False
        df['is_swing_low'] = False
        # Ensure 'high' and 'low' columns exist
        if 'high' not in df.columns or 'low' not in df.columns:
            logging.warning("DataFrame missing 'high' or 'low' columns for PivotEngine.")
            return df

        for i in range(n, len(df) - n):
            window = df.iloc[i-n:i+n+1]
            current_high = df.iloc[i]['high']
            current_low = df.iloc[i]['low']
            if current_high == window['high'].max():
                df.loc[df.index[i], 'is_swing_high'] = True
            if current_low == window['low'].min():
                df.loc[df.index[i], 'is_swing_low'] = True
        return df

################################################################################
# COMPONENT 2: The Multi-Timeframe Analyzer (Now more focused on basic TA and broad trendlines)
################################################################################
class MultiTimeframeAnalyzer:
    """Orchestrates analysis, including broad trendline search and standard indicators."""
    def __init__(self, daily_df: pd.DataFrame):
        self.timeframes = {}
        self._resample_data(daily_df)

    def _resample_data(self, daily_df: pd.DataFrame):
        if daily_df.empty:
            logging.warning("Daily DataFrame is empty, cannot resample.")
            return

        self.timeframes['daily'] = daily_df.copy()
        ohlc_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        
        # Ensure sufficient data for resampling
        if len(daily_df) >= 7: # At least one week of data
            self.timeframes['weekly'] = daily_df.resample('W').agg(ohlc_dict).dropna()
        else:
            self.timeframes['weekly'] = pd.DataFrame() # Empty if not enough data
            logging.debug("Not enough daily data for weekly resampling.")

        if len(daily_df) >= 30: # At least one month of data
            self.timeframes['monthly'] = daily_df.resample('M').agg(ohlc_dict).dropna()
        else:
            self.timeframes['monthly'] = pd.DataFrame() # Empty if not enough data
            logging.debug("Not enough daily data for monthly resampling.")
        
    def _analyze_rsi(self, df: pd.DataFrame):
        if len(df) < 14: return {'value': np.nan, 'status': "Not enough data"}
        rsi = df.ta.rsi(length=14).iloc[-1]
        status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
        return {'value': rsi, 'status': status}

    def _analyze_macd(self, df: pd.DataFrame):
        if len(df) < 34: return {'histogram': np.nan, 'crossover': "Not enough data"} # 26 (slow) + 9 (signal)
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        if macd.empty or len(macd) < 2: return {'histogram': np.nan, 'crossover': "Not enough data"}
        
        histogram = macd[f'MACDh_12_26_9'].iloc[-1]
        prev_histogram = macd[f'MACDh_12_26_9'].iloc[-2]
        crossover = "Bullish" if histogram > 0 and prev_histogram < 0 else "Bearish" if histogram < 0 and prev_histogram > 0 else "None"
        return {'histogram': histogram, 'crossover': crossover}

    def run_standard_analysis(self):
        """
        Runs analysis for standard TA indicators only. All complex pattern
        detection is now handled by AdvancedPatternAnalyzer.
        """
        all_results = {}
        for tf, df in self.timeframes.items():
            if not df.empty and len(df) > 35:
                all_results[tf] = {
                    'rsi': self._analyze_rsi(df),
                    'macd': self._analyze_macd(df),
                }
            else:
                all_results[tf] = {
                    'rsi': {'value': np.nan, 'status': "Not enough data"},
                    'macd': {'histogram': np.nan, 'crossover': "Not enough data"},
                }
        return all_results

################################################################################
# COMPONENT 3: The Gemini Narrative Engine
################################################################################
class GeminiNarrativeEngine:
    """Uses the Gemini API to translate mathematical evidence into analyst-speak."""
    def __init__(self):
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            gemini_api_key = config['GEMINI']['API_KEY']
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-pro')
        except Exception as e:
            logging.warning(f"Could not initialize Gemini Engine. Error: {e}")
            self.model = None

    def generate_narrative(self, symbol: str, timeframe: str, analysis_details: dict) -> str:
        if not self.model: return "Gemini Engine not available."

        advanced_analysis = analysis_details.get('advanced_patterns', {})
        
        # --- Prepare specific pattern narrative from the new AdvancedPatternAnalyzer results ---
        pattern_narrative_part = ""
        top_patterns = advanced_analysis.get('pattern_reliability', [])
        if top_patterns:
            top_pattern_info = top_patterns[0]
            pattern = top_pattern_info['pattern']
            reliability = top_pattern_info['reliability_score']
            bias = "bullish" if pattern.get('bullish') else "bearish" if pattern.get('bearish') else "neutral"

            pattern_narrative_part = f"A high-confidence **{pattern['type']}** pattern has been identified, which is a {bias} formation with a reliability score of {reliability:.1%}."
            if 'time_to_apex' in pattern:
                status = "is currently active and consolidating" if pattern.get('is_active') else "has likely completed its formation"
                pattern_narrative_part += f" This pattern {status}, with a potential breakout point projected in approximately {pattern['time_to_apex']:.0f} periods."
        else:
            pattern_narrative_part = "No distinct, mathematically robust chart patterns were detected with high confidence."

        # --- Prepare mathematical indicators narrative ---
        math_indicators = advanced_analysis.get('mathematical_indicators', {})
        hurst = math_indicators.get('hurst_exponent', 0.5)
        hurst_desc = "showing strong trending behavior" if hurst > 0.55 else "indicating a tendency for mean-reversion" if hurst < 0.45 else "suggesting a more random walk"

        math_indicators_narrative_part = f"From a quantitative perspective, the Hurst Exponent is {hurst:.3f}, {hurst_desc}."

        rsi_info = analysis_details.get('rsi', {})
        macd_info = analysis_details.get('macd', {})
        rsi_desc = f"RSI is currently at {rsi_info.get('value', 'N/A'):.2f}, indicating a {rsi_info.get('status', 'N/A')} condition."
        macd_desc = f"The MACD has registered a {macd_info.get('crossover', 'N/A')} crossover, signaling a recent shift in momentum."

        prompt = f"""
        You are a seasoned financial analyst writing a concise technical analysis report for {symbol} on the {timeframe.upper()} timeframe.
        Combine the provided objective data points into a coherent, one-paragraph narrative.
        Focus on the current market structure, momentum, and identified patterns.
        Do NOT use mathematical terms like 'slope' or 'intercept'. Use confident, direct language.

        Objective Evidence:
        - {rsi_desc}
        - {macd_desc}
        - {pattern_narrative_part}
        - {math_indicators_narrative_part}

        Based ONLY on this evidence, write a compelling technical report.
        """
        try:
            time.sleep(2) # Avoid hitting rate limits
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini API call failed for {symbol} ({timeframe}): {e}")
            return "Failed to generate narrative from Gemini API."
        
################################################################################
# COMPONENT 4: The Multi-Timeframe Decision Engine
################################################################################
class DecisionEngine:
    """Converges analysis and generates detailed reasoning using the Gemini Engine."""
    def __init__(self):
        self.narrative_engine = GeminiNarrativeEngine()

    def generate_recommendations(self, symbol: str, mta_results: dict, advanced_analysis_results: dict) -> dict:
        recommendations = {}
        for timeframe, mta_analysis in mta_results.items():
            score = 50  # Base neutral score
            
            full_analysis_details = {
                **mta_analysis,
                'advanced_patterns': advanced_analysis_results
            }

            # --- Score based on standard indicators ---
            if mta_analysis.get('macd', {}).get('crossover') == 'Bullish': score += 10
            elif mta_analysis.get('macd', {}).get('crossover') == 'Bearish': score -= 10
            
            if mta_analysis.get('rsi', {}).get('status') == 'Oversold': score += 8
            elif mta_analysis.get('rsi', {}).get('status') == 'Overbought': score -= 8

            # --- Score based on the new, reliable AdvancedPatternAnalyzer results ---
            top_patterns = advanced_analysis_results.get('pattern_reliability', [])
            if top_patterns:
                top_pattern_info = top_patterns[0]
                pattern = top_pattern_info['pattern']
                reliability = top_pattern_info['reliability_score']

                if reliability > 0.65:  # Only consider high-reliability patterns
                    bias_multiplier = 1 if pattern.get('bullish') else -1 if pattern.get('bearish') else 0
                    
                    # Active, consolidating patterns get a stronger score boost as a breakout is nearer
                    pattern_score_boost = 25 if pattern.get('is_active', False) else 15
                    score += pattern_score_boost * bias_multiplier

            narrative = self.narrative_engine.generate_narrative(symbol, timeframe, full_analysis_details)
            
            rec = "Hold"
            if score >= 70: rec = "Strong Buy"
            elif score >= 60: rec = "Buy"
            elif score <= 30: rec = "Strong Sell"
            elif score <= 40: rec = "Sell"

            recommendations[timeframe] = {
                'recommendation': rec,
                'confidence': int(max(0, min(100, score))),
                'narrative_reasoning': narrative,
                'details': full_analysis_details
            }
        return recommendations

################################################################################
# COMPONENT 5 & 6: Kite Connector and Main Agent
################################################################################
class LivePositionalAgent:
    """The main agent that orchestrates the advanced analysis and live monitoring."""
    def __init__(self):
        logging.info("Initializing Kite Connect API...")
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.api_key = config['KITE']['API_KEY']
        try:
            with open("access_token.txt", "r") as f:
                self.access_token = f.read().strip()
        except FileNotFoundError:
            logging.error("access_token.txt not found. Please run kite_authentication.py first.")
            raise
        self.kite_connect = KiteConnect(api_key=self.api_key)
        self.kite_connect.set_access_token(self.access_token)
        self.decision_engine = DecisionEngine()
        self.portfolio = {}
        self.analysis_results = {}
        self.token_to_symbol_map = {}
        self.instrument_map = self._get_instrument_map()
        
        logging.info("Initializing Kite Ticker (MCP)...")
        self.kws = KiteTicker(self.api_key, self.access_token)
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close

    def _get_instrument_map(self):
        logging.info("Fetching instrument list for NSE and BSE...")
        try:
            # *** MODIFICATION START ***
            # Fetch instruments from both NSE and BSE
            nse_instruments = self.kite_connect.instruments("NSE")
            bse_instruments = self.kite_connect.instruments("BSE")
            all_instruments = nse_instruments + bse_instruments
            
            # Filter for equity instruments ('EQ') from both exchanges
            instrument_map = {
                item['tradingsymbol']: item['instrument_token'] 
                for item in all_instruments 
                if item['instrument_type'] == 'EQ'
            }
            # *** MODIFICATION END ***
            
            self.token_to_symbol_map = {v: k for k, v in instrument_map.items()}
            logging.info(f"Loaded {len(instrument_map)} NSE & BSE equity instruments.")
            return instrument_map
        except Exception as e:
            logging.error(f"Failed to fetch instruments: {e}")
            return {}

    def _fetch_daily_data(self, instrument_token: int, num_years: int = 2) -> pd.DataFrame:
        to_date = datetime.now().date()
        from_date = to_date - timedelta(days=365 * num_years)
        logging.info(f"Fetching historical data for token {instrument_token} from {from_date} to {to_date}")
        try:
            records = self.kite_connect.historical_data(instrument_token, from_date, to_date, "day")
            df = pd.DataFrame(records)
            if df.empty:
                logging.warning(f"No historical data found for token {instrument_token}.")
                return pd.DataFrame()
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
        except Exception as e:
            logging.error(f"Error fetching historical data for token {instrument_token}: {e}")
            return pd.DataFrame()

    def _perform_initial_analysis(self):
        logging.info("--- Performing Initial Comprehensive Analysis for JSON Output ---")
        try:
            holdings = self.kite_connect.holdings()
        except Exception as e:
            logging.error(f"Could not fetch holdings: {e}. Please check Kite Connect access.")
            return

        for h in holdings:
            symbol = h['tradingsymbol']
            instrument_token = self.instrument_map.get(symbol)
            if instrument_token:
                self.portfolio[symbol] = {'quantity': h['quantity'], 'average_price': h['average_price']}
                df = self._fetch_daily_data(instrument_token)

                if df.empty or len(df) < 100:
                    logging.warning(f"Not enough data for {symbol} (<100 days). Skipping.")
                    continue

                # Run Multi-timeframe analysis first
                mta = MultiTimeframeAnalyzer(df)
                mta_results = mta.run_standard_analysis()

                # Run Advanced Pattern Analysis
                analyzer = AdvancedPatternAnalyzer(df)
                advanced_results = analyzer.comprehensive_analysis(symbol=symbol)
                
                # Generate final recommendations using DecisionEngine
                recommendations = self.decision_engine.generate_recommendations(
                    symbol, mta_results, advanced_results
                )
                
                # Generate COMPREHENSIVE market analysis (Trendlines + Patterns + Volume + Fibonacci)
                try:
                    current_analysis = generate_comprehensive_market_analysis(df, symbol, analysis_window=60)
                    
                    # Also generate business-focused analysis as secondary
                    try:
                        business_analysis = generate_business_analysis_for_symbol(df, symbol)
                    except Exception as e:
                        logging.warning(f"Business analysis failed for {symbol}: {e}")
                        business_analysis = None
                    
                    # Store current analysis as primary, others as secondary
                    self.analysis_results[symbol] = {
                        'current_analysis': current_analysis,  # PRIMARY - what's happening NOW
                        'traditional_analysis': recommendations,
                        'business_analysis': business_analysis
                    }
                    
                except Exception as e:
                    logging.error(f"Current market analysis failed for {symbol}: {e}")
                    # Fallback to business analysis if available, then traditional
                    try:
                        business_analysis = generate_business_analysis_for_symbol(df, symbol)
                        self.analysis_results[symbol] = {
                            'business_analysis': business_analysis,
                            'traditional_analysis': recommendations
                        }
                    except Exception as e2:
                        logging.error(f"All advanced analysis failed for {symbol}: {e2}")
                        self.analysis_results[symbol] = recommendations

    def on_ticks(self, ws, ticks):
        # Placeholder for real-time logic.
        # This is where you would update your data, run a quick pattern check,
        # and potentially generate real-time trade signals.
        # For this comprehensive initial analysis, we are leaving it empty for now.
        for tick in ticks:
            # print(f"LTP for {self.token_to_symbol_map.get(tick['instrument_token'])}: {tick['last_price']}")
            pass

    def on_connect(self, ws, response):
        logging.info("MCP WebSocket Connection Successful.")
        instrument_tokens = [self.instrument_map[s] for s in self.portfolio.keys() if s in self.instrument_map]
        if instrument_tokens:
            ws.subscribe(instrument_tokens)
            ws.set_mode(ws.MODE_LTP, instrument_tokens)
            logging.info(f"Subscribed to LTP for {len(instrument_tokens)} instruments.")
        else:
            logging.warning("No instruments to subscribe to for live monitoring.")

    def on_close(self, ws, code, reason):
        logging.error(f"MCP Connection closed: {code} - {reason}")

    def start(self):
        self._perform_initial_analysis()
        logging.info("--- Agent Startup Complete. Initial Analysis Report: ---")
        if not self.analysis_results:
            print("\nNo analysis results available. Check logs for errors or insufficient data.")
            return

        for symbol, analysis_data in self.analysis_results.items():
            port_info = self.portfolio.get(symbol, {})
            
            # Check if we have CURRENT analysis (new approach)
            if isinstance(analysis_data, dict) and 'current_analysis' in analysis_data:
                print(f"\n{'='*110}")
                print(f"🎯 COMPREHENSIVE MARKET ANALYSIS FOR: {symbol}")
                print(f"📈 TRENDLINES • 📊 CHART PATTERNS • 📊 VOLUME • 📐 FIBONACCI")
                print(f"{'='*110}")
                print(f"📊 PORTFOLIO: {port_info.get('quantity', 'N/A')} shares @ avg. ₹{port_info.get('average_price', 0):.2f}")
                
                current_analysis = analysis_data['current_analysis']
                
                # Print current market structure
                market_structure = current_analysis.get('current_market_structure', {})
                trend_info = market_structure.get('trend', {})
                price_action = market_structure.get('price_action', {})
                
                print(f"\n📈 CURRENT MARKET STATUS:")
                print(f"   Current Price: ₹{current_analysis['analysis_summary']['current_price']}")
                print(f"   Trend: {trend_info.get('direction', 'N/A')} ({trend_info.get('strength', 'N/A')})")
                print(f"   SMA 10: ₹{trend_info.get('sma_10', 'N/A')}  |  SMA 20: ₹{trend_info.get('sma_20', 'N/A')}")
                
                if price_action:
                    day_1 = price_action.get('1_day_change', {})
                    day_5 = price_action.get('5_day_change', {})
                    print(f"   1-Day Change: ₹{day_1.get('absolute', 'N/A')} ({day_1.get('percent', 'N/A')}%)")
                    print(f"   5-Day Change: ₹{day_5.get('absolute', 'N/A')} ({day_5.get('percent', 'N/A')}%)")
                
                # Print FORWARD-LOOKING TRENDLINES
                trendline_analysis = current_analysis.get('trendline_analysis', {})
                trendlines = trendline_analysis.get('trendlines', [])
                summary = trendline_analysis.get('trendline_summary', {})
                
                if trendlines:
                    print(f"\n📈 FORWARD-LOOKING TRENDLINES:")
                    print(f"   📊 Total: {summary.get('total_trendlines', 0)} | High Relevance: {summary.get('high_relevance_lines', 0)}")
                    
                    for i, tl in enumerate(trendlines[:4], 1):  # Top 4 most relevant trendlines
                        relevance = tl.get('trading_relevance', 'N/A')
                        relevance_icon = "🔥" if "High" in relevance else "⚡" if "Medium" in relevance else "💤"
                        
                        print(f"\n   {relevance_icon} #{i}: {tl.get('type', 'N/A')} - {tl.get('direction', 'N/A')} ({tl.get('strength', 'N/A')})")
                        print(f"       Current Level: ₹{tl.get('current_value', 'N/A')} ({tl.get('distance_percent', 'N/A')}% away)")
                        print(f"       Trading Relevance: {relevance}")
                        print(f"       Touches: {tl.get('touches', 'N/A')} | {tl.get('significance', 'N/A')}")
                        
                        # Show forward projections
                        projections = tl.get('forward_projections', {})
                        if projections:
                            print(f"       📅 FORWARD PROJECTIONS:")
                            print(f"         Tomorrow: ₹{projections.get('1_day_ahead', 'N/A')}")
                            print(f"         Next Week: ₹{projections.get('7_days_ahead', 'N/A')}")
                            print(f"         Next Month: ₹{projections.get('30_days_ahead', 'N/A')}")
                        
                        # Show days to intersection if calculated
                        days_to_intersection = tl.get('days_to_intersection')
                        if days_to_intersection is not None:
                            if days_to_intersection < 30:
                                print(f"       ⏰ Price-Trendline Intersection: ~{days_to_intersection} days")
                            
                        # Show recent touch point dates and prices
                        touch_points = tl.get('touch_points', [])
                        if touch_points:
                            print(f"       📍 Recent Touch Points:")
                            for j, touch in enumerate(touch_points[-2:], 1):  # Show last 2 touch points
                                print(f"         {touch.get('date', 'N/A')} at ₹{touch.get('price', 'N/A')}")
                
                # Print CHART PATTERNS with formation dates
                chart_patterns = current_analysis.get('chart_patterns', [])
                if chart_patterns:
                    print(f"\n📊 CHART PATTERNS ({len(chart_patterns)} found):")
                    for i, pattern in enumerate(chart_patterns[:3], 1):  # Top 3 patterns
                        print(f"\n   #{i}: {pattern.get('pattern_name', 'N/A')} ({pattern.get('pattern_type', 'N/A')})")
                        print(f"       Bias: {pattern.get('bias', 'N/A')}")
                        print(f"       Reliability: {pattern.get('reliability_score', 'N/A')}")
                        print(f"       Status: {pattern.get('status', 'N/A')}")
                        
                        # Show formation dates
                        if 'formation_start' in pattern:
                            print(f"       Formation: {pattern.get('formation_start', 'N/A')} - Present")
                        if 'analysis_date' in pattern:
                            print(f"       Analysis Date: {pattern.get('analysis_date', 'N/A')}")
                        if 'apex_date' in pattern:
                            print(f"       Expected Apex: {pattern.get('apex_date', 'N/A')}")
                        
                        # Show trading setup
                        setup = pattern.get('trading_setup', {})
                        if setup:
                            # For breakout setups
                            if 'entry_trigger' in setup:
                                print(f"       Entry: ₹{setup.get('entry_trigger', 'N/A')}")
                                print(f"       Target: ₹{setup.get('target_price', 'N/A')}")
                                print(f"       Stop: ₹{setup.get('stop_loss', 'N/A')}")
                            
                            # For triangle patterns with both scenarios
                            elif 'bullish_breakout' in setup:
                                bull_setup = setup['bullish_breakout']
                                bear_setup = setup.get('bearish_breakdown', {})
                                print(f"       Bullish Breakout: Entry ₹{bull_setup.get('entry_trigger', 'N/A')}, Target ₹{bull_setup.get('target_1', 'N/A')}")
                                if bear_setup:
                                    print(f"       Bearish Breakdown: Entry ₹{bear_setup.get('entry_trigger', 'N/A')}, Target ₹{bear_setup.get('target_1', 'N/A')}")
                        
                        # Show timeline if available
                        if 'timeline' in pattern:
                            print(f"       Timeline: {pattern['timeline']}")
                        elif 'time_to_apex_days' in pattern:
                            print(f"       Apex in: {pattern['time_to_apex_days']} days")
                
                # Print key levels with establishment dates
                key_levels = current_analysis.get('current_key_levels', {})
                resistance_levels = key_levels.get('current_resistance_levels', [])
                support_levels = key_levels.get('current_support_levels', [])
                
                if resistance_levels or support_levels:
                    print(f"\n🎯 KEY LEVELS (WITH DATES):")
                    if resistance_levels:
                        for j, resistance in enumerate(resistance_levels[:2], 1):  # Show top 2
                            print(f"       Resistance #{j}: ₹{resistance['price']} ({resistance['distance_percent']}% away)")
                            print(f"                       Type: {resistance.get('type', 'N/A')}")
                            if 'established_date' in resistance:
                                print(f"                       Established: {resistance['established_date']}")
                            if 'last_tested' in resistance:
                                print(f"                       Last Tested: {resistance['last_tested']}")
                    if support_levels:
                        for j, support in enumerate(support_levels[:2], 1):  # Show top 2
                            print(f"       Support #{j}: ₹{support['price']} ({support['distance_percent']}% away)")
                            print(f"                     Type: {support.get('type', 'N/A')}")
                            if 'established_date' in support:
                                print(f"                     Established: {support['established_date']}")
                            if 'last_tested' in support:
                                print(f"                     Last Tested: {support['last_tested']}")
                
                # Print forward-looking forecast with Fibonacci alignment
                forecast = current_analysis.get('forward_looking_forecast', {})
                forecast_summary = forecast.get('forecast_summary', {})
                scenarios = forecast.get('scenarios', [])
                
                if forecast_summary:
                    print(f"\n🔮 FORWARD-LOOKING FORECAST:")
                    print(f"       Analysis Date: {forecast_summary.get('analysis_date', 'N/A')}")
                    print(f"       Primary Bias: {forecast_summary.get('primary_bias', 'N/A')}")
                    print(f"       Forecast Horizon: {forecast_summary.get('forecast_horizon', 'N/A')}")
                    print(f"       Active Patterns: {forecast_summary.get('active_patterns_count', 0)}")
                
                if scenarios:
                    print(f"\n       SCENARIOS WITH FIBONACCI CONTEXT:")
                    for i, scenario in enumerate(scenarios[:2], 1):  # Top 2 scenarios
                        print(f"       #{i}: {scenario.get('scenario_name', 'N/A')} ({scenario.get('probability', 'N/A')})")
                        target_price = scenario.get('target_price', 0)
                        print(f"           Target: ₹{target_price} in {scenario.get('timeline', 'N/A')}")
                        
                        # Check if target aligns with Fibonacci levels
                        if fibonacci_analysis and key_levels:
                            for fib_level in key_levels:
                                fib_price = fib_level.get('price', 0)
                                if fib_price > 0 and abs(target_price - fib_price) / fib_price < 0.02:  # Within 2%
                                    print(f"           🎯 FIBONACCI ALIGNMENT: Near {fib_level.get('level', 'N/A')} at ₹{fib_price}")
                                    break
                        
                        print(f"           Trigger: {scenario.get('trigger_conditions', 'N/A')}")
                        if 'invalidation_level' in scenario:
                            print(f"           Stop/Invalid: ₹{scenario.get('invalidation_level', 'N/A')}")
                
                # Print immediate trading plan
                trading_plan = current_analysis.get('immediate_trading_plan', {})
                immediate_actions = trading_plan.get('immediate_actions', [])
                if immediate_actions:
                    print(f"\n📋 IMMEDIATE ACTIONS (NEXT 1-5 DAYS):")
                    for action in immediate_actions:
                        print(f"       {action.get('priority', 'N/A')}: {action.get('specific_action', 'N/A')}")
                        print(f"                    Timeline: {action.get('timeline', 'N/A')}")
                        if action.get('trigger_price'):
                            print(f"                    Watch Level: ₹{action.get('trigger_price')}")
                
                # Print position recommendation
                position_rec = trading_plan.get('position_recommendations', {})
                if position_rec:
                    print(f"\n💼 POSITION RECOMMENDATION:")
                    print(f"       Current Stance: {position_rec.get('current_stance', 'N/A')}")
                    print(f"       Position Sizing: {position_rec.get('position_sizing', 'N/A')}")
                    print(f"       Hold Period: {position_rec.get('hold_period', 'N/A')}")
                
                # Print VOLUME ANALYSIS
                volume_analysis = current_analysis.get('volume_analysis', {})
                if volume_analysis and 'error' not in volume_analysis:
                    print(f"\n📊 VOLUME ANALYSIS:")
                    print(f"       Current Volume: {volume_analysis.get('current_volume', 'N/A'):,} shares")
                    print(f"       Assessment: {volume_analysis.get('volume_assessment', 'N/A')}")
                    print(f"       Trend: {volume_analysis.get('volume_trend', 'N/A')}")
                    print(f"       Significance: {volume_analysis.get('significance', 'N/A')}")
                    print(f"       vs Average: {volume_analysis.get('volume_ratio', 'N/A')}x")
                
                # Show recent volume spikes with more details
                spikes = volume_analysis.get('recent_spikes', [])
                if spikes:
                    print(f"       Recent Volume Spikes ({len(spikes)} detected):")
                    for spike in spikes[:3]:  # Show top 3
                        print(f"         {spike.get('date', 'N/A')}: {spike.get('volume', 0):,} shares")
                        print(f"           {spike.get('multiple_of_average', 'N/A')}x average | Price: ₹{spike.get('price', 'N/A')}")
                        if 'z_score' in spike:
                            print(f"           Z-Score: {spike.get('z_score', 'N/A')} | {spike.get('significance', 'N/A')}")
                
                # Print COMPREHENSIVE FIBONACCI ANALYSIS
                fibonacci_analysis = current_analysis.get('fibonacci_analysis', {})
                if fibonacci_analysis and 'error' not in fibonacci_analysis:
                    fib_info = fibonacci_analysis.get('fibonacci_analysis', {})
                    key_levels = fibonacci_analysis.get('key_levels', [])
                    nearest_level = fibonacci_analysis.get('nearest_level', {})
                    
                    print(f"\n📐 TREND-BASED FIBONACCI ANALYSIS:")
                    
                    # Trend and method information
                    if fib_info:
                        current_price = current_analysis['analysis_summary']['current_price']
                        trend_direction = fib_info.get('trend_direction', 'N/A')
                        print(f"       Current Price: ₹{current_price}")
                        print(f"       Market Trend: {trend_direction.upper()}")
                        print(f"       Method: {fib_info.get('fibonacci_method', 'N/A')}")
                        print(f"       Detection: {fib_info.get('swing_detection', 'N/A')}")
                        
                        # Show the swing selection logic
                        swing_logic = fib_info.get('swing_selection_logic', 'N/A')
                        used_current = fib_info.get('used_current_date_as_swing', False)
                        print(f"\n       🔍 SWING SELECTION PROCESS:")
                        print(f"         {swing_logic}")
                        if used_current:
                            print(f"         ⭐ Current date used as swing point")
                        
                        # Show the 0% and 100% reference points
                        zero_ref = fib_info.get('zero_percent_reference', 'N/A')
                        hundred_ref = fib_info.get('hundred_percent_reference', 'N/A')
                        print(f"\n       🎯 FIBONACCI REFERENCE POINTS:")
                        print(f"         0% Level: {zero_ref}")
                        print(f"         100% Level: {hundred_ref}")
                        
                        swing_high = fib_info.get('recent_swing_high', {})
                        swing_low = fib_info.get('recent_swing_low', {})
                        if swing_high and swing_low:
                            print(f"\n       📊 SWING IDENTIFICATION:")
                            print(f"         📈 Swing High: ₹{swing_high.get('price', 'N/A')} on {swing_high.get('date', 'N/A')}")
                            print(f"         📉 Swing Low: ₹{swing_low.get('price', 'N/A')} on {swing_low.get('date', 'N/A')}")
                            
                            if trend_direction == "uptrend":
                                print(f"         🔄 UPTREND FIBONACCI: From Swing High → Down to Swing Low (0%)")
                            else:
                                print(f"         🔄 DOWNTREND FIBONACCI: From Swing Low → Up to Swing High (0%)")
                            
                            price_range = fib_info.get('price_range', 0)
                            if price_range:
                                swing_low_price = swing_low.get('price', 1)
                                swing_high_price = swing_high.get('price', 1)
                                percentage_move = (price_range / min(swing_low_price, swing_high_price)) * 100 if min(swing_low_price, swing_high_price) > 0 else 0
                                print(f"         Range Size: ₹{price_range} ({percentage_move:.1f}% total move)")
                                
                                # Show current price position within the range
                                if trend_direction == "uptrend" and swing_low_price > 0:
                                    current_position = (current_price - swing_low_price) / price_range * 100
                                    print(f"         Current Position: {current_position:.1f}% from swing low (uptrend reference)")
                                elif trend_direction == "downtrend" and swing_high_price > 0:
                                    current_position = (swing_high_price - current_price) / price_range * 100
                                    print(f"         Current Position: {current_position:.1f}% from swing high (downtrend reference)")
                    
                    # Current position relative to nearest Fibonacci level
                    if nearest_level:
                        print(f"\n       🎯 CURRENT POSITION:")
                        print(f"         Nearest Level: {nearest_level.get('level', 'N/A')}")
                        print(f"         Price: ₹{nearest_level.get('price', 'N/A')} ({nearest_level.get('distance_percent', 'N/A')}% away)")
                        print(f"         Significance: {nearest_level.get('significance', 'N/A')}")
                    
                    # All Fibonacci levels categorized
                    if key_levels:
                        retracements = [level for level in key_levels if 'Retracement' in level.get('level', '')]
                        extensions = [level for level in key_levels if 'Extension' in level.get('level', '')]
                        
                        if retracements:
                            if trend_direction == "uptrend":
                                print(f"\n       📊 FIBONACCI RETRACEMENTS (UPTREND - From High to Low):")
                                print(f"            💡 0% = Swing Low (end point), 100% = Swing High (start point)")
                                print(f"            💡 Higher % = Closer to swing high (resistance)")
                            else:
                                print(f"\n       📊 FIBONACCI RETRACEMENTS (DOWNTREND - From Low to High):")
                                print(f"            💡 0% = Swing High (end point), 100% = Swing Low (start point)")
                                print(f"            💡 Higher % = Closer to swing low (support)")
                            
                            for i, level in enumerate(retracements, 1):
                                distance = level.get('distance_percent', 0)
                                price = level.get('price', 0)
                                ratio = level.get('ratio', 0)
                                current_price_val = current_analysis['analysis_summary']['current_price']
                                
                                # Determine if level is above or below current price
                                position = "above" if price > current_price_val else "below"
                                
                                # Determine function based on trend and position
                                if trend_direction == "uptrend":
                                    if price > current_price_val:
                                        function = "resistance (pullback target)"
                                    else:
                                        function = "support (broken retracement)"
                                else:  # downtrend
                                    if price > current_price_val:
                                        function = "resistance (broken retracement)" 
                                    else:
                                        function = "support (bounce target)"
                                
                                print(f"         {i}. {level.get('level', 'N/A')} - ₹{price} ({distance:.1f}% {position})")
                                print(f"            Function: Acts as {function}")
                                print(f"            Significance: {level.get('significance', 'N/A')}")
                                
                                # Add trading context
                                if abs(distance) < 1.0:
                                    print(f"            🟡 VERY CLOSE - Watch for reaction")
                                elif abs(distance) < 3.0:
                                    print(f"            🟢 NEARBY - Key level to monitor")
                        
                        if extensions:
                            if trend_direction == "uptrend":
                                print(f"\n       🔽 FIBONACCI EXTENSIONS (UPTREND - Targets Below Swing Low):")
                                print(f"            💡 Extensions project below 0% level (swing low)")
                                print(f"            💡 Bearish targets if trend reverses or deep correction")
                            else:
                                print(f"\n       🚀 FIBONACCI EXTENSIONS (DOWNTREND - Targets Above Swing High):")
                                print(f"            💡 Extensions project above 0% level (swing high)")
                                print(f"            💡 Bullish targets if trend reverses or strong bounce")
                            
                            for i, level in enumerate(extensions, 1):
                                distance = level.get('distance_percent', 0)
                                price = level.get('price', 0)
                                current_price_val = current_analysis['analysis_summary']['current_price']
                                
                                # Determine if level is above or below current price
                                position = "above" if price > current_price_val else "below"
                                
                                print(f"         {i}. {level.get('level', 'N/A')} - ₹{price} ({distance:.1f}% {position})")
                                print(f"            {level.get('significance', 'N/A')}")
                                
                                # Add trading context for targets
                                if distance < 5.0:
                                    print(f"            🎯 NEAR-TERM TARGET - Achievable")
                                elif distance < 10.0:
                                    print(f"            🎯 MEDIUM-TERM TARGET - Reasonable")
                                elif distance < 20.0:
                                    print(f"            🎯 LONG-TERM TARGET - Ambitious")
                        
                        # Summary of actionable levels
                        close_levels = [level for level in key_levels if abs(level.get('distance_percent', 100)) < 3.0]
                        if close_levels:
                            print(f"\n       ⚡ IMMEDIATE FIBONACCI LEVELS TO WATCH:")
                            for level in close_levels:
                                distance = level.get('distance_percent', 0)
                                direction = "above" if distance > 0 else "below"
                                action = "resistance" if "Extension" in level.get('level', '') or distance > 0 else "support"
                                print(f"         ₹{level.get('price', 'N/A')} ({level.get('level', 'N/A')}) - {abs(distance):.1f}% {direction}")
                                print(f"         Expected to act as {action} - {level.get('significance', 'N/A')}")
                
                # Print TRADING OPPORTUNITIES
                opportunities = current_analysis.get('trading_opportunities', [])
                if opportunities:
                    print(f"\n🎯 TRADING OPPORTUNITIES ({len(opportunities)} found):")
                    for i, opp in enumerate(opportunities[:3], 1):  # Top 3 opportunities
                        print(f"\n   #{i}: {opp.get('type', 'N/A')} - {opp.get('pattern_name', opp.get('trendline_type', 'N/A'))}")
                        print(f"       Bias: {opp.get('bias', 'N/A')}")
                        print(f"       Reliability: {opp.get('reliability', 'N/A')}")
                        
                        # Show setup details
                        setup = opp.get('setup', {})
                        if setup:
                            if 'entry_trigger' in setup:
                                print(f"       Entry: ₹{setup.get('entry_trigger', 'N/A')}")
                                print(f"       Target: ₹{setup.get('target_price', 'N/A')}")
                                print(f"       Stop: ₹{setup.get('stop_loss', 'N/A')}")
                            elif 'bullish_breakout' in setup:
                                bull = setup['bullish_breakout']
                                print(f"       Bullish Entry: ₹{bull.get('entry_trigger', 'N/A')}, Target: ₹{bull.get('target_1', 'N/A')}")
                        
                        # Show confirmations with enhanced Fibonacci details
                        vol_conf = opp.get('volume_confirmation', 'N/A')
                        fib_conf = opp.get('fibonacci_confirmation', 'N/A')
                        if vol_conf != 'N/A':
                            print(f"       Volume: {vol_conf}")
                        if fib_conf != 'N/A':
                            print(f"       Fibonacci: {fib_conf}")
                            
                            # Show which specific Fibonacci levels support this opportunity
                            if 'setup' in opp and fibonacci_analysis and key_levels:
                                setup = opp['setup']
                                target_price = setup.get('target_price') or setup.get('target_1')
                                entry_price = setup.get('entry_trigger')
                                
                                if target_price:
                                    supporting_fibs = []
                                    for fib_level in key_levels:
                                        fib_price = fib_level.get('price', 0)
                                        # Check if target aligns with Fibonacci (within 3%)
                                        if abs(target_price - fib_price) / fib_price < 0.03:
                                            supporting_fibs.append(f"{fib_level.get('level', 'N/A')} (₹{fib_price})")
                                    
                                    if supporting_fibs:
                                        print(f"         🎯 Supporting Fib Levels: {', '.join(supporting_fibs)}")
                
                # Print RISK MANAGEMENT
                risk_mgmt = current_analysis.get('risk_management', {})
                if risk_mgmt:
                    stop_levels = risk_mgmt.get('stop_loss_levels', {})
                    if stop_levels:
                        print(f"\n🛡️ RISK MANAGEMENT:")
                        print(f"       Nearest Support: ₹{stop_levels.get('nearest_support', 'N/A')}")
                        print(f"       Nearest Resistance: ₹{stop_levels.get('nearest_resistance', 'N/A')}")
                        
                        pct_stops = stop_levels.get('percentage_stops', {})
                        if pct_stops:
                            print(f"       Conservative Stop: ₹{pct_stops.get('conservative', 'N/A')} (5%)")
                            print(f"       Moderate Stop: ₹{pct_stops.get('moderate', 'N/A')} (3%)")
            
            # Fallback to business analysis if current analysis not available
            elif isinstance(analysis_data, dict) and 'business_analysis' in analysis_data:
                print(f"\n{'='*80}")
                print(f"🎯 BUSINESS-FOCUSED ANALYSIS FOR: {symbol}")
                print(f"{'='*80}")
                print(f"📊 PORTFOLIO: {port_info.get('quantity', 'N/A')} shares @ avg. ₹{port_info.get('average_price', 0):.2f}")
                
                business_analysis = analysis_data['business_analysis']
                
                # Print analysis summary
                summary = business_analysis['analysis_summary']
                print(f"\n📈 CURRENT STATUS:")
                print(f"   Current Price: ₹{summary['current_price']}")
                print(f"   Market Sentiment: {summary['overall_market_sentiment']}")
                print(f"   Analysis Period: {summary['analysis_period']}")
                
                # Print key patterns with trading setups
                patterns = business_analysis.get('chart_patterns_identified', [])
                if patterns:
                    print(f"\n🎯 TOP TRADING OPPORTUNITIES:")
                    for i, pattern in enumerate(patterns[:2], 1):  # Top 2 patterns
                        print(f"\n   #{i}: {pattern['pattern_name']} ({pattern['expected_direction']})")
                        print(f"       Reliability: {pattern['reliability_score']}")
                        
                        setup = pattern.get('trading_setup', {})
                        entry = setup.get('entry_strategy', {})
                        targets = setup.get('price_targets', {})
                        risk = setup.get('risk_management', {})
                        
                        if entry:
                            print(f"       Entry: ₹{entry.get('trigger_price', 'N/A')} ({entry.get('trigger_reason', 'N/A')})")
                        if targets:
                            print(f"       Target: ₹{targets.get('primary_target', 'N/A')} ({targets.get('probability_of_reaching', 'N/A')})")
                        if risk:
                            print(f"       Stop Loss: ₹{risk.get('stop_loss', 'N/A')} (R:R = {risk.get('risk_reward_ratio', 'N/A')})")
                
                # Print key levels with dates
                key_levels = business_analysis.get('key_levels_identified', {})
                resistance_levels = key_levels.get('current_resistance_levels', [])
                support_levels = key_levels.get('current_support_levels', [])
                
                if resistance_levels or support_levels:
                    print(f"\n🎯 KEY LEVELS TO WATCH:")
                    if resistance_levels:
                        for j, resistance in enumerate(resistance_levels[:2], 1):  # Show top 2
                            print(f"       Resistance #{j}: ₹{resistance['price']} ({resistance['strength']})")
                            print(f"                       {resistance['description']}")
                            if 'established_date' in resistance:
                                print(f"                       Established: {resistance['established_date']}")
                            if 'last_tested' in resistance:
                                print(f"                       Last Tested: {resistance['last_tested']}")
                    if support_levels:
                        for j, support in enumerate(support_levels[:2], 1):  # Show top 2
                            print(f"       Support #{j}: ₹{support['price']} ({support['strength']})")
                            print(f"                     {support['description']}")
                            if 'established_date' in support:
                                print(f"                     Established: {support['established_date']}")
                            if 'last_tested' in support:
                                print(f"                     Last Tested: {support['last_tested']}")
                
                # Print business recommendations
                recommendations = business_analysis.get('business_recommendations', {})
                immediate_actions = recommendations.get('immediate_actions', [])
                if immediate_actions:
                    print(f"\n📋 IMMEDIATE ACTIONS:")
                    for action in immediate_actions[:2]:
                        print(f"       {action['priority']}: {action['action']}")
                        print(f"                    Timeline: {action['timeline']}")
                        print(f"                    Success Rate: {action['success_probability']}")
                
                # Print portfolio impact
                portfolio_impact = business_analysis.get('portfolio_impact_summary', {})
                if portfolio_impact:
                    print(f"\n💼 PORTFOLIO RECOMMENDATION:")
                    print(f"       Overall Bias: {portfolio_impact.get('overall_bias', 'N/A')}")
                    print(f"       Confidence: {portfolio_impact.get('confidence_level', 'N/A')}")
                    print(f"       Expected Return: {portfolio_impact.get('expected_return', 'N/A')}")
                    print(f"       Max Risk: {portfolio_impact.get('maximum_risk', 'N/A')}")
                    print(f"       Holding Period: {portfolio_impact.get('holding_period', 'N/A')}")
                
            else:
                # Fallback to traditional analysis display
                recommendations = analysis_data
                print(f"\n==================== TRADITIONAL ANALYSIS FOR: {symbol} ====================")
                print(f"  PORTFOLIO: {port_info.get('quantity', 'N/A')} shares @ avg. ₹{port_info.get('average_price', 0):.2f}")
                
                if not recommendations:
                    print(f"  No recommendations available for {symbol}.")
                    continue

                for timeframe, rec in recommendations.items():
                    if isinstance(rec, dict):
                        print(f"\n  --- {timeframe.upper()} TIMEFRAME ---")
                        print(f"    Recommendation: {rec.get('recommendation', 'N/A')} (Confidence: {rec.get('confidence', 0)}%)")
                        print(f"      Technical Summary (Powered by Gemini):")
                        narrative_lines = rec.get('narrative_reasoning', 'No narrative generated.').split('\n')
                        for line in narrative_lines:
                            if line.strip():
                                print(f"        {line.strip()}")

        if self.instrument_map: # Only connect if there are instruments to monitor
            self.kws.connect(threaded=True)
            logging.info("\n--- Agent is now monitoring live prices. Press Ctrl+C to stop. ---")
            while True:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    logging.info("Stopping agent...")
                    self.kws.close()
                    break
        else:
            logging.warning("No instruments to monitor, skipping live connection.")

if __name__ == "__main__":
    # Ensure you have a 'config.ini' file in the same directory with:
    # [KITE]
    # API_KEY = YOUR_KITE_API_KEY
    # [GEMINI]
    # API_KEY = YOUR_GEMINI_API_KEY
    # And an 'access_token.txt' generated by kite_authentication.py
    
    try:
        agent = LivePositionalAgent()
        agent.start()
    except Exception as e:
        logging.error(f"A critical error occurred on startup: {e}", exc_info=True)