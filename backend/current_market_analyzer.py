import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta
from detector import NpEncoder
import logging

class CurrentMarketAnalyzer:
    """
    Focuses on CURRENT market structure and ACTIVE patterns only.
    Analyzes what's happening RIGHT NOW and where price is likely to go next.
    """
    
    def __init__(self, df, symbol="UNKNOWN", analysis_window=60):
        """
        Initialize with focus on recent price action only.
        
        Args:
            df: OHLCV DataFrame with DatetimeIndex
            symbol: Stock symbol
            analysis_window: Days to look back for current analysis (default 60)
        """
        self.symbol = symbol
        self.analysis_window = analysis_window
        
        # Focus on recent data only
        self.df = df.tail(analysis_window * 2)  # Extra buffer for calculations
        self.current_df = df.tail(analysis_window)  # Main analysis window
        
        self.current_price = df['close'].iloc[-1]
        self.current_date = df.index[-1]
        
        # Key price levels from recent action
        self.current_high = self.current_df['high'].max()
        self.current_low = self.current_df['low'].min()
        self.current_range = self.current_high - self.current_low
        
        # Recent performance
        self.price_change_1d = df['close'].iloc[-1] - df['close'].iloc[-2] if len(df) > 1 else 0
        self.price_change_5d = df['close'].iloc[-1] - df['close'].iloc[-6] if len(df) > 5 else 0
        self.price_change_20d = df['close'].iloc[-1] - df['close'].iloc[-21] if len(df) > 20 else 0
        
        self.results = {}
    
    def analyze_current_trend(self):
        """Analyze the current trend structure - what's happening RIGHT NOW."""
        
        recent_data = self.current_df.copy()
        
        # Moving averages for trend context
        recent_data['sma_10'] = recent_data['close'].rolling(10).mean()
        recent_data['sma_20'] = recent_data['close'].rolling(20).mean()
        recent_data['ema_10'] = recent_data['close'].ewm(span=10).mean()
        
        current_sma10 = recent_data['sma_10'].iloc[-1] if not pd.isna(recent_data['sma_10'].iloc[-1]) else self.current_price
        current_sma20 = recent_data['sma_20'].iloc[-1] if not pd.isna(recent_data['sma_20'].iloc[-1]) else self.current_price
        
        # Trend determination
        if self.current_price > current_sma10 > current_sma20:
            trend_direction = "Strong Uptrend"
            trend_strength = "Strong"
            bias = "Bullish"
        elif self.current_price > current_sma10 and current_sma10 < current_sma20:
            trend_direction = "Weak Uptrend" 
            trend_strength = "Weak"
            bias = "Cautiously Bullish"
        elif self.current_price < current_sma10 < current_sma20:
            trend_direction = "Strong Downtrend"
            trend_strength = "Strong" 
            bias = "Bearish"
        elif self.current_price < current_sma10 and current_sma10 > current_sma20:
            trend_direction = "Weak Downtrend"
            trend_strength = "Weak"
            bias = "Cautiously Bearish"
        else:
            trend_direction = "Sideways/Consolidation"
            trend_strength = "Neutral"
            bias = "Neutral"
        
        # Momentum analysis
        momentum_1d = "Positive" if self.price_change_1d > 0 else "Negative"
        momentum_5d = "Positive" if self.price_change_5d > 0 else "Negative"
        momentum_20d = "Positive" if self.price_change_20d > 0 else "Negative"
        
        # Current volatility
        recent_returns = recent_data['close'].pct_change().dropna()
        current_volatility = recent_returns.std() * np.sqrt(252) * 100  # Annualized volatility %
        
        return {
            "current_trend": {
                "direction": trend_direction,
                "strength": trend_strength,
                "bias": bias,
                "current_price": self.current_price,
                "sma_10": round(current_sma10, 2),
                "sma_20": round(current_sma20, 2)
            },
            "momentum": {
                "1_day": {"direction": momentum_1d, "change": round(self.price_change_1d, 2), "change_pct": round(self.price_change_1d/self.current_price*100, 2)},
                "5_day": {"direction": momentum_5d, "change": round(self.price_change_5d, 2), "change_pct": round(self.price_change_5d/self.current_price*100, 2)},
                "20_day": {"direction": momentum_20d, "change": round(self.price_change_20d, 2), "change_pct": round(self.price_change_20d/self.current_price*100, 2)}
            },
            "volatility": {
                "current_volatility_annualized": round(current_volatility, 1),
                "volatility_assessment": "High" if current_volatility > 30 else "Normal" if current_volatility > 15 else "Low"
            }
        }
    
    def identify_current_support_resistance(self):
        """Identify CURRENT support and resistance levels based on recent price action."""
        
        recent_data = self.current_df.copy()
        
        # Find recent significant highs and lows
        def find_recent_pivots(data, window=5):
            highs = []
            lows = []
            
            for i in range(window, len(data) - window):
                # Check if it's a local high
                if all(data['high'].iloc[i] >= data['high'].iloc[i-j] for j in range(1, window+1)) and \
                   all(data['high'].iloc[i] >= data['high'].iloc[i+j] for j in range(1, window+1)):
                    highs.append({
                        'date': data.index[i],
                        'price': data['high'].iloc[i],
                        'days_ago': (self.current_date - data.index[i]).days,
                        'volume': data['volume'].iloc[i] if 'volume' in data.columns else 0
                    })
                
                # Check if it's a local low
                if all(data['low'].iloc[i] <= data['low'].iloc[i-j] for j in range(1, window+1)) and \
                   all(data['low'].iloc[i] <= data['low'].iloc[i+j] for j in range(1, window+1)):
                    lows.append({
                        'date': data.index[i],
                        'price': data['low'].iloc[i],
                        'days_ago': (self.current_date - data.index[i]).days,
                        'volume': data['volume'].iloc[i] if 'volume' in data.columns else 0
                    })
            
            return highs, lows
        
        recent_highs, recent_lows = find_recent_pivots(recent_data)
        
        # Filter for significant levels (within reasonable distance from current price)
        price_tolerance = self.current_price * 0.15  # 15% from current price
        
        relevant_resistance = [h for h in recent_highs if 
                             h['price'] > self.current_price and 
                             h['price'] <= self.current_price + price_tolerance]
        
        relevant_support = [l for l in recent_lows if 
                          l['price'] < self.current_price and 
                          l['price'] >= self.current_price - price_tolerance]
        
        # Sort by proximity to current price
        relevant_resistance.sort(key=lambda x: abs(x['price'] - self.current_price))
        relevant_support.sort(key=lambda x: abs(x['price'] - self.current_price))
        
        # Add psychological levels (round numbers)
        def get_psychological_levels():
            # Find nearest round numbers
            levels = []
            current = self.current_price
            
            # Major round numbers (100s, 50s)
            for multiplier in [50, 100, 250, 500]:
                lower_level = (int(current / multiplier) * multiplier)
                upper_level = lower_level + multiplier
                
                if abs(lower_level - current) < current * 0.1 and lower_level != current:
                    levels.append(lower_level)
                if abs(upper_level - current) < current * 0.1 and upper_level != current:
                    levels.append(upper_level)
            
            return sorted(set(levels))
        
        psychological_levels = get_psychological_levels()
        
        # Format resistance levels
        resistance_levels = []
        for i, res in enumerate(relevant_resistance[:3]):  # Top 3
            distance_pct = (res['price'] - self.current_price) / self.current_price * 100
            strength = "Strong" if res['days_ago'] < 20 else "Medium"
            
            resistance_levels.append({
                "price": round(res['price'], 2),
                "strength": strength,
                "established_date": res['date'].strftime("%B %d, %Y"),
                "days_ago": res['days_ago'],
                "distance_percent": round(distance_pct, 1),
                "type": "Technical Resistance",
                "description": f"Recent high formed {res['days_ago']} days ago - {distance_pct:.1f}% above current price"
            })
        
        # Format support levels
        support_levels = []
        for i, sup in enumerate(relevant_support[:3]):  # Top 3
            distance_pct = (self.current_price - sup['price']) / self.current_price * 100
            strength = "Strong" if sup['days_ago'] < 20 else "Medium"
            
            support_levels.append({
                "price": round(sup['price'], 2),
                "strength": strength,
                "established_date": sup['date'].strftime("%B %d, %Y"),
                "days_ago": sup['days_ago'],
                "distance_percent": round(distance_pct, 1),
                "type": "Technical Support",
                "description": f"Recent low formed {sup['days_ago']} days ago - {distance_pct:.1f}% below current price"
            })
        
        # Add psychological levels
        for level in psychological_levels:
            if level > self.current_price:
                distance_pct = (level - self.current_price) / self.current_price * 100
                if distance_pct < 10:  # Only if within 10%
                    resistance_levels.append({
                        "price": level,
                        "strength": "Medium",
                        "established_date": "Ongoing",
                        "days_ago": 0,
                        "distance_percent": round(distance_pct, 1),
                        "type": "Psychological Resistance",
                        "description": f"Round number resistance at {level} - {distance_pct:.1f}% above current price"
                    })
            elif level < self.current_price:
                distance_pct = (self.current_price - level) / self.current_price * 100
                if distance_pct < 10:  # Only if within 10%
                    support_levels.append({
                        "price": level,
                        "strength": "Medium", 
                        "established_date": "Ongoing",
                        "days_ago": 0,
                        "distance_percent": round(distance_pct, 1),
                        "type": "Psychological Support",
                        "description": f"Round number support at {level} - {distance_pct:.1f}% below current price"
                    })
        
        # Sort by proximity and limit to top 3 each
        resistance_levels = sorted(resistance_levels, key=lambda x: x['distance_percent'])[:3]
        support_levels = sorted(support_levels, key=lambda x: x['distance_percent'])[:3]
        
        return {
            "current_support_levels": support_levels,
            "current_resistance_levels": resistance_levels
        }
    
    def detect_active_patterns(self):
        """Detect patterns that are CURRENTLY forming or about to complete."""
        
        recent_data = self.current_df.copy()
        active_patterns = []
        
        # 1. Current Consolidation Patterns
        consolidation_pattern = self._detect_current_consolidation(recent_data)
        if consolidation_pattern:
            active_patterns.append(consolidation_pattern)
        
        # 2. Current Breakout Setup
        breakout_pattern = self._detect_breakout_setup(recent_data)
        if breakout_pattern:
            active_patterns.append(breakout_pattern)
        
        # 3. Current Trend Continuation Setup
        trend_continuation = self._detect_trend_continuation(recent_data)
        if trend_continuation:
            active_patterns.append(trend_continuation)
        
        return active_patterns
    
    def _detect_current_consolidation(self, data):
        """Detect if price is currently in a consolidation phase."""
        
        # Look at last 20 days for consolidation
        consolidation_period = min(20, len(data))
        recent_period = data.tail(consolidation_period)
        
        if len(recent_period) < 10:
            return None
        
        period_high = recent_period['high'].max()
        period_low = recent_period['low'].min()
        period_range = period_high - period_low
        range_pct = period_range / self.current_price * 100
        
        # Check if we're in a tight range
        if range_pct < 8:  # Less than 8% range indicates consolidation
            
            # Determine consolidation type
            first_half_avg = recent_period.head(consolidation_period//2)['close'].mean()
            second_half_avg = recent_period.tail(consolidation_period//2)['close'].mean()
            
            if second_half_avg > first_half_avg * 1.02:
                consolidation_type = "Bullish Consolidation"
                bias = "Bullish"
                expected_direction = "Upward breakout expected"
            elif second_half_avg < first_half_avg * 0.98:
                consolidation_type = "Bearish Consolidation" 
                bias = "Bearish"
                expected_direction = "Downward breakdown expected"
            else:
                consolidation_type = "Neutral Consolidation"
                bias = "Neutral"
                expected_direction = "Direction unclear - wait for breakout"
            
            # Entry and target calculations
            breakout_level_up = period_high * 1.005  # 0.5% above high
            breakout_level_down = period_low * 0.995  # 0.5% below low
            
            target_up = breakout_level_up + period_range  # Range projection upward
            target_down = breakout_level_down - period_range  # Range projection downward
            
            return {
                "pattern_id": f"CONSOLIDATION_CURRENT",
                "pattern_name": consolidation_type,
                "pattern_type": "Continuation Pattern",
                "status": "Currently Active",
                "expected_direction": expected_direction,
                "reliability_score": "Medium (65%)",
                
                "current_structure": {
                    "consolidation_range": f"{period_low:.2f} - {period_high:.2f}",
                    "range_percentage": f"{range_pct:.1f}%",
                    "days_in_consolidation": consolidation_period,
                    "current_position_in_range": f"{((self.current_price - period_low) / period_range * 100):.0f}%"
                },
                
                "trading_setup": {
                    "bullish_scenario": {
                        "trigger_price": round(breakout_level_up, 2),
                        "target_price": round(target_up, 2),
                        "stop_loss": round(period_low * 0.995, 2),
                        "risk_reward_ratio": f"1:{((target_up - breakout_level_up) / (breakout_level_up - period_low * 0.995)):.2f}"
                    },
                    "bearish_scenario": {
                        "trigger_price": round(breakout_level_down, 2),
                        "target_price": round(target_down, 2),
                        "stop_loss": round(period_high * 1.005, 2),
                        "risk_reward_ratio": f"1:{((breakout_level_down - target_down) / (period_high * 1.005 - breakout_level_down)):.2f}"
                    }
                },
                
                "next_action": f"Wait for breakout above {breakout_level_up:.2f} or below {breakout_level_down:.2f} with volume",
                "timeline": "Expected resolution within 5-15 days"
            }
        
        return None
    
    def _detect_breakout_setup(self, data):
        """Detect if we're at a key breakout level RIGHT NOW."""
        
        # Look for resistance/support test in progress
        recent_3_days = data.tail(3)
        if len(recent_3_days) < 3:
            return None
        
        # Check if we're near recent high or low
        recent_30_high = data.tail(30)['high'].max()
        recent_30_low = data.tail(30)['low'].min()
        
        current_price = self.current_price
        
        # Are we near a breakout level?
        near_resistance = abs(current_price - recent_30_high) / current_price < 0.02  # Within 2%
        near_support = abs(current_price - recent_30_low) / current_price < 0.02  # Within 2%
        
        if near_resistance:
            return {
                "pattern_id": f"BREAKOUT_RESISTANCE_CURRENT",
                "pattern_name": "Resistance Breakout Setup",
                "pattern_type": "Breakout Pattern",
                "status": "Currently Testing Resistance",
                "expected_direction": "Bullish if breaks above resistance",
                "reliability_score": "High (75%)",
                
                "current_structure": {
                    "resistance_level": round(recent_30_high, 2),
                    "current_price": round(current_price, 2),
                    "distance_to_breakout": f"{((recent_30_high - current_price) / current_price * 100):.1f}%",
                    "attempts_at_level": self._count_resistance_tests(data, recent_30_high)
                },
                
                "trading_setup": {
                    "entry_strategy": {
                        "trigger_price": round(recent_30_high * 1.002, 2),  # 0.2% above resistance
                        "confirmation_needed": "Close above resistance on above-average volume",
                        "target_price": round(recent_30_high + (recent_30_high - recent_30_low) * 0.618, 2),  # 61.8% of range
                        "stop_loss": round(recent_30_high * 0.98, 2),  # 2% below resistance
                        "position_sizing": "Risk 1-2% of portfolio"
                    }
                },
                
                "next_action": f"Watch for break above {recent_30_high:.2f} with volume",
                "timeline": "Breakout attempt likely within 1-5 days"
            }
        
        elif near_support:
            return {
                "pattern_id": f"BREAKDOWN_SUPPORT_CURRENT", 
                "pattern_name": "Support Breakdown Setup",
                "pattern_type": "Breakdown Pattern",
                "status": "Currently Testing Support",
                "expected_direction": "Bearish if breaks below support",
                "reliability_score": "High (75%)",
                
                "current_structure": {
                    "support_level": round(recent_30_low, 2),
                    "current_price": round(current_price, 2),
                    "distance_to_breakdown": f"{((current_price - recent_30_low) / current_price * 100):.1f}%",
                    "attempts_at_level": self._count_support_tests(data, recent_30_low)
                },
                
                "trading_setup": {
                    "entry_strategy": {
                        "trigger_price": round(recent_30_low * 0.998, 2),  # 0.2% below support
                        "confirmation_needed": "Close below support on above-average volume",
                        "target_price": round(recent_30_low - (recent_30_high - recent_30_low) * 0.618, 2),  # 61.8% of range
                        "stop_loss": round(recent_30_low * 1.02, 2),  # 2% above support  
                        "position_sizing": "Risk 1-2% of portfolio"
                    }
                },
                
                "next_action": f"Watch for break below {recent_30_low:.2f} with volume",
                "timeline": "Breakdown attempt likely within 1-5 days"
            }
        
        return None
    
    def _detect_trend_continuation(self, data):
        """Detect trend continuation setups based on current trend."""
        
        # Analyze trend from trend analysis
        trend_analysis = self.analyze_current_trend()
        current_trend = trend_analysis['current_trend']['direction']
        
        if "Uptrend" in current_trend:
            # Look for pullback buying opportunity
            recent_10_days = data.tail(10)
            if len(recent_10_days) < 10:
                return None
                
            pullback_low = recent_10_days['low'].min()
            trend_high = data.tail(30)['high'].max()
            
            # Check if we've pulled back enough but not too much
            pullback_pct = (trend_high - pullback_low) / trend_high * 100
            
            if 3 < pullback_pct < 15:  # 3-15% pullback is healthy
                sma_20 = data['close'].rolling(20).mean().iloc[-1] if len(data) >= 20 else self.current_price
                
                return {
                    "pattern_id": f"TREND_CONTINUATION_BULLISH_CURRENT",
                    "pattern_name": "Bullish Trend Continuation",
                    "pattern_type": "Trend Continuation", 
                    "status": "Currently in Pullback Phase",
                    "expected_direction": "Bullish continuation expected",
                    "reliability_score": "High (80%)",
                    
                    "current_structure": {
                        "trend_direction": "Uptrend",
                        "pullback_percentage": f"{pullback_pct:.1f}%",
                        "pullback_low": round(pullback_low, 2),
                        "trend_high": round(trend_high, 2),
                        "sma_20_support": round(sma_20, 2) if not pd.isna(sma_20) else "N/A"
                    },
                    
                    "trading_setup": {
                        "entry_strategy": {
                            "trigger_price": round(max(sma_20, pullback_low * 1.01), 2),
                            "confirmation_needed": "Bounce from support with volume increase",
                            "target_price": round(trend_high * 1.05, 2),  # 5% above previous high
                            "stop_loss": round(pullback_low * 0.97, 2),  # 3% below pullback low
                            "position_sizing": "Risk 1.5-2.5% of portfolio"
                        }
                    },
                    
                    "next_action": f"Look for bounce from {max(sma_20, pullback_low):.2f} area",
                    "timeline": "Bounce expected within 2-7 days"
                }
        
        elif "Downtrend" in current_trend:
            # Look for rally selling opportunity
            recent_10_days = data.tail(10)
            if len(recent_10_days) < 10:
                return None
                
            rally_high = recent_10_days['high'].max()
            trend_low = data.tail(30)['low'].min()
            
            # Check if we've rallied enough but not too much
            rally_pct = (rally_high - trend_low) / trend_low * 100
            
            if 3 < rally_pct < 15:  # 3-15% rally in downtrend
                sma_20 = data['close'].rolling(20).mean().iloc[-1] if len(data) >= 20 else self.current_price
                
                return {
                    "pattern_id": f"TREND_CONTINUATION_BEARISH_CURRENT",
                    "pattern_name": "Bearish Trend Continuation",
                    "pattern_type": "Trend Continuation",
                    "status": "Currently in Rally Phase", 
                    "expected_direction": "Bearish continuation expected",
                    "reliability_score": "High (80%)",
                    
                    "current_structure": {
                        "trend_direction": "Downtrend",
                        "rally_percentage": f"{rally_pct:.1f}%",
                        "rally_high": round(rally_high, 2),
                        "trend_low": round(trend_low, 2),
                        "sma_20_resistance": round(sma_20, 2) if not pd.isna(sma_20) else "N/A"
                    },
                    
                    "trading_setup": {
                        "entry_strategy": {
                            "trigger_price": round(min(sma_20, rally_high * 0.99), 2),
                            "confirmation_needed": "Rejection from resistance with volume increase", 
                            "target_price": round(trend_low * 0.95, 2),  # 5% below previous low
                            "stop_loss": round(rally_high * 1.03, 2),  # 3% above rally high
                            "position_sizing": "Risk 1.5-2.5% of portfolio"
                        }
                    },
                    
                    "next_action": f"Look for rejection from {min(sma_20, rally_high):.2f} area",
                    "timeline": "Rejection expected within 2-7 days"
                }
        
        return None
    
    def _count_resistance_tests(self, data, resistance_level, tolerance=0.02):
        """Count how many times resistance has been tested recently."""
        count = 0
        tolerance_range = resistance_level * tolerance
        
        for i in range(len(data)):
            if abs(data['high'].iloc[i] - resistance_level) <= tolerance_range:
                count += 1
        
        return count
    
    def _count_support_tests(self, data, support_level, tolerance=0.02):
        """Count how many times support has been tested recently.""" 
        count = 0
        tolerance_range = support_level * tolerance
        
        for i in range(len(data)):
            if abs(data['low'].iloc[i] - support_level) <= tolerance_range:
                count += 1
                
        return count
    
    def generate_current_market_forecast(self):
        """Generate forward-looking forecast based on current analysis."""
        
        # Get all current analysis components
        trend_analysis = self.analyze_current_trend()
        levels_analysis = self.identify_current_support_resistance()
        active_patterns = self.detect_active_patterns()
        
        # Determine overall bias and confidence
        trend_bias = trend_analysis['current_trend']['bias']
        momentum_alignment = self._assess_momentum_alignment(trend_analysis['momentum'])
        
        # Generate forecast scenarios
        forecast_scenarios = self._generate_forecast_scenarios(
            trend_analysis, levels_analysis, active_patterns
        )
        
        return {
            "forecast_summary": {
                "analysis_date": self.current_date.strftime("%B %d, %Y"),
                "current_price": self.current_price,
                "primary_bias": trend_bias,
                "momentum_alignment": momentum_alignment,
                "active_patterns_count": len(active_patterns),
                "forecast_horizon": "5-20 trading days"
            },
            "scenarios": forecast_scenarios,
            "key_levels_to_watch": {
                "immediate_resistance": levels_analysis['current_resistance_levels'][:2],
                "immediate_support": levels_analysis['current_support_levels'][:2]
            },
            "active_setups": active_patterns
        }
    
    def _assess_momentum_alignment(self, momentum_data):
        """Assess if short, medium, and long-term momentum are aligned."""
        
        momentum_1d = momentum_data['1_day']['direction'] 
        momentum_5d = momentum_data['5_day']['direction']
        momentum_20d = momentum_data['20_day']['direction']
        
        if momentum_1d == momentum_5d == momentum_20d == "Positive":
            return "Strong Bullish Alignment"
        elif momentum_1d == momentum_5d == momentum_20d == "Negative":
            return "Strong Bearish Alignment"
        elif momentum_5d == momentum_20d:
            return f"Medium-term {momentum_5d} Alignment"
        else:
            return "Mixed - No Clear Alignment"
    
    def _generate_forecast_scenarios(self, trend_analysis, levels_analysis, active_patterns):
        """Generate specific forecast scenarios with probabilities."""
        
        scenarios = []
        
        # Get key levels
        resistance_levels = levels_analysis['current_resistance_levels']
        support_levels = levels_analysis['current_support_levels']
        
        # Primary scenario based on trend and patterns
        trend_direction = trend_analysis['current_trend']['direction']
        
        if "Uptrend" in trend_direction and resistance_levels:
            next_resistance = resistance_levels[0]['price']
            probability = 65 if trend_analysis['current_trend']['strength'] == "Strong" else 45
            
            scenarios.append({
                "scenario_name": "Bullish Continuation",
                "probability": f"{probability}%",
                "target_price": next_resistance,
                "timeline": "5-15 days",
                "trigger_conditions": f"Hold above {support_levels[0]['price'] if support_levels else self.current_price * 0.95:.2f}",
                "invalidation_level": support_levels[0]['price'] if support_levels else self.current_price * 0.95,
                "description": f"Uptrend continues toward {next_resistance:.2f} resistance"
            })
        
        elif "Downtrend" in trend_direction and support_levels:
            next_support = support_levels[0]['price']
            probability = 65 if trend_analysis['current_trend']['strength'] == "Strong" else 45
            
            scenarios.append({
                "scenario_name": "Bearish Continuation", 
                "probability": f"{probability}%",
                "target_price": next_support,
                "timeline": "5-15 days",
                "trigger_conditions": f"Break below {resistance_levels[0]['price'] if resistance_levels else self.current_price * 1.05:.2f}",
                "invalidation_level": resistance_levels[0]['price'] if resistance_levels else self.current_price * 1.05,
                "description": f"Downtrend continues toward {next_support:.2f} support"
            })
        
        # Add consolidation scenario
        if len([p for p in active_patterns if "Consolidation" in p.get('pattern_name', '')]) > 0:
            scenarios.append({
                "scenario_name": "Range-bound Consolidation",
                "probability": "35%", 
                "target_price": f"{support_levels[0]['price'] if support_levels else self.current_price * 0.95:.2f} - {resistance_levels[0]['price'] if resistance_levels else self.current_price * 1.05:.2f}",
                "timeline": "10-30 days",
                "trigger_conditions": "Rejection at resistance and support holds",
                "invalidation_level": "Break outside range",
                "description": "Price continues to trade within established range"
            })
        
        return scenarios
    
    def generate_comprehensive_current_analysis(self):
        """Generate complete current market analysis focused on TODAY and forward-looking."""
        
        print(f"🎯 Analyzing CURRENT market structure for {self.symbol} as of {self.current_date.strftime('%B %d, %Y')}...")
        
        # Core analysis components
        trend_analysis = self.analyze_current_trend()
        levels_analysis = self.identify_current_support_resistance() 
        active_patterns = self.detect_active_patterns()
        market_forecast = self.generate_current_market_forecast()
        
        # Compile comprehensive analysis
        current_analysis = {
            "analysis_summary": {
                "stock_symbol": self.symbol,
                "analysis_date": self.current_date.strftime("%B %d, %Y"),
                "analysis_focus": f"Current market structure - last {self.analysis_window} days",
                "current_price": round(self.current_price, 2),
                "analysis_window": f"{self.analysis_window} days",
                "market_session": "Regular Trading Hours" # Could be enhanced with actual market hours
            },
            
            "current_market_structure": trend_analysis,
            "current_key_levels": levels_analysis,
            "active_patterns": active_patterns,
            "forward_looking_forecast": market_forecast,
            
            "immediate_trading_plan": self._generate_immediate_trading_plan(
                trend_analysis, levels_analysis, active_patterns, market_forecast
            ),
            
            "risk_management": self._generate_risk_management_plan(
                levels_analysis, active_patterns
            )
        }
        
        return current_analysis
    
    def _generate_immediate_trading_plan(self, trend, levels, patterns, forecast):
        """Generate specific actions to take in next 1-5 days."""
        
        immediate_actions = []
        
        # Based on active patterns
        for pattern in patterns:
            setup = pattern.get('trading_setup', {})
            if 'entry_strategy' in setup:
                entry = setup['entry_strategy']
                immediate_actions.append({
                    "action_type": "Pattern Setup",
                    "priority": "High",
                    "specific_action": pattern.get('next_action', 'Monitor pattern development'),
                    "trigger_price": entry.get('trigger_price'),
                    "timeline": pattern.get('timeline', 'Next 5 days'),
                    "pattern_type": pattern.get('pattern_name')
                })
        
        # Based on key levels
        resistance_levels = levels['current_resistance_levels']
        support_levels = levels['current_support_levels']
        
        if resistance_levels:
            next_res = resistance_levels[0]
            if next_res['distance_percent'] < 5:  # Within 5%
                immediate_actions.append({
                    "action_type": "Level Watch",
                    "priority": "High", 
                    "specific_action": f"Watch for reaction at resistance {next_res['price']:.2f}",
                    "trigger_price": next_res['price'],
                    "timeline": "Next 2-5 days",
                    "level_type": "Resistance"
                })
        
        if support_levels:
            next_sup = support_levels[0]
            if next_sup['distance_percent'] < 5:  # Within 5%
                immediate_actions.append({
                    "action_type": "Level Watch",
                    "priority": "High",
                    "specific_action": f"Watch for reaction at support {next_sup['price']:.2f}",
                    "trigger_price": next_sup['price'],
                    "timeline": "Next 2-5 days", 
                    "level_type": "Support"
                })
        
        return {
            "trading_bias": trend['current_trend']['bias'],
            "immediate_actions": immediate_actions,
            "position_recommendations": {
                "current_stance": self._determine_current_stance(trend, patterns),
                "position_sizing": "Conservative" if len(patterns) == 0 else "Moderate",
                "hold_period": "5-20 days for pattern completion"
            }
        }
    
    def _determine_current_stance(self, trend, patterns):
        """Determine whether to be long, short, or neutral right now."""
        
        trend_bias = trend['current_trend']['bias']
        bullish_patterns = len([p for p in patterns if 'Bullish' in p.get('expected_direction', '')])
        bearish_patterns = len([p for p in patterns if 'Bearish' in p.get('expected_direction', '')])
        
        if "Bullish" in trend_bias and bullish_patterns > bearish_patterns:
            return "Long Bias - Look for buying opportunities"
        elif "Bearish" in trend_bias and bearish_patterns > bullish_patterns:
            return "Short Bias - Look for selling opportunities"
        else:
            return "Neutral - Wait for clear setup"
    
    def _generate_risk_management_plan(self, levels, patterns):
        """Generate specific risk management based on current levels and patterns."""
        
        support_levels = levels['current_support_levels']
        resistance_levels = levels['current_resistance_levels']
        
        # Determine stop levels
        if support_levels:
            primary_stop_long = support_levels[0]['price'] * 0.99  # Just below support
        else:
            primary_stop_long = self.current_price * 0.95  # 5% stop
            
        if resistance_levels:
            primary_stop_short = resistance_levels[0]['price'] * 1.01  # Just above resistance
        else:
            primary_stop_short = self.current_price * 1.05  # 5% stop
        
        return {
            "stop_loss_levels": {
                "for_long_positions": round(primary_stop_long, 2),
                "for_short_positions": round(primary_stop_short, 2),
                "trailing_stop_recommendation": "Use 3-5% trailing stop once in profit"
            },
            "position_sizing": {
                "maximum_risk_per_trade": "2% of portfolio",
                "recommended_risk": "1-1.5% for current setups",
                "concentration_limit": f"Maximum 5% of portfolio in {self.symbol}"
            },
            "exit_strategy": {
                "profit_target_1": resistance_levels[0]['price'] if resistance_levels else self.current_price * 1.05,
                "profit_target_2": resistance_levels[1]['price'] if len(resistance_levels) > 1 else self.current_price * 1.10,
                "partial_exit_rule": "Take 50% profits at first target, let rest run"
            }
        }


def generate_current_market_analysis(df, symbol, analysis_window=60):
    """
    Main function to generate current market analysis.
    This replaces the old historical pattern detection approach.
    """
    
    analyzer = CurrentMarketAnalyzer(df, symbol, analysis_window)
    analysis = analyzer.generate_comprehensive_current_analysis()
    
    # Save to JSON with current date
    filename = f"{symbol}_current_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2, cls=NpEncoder)
    
    print(f"✅ Current market analysis saved to: {filename}")
    return analysis


if __name__ == "__main__":
    # Example usage - this would be called by your main agent
    print("🎯 Current Market Analyzer - Focus on TODAY and Forward-Looking Analysis")
    print("=" * 80)
    print("This analyzer focuses ONLY on:")
    print("• Current active patterns (forming now)")
    print("• Recent support/resistance levels (last 60 days)")  
    print("• Forward-looking projections (next 5-20 days)")
    print("• Immediate trading opportunities (next 1-5 days)")
    print("=" * 80)