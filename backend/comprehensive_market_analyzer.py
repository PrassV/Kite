import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta
from detector import NpEncoder, TrendlineEngine
import logging

class ComprehensiveMarketAnalyzer:
    """
    Complete market analyzer that combines:
    1. Trendlines (support/resistance identification)
    2. Chart Patterns (triangles, flags, H&S, etc.)
    3. Volume Analysis (confirmation and anomalies)
    4. Fibonacci Analysis (retracements and extensions)
    """
    
    def __init__(self, df, symbol="UNKNOWN", analysis_window=60):
        self.symbol = symbol
        self.analysis_window = analysis_window
        
        # Use full dataset but focus on recent window
        self.df = df.tail(analysis_window * 2)  # Extra buffer for calculations
        self.current_df = df.tail(analysis_window)  # Main analysis window
        
        self.current_price = df['close'].iloc[-1]
        self.current_date = df.index[-1]
        self.prices = df['close'].values
        self.high = df['high'].values
        self.low = df['low'].values
        self.volume = df['volume'].values if 'volume' in df.columns else None
        
        # Initialize components
        self._detect_peaks_valleys()
        
    def _detect_peaks_valleys(self):
        """Detect peaks and valleys for trendline and pattern analysis."""
        from scipy import signal
        
        # Use recent data for pivot detection
        recent_data = self.current_df.copy()
        
        # Gaussian smooth for better pivot detection
        from scipy.ndimage import gaussian_filter1d
        smoothed_high = gaussian_filter1d(recent_data['high'].values, sigma=1.5)
        smoothed_low = gaussian_filter1d(recent_data['low'].values, sigma=1.5)
        
        # Find peaks and valleys
        peak_indices, _ = signal.find_peaks(smoothed_high, distance=5, prominence=0.5)
        valley_indices, _ = signal.find_peaks(-smoothed_low, distance=5, prominence=0.5)
        
        # Convert to dictionary format
        self.peaks = []
        for idx in peak_indices:
            if idx < len(recent_data):
                self.peaks.append({
                    'index': idx,
                    'date': recent_data.index[idx],
                    'price': recent_data['high'].iloc[idx],
                    'type': 'high'
                })
        
        self.valleys = []
        for idx in valley_indices:
            if idx < len(recent_data):
                self.valleys.append({
                    'index': idx,
                    'date': recent_data.index[idx],
                    'price': recent_data['low'].iloc[idx],
                    'type': 'low'
                })
        
        # Sort by date
        self.peaks = sorted(self.peaks, key=lambda x: x['date'])
        self.valleys = sorted(self.valleys, key=lambda x: x['date'])
        
        logging.info(f"Detected {len(self.peaks)} peaks and {len(self.valleys)} valleys for {self.symbol}")
    
    def analyze_trendlines(self):
        """Forward-looking trendline analysis for current trading decisions."""
        
        if len(self.peaks) < 2 or len(self.valleys) < 2:
            return {"error": "Insufficient peaks/valleys for trendline analysis"}
        
        # Focus on RECENT swing points for forward-looking analysis
        lookback_days = 60  # Only consider swings from last 60 days
        recent_cutoff = self.current_df.index[-lookback_days] if len(self.current_df) >= lookback_days else self.current_df.index[0]
        
        recent_peaks = [p for p in self.peaks if p['date'] >= recent_cutoff]
        recent_valleys = [v for v in self.valleys if v['date'] >= recent_cutoff]
        
        if len(recent_peaks) < 2 or len(recent_valleys) < 2:
            # Fallback to all available data if insufficient recent swings
            recent_peaks = self.peaks[-4:] if len(self.peaks) >= 4 else self.peaks
            recent_valleys = self.valleys[-4:] if len(self.valleys) >= 4 else self.valleys
        
        # Use TrendlineEngine with recent swing points only
        trendline_engine = TrendlineEngine(recent_peaks, recent_valleys, self.current_df['close'].values)
        
        # Get best support and resistance lines (minimum 2 touches)
        resistance_lines = trendline_engine.find_best_trendlines(is_resistance=True, min_touches=2)
        support_lines = trendline_engine.find_best_trendlines(is_resistance=False, min_touches=2)
        
        trendlines = []
        current_date_index = len(self.current_df) - 1
        
        # Process resistance trendlines with forward-looking perspective
        for i, res_line in enumerate(resistance_lines[:3]):
            # Current trendline value (today)
            current_value = res_line['slope'] * current_date_index + res_line['intercept']
            
            # Future trendline values (1, 7, 30 days ahead)
            future_1d = res_line['slope'] * (current_date_index + 1) + res_line['intercept']
            future_7d = res_line['slope'] * (current_date_index + 7) + res_line['intercept']
            future_30d = res_line['slope'] * (current_date_index + 30) + res_line['intercept']
            
            touches = res_line['touches']
            direction = "Rising" if res_line['slope'] > 0 else "Falling" if res_line['slope'] < 0 else "Flat"
            
            # Calculate days until trendline intersects with current price (if trending toward price)
            days_to_intersection = None
            if abs(res_line['slope']) > 0.01:  # Avoid division by very small slopes
                intersection_x = (self.current_price - res_line['intercept']) / res_line['slope']
                days_to_intersection = max(0, int(intersection_x - current_date_index))
                if days_to_intersection > 365:  # Cap at 1 year
                    days_to_intersection = None
            
            # Determine relevance for trading (how soon will price interact with this trendline)
            distance_pct = abs(current_value - self.current_price) / self.current_price * 100
            if distance_pct <= 5.0:
                trading_relevance = "High - Price close to trendline"
            elif distance_pct <= 15.0:
                trading_relevance = "Medium - Trendline within reach"
            else:
                trading_relevance = "Low - Trendline distant from current price"
            
            trendlines.append({
                "trendline_id": f"RES_{i+1:02d}",
                "type": "Resistance",
                "direction": direction,
                "current_value": round(current_value, 2),
                "slope": round(res_line['slope'], 4),
                "touches": len(touches),
                "strength": "Strong" if len(touches) >= 3 else "Medium",
                "touch_points": [
                    {
                        "date": touch['date'].strftime("%Y-%m-%d"),
                        "price": round(touch['price'], 2)
                    } for touch in touches[:4]  # Recent touch points
                ],
                "distance_from_current": round(abs(current_value - self.current_price), 2),
                "distance_percent": round(distance_pct, 2),
                "trading_relevance": trading_relevance,
                "forward_projections": {
                    "1_day_ahead": round(future_1d, 2),
                    "7_days_ahead": round(future_7d, 2),
                    "30_days_ahead": round(future_30d, 2)
                },
                "days_to_intersection": days_to_intersection,
                "significance": f"{direction} resistance - {trading_relevance.split(' - ')[1]}"
            })
        
        # Process support trendlines with forward-looking perspective
        for i, sup_line in enumerate(support_lines[:3]):
            # Current trendline value (today)
            current_value = sup_line['slope'] * current_date_index + sup_line['intercept']
            
            # Future trendline values (1, 7, 30 days ahead)
            future_1d = sup_line['slope'] * (current_date_index + 1) + sup_line['intercept']
            future_7d = sup_line['slope'] * (current_date_index + 7) + sup_line['intercept']
            future_30d = sup_line['slope'] * (current_date_index + 30) + sup_line['intercept']
            
            touches = sup_line['touches']
            direction = "Rising" if sup_line['slope'] > 0 else "Falling" if sup_line['slope'] < 0 else "Flat"
            
            # Calculate days until trendline intersects with current price
            days_to_intersection = None
            if abs(sup_line['slope']) > 0.01:
                intersection_x = (self.current_price - sup_line['intercept']) / sup_line['slope']
                days_to_intersection = max(0, int(intersection_x - current_date_index))
                if days_to_intersection > 365:
                    days_to_intersection = None
            
            # Determine trading relevance
            distance_pct = abs(current_value - self.current_price) / self.current_price * 100
            if distance_pct <= 5.0:
                trading_relevance = "High - Price close to trendline"
            elif distance_pct <= 15.0:
                trading_relevance = "Medium - Trendline within reach"
            else:
                trading_relevance = "Low - Trendline distant from current price"
            
            trendlines.append({
                "trendline_id": f"SUP_{i+1:02d}",
                "type": "Support",
                "direction": direction,
                "current_value": round(current_value, 2),
                "slope": round(sup_line['slope'], 4),
                "touches": len(touches),
                "strength": "Strong" if len(touches) >= 3 else "Medium",
                "touch_points": [
                    {
                        "date": touch['date'].strftime("%Y-%m-%d"),
                        "price": round(touch['price'], 2)
                    } for touch in touches[:4]  # Recent touch points
                ],
                "distance_from_current": round(abs(current_value - self.current_price), 2),
                "distance_percent": round(distance_pct, 2),
                "trading_relevance": trading_relevance,
                "forward_projections": {
                    "1_day_ahead": round(future_1d, 2),
                    "7_days_ahead": round(future_7d, 2),
                    "30_days_ahead": round(future_30d, 2)
                },
                "days_to_intersection": days_to_intersection,
                "significance": f"{direction} support - {trading_relevance.split(' - ')[1]}"
            })
        
        # Sort by trading relevance (High first, then by proximity to current price)
        def sort_key(trendline):
            relevance_priority = {"High": 0, "Medium": 1, "Low": 2}
            return (relevance_priority.get(trendline['trading_relevance'].split(' - ')[0], 3), 
                   trendline['distance_percent'])
        
        trendlines = sorted(trendlines, key=sort_key)
        
        return {
            "trendlines": trendlines,
            "trendline_summary": {
                "total_trendlines": len(trendlines),
                "resistance_lines": len([t for t in trendlines if t['type'] == 'Resistance']),
                "support_lines": len([t for t in trendlines if t['type'] == 'Support']),
                "strong_lines": len([t for t in trendlines if t['strength'] == 'Strong']),
                "high_relevance_lines": len([t for t in trendlines if t['trading_relevance'].startswith('High')])
            }
        }
    
    def detect_chart_patterns(self):
        """Detect comprehensive chart patterns."""
        
        patterns = []
        
        # 1. Triangle Patterns
        triangle_patterns = self._detect_triangles()
        patterns.extend(triangle_patterns)
        
        # 2. Flag Patterns
        flag_patterns = self._detect_flags()
        patterns.extend(flag_patterns)
        
        # 3. Head and Shoulders
        hs_patterns = self._detect_head_shoulders()
        patterns.extend(hs_patterns)
        
        # 4. Double Top/Bottom
        double_patterns = self._detect_double_patterns()
        patterns.extend(double_patterns)
        
        # 5. Breakout/Breakdown setups
        breakout_patterns = self._detect_breakout_setups()
        patterns.extend(breakout_patterns)
        
        # Add pattern metadata
        for i, pattern in enumerate(patterns):
            pattern['pattern_id'] = f"PATTERN_{i+1:03d}"
            pattern['analysis_date'] = self.current_date.strftime("%Y-%m-%d")
            pattern['current_price'] = self.current_price
        
        return patterns
    
    def _detect_triangles(self):
        """Detect triangle patterns using trendline convergence."""
        
        if len(self.peaks) < 2 or len(self.valleys) < 2:
            return []
        
        patterns = []
        trendline_engine = TrendlineEngine(self.peaks, self.valleys, self.current_df['close'].values)
        
        # Get recent trendlines
        resistance_lines = trendline_engine.find_best_trendlines(is_resistance=True)
        support_lines = trendline_engine.find_best_trendlines(is_resistance=False)
        
        if not resistance_lines or not support_lines:
            return patterns
        
        # Check for triangle patterns
        for res_line in resistance_lines[:2]:
            for sup_line in support_lines[:2]:
                res_slope = res_line['slope']
                sup_slope = sup_line['slope']
                
                # Calculate convergence point (apex)
                if res_slope == sup_slope:
                    continue
                
                apex_x = (sup_line['intercept'] - res_line['intercept']) / (res_slope - sup_slope)
                apex_y = res_slope * apex_x + res_line['intercept']
                
                current_x = len(self.current_df) - 1
                time_to_apex = apex_x - current_x
                
                # Only consider patterns where apex is in the future (active patterns)
                if time_to_apex > 0 and time_to_apex < 30:  # Within 30 days
                    
                    # Classify triangle type
                    flat_tolerance = 0.1
                    
                    if abs(res_slope) < flat_tolerance and sup_slope > 0.1:
                        pattern_type = "Ascending Triangle"
                        bias = "Bullish"
                        reliability = 0.75
                    elif res_slope < -0.1 and abs(sup_slope) < flat_tolerance:
                        pattern_type = "Descending Triangle"
                        bias = "Bearish"
                        reliability = 0.72
                    elif res_slope < 0 and sup_slope > 0 and res_slope < sup_slope:
                        pattern_type = "Symmetrical Triangle"
                        bias = "Neutral (Direction depends on breakout)"
                        reliability = 0.68
                    else:
                        continue
                    
                    # Get all touch points
                    all_touches = res_line['touches'] + sup_line['touches']
                    start_date = min(touch['date'] for touch in all_touches)
                    
                    patterns.append({
                        'pattern_name': pattern_type,
                        'pattern_type': 'Triangle Pattern',
                        'bias': bias,
                        'reliability_score': reliability,
                        'status': 'Currently Active',
                        'formation_start': start_date.strftime("%Y-%m-%d"),
                        'apex_date': (self.current_date + timedelta(days=int(time_to_apex))).strftime("%Y-%m-%d"),
                        'time_to_apex_days': round(time_to_apex, 1),
                        'resistance_trendline': {
                            'slope': res_slope,
                            'current_value': res_slope * current_x + res_line['intercept'],
                            'touches': len(res_line['touches'])
                        },
                        'support_trendline': {
                            'slope': sup_slope,
                            'current_value': sup_slope * current_x + sup_line['intercept'],
                            'touches': len(sup_line['touches'])
                        },
                        'trading_setup': self._generate_triangle_trading_setup(pattern_type, res_line, sup_line, current_x),
                        'expected_direction': f"Breakout expected in {int(time_to_apex)} days"
                    })
        
        return patterns
    
    def _generate_triangle_trading_setup(self, pattern_type, res_line, sup_line, current_x):
        """Generate trading setup for triangle patterns."""
        
        resistance_level = res_line['slope'] * current_x + res_line['intercept']
        support_level = sup_line['slope'] * current_x + sup_line['intercept']
        
        triangle_height = resistance_level - support_level
        
        setup = {
            'bullish_breakout': {
                'entry_trigger': round(resistance_level * 1.005, 2),  # 0.5% above resistance
                'target_1': round(resistance_level + triangle_height * 0.618, 2),  # 61.8% projection
                'target_2': round(resistance_level + triangle_height, 2),  # Full projection
                'stop_loss': round(support_level * 0.99, 2),  # Below support
                'risk_reward_ratio': f"1:{round((triangle_height * 0.618) / (resistance_level - support_level), 2)}"
            },
            'bearish_breakdown': {
                'entry_trigger': round(support_level * 0.995, 2),  # 0.5% below support
                'target_1': round(support_level - triangle_height * 0.618, 2),  # 61.8% projection
                'target_2': round(support_level - triangle_height, 2),  # Full projection
                'stop_loss': round(resistance_level * 1.01, 2),  # Above resistance
                'risk_reward_ratio': f"1:{round((triangle_height * 0.618) / (resistance_level - support_level), 2)}"
            }
        }
        
        return setup
    
    def _detect_flags(self):
        """Detect flag patterns."""
        patterns = []
        
        # Look for sharp moves followed by consolidation
        recent_data = self.current_df.tail(40)  # Last 40 days
        
        if len(recent_data) < 30:
            return patterns
        
        # Find potential flagpoles (sharp moves)
        for i in range(15, len(recent_data) - 10):  # Pole + flag minimum length
            pole_start = i - 15
            pole_end = i
            flag_end = min(i + 10, len(recent_data) - 1)
            
            pole_data = recent_data.iloc[pole_start:pole_end]
            flag_data = recent_data.iloc[pole_end:flag_end]
            
            # Calculate pole characteristics
            pole_change = (pole_data['close'].iloc[-1] - pole_data['close'].iloc[0])
            pole_change_pct = pole_change / pole_data['close'].iloc[0] * 100
            
            # Check for significant pole (>3% move)
            if abs(pole_change_pct) > 3:
                
                # Check flag characteristics (consolidation)
                flag_high = flag_data['high'].max()
                flag_low = flag_data['low'].min()
                flag_range_pct = (flag_high - flag_low) / flag_data['close'].iloc[0] * 100
                
                # Flag should be smaller range than pole
                if flag_range_pct < abs(pole_change_pct) * 0.5:
                    
                    pattern_type = "Bull Flag" if pole_change > 0 else "Bear Flag"
                    bias = "Bullish" if pole_change > 0 else "Bearish"
                    
                    # Calculate targets
                    current_price = recent_data['close'].iloc[flag_end]
                    target_move = pole_change
                    target_price = current_price + target_move
                    
                    patterns.append({
                        'pattern_name': pattern_type,
                        'pattern_type': 'Flag Pattern',
                        'bias': bias,
                        'reliability_score': 0.78,
                        'status': 'Currently Forming',
                        'pole_start': recent_data.index[pole_start].strftime("%Y-%m-%d"),
                        'pole_end': recent_data.index[pole_end].strftime("%Y-%m-%d"),
                        'flag_end': recent_data.index[flag_end].strftime("%Y-%m-%d"),
                        'pole_change_percent': round(pole_change_pct, 2),
                        'flag_range_percent': round(flag_range_pct, 2),
                        'trading_setup': {
                            'entry_trigger': round(flag_high * 1.002 if pole_change > 0 else flag_low * 0.998, 2),
                            'target_price': round(target_price, 2),
                            'stop_loss': round(flag_low * 0.98 if pole_change > 0 else flag_high * 1.02, 2),
                            'expected_move': f"{abs(pole_change_pct):.1f}% continuation"
                        },
                        'pattern_structure': {
                            'pole_height': round(abs(pole_change), 2),
                            'flag_consolidation_range': f"{flag_low:.2f} - {flag_high:.2f}",
                            'breakout_level': flag_high if pole_change > 0 else flag_low
                        }
                    })
        
        return patterns
    
    def _detect_head_shoulders(self):
        """Detect Head and Shoulders patterns."""
        patterns = []
        
        if len(self.peaks) < 3:
            return patterns
        
        # Look for 3 consecutive peaks forming H&S
        for i in range(len(self.peaks) - 2):
            left_shoulder = self.peaks[i]
            head = self.peaks[i + 1]
            right_shoulder = self.peaks[i + 2]
            
            # Find valleys between peaks
            left_valley = None
            right_valley = None
            
            for valley in self.valleys:
                if left_shoulder['date'] < valley['date'] < head['date']:
                    if left_valley is None or valley['price'] < left_valley['price']:
                        left_valley = valley
                
                if head['date'] < valley['date'] < right_shoulder['date']:
                    if right_valley is None or valley['price'] < right_valley['price']:
                        right_valley = valley
            
            if left_valley and right_valley:
                # Check H&S criteria
                head_higher = head['price'] > left_shoulder['price'] and head['price'] > right_shoulder['price']
                shoulders_similar = abs(left_shoulder['price'] - right_shoulder['price']) / left_shoulder['price'] < 0.05
                neckline_level = min(left_valley['price'], right_valley['price'])
                
                if head_higher and shoulders_similar:
                    # Calculate target
                    head_to_neckline = head['price'] - neckline_level
                    target_price = neckline_level - head_to_neckline
                    
                    patterns.append({
                        'pattern_name': 'Head and Shoulders',
                        'pattern_type': 'Reversal Pattern',
                        'bias': 'Bearish',
                        'reliability_score': 0.72,
                        'status': 'Pattern Complete - Watch for Neckline Break',
                        'formation_start': left_shoulder['date'].strftime("%Y-%m-%d"),
                        'formation_end': right_shoulder['date'].strftime("%Y-%m-%d"),
                        'key_points': {
                            'left_shoulder': {'date': left_shoulder['date'].strftime("%Y-%m-%d"), 'price': left_shoulder['price']},
                            'head': {'date': head['date'].strftime("%Y-%m-%d"), 'price': head['price']},
                            'right_shoulder': {'date': right_shoulder['date'].strftime("%Y-%m-%d"), 'price': right_shoulder['price']},
                            'neckline_level': round(neckline_level, 2)
                        },
                        'trading_setup': {
                            'entry_trigger': round(neckline_level * 0.995, 2),  # Break below neckline
                            'target_price': round(target_price, 2),
                            'stop_loss': round(right_shoulder['price'] * 1.02, 2),
                            'measured_move': round(head_to_neckline, 2)
                        }
                    })
        
        return patterns
    
    def _detect_double_patterns(self):
        """Detect Double Top/Bottom patterns."""
        patterns = []
        
        # Double Tops
        if len(self.peaks) >= 2:
            for i in range(len(self.peaks) - 1):
                peak1 = self.peaks[i]
                peak2 = self.peaks[i + 1]
                
                price_similarity = abs(peak1['price'] - peak2['price']) / peak1['price'] < 0.03  # Within 3%
                time_gap = (peak2['date'] - peak1['date']).days
                
                if price_similarity and 10 < time_gap < 60:  # Reasonable time gap
                    # Find valley between peaks
                    valley_between = None
                    for valley in self.valleys:
                        if peak1['date'] < valley['date'] < peak2['date']:
                            if valley_between is None or valley['price'] < valley_between['price']:
                                valley_between = valley
                    
                    if valley_between:
                        valley_depth = (min(peak1['price'], peak2['price']) - valley_between['price']) / min(peak1['price'], peak2['price'])
                        
                        if valley_depth > 0.03:  # Significant valley
                            target_price = valley_between['price'] - (min(peak1['price'], peak2['price']) - valley_between['price'])
                            
                            patterns.append({
                                'pattern_name': 'Double Top',
                                'pattern_type': 'Reversal Pattern',
                                'bias': 'Bearish',
                                'reliability_score': 0.68,
                                'status': 'Pattern Complete - Watch for Support Break',
                                'formation_start': peak1['date'].strftime("%Y-%m-%d"),
                                'formation_end': peak2['date'].strftime("%Y-%m-%d"),
                                'key_points': {
                                    'first_peak': {'date': peak1['date'].strftime("%Y-%m-%d"), 'price': peak1['price']},
                                    'second_peak': {'date': peak2['date'].strftime("%Y-%m-%d"), 'price': peak2['price']},
                                    'valley': {'date': valley_between['date'].strftime("%Y-%m-%d"), 'price': valley_between['price']}
                                },
                                'trading_setup': {
                                    'entry_trigger': round(valley_between['price'] * 0.995, 2),
                                    'target_price': round(target_price, 2),
                                    'stop_loss': round(max(peak1['price'], peak2['price']) * 1.02, 2)
                                }
                            })
        
        # Double Bottoms
        if len(self.valleys) >= 2:
            for i in range(len(self.valleys) - 1):
                valley1 = self.valleys[i]
                valley2 = self.valleys[i + 1]
                
                price_similarity = abs(valley1['price'] - valley2['price']) / valley1['price'] < 0.03  # Within 3%
                time_gap = (valley2['date'] - valley1['date']).days
                
                if price_similarity and 10 < time_gap < 60:  # Reasonable time gap
                    # Find peak between valleys
                    peak_between = None
                    for peak in self.peaks:
                        if valley1['date'] < peak['date'] < valley2['date']:
                            if peak_between is None or peak['price'] > peak_between['price']:
                                peak_between = peak
                    
                    if peak_between:
                        peak_height = (peak_between['price'] - max(valley1['price'], valley2['price'])) / max(valley1['price'], valley2['price'])
                        
                        if peak_height > 0.03:  # Significant peak
                            target_price = peak_between['price'] + (peak_between['price'] - max(valley1['price'], valley2['price']))
                            
                            patterns.append({
                                'pattern_name': 'Double Bottom',
                                'pattern_type': 'Reversal Pattern',
                                'bias': 'Bullish',
                                'reliability_score': 0.70,
                                'status': 'Pattern Complete - Watch for Resistance Break',
                                'formation_start': valley1['date'].strftime("%Y-%m-%d"),
                                'formation_end': valley2['date'].strftime("%Y-%m-%d"),
                                'key_points': {
                                    'first_bottom': {'date': valley1['date'].strftime("%Y-%m-%d"), 'price': valley1['price']},
                                    'second_bottom': {'date': valley2['date'].strftime("%Y-%m-%d"), 'price': valley2['price']},
                                    'peak': {'date': peak_between['date'].strftime("%Y-%m-%d"), 'price': peak_between['price']}
                                },
                                'trading_setup': {
                                    'entry_trigger': round(peak_between['price'] * 1.005, 2),
                                    'target_price': round(target_price, 2),
                                    'stop_loss': round(min(valley1['price'], valley2['price']) * 0.98, 2)
                                }
                            })
        
        return patterns
    
    def _detect_breakout_setups(self):
        """Detect current breakout/breakdown setups."""
        patterns = []
        
        # Get recent highs and lows
        recent_30_high = self.current_df.tail(30)['high'].max()
        recent_30_low = self.current_df.tail(30)['low'].min()
        
        # Check if current price is near breakout levels
        near_resistance = abs(self.current_price - recent_30_high) / self.current_price < 0.02  # Within 2%
        near_support = abs(self.current_price - recent_30_low) / self.current_price < 0.02  # Within 2%
        
        if near_resistance:
            patterns.append({
                'pattern_name': 'Resistance Breakout Setup',
                'pattern_type': 'Breakout Pattern',
                'bias': 'Bullish (if breaks above)',
                'reliability_score': 0.75,
                'status': 'Currently at Resistance - Breakout Imminent',
                'resistance_level': round(recent_30_high, 2),
                'distance_to_breakout_pct': round((recent_30_high - self.current_price) / self.current_price * 100, 2),
                'trading_setup': {
                    'entry_trigger': round(recent_30_high * 1.002, 2),  # 0.2% above resistance
                    'target_price': round(recent_30_high + (recent_30_high - recent_30_low) * 0.618, 2),
                    'stop_loss': round(recent_30_high * 0.98, 2),  # 2% below resistance
                    'volume_confirmation_needed': True
                },
                'timeline': 'Breakout expected within 1-5 days'
            })
        
        if near_support:
            patterns.append({
                'pattern_name': 'Support Breakdown Setup',
                'pattern_type': 'Breakdown Pattern',
                'bias': 'Bearish (if breaks below)',
                'reliability_score': 0.75,
                'status': 'Currently at Support - Breakdown Possible',
                'support_level': round(recent_30_low, 2),
                'distance_to_breakdown_pct': round((self.current_price - recent_30_low) / self.current_price * 100, 2),
                'trading_setup': {
                    'entry_trigger': round(recent_30_low * 0.998, 2),  # 0.2% below support
                    'target_price': round(recent_30_low - (recent_30_high - recent_30_low) * 0.618, 2),
                    'stop_loss': round(recent_30_low * 1.02, 2),  # 2% above support
                    'volume_confirmation_needed': True
                },
                'timeline': 'Breakdown possible within 1-5 days'
            })
        
        return patterns
    
    def analyze_volume(self):
        """Comprehensive volume analysis."""
        
        if self.volume is None:
            return {"error": "No volume data available"}
        
        recent_volume = self.current_df['volume']
        current_vol = recent_volume.iloc[-1]
        avg_vol = recent_volume.mean()
        vol_std = recent_volume.std()
        
        # Volume assessment
        if current_vol > avg_vol + 2 * vol_std:
            vol_assessment = "Extremely High"
            significance = "Major institutional activity"
        elif current_vol > avg_vol + vol_std:
            vol_assessment = "High"
            significance = "Above normal activity"
        elif current_vol < avg_vol - vol_std:
            vol_assessment = "Low"
            significance = "Below normal activity"
        else:
            vol_assessment = "Normal"
            significance = "Average trading activity"
        
        # Volume trend
        vol_ma_5 = recent_volume.rolling(5).mean().iloc[-1]
        vol_ma_20 = recent_volume.rolling(20).mean().iloc[-1] if len(recent_volume) >= 20 else avg_vol
        
        if vol_ma_5 > vol_ma_20 * 1.2:
            vol_trend = "Strongly Increasing"
        elif vol_ma_5 > vol_ma_20 * 1.1:
            vol_trend = "Increasing"
        elif vol_ma_5 < vol_ma_20 * 0.8:
            vol_trend = "Strongly Decreasing"
        elif vol_ma_5 < vol_ma_20 * 0.9:
            vol_trend = "Decreasing"
        else:
            vol_trend = "Stable"
        
        # Recent volume spikes
        volume_spikes = []
        for i in range(max(0, len(recent_volume) - 10), len(recent_volume)):
            vol = recent_volume.iloc[i]
            z_score = (vol - avg_vol) / vol_std if vol_std > 0 else 0
            
            if z_score > 2:
                volume_spikes.append({
                    'date': recent_volume.index[i].strftime("%Y-%m-%d"),
                    'volume': int(vol),
                    'z_score': round(z_score, 2),
                    'multiple_of_average': round(vol / avg_vol, 2)
                })
        
        return {
            "current_volume": int(current_vol),
            "average_volume": int(avg_vol),
            "volume_assessment": vol_assessment,
            "significance": significance,
            "volume_trend": vol_trend,
            "volume_ratio": round(current_vol / avg_vol, 2),
            "recent_spikes": volume_spikes[-5:],  # Last 5 spikes
            "volume_ma_5": int(vol_ma_5),
            "volume_ma_20": int(vol_ma_20)
        }
    
    def analyze_fibonacci(self):
        """Proper Fibonacci analysis: Swing Low = 0%, Swing High = 100%, using wicks."""
        
        # Step 1: Identify current trend direction using SMA
        sma_10 = self.current_df['close'].rolling(10).mean().iloc[-1]
        sma_20 = self.current_df['close'].rolling(20).mean().iloc[-1]
        sma_50 = self.current_df['close'].rolling(50).mean().iloc[-1]
        
        # Determine trend based on SMA alignment and price position
        if self.current_price > sma_10 > sma_20 > sma_50:
            current_trend = "uptrend"
        elif self.current_price < sma_10 < sma_20 < sma_50:
            current_trend = "downtrend"
        else:
            # Use recent price action to determine trend
            recent_high = self.current_df['high'].tail(20).max()
            recent_low = self.current_df['low'].tail(20).min()
            if self.current_price > (recent_high + recent_low) / 2:
                current_trend = "uptrend"
            else:
                current_trend = "downtrend"
        
        # Step 2: Go back from current date to find swing high and swing low using wicks
        # Find all potential swings within lookback period, working backwards from current date
        lookback_days = 60
        lookback_data = self.current_df.tail(lookback_days)
        
        # Find swing highs and lows using wicks (high/low prices)
        swing_highs = []
        swing_lows = []
        
        # Look for swings, excluding the very recent days to avoid incomplete patterns
        for i in range(5, len(lookback_data) - 3):  # Leave 3 days buffer from current
            high_price = lookback_data['high'].iloc[i]
            low_price = lookback_data['low'].iloc[i]
            swing_date = lookback_data.index[i]
            
            # Check if it's a swing high (higher than surrounding 5 days on each side)
            is_swing_high = all(high_price >= lookback_data['high'].iloc[i-j] for j in range(1, 6)) and \
                           all(high_price >= lookback_data['high'].iloc[i+j] for j in range(1, 6))
            
            # Check if it's a swing low (lower than surrounding 5 days on each side) 
            is_swing_low = all(low_price <= lookback_data['low'].iloc[i-j] for j in range(1, 6)) and \
                          all(low_price <= lookback_data['low'].iloc[i+j] for j in range(1, 6))
            
            if is_swing_high:
                swing_highs.append({
                    'price': high_price,
                    'date': swing_date,
                    'index': i
                })
            
            if is_swing_low:
                swing_lows.append({
                    'price': low_price,
                    'date': swing_date, 
                    'index': i
                })
        
        # Step 3: Select swing pair using new logic - work backwards from current date
        if not swing_highs or not swing_lows:
            # Fallback if no clear swings found
            recent_data = self.current_df.tail(30)
            swing_high = {
                'price': recent_data['high'].max(),
                'date': recent_data['high'].idxmax()
            }
            swing_low = {
                'price': recent_data['low'].min(), 
                'date': recent_data['low'].idxmin()
            }
        else:
            if current_trend == "uptrend":
                # UPTREND LOGIC:
                # 1. Find first swing low from current date (including current date if it's a swing low)
                # 2. Find first swing high before that swing low
                
                # Check if current date itself is a swing low
                current_date = self.current_df.index[-1]
                current_low_price = self.current_df['low'].iloc[-1]
                
                # See if current price area could be considered a swing low
                recent_lows = self.current_df['low'].tail(10)  # Last 10 days
                is_current_area_low = current_low_price <= recent_lows.min() * 1.02  # Within 2% of recent low
                
                if is_current_area_low:
                    # Current area is the swing low - use it
                    first_swing_low = {
                        'price': current_low_price,
                        'date': current_date,
                        'index': len(self.current_df) - 1
                    }
                else:
                    # Find first swing low going backwards from current date
                    swing_lows_by_date = sorted(swing_lows, key=lambda x: x['date'], reverse=True)
                    first_swing_low = swing_lows_by_date[0]  # Most recent swing low
                
                # Now find first swing high before this swing low
                swing_highs_before = [sh for sh in swing_highs if sh['date'] < first_swing_low['date']]
                if swing_highs_before:
                    # Get the swing high closest to (but before) the swing low
                    swing_high = max(swing_highs_before, key=lambda x: x['date'])
                else:
                    # Fallback: use any swing high we have
                    swing_high = max(swing_highs, key=lambda x: x['date'])
                
                swing_low = first_swing_low
                    
            else:  # downtrend
                # DOWNTREND LOGIC (Same as uptrend but finding swing high first):
                # 1. Find first swing high from current date (including current date if it's a swing high)
                # 2. Find first swing low before that swing high
                
                # Check if current date itself is a swing high
                current_date = self.current_df.index[-1]
                current_high_price = self.current_df['high'].iloc[-1]
                
                # See if current price area could be considered a swing high
                recent_highs = self.current_df['high'].tail(10)  # Last 10 days
                is_current_area_high = current_high_price >= recent_highs.max() * 0.98  # Within 2% of recent high
                
                if is_current_area_high:
                    # Current area is the swing high - use it
                    first_swing_high = {
                        'price': current_high_price,
                        'date': current_date,
                        'index': len(self.current_df) - 1
                    }
                else:
                    # Find first swing high going backwards from current date
                    swing_highs_by_date = sorted(swing_highs, key=lambda x: x['date'], reverse=True)
                    first_swing_high = swing_highs_by_date[0]  # Most recent swing high
                
                # Now find first swing low before this swing high
                swing_lows_before = [sl for sl in swing_lows if sl['date'] < first_swing_high['date']]
                if swing_lows_before:
                    # Get the swing low closest to (but before) the swing high
                    swing_low = max(swing_lows_before, key=lambda x: x['date'])
                else:
                    # Fallback: use any swing low we have
                    swing_low = max(swing_lows, key=lambda x: x['date'])
                
                swing_high = first_swing_high
        
        # Step 4: ALWAYS use Swing Low = 0%, Swing High = 100% (standard Fibonacci)
        swing_low_price = swing_low['price']
        swing_high_price = swing_high['price']
        price_range = swing_high_price - swing_low_price
        
        if price_range <= 0:
            return {"error": "Invalid swing range - swing high must be above swing low"}
        
        # Step 5: Calculate Fibonacci levels - ALWAYS from swing low to swing high, but with different 0% references
        fib_levels = []
        fib_ratios = [0.0, 0.236, 0.382, 0.500, 0.618, 0.786, 1.0]
        extension_ratios = [1.272, 1.414, 1.618, 2.0, 2.618]
        
        # Calculate retracement levels - CONSISTENT CALCULATION: Always from swing low to swing high
        for ratio in fib_ratios:
            # Both trends: Always calculate from swing low (0%) to swing high (100%)
            # This ensures consistent Fibonacci structure regardless of trend
            level_price = swing_low_price + (price_range * ratio)
            level_type = f"Retracement {ratio*100:.1f}%"
            
            distance_pct = abs(level_price - self.current_price) / self.current_price * 100
            
            fib_levels.append({
                'level': level_type,
                'price': round(level_price, 2),
                'ratio': ratio,
                'distance_percent': round(distance_pct, 2),
                'significance': self._get_fib_significance(ratio)
            })
        
        # Calculate extension levels - CONSISTENT CALCULATION: Always extend beyond swing high
        for ratio in extension_ratios:
            # Both trends: Extensions always go beyond swing high (100% level)
            # This provides upside targets regardless of current trend direction
            level_price = swing_high_price + (price_range * (ratio - 1))
            level_type = f"Extension {ratio*100:.1f}%"
            
            distance_pct = abs(level_price - self.current_price) / self.current_price * 100
            
            fib_levels.append({
                'level': level_type,
                'price': round(level_price, 2),
                'ratio': ratio,
                'distance_percent': round(distance_pct, 2),
                'significance': self._get_extension_significance(ratio)
            })
        
        # Sort by distance to current price
        fib_levels.sort(key=lambda x: x['distance_percent'])
        
        # Check if current date was used as a swing point
        current_date = self.current_df.index[-1]
        used_current_as_swing = (swing_high['date'] == current_date) or (swing_low['date'] == current_date)
        
        if current_trend == "uptrend":
            fib_method = "UPTREND: First swing low from current date → First swing high before that"
            zero_percent_level = f"Swing Low (₹{swing_low_price}) = 0%"
            hundred_percent_level = f"Swing High (₹{swing_high_price}) = 100%"
            swing_selection_logic = "1. Found first swing low from current date 2. Found first swing high before that swing low"
        else:
            fib_method = "DOWNTREND: First swing high from current date → First swing low before that" 
            zero_percent_level = f"Swing High (₹{swing_high_price}) = 0%"
            hundred_percent_level = f"Swing Low (₹{swing_low_price}) = 100%"
            swing_selection_logic = "1. Found first swing high from current date 2. Found first swing low before that swing high"
        
        return {
            "fibonacci_analysis": {
                "trend_direction": current_trend,
                "recent_swing_high": {
                    "price": swing_high_price,
                    "date": swing_high['date'].strftime("%Y-%m-%d")
                },
                "recent_swing_low": {
                    "price": swing_low_price,
                    "date": swing_low['date'].strftime("%Y-%m-%d")
                },
                "price_range": round(price_range, 2),
                "fibonacci_method": fib_method,
                "zero_percent_reference": zero_percent_level,
                "hundred_percent_reference": hundred_percent_level,
                "swing_selection_logic": swing_selection_logic,
                "used_current_date_as_swing": used_current_as_swing,
                "swing_detection": "Recent swing pair: Working backwards from current date using wicks"
            },
            "key_levels": fib_levels[:10],  # Top 10 levels
            "nearest_level": fib_levels[0] if fib_levels else None
        }
    
    def _get_fib_significance(self, ratio):
        """Get significance for Fibonacci ratios."""
        significance_map = {
            0.236: "Shallow retracement - strong trend",
            0.382: "Moderate retracement - common level",
            0.500: "Half retracement - psychological level",
            0.618: "Golden ratio - key reversal level",
            0.786: "Deep retracement - trend weakness"
        }
        return significance_map.get(ratio, "Reference level")
    
    def _get_extension_significance(self, ratio):
        """Get significance for Fibonacci extensions."""
        significance_map = {
            1.272: "Common first target",
            1.414: "Secondary target level",
            1.618: "Golden ratio target - major level",
            2.0: "Double extension - psychological target"
        }
        return significance_map.get(ratio, "Extension target")
    
    def generate_comprehensive_analysis(self):
        """Generate complete comprehensive analysis."""
        
        print(f"🎯 Generating COMPREHENSIVE analysis for {self.symbol}...")
        print(f"   📊 Trendlines, Chart Patterns, Volume & Fibonacci")
        
        # Get all analysis components
        trendline_analysis = self.analyze_trendlines()
        chart_patterns = self.detect_chart_patterns()
        volume_analysis = self.analyze_volume()
        fibonacci_analysis = self.analyze_fibonacci()
        
        # Market structure
        current_trend = self._determine_current_trend()
        
        # Compile comprehensive analysis
        comprehensive_analysis = {
            "analysis_summary": {
                "stock_symbol": self.symbol,
                "analysis_date": self.current_date.strftime("%B %d, %Y"),
                "analysis_focus": f"Comprehensive analysis - last {self.analysis_window} days",
                "current_price": round(self.current_price, 2),
                "analysis_components": ["Trendlines", "Chart Patterns", "Volume Analysis", "Fibonacci Levels"]
            },
            
            "current_market_structure": {
                "trend": current_trend,
                "price_action": self._analyze_price_action()
            },
            
            "trendline_analysis": trendline_analysis,
            "chart_patterns": chart_patterns,
            "volume_analysis": volume_analysis,
            "fibonacci_analysis": fibonacci_analysis,
            
            "trading_opportunities": self._identify_trading_opportunities(
                trendline_analysis, chart_patterns, volume_analysis, fibonacci_analysis
            ),
            
            "risk_management": self._generate_risk_management(
                trendline_analysis, chart_patterns
            )
        }
        
        return comprehensive_analysis
    
    def _determine_current_trend(self):
        """Determine current market trend."""
        
        # Price vs moving averages
        sma_10 = self.current_df['close'].rolling(10).mean().iloc[-1] if len(self.current_df) >= 10 else self.current_price
        sma_20 = self.current_df['close'].rolling(20).mean().iloc[-1] if len(self.current_df) >= 20 else self.current_price
        
        if self.current_price > sma_10 > sma_20:
            trend_direction = "Strong Uptrend"
            trend_strength = "Strong"
        elif self.current_price > sma_10:
            trend_direction = "Uptrend"
            trend_strength = "Moderate"
        elif self.current_price < sma_10 < sma_20:
            trend_direction = "Strong Downtrend"
            trend_strength = "Strong"
        elif self.current_price < sma_10:
            trend_direction = "Downtrend"
            trend_strength = "Moderate"
        else:
            trend_direction = "Sideways"
            trend_strength = "Weak"
        
        return {
            "direction": trend_direction,
            "strength": trend_strength,
            "sma_10": round(sma_10, 2),
            "sma_20": round(sma_20, 2)
        }
    
    def _analyze_price_action(self):
        """Analyze recent price action."""
        
        # Recent changes
        price_1d = (self.current_price - self.current_df['close'].iloc[-2]) if len(self.current_df) > 1 else 0
        price_5d = (self.current_price - self.current_df['close'].iloc[-6]) if len(self.current_df) > 5 else 0
        price_20d = (self.current_price - self.current_df['close'].iloc[-21]) if len(self.current_df) > 20 else 0
        
        return {
            "1_day_change": {"absolute": round(price_1d, 2), "percent": round(price_1d/self.current_price*100, 2)},
            "5_day_change": {"absolute": round(price_5d, 2), "percent": round(price_5d/self.current_price*100, 2)},
            "20_day_change": {"absolute": round(price_20d, 2), "percent": round(price_20d/self.current_price*100, 2)}
        }
    
    def _identify_trading_opportunities(self, trendlines, patterns, volume, fibonacci):
        """Identify specific trading opportunities."""
        
        opportunities = []
        
        # Pattern-based opportunities
        for pattern in patterns:
            setup = pattern.get('trading_setup', {})
            if setup:
                opportunities.append({
                    'type': 'Pattern Setup',
                    'pattern_name': pattern['pattern_name'],
                    'bias': pattern['bias'],
                    'reliability': pattern['reliability_score'],
                    'setup': setup,
                    'volume_confirmation': self._assess_volume_for_pattern(pattern, volume),
                    'fibonacci_confirmation': self._assess_fibonacci_for_pattern(pattern, fibonacci)
                })
        
        # Trendline-based opportunities
        if 'trendlines' in trendlines:
            for trendline in trendlines['trendlines'][:3]:  # Top 3 trendlines
                if trendline['distance_percent'] < 3:  # Within 3% of current price
                    opportunities.append({
                        'type': 'Trendline Setup',
                        'trendline_type': trendline['type'],
                        'level': trendline['current_value'],
                        'strength': trendline['strength'],
                        'setup': self._generate_trendline_setup(trendline)
                    })
        
        return opportunities
    
    def _assess_volume_for_pattern(self, pattern, volume_analysis):
        """Assess volume support for pattern."""
        
        if 'error' in volume_analysis:
            return "Volume data not available"
        
        volume_assessment = volume_analysis.get('volume_assessment', 'Normal')
        volume_trend = volume_analysis.get('volume_trend', 'Stable')
        
        if 'Breakout' in pattern['pattern_name']:
            if volume_assessment in ['High', 'Extremely High']:
                return "Strong volume support - breakout likely valid"
            else:
                return "Weak volume - breakout may fail"
        
        return f"Volume: {volume_assessment}, Trend: {volume_trend}"
    
    def _assess_fibonacci_for_pattern(self, pattern, fibonacci_analysis):
        """Assess Fibonacci support for pattern."""
        
        if 'error' in fibonacci_analysis:
            return "Fibonacci levels not available"
        
        # Check if pattern levels align with Fibonacci
        setup = pattern.get('trading_setup', {})
        fib_levels = fibonacci_analysis.get('key_levels', [])
        
        alignments = []
        for level in fib_levels[:5]:  # Check top 5 Fib levels
            fib_price = level['price']
            
            # Check various setup prices
            for setup_key, setup_value in setup.items():
                if isinstance(setup_value, dict):
                    for price_key, price_value in setup_value.items():
                        if isinstance(price_value, (int, float)):
                            distance_pct = abs(price_value - fib_price) / price_value * 100
                            if distance_pct < 2:  # Within 2%
                                alignments.append(f"{level['level']} aligns with {setup_key}")
        
        if alignments:
            return f"Fibonacci support: {len(alignments)} level(s) align"
        else:
            return "No direct Fibonacci alignment"
    
    def _generate_trendline_setup(self, trendline):
        """Generate trading setup for trendline."""
        
        level = trendline['current_value']
        
        if trendline['type'] == 'Resistance':
            return {
                'breakout_entry': round(level * 1.005, 2),
                'target': round(level * 1.03, 2),
                'stop_loss': round(level * 0.985, 2)
            }
        else:  # Support
            return {
                'bounce_entry': round(level * 1.005, 2),
                'target': round(level * 1.025, 2),
                'stop_loss': round(level * 0.98, 2)
            }
    
    def _generate_risk_management(self, trendlines, patterns):
        """Generate risk management guidelines."""
        
        # Find nearest support/resistance
        nearest_support = None
        nearest_resistance = None
        
        if 'trendlines' in trendlines:
            for trendline in trendlines['trendlines']:
                if trendline['type'] == 'Support' and trendline['current_value'] < self.current_price:
                    if nearest_support is None or trendline['current_value'] > nearest_support:
                        nearest_support = trendline['current_value']
                
                if trendline['type'] == 'Resistance' and trendline['current_value'] > self.current_price:
                    if nearest_resistance is None or trendline['current_value'] < nearest_resistance:
                        nearest_resistance = trendline['current_value']
        
        return {
            "stop_loss_levels": {
                "nearest_support": round(nearest_support, 2) if nearest_support else None,
                "nearest_resistance": round(nearest_resistance, 2) if nearest_resistance else None,
                "percentage_stops": {
                    "conservative": round(self.current_price * 0.95, 2),  # 5% stop
                    "moderate": round(self.current_price * 0.97, 2),     # 3% stop
                    "tight": round(self.current_price * 0.985, 2)       # 1.5% stop
                }
            },
            "position_sizing": {
                "max_risk_per_trade": "1-2% of portfolio",
                "pattern_based_sizing": "Higher allocation for high-reliability patterns",
                "volume_confirmation": "Increase size when volume confirms setup"
            }
        }


def generate_comprehensive_market_analysis(df, symbol, analysis_window=60):
    """
    Main function to generate comprehensive market analysis.
    Combines trendlines, patterns, volume, and Fibonacci.
    """
    
    analyzer = ComprehensiveMarketAnalyzer(df, symbol, analysis_window)
    analysis = analyzer.generate_comprehensive_analysis()
    
    # Save to JSON with timestamp
    filename = f"{symbol}_comprehensive_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2, cls=NpEncoder)
    
    print(f"✅ Comprehensive analysis saved to: {filename}")
    return analysis


if __name__ == "__main__":
    print("🎯 COMPREHENSIVE MARKET ANALYZER")
    print("=" * 80)
    print("COMPLETE ANALYSIS INCLUDES:")
    print("📈 Trendlines: Support/resistance with touch points")
    print("📊 Chart Patterns: Triangles, flags, H&S, double tops/bottoms")
    print("📊 Volume Analysis: Confirmation, spikes, trends")
    print("📐 Fibonacci: Retracements and extensions")
    print("🎯 Trading Setups: Entry, target, stop loss for each")
    print("=" * 80)