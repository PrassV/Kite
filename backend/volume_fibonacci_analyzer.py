import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

class VolumeAnalyzer:
    """
    Comprehensive volume analysis for validating patterns and identifying unusual activity.
    """
    
    def __init__(self, df):
        self.df = df
        self.volume = df['volume'] if 'volume' in df.columns else None
        self.close = df['close']
        self.high = df['high']
        self.low = df['low']
        
        if self.volume is None:
            logging.warning("No volume data available - volume analysis will be limited")
    
    def analyze_volume_profile(self, lookback_days=30):
        """Analyze volume profile and identify key volume levels."""
        
        if self.volume is None:
            return {"error": "No volume data available"}
        
        recent_data = self.df.tail(lookback_days)
        
        # Calculate volume statistics
        avg_volume = recent_data['volume'].mean()
        volume_std = recent_data['volume'].std()
        current_volume = recent_data['volume'].iloc[-1]
        
        # Volume trend
        volume_ma_10 = recent_data['volume'].rolling(10).mean().iloc[-1] if len(recent_data) >= 10 else avg_volume
        volume_ma_20 = recent_data['volume'].rolling(20).mean().iloc[-1] if len(recent_data) >= 20 else avg_volume
        
        # Classify current volume
        if current_volume > avg_volume + 2 * volume_std:
            volume_assessment = "Extremely High"
            volume_significance = "Major institutional activity - very significant"
        elif current_volume > avg_volume + volume_std:
            volume_assessment = "High"
            volume_significance = "Above normal activity - significant"
        elif current_volume < avg_volume - volume_std:
            volume_assessment = "Low"
            volume_significance = "Below normal activity - lack of interest"
        else:
            volume_assessment = "Normal"
            volume_significance = "Average trading activity"
        
        # Volume trend assessment
        if volume_ma_10 > volume_ma_20 * 1.15:
            volume_trend = "Increasing"
            trend_significance = "Growing interest - bullish for continuation"
        elif volume_ma_10 < volume_ma_20 * 0.85:
            volume_trend = "Decreasing"
            trend_significance = "Declining interest - potential exhaustion"
        else:
            volume_trend = "Stable"
            trend_significance = "Consistent participation levels"
        
        return {
            "current_volume": int(current_volume),
            "average_volume_30d": int(avg_volume),
            "volume_assessment": volume_assessment,
            "volume_significance": volume_significance,
            "volume_trend": volume_trend,
            "trend_significance": trend_significance,
            "volume_ratio_to_average": round(current_volume / avg_volume, 2),
            "volume_ma_10": int(volume_ma_10),
            "volume_ma_20": int(volume_ma_20)
        }
    
    def identify_volume_confirmation(self, price_moves):
        """Identify if volume confirms price moves."""
        
        if self.volume is None:
            return {"error": "No volume data available"}
        
        confirmations = []
        recent_data = self.df.tail(20)  # Last 20 days
        
        for i in range(1, len(recent_data)):
            prev_close = recent_data['close'].iloc[i-1]
            curr_close = recent_data['close'].iloc[i]
            curr_volume = recent_data['volume'].iloc[i]
            avg_volume = recent_data['volume'].rolling(10).mean().iloc[i]
            
            price_change_pct = (curr_close - prev_close) / prev_close * 100
            volume_ratio = curr_volume / avg_volume if avg_volume > 0 else 1
            
            # Significant price moves (>1%)
            if abs(price_change_pct) > 1:
                if price_change_pct > 0:  # Up move
                    if volume_ratio > 1.2:  # 20% above average
                        confirmation_status = "Confirmed"
                        significance = "Bullish move confirmed by volume"
                    else:
                        confirmation_status = "Weak"
                        significance = "Bullish move but weak volume"
                else:  # Down move
                    if volume_ratio > 1.2:  # 20% above average
                        confirmation_status = "Confirmed"
                        significance = "Bearish move confirmed by volume"
                    else:
                        confirmation_status = "Weak"
                        significance = "Bearish move but weak volume"
                
                confirmations.append({
                    "date": recent_data.index[i].strftime("%Y-%m-%d"),
                    "price_change_pct": round(price_change_pct, 2),
                    "volume_ratio": round(volume_ratio, 2),
                    "confirmation_status": confirmation_status,
                    "significance": significance
                })
        
        # Get recent confirmations (last 5)
        recent_confirmations = confirmations[-5:] if confirmations else []
        
        # Overall volume-price relationship
        confirmed_moves = len([c for c in recent_confirmations if c['confirmation_status'] == 'Confirmed'])
        total_moves = len(recent_confirmations)
        
        if total_moves > 0:
            confirmation_rate = confirmed_moves / total_moves * 100
            if confirmation_rate > 70:
                overall_assessment = "Strong volume-price correlation"
            elif confirmation_rate > 50:
                overall_assessment = "Moderate volume-price correlation"
            else:
                overall_assessment = "Weak volume-price correlation"
        else:
            overall_assessment = "Insufficient data for assessment"
        
        return {
            "recent_confirmations": recent_confirmations,
            "confirmation_rate": f"{confirmation_rate:.0f}%" if total_moves > 0 else "N/A",
            "overall_assessment": overall_assessment
        }
    
    def detect_volume_anomalies(self, lookback_days=30):
        """Detect unusual volume spikes that might indicate significant events."""
        
        if self.volume is None:
            return {"error": "No volume data available"}
        
        recent_data = self.df.tail(lookback_days)
        avg_volume = recent_data['volume'].mean()
        volume_std = recent_data['volume'].std()
        
        anomalies = []
        
        for i in range(len(recent_data)):
            date = recent_data.index[i]
            volume = recent_data['volume'].iloc[i]
            close = recent_data['close'].iloc[i]
            
            # Calculate z-score
            z_score = (volume - avg_volume) / volume_std if volume_std > 0 else 0
            
            # Identify anomalies (z-score > 2 = unusual, > 3 = extreme)
            if z_score > 3:
                anomaly_type = "Extreme Volume Spike"
                significance = "Major institutional activity or news event"
            elif z_score > 2:
                anomaly_type = "High Volume"
                significance = "Unusual trading activity"
            elif z_score < -2:
                anomaly_type = "Extremely Low Volume"
                significance = "Very low interest - potential holiday or news vacuum"
            else:
                continue
            
            anomalies.append({
                "date": date.strftime("%Y-%m-%d"),
                "volume": int(volume),
                "z_score": round(z_score, 2),
                "anomaly_type": anomaly_type,
                "significance": significance,
                "price": round(close, 2),
                "volume_ratio": round(volume / avg_volume, 2)
            })
        
        # Sort by date (most recent first)
        anomalies = sorted(anomalies, key=lambda x: x['date'], reverse=True)
        
        return {
            "volume_anomalies": anomalies[:10],  # Last 10 anomalies
            "average_volume": int(avg_volume),
            "volume_std": int(volume_std)
        }


class FibonacciAnalyzer:
    """
    Fibonacci retracement and extension analysis for current market structure.
    """
    
    def __init__(self, df):
        self.df = df
        self.close = df['close']
        self.high = df['high']
        self.low = df['low']
        
        # Standard Fibonacci ratios
        self.fib_ratios = [0.0, 0.236, 0.382, 0.500, 0.618, 0.786, 1.0]
        self.fib_extensions = [1.272, 1.414, 1.618, 2.0, 2.618]
    
    def find_significant_swings(self, lookback_days=60, min_swing_pct=3):
        """Find significant price swings for Fibonacci analysis."""
        
        recent_data = self.df.tail(lookback_days)
        swings = []
        
        # Simple swing detection - look for significant highs and lows
        for i in range(5, len(recent_data) - 5):  # Leave buffer on both sides
            current_high = recent_data['high'].iloc[i]
            current_low = recent_data['low'].iloc[i]
            current_date = recent_data.index[i]
            
            # Check if it's a swing high
            is_swing_high = all(current_high >= recent_data['high'].iloc[i-j] for j in range(1, 6)) and \
                           all(current_high >= recent_data['high'].iloc[i+j] for j in range(1, 6))
            
            # Check if it's a swing low  
            is_swing_low = all(current_low <= recent_data['low'].iloc[i-j] for j in range(1, 6)) and \
                          all(current_low <= recent_data['low'].iloc[i+j] for j in range(1, 6))
            
            if is_swing_high:
                swings.append({
                    'type': 'high',
                    'price': current_high,
                    'date': current_date,
                    'index': i
                })
            
            if is_swing_low:
                swings.append({
                    'type': 'low', 
                    'price': current_low,
                    'date': current_date,
                    'index': i
                })
        
        # Sort by date
        swings = sorted(swings, key=lambda x: x['date'])
        
        # Filter for significant swings only
        significant_swings = []
        if len(swings) > 0:
            base_price = swings[0]['price']
            significant_swings.append(swings[0])
            
            for swing in swings[1:]:
                price_change_pct = abs(swing['price'] - base_price) / base_price * 100
                if price_change_pct >= min_swing_pct:
                    significant_swings.append(swing)
                    base_price = swing['price']
        
        return significant_swings[-6:]  # Last 6 significant swings
    
    def calculate_fibonacci_retracements(self, swing_high, swing_low, current_trend="up"):
        """Calculate Fibonacci retracement levels."""
        
        high_price = swing_high['price']
        low_price = swing_low['price']
        price_range = high_price - low_price
        
        retracements = []
        
        for ratio in self.fib_ratios:
            if current_trend == "up":
                # In uptrend, retracements are down from the high
                level_price = high_price - (price_range * ratio)
                level_type = f"Retracement {ratio*100:.1f}%"
            else:
                # In downtrend, retracements are up from the low
                level_price = low_price + (price_range * ratio)
                level_type = f"Retracement {ratio*100:.1f}%"
            
            retracements.append({
                'level': level_type,
                'price': round(level_price, 2),
                'ratio': ratio,
                'significance': self._get_fib_significance(ratio)
            })
        
        return {
            'swing_high': {
                'price': high_price,
                'date': swing_high['date'].strftime("%Y-%m-%d")
            },
            'swing_low': {
                'price': low_price,
                'date': swing_low['date'].strftime("%Y-%m-%d")
            },
            'trend_direction': current_trend,
            'price_range': round(price_range, 2),
            'retracement_levels': retracements
        }
    
    def calculate_fibonacci_extensions(self, swing_high, swing_low, current_trend="up"):
        """Calculate Fibonacci extension levels for price targets."""
        
        high_price = swing_high['price']
        low_price = swing_low['price']
        price_range = high_price - low_price
        
        extensions = []
        
        for ratio in self.fib_extensions:
            if current_trend == "up":
                # Extensions above the swing high
                level_price = high_price + (price_range * (ratio - 1))
                level_type = f"Extension {ratio*100:.1f}%"
            else:
                # Extensions below the swing low
                level_price = low_price - (price_range * (ratio - 1))
                level_type = f"Extension {ratio*100:.1f}%"
            
            extensions.append({
                'level': level_type,
                'price': round(level_price, 2),
                'ratio': ratio,
                'significance': self._get_extension_significance(ratio)
            })
        
        return {
            'swing_high': {
                'price': high_price,
                'date': swing_high['date'].strftime("%Y-%m-%d")
            },
            'swing_low': {
                'price': low_price,
                'date': swing_low['date'].strftime("%Y-%m-%d")
            },
            'trend_direction': current_trend,
            'extension_levels': extensions
        }
    
    def _get_fib_significance(self, ratio):
        """Get significance description for Fibonacci ratios."""
        significance_map = {
            0.236: "Shallow retracement - strong trend",
            0.382: "Moderate retracement - common level",
            0.500: "Half retracement - psychological level", 
            0.618: "Golden ratio - key reversal level",
            0.786: "Deep retracement - trend weakness"
        }
        return significance_map.get(ratio, "Reference level")
    
    def _get_extension_significance(self, ratio):
        """Get significance description for Fibonacci extensions."""
        significance_map = {
            1.272: "Common first target",
            1.414: "Secondary target level",
            1.618: "Golden ratio target - major level",
            2.0: "Double extension - psychological target",
            2.618: "Extended target - momentum extreme"
        }
        return significance_map.get(ratio, "Extension target")
    
    def analyze_current_fibonacci_levels(self, current_price):
        """Analyze current position relative to Fibonacci levels."""
        
        # Find recent significant swings
        swings = self.find_significant_swings()
        
        if len(swings) < 2:
            return {"error": "Insufficient swing data for Fibonacci analysis"}
        
        # Find the most recent major swing
        recent_highs = [s for s in swings if s['type'] == 'high']
        recent_lows = [s for s in swings if s['type'] == 'low']
        
        if not recent_highs or not recent_lows:
            return {"error": "No significant highs or lows found"}
        
        # Get most recent high and low
        latest_high = max(recent_highs, key=lambda x: x['date'])
        latest_low = max(recent_lows, key=lambda x: x['date'])
        
        # Determine current trend based on which came last
        if latest_high['date'] > latest_low['date']:
            current_trend = "down"  # High came after low, so we're in potential downtrend
            swing_high = latest_high
            swing_low = latest_low
        else:
            current_trend = "up"  # Low came after high, so we're in potential uptrend  
            swing_high = latest_high
            swing_low = latest_low
        
        # Calculate retracements and extensions
        retracements = self.calculate_fibonacci_retracements(swing_high, swing_low, current_trend)
        extensions = self.calculate_fibonacci_extensions(swing_high, swing_low, current_trend)
        
        # Find closest levels to current price
        all_levels = retracements['retracement_levels'] + extensions['extension_levels']
        
        # Add distance to current price
        for level in all_levels:
            distance = abs(level['price'] - current_price)
            distance_pct = distance / current_price * 100
            level['distance_from_current'] = round(distance, 2)
            level['distance_percent'] = round(distance_pct, 2)
        
        # Sort by distance to current price
        all_levels.sort(key=lambda x: x['distance_percent'])
        
        # Find current level context
        current_context = self._get_current_level_context(current_price, all_levels[:5])
        
        return {
            'current_fibonacci_analysis': {
                'current_price': current_price,
                'trend_direction': current_trend,
                'most_recent_swing_high': {
                    'price': swing_high['price'],
                    'date': swing_high['date'].strftime("%Y-%m-%d")
                },
                'most_recent_swing_low': {
                    'price': swing_low['price'],
                    'date': swing_low['date'].strftime("%Y-%m-%d")
                }
            },
            'fibonacci_retracements': retracements,
            'fibonacci_extensions': extensions,
            'closest_levels': all_levels[:5],  # 5 closest levels
            'current_level_context': current_context
        }
    
    def _get_current_level_context(self, current_price, closest_levels):
        """Determine where current price is relative to key Fibonacci levels."""
        
        if not closest_levels:
            return "No nearby Fibonacci levels identified"
        
        closest_level = closest_levels[0]
        
        if closest_level['distance_percent'] < 1:  # Within 1%
            return f"Currently near {closest_level['level']} at ₹{closest_level['price']} - {closest_level['significance']}"
        elif closest_level['distance_percent'] < 3:  # Within 3%
            direction = "above" if current_price > closest_level['price'] else "below"
            return f"Currently {direction} {closest_level['level']} (₹{closest_level['price']}) by {closest_level['distance_percent']:.1f}%"
        else:
            return f"Between Fibonacci levels - closest is {closest_level['level']} at ₹{closest_level['price']}"


class EnhancedCurrentMarketAnalyzer:
    """
    Enhanced version of CurrentMarketAnalyzer with Volume and Fibonacci analysis.
    """
    
    def __init__(self, df, symbol="UNKNOWN", analysis_window=60):
        self.df = df.tail(analysis_window * 2)  # Extra buffer
        self.current_df = df.tail(analysis_window)
        self.symbol = symbol
        self.analysis_window = analysis_window
        self.current_price = df['close'].iloc[-1]
        self.current_date = df.index[-1]
        
        # Initialize analyzers
        self.volume_analyzer = VolumeAnalyzer(self.current_df)
        self.fibonacci_analyzer = FibonacciAnalyzer(self.current_df)
        
        # Import the original analyzer components
        from current_market_analyzer import CurrentMarketAnalyzer
        self.base_analyzer = CurrentMarketAnalyzer(df, symbol, analysis_window)
    
    def analyze_volume_structure(self):
        """Comprehensive volume analysis for current market structure."""
        
        volume_profile = self.volume_analyzer.analyze_volume_profile()
        volume_confirmations = self.volume_analyzer.identify_volume_confirmation(None)
        volume_anomalies = self.volume_analyzer.detect_volume_anomalies()
        
        return {
            "volume_profile": volume_profile,
            "volume_price_confirmation": volume_confirmations,
            "recent_volume_anomalies": volume_anomalies
        }
    
    def analyze_fibonacci_structure(self):
        """Comprehensive Fibonacci analysis for current market structure."""
        
        fibonacci_analysis = self.fibonacci_analyzer.analyze_current_fibonacci_levels(self.current_price)
        
        return fibonacci_analysis
    
    def generate_enhanced_pattern_analysis(self):
        """Enhanced pattern analysis with volume and Fibonacci confirmation."""
        
        # Get base pattern analysis
        base_patterns = self.base_analyzer.detect_active_patterns()
        
        # Get volume and Fibonacci analysis
        volume_analysis = self.analyze_volume_structure()
        fibonacci_analysis = self.analyze_fibonacci_structure()
        
        # Enhance each pattern with volume and Fibonacci confirmation
        enhanced_patterns = []
        
        for pattern in base_patterns:
            enhanced_pattern = pattern.copy()
            
            # Add volume confirmation
            volume_profile = volume_analysis.get('volume_profile', {})
            if not isinstance(volume_profile, dict) or 'error' not in volume_profile:
                enhanced_pattern['volume_confirmation'] = {
                    'current_volume_assessment': volume_profile.get('volume_assessment', 'N/A'),
                    'volume_trend': volume_profile.get('volume_trend', 'N/A'),
                    'volume_significance': volume_profile.get('volume_significance', 'N/A'),
                    'pattern_volume_support': self._assess_pattern_volume_support(pattern, volume_profile)
                }
            
            # Add Fibonacci support
            if not isinstance(fibonacci_analysis, dict) or 'error' not in fibonacci_analysis:
                fib_support = self._assess_fibonacci_support(pattern, fibonacci_analysis)
                enhanced_pattern['fibonacci_confirmation'] = fib_support
            
            enhanced_patterns.append(enhanced_pattern)
        
        return enhanced_patterns
    
    def _assess_pattern_volume_support(self, pattern, volume_profile):
        """Assess if volume supports the pattern."""
        
        pattern_type = pattern.get('pattern_name', '')
        volume_assessment = volume_profile.get('volume_assessment', 'Normal')
        volume_trend = volume_profile.get('volume_trend', 'Stable')
        
        if 'Breakout' in pattern_type:
            if volume_assessment in ['High', 'Extremely High']:
                return "Strong volume support - breakout likely genuine"
            else:
                return "Weak volume support - breakout may fail"
        
        elif 'Consolidation' in pattern_type:
            if volume_trend == 'Decreasing':
                return "Volume declining during consolidation - healthy pattern"
            else:
                return "Volume not declining - pattern may be weaker"
        
        elif 'Continuation' in pattern_type:
            if volume_assessment == 'High' and volume_trend == 'Increasing':
                return "Strong volume support - continuation likely"
            else:
                return "Moderate volume support - watch for confirmation"
        
        return "Volume analysis neutral for this pattern"
    
    def _assess_fibonacci_support(self, pattern, fibonacci_analysis):
        """Assess if Fibonacci levels support the pattern."""
        
        if isinstance(fibonacci_analysis, dict) and 'error' in fibonacci_analysis:
            return {"error": "Insufficient data for Fibonacci analysis"}
        
        closest_levels = fibonacci_analysis.get('closest_levels', [])
        current_context = fibonacci_analysis.get('current_level_context', '')
        
        pattern_price_levels = []
        
        # Extract key price levels from pattern
        trading_setup = pattern.get('trading_setup', {})
        if trading_setup:
            for setup_name, setup_data in trading_setup.items():
                if isinstance(setup_data, dict):
                    if 'trigger_price' in setup_data:
                        pattern_price_levels.append(('trigger', setup_data['trigger_price']))
                    if 'target_price' in setup_data:
                        pattern_price_levels.append(('target', setup_data['target_price']))
                    if 'stop_loss' in setup_data:
                        pattern_price_levels.append(('stop', setup_data['stop_loss']))
        
        # Check if pattern levels align with Fibonacci levels
        fibonacci_alignments = []
        
        for level_type, price in pattern_price_levels:
            for fib_level in closest_levels:
                distance_pct = abs(price - fib_level['price']) / price * 100
                if distance_pct < 2:  # Within 2%
                    fibonacci_alignments.append({
                        'pattern_level_type': level_type,
                        'pattern_price': price,
                        'fibonacci_level': fib_level['level'],
                        'fibonacci_price': fib_level['price'],
                        'alignment_strength': 'Strong' if distance_pct < 1 else 'Moderate',
                        'significance': fib_level['significance']
                    })
        
        if fibonacci_alignments:
            support_assessment = f"Strong Fibonacci support - {len(fibonacci_alignments)} level(s) align"
        else:
            support_assessment = "No direct Fibonacci alignment - pattern independent"
        
        return {
            'current_fibonacci_context': current_context,
            'fibonacci_alignments': fibonacci_alignments,
            'support_assessment': support_assessment,
            'nearest_fibonacci_levels': closest_levels[:3]
        }
    
    def generate_enhanced_comprehensive_analysis(self):
        """Generate comprehensive analysis with volume and Fibonacci integration."""
        
        print(f"🎯 Generating ENHANCED current market analysis for {self.symbol}...")
        
        # Get base analysis
        base_analysis = self.base_analyzer.generate_comprehensive_current_analysis()
        
        # Add volume analysis
        volume_analysis = self.analyze_volume_structure()
        
        # Add Fibonacci analysis
        fibonacci_analysis = self.analyze_fibonacci_structure()
        
        # Get enhanced patterns
        enhanced_patterns = self.generate_enhanced_pattern_analysis()
        
        # Create enhanced analysis
        enhanced_analysis = base_analysis.copy()
        
        # Add new sections
        enhanced_analysis['volume_analysis'] = volume_analysis
        enhanced_analysis['fibonacci_analysis'] = fibonacci_analysis
        enhanced_analysis['active_patterns'] = enhanced_patterns
        
        # Enhance immediate trading plan with volume and Fibonacci
        enhanced_analysis['immediate_trading_plan'] = self._enhance_trading_plan(
            base_analysis.get('immediate_trading_plan', {}),
            volume_analysis,
            fibonacci_analysis
        )
        
        return enhanced_analysis
    
    def _enhance_trading_plan(self, base_plan, volume_analysis, fibonacci_analysis):
        """Enhance trading plan with volume and Fibonacci insights."""
        
        enhanced_plan = base_plan.copy()
        
        # Add volume-based recommendations
        volume_profile = volume_analysis.get('volume_profile', {})
        if not isinstance(volume_profile, dict) or 'error' not in volume_profile:
            volume_recommendations = []
            
            volume_assessment = volume_profile.get('volume_assessment', 'Normal')
            if volume_assessment == 'Extremely High':
                volume_recommendations.append({
                    'recommendation': 'High volume detected - significant move likely',
                    'action': 'Watch for continuation with sustained volume',
                    'significance': 'Major institutional activity'
                })
            elif volume_assessment == 'Low':
                volume_recommendations.append({
                    'recommendation': 'Low volume detected - moves may not sustain',
                    'action': 'Wait for volume confirmation before entering',
                    'significance': 'Lack of institutional interest'
                })
            
            enhanced_plan['volume_based_recommendations'] = volume_recommendations
        
        # Add Fibonacci-based levels
        if not isinstance(fibonacci_analysis, dict) or 'error' not in fibonacci_analysis:
            closest_levels = fibonacci_analysis.get('closest_levels', [])[:3]
            enhanced_plan['fibonacci_key_levels'] = [
                {
                    'level_name': level['level'],
                    'price': level['price'],
                    'significance': level['significance'],
                    'distance_percent': level['distance_percent']
                } for level in closest_levels
            ]
        
        return enhanced_plan


def generate_enhanced_current_market_analysis(df, symbol, analysis_window=60):
    """
    Main function to generate enhanced current market analysis with Volume and Fibonacci.
    """
    
    analyzer = EnhancedCurrentMarketAnalyzer(df, symbol, analysis_window)
    analysis = analyzer.generate_enhanced_comprehensive_analysis()
    
    # Save to JSON with current date and time
    filename = f"{symbol}_enhanced_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    
    # Use the NpEncoder from detector.py for JSON serialization
    from detector import NpEncoder
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2, cls=NpEncoder)
    
    print(f"✅ Enhanced current market analysis saved to: {filename}")
    return analysis


if __name__ == "__main__":
    print("🚀 Enhanced Current Market Analyzer")
    print("=" * 60)
    print("NEW FEATURES:")
    print("📊 Volume Analysis:")
    print("  • Volume profile and trend analysis")
    print("  • Volume-price confirmation tracking")  
    print("  • Unusual volume spike detection")
    print("  • Pattern validation with volume")
    print()
    print("📐 Fibonacci Analysis:")
    print("  • Automatic swing detection") 
    print("  • Retracement level calculation")
    print("  • Extension targets")
    print("  • Current position relative to Fib levels")
    print("  • Pattern confirmation with Fibonacci")
    print("=" * 60)