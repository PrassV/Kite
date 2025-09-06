import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import curve_fit
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')
from itertools import combinations
import logging
import json
from datetime import datetime

# ADD THIS HELPER CLASS
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        return super(NpEncoder, self).default(obj)

class DeterministicPatternDetector:
    def __init__(self, data):
        """
        Initialize with stock price data
        data: pandas Series or numpy array of prices
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input 'data' must be a pandas DataFrame.")
        
        self.df = data
        self.prices = data['close'].values
        self.dates = data.index
        #self.prices = np.array(data)
        self.smoothed_prices = None
        self.slopes = None
        self.curvature = None
        self.peaks = []
        self.valleys = []
        self.patterns = []
        
        self.params = {
        'gaussian_sigma': 2,
        'peak_valley_min_distance': 5,
        'prominence_threshold': 0.5
    }
        
    def gaussian_smooth(self, sigma=2):
        """
        Apply Gaussian smoothing to remove noise
        Formula: S(i) = Σ P(i+j) × e^(-j²/2σ²) / Σ e^(-j²/2σ²)
        """
        self.smoothed_prices = gaussian_filter1d(self.prices, sigma=sigma)
        return self.smoothed_prices
    
    def calculate_derivatives(self):
        """
        Calculate first and second derivatives (slope and curvature)
        First derivative: slope(i) = (P(i+1) - P(i-1)) / 2
        Second derivative: curvature(i) = slope(i+1) - slope(i-1)
        """
        # First derivative (slope)
        self.slopes = np.gradient(self.smoothed_prices)
        
        # Second derivative (curvature)
        self.curvature = np.gradient(self.slopes)
        
        return self.slopes, self.curvature
    
    # REPLACE this method in DeterministicPatternDetector
    def find_peaks_valleys(self, min_distance=5, prominence_threshold=0.5):
        """
        Find local maxima and minima, returning structured dictionaries.
        """
        self.params['peak_valley_min_distance'] = min_distance
        self.params['prominence_threshold'] = prominence_threshold

        peak_indices, peak_props = signal.find_peaks(
            self.smoothed_prices,
            distance=min_distance,
            prominence=prominence_threshold
        )
        valley_indices, valley_props = signal.find_peaks(
            -self.smoothed_prices,
            distance=min_distance,
            prominence=prominence_threshold
        )

        self.peaks = [{
            "index": int(idx),
            "date": self.dates[idx],
            "price": self.smoothed_prices[idx],
            "confirmation_method": "local_maxima",
            "strength": peak_props['prominences'][i]
        } for i, idx in enumerate(peak_indices)]

        self.valleys = [{
            "index": int(idx),
            "date": self.dates[idx],
            "price": self.smoothed_prices[idx],
            "confirmation_method": "local_minima",
            "strength": valley_props['prominences'][i]
        } for i, idx in enumerate(valley_indices)]

        return self.peaks, self.valleys
    
    def euclidean_distance(self, pattern1, pattern2):
        """
        Calculate Euclidean distance between two patterns
        d = √(Σ(pattern₁(i) - pattern₂(i))²)
        """
        if len(pattern1) != len(pattern2):
            return float('inf')
        
        return np.sqrt(np.sum((pattern1 - pattern2) ** 2))
    
    def normalize_pattern(self, pattern):
        """
        Normalize pattern to 0-1 range for comparison
        """
        pattern = np.array(pattern)
        min_val, max_val = pattern.min(), pattern.max()
        if max_val == min_val:
            return np.zeros_like(pattern)
        return (pattern - min_val) / (max_val - min_val)
    
    def calculate_trend_line(self, points):
        """
        Calculate trend line using least squares regression
        y = mx + b where m = (nΣxy - ΣxΣy) / (nΣx² - (Σx)²)
        """
        if len(points) < 2:
            return 0, 0
        
        # Handle both tuple format (index, price) and dict format
        if isinstance(points[0], dict):
            x = np.array([p['index'] for p in points])
            y = np.array([p['price'] for p in points])
        else:
            x = np.array([p[0] for p in points])
            y = np.array([p[1] for p in points])
        
        n = len(points)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x ** 2)
        
        if n * sum_x2 - sum_x ** 2 == 0:
            return 0, y[0]
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        return slope, intercept
    
    # REPLACE this method in DeterministicPatternDetector
    def detect_head_and_shoulders(self, tolerance=0.05):
        """
        Detects Head and Shoulders patterns and returns detailed dictionaries for
        both valid and failed attempts, explaining the mathematical reasoning.
        """
        valid_patterns = []
        failed_patterns = []
        
        for i in range(len(self.peaks) - 2):
            p1, p2, p3 = self.peaks[i], self.peaks[i+1], self.peaks[i+2]
            
            v1_candidates = [v for v in self.valleys if p1['index'] < v['index'] < p2['index']]
            v2_candidates = [v for v in self.valleys if p2['index'] < v['index'] < p3['index']]

            if not v1_candidates or not v2_candidates: continue

            v1 = min(v1_candidates, key=lambda x: x['price'])
            v2 = min(v2_candidates, key=lambda x: x['price'])
            
            ls_p, h_p, rs_p = p1['price'], p2['price'], p3['price']
            nl_p, nr_p = v1['price'], v2['price']

            # --- Detailed Mathematical Condition Checking ---
            conditions = {}
            cond1_res = h_p > ls_p and h_p > rs_p
            conditions['head_dominance'] = {"condition": "head > left_shoulder AND head > right_shoulder", "head_value": h_p, "left_shoulder_value": ls_p, "right_shoulder_value": rs_p, "result": bool(cond1_res)}

            sym_diff_pct = abs(ls_p - rs_p) / ls_p if ls_p != 0 else float('inf')
            cond2_res = sym_diff_pct < tolerance
            conditions['shoulder_symmetry'] = {"condition": f"|left_shoulder - right_shoulder| / left_shoulder < {tolerance}", "difference_percentage": sym_diff_pct, "threshold": tolerance, "result": bool(cond2_res)}

            neck_diff_pct = abs(nl_p - nr_p) / nl_p if nl_p != 0 else float('inf')
            cond3_res = neck_diff_pct < (tolerance * 0.6)
            conditions['neckline_level'] = {"condition": f"|neckline_left - neckline_right| / neckline_left < {tolerance * 0.6}", "difference_percentage": neck_diff_pct, "threshold": tolerance * 0.6, "result": bool(cond3_res)}
            
            head_sig_ratio = (h_p - max(ls_p, rs_p)) / h_p if h_p != 0 else 0
            cond4_res = head_sig_ratio > (tolerance * 0.4)
            conditions['head_significance'] = {"condition": f"(head - max(shoulders)) / head > {tolerance * 0.4}", "significance_ratio": head_sig_ratio, "threshold": tolerance * 0.4, "result": bool(cond4_res)}
            
            passing_conditions = sum(c['result'] for c in conditions.values())
            all_met = passing_conditions == len(conditions)
            
            m, c = np.polyfit([v1['index'], v2['index']], [v1['price'], v2['price']], 1)
            time_range = {"start_index": p1['index'], "end_index": p3['index'], "start_date": p1['date'], "end_date": p3['date'], "duration_days": (p3['date'] - p1['date']).days}
            key_points = {"left_shoulder": p1, "head": p2, "right_shoulder": p3, "left_valley": v1, "right_valley": v2, "neckline": {"slope": m, "equation": f"y = {m:.3f}x + {c:.2f}"}}
            final_condition = {"all_conditions_met": all_met, "passing_conditions": passing_conditions, "total_conditions": len(conditions)}
            
            if all_met:
                valid_patterns.append({"pattern_id": f"HS_{p1['index']}", "type": "Head and Shoulders", "subtype": "bearish", "time_range": time_range, "key_points": key_points, "mathematical_conditions": conditions, "final_condition": final_condition, "target_calculation": {"neckline_break_target": nr_p - (h_p - max(nl_p, nr_p)), "calculation_method": "head_height_projection"}, "start": p1['index'], "end": p3['index'], "confidence": 0.85, "bearish": True})
            else:
                failed_keys = [k for k, v in conditions.items() if not v['result']]
                final_condition['reason'] = f"Failed on: {', '.join(failed_keys)}"
                failed_patterns.append({"pattern_id": f"FAIL_HS_{p1['index']}", "attempted_type": "Head and Shoulders", "time_range": time_range, "key_points": key_points, "condition_failures": {k:v for k,v in conditions.items() if not v['result']}, "failure_summary": final_condition})

        return valid_patterns, failed_patterns
    
    def detect_double_top_bottom(self, tolerance=0.02):
        """
        Detect Double Top/Bottom patterns - FIXED to use dictionary structure
        """
        patterns = []
        
        # Double Top detection
        for i in range(len(self.peaks) - 1):
            p1, p2 = self.peaks[i], self.peaks[i + 1]
            
            height_diff = abs(p1['price'] - p2['price']) / p1['price']
            time_separation = p2['index'] - p1['index']
            
            if height_diff < tolerance and 10 < time_separation < 50:
                # Find valley between peaks
                valleys_between = [v for v in self.valleys if p1['index'] < v['index'] < p2['index']]
                
                if valleys_between:
                    valley = min(valleys_between, key=lambda x: x['price'])
                    valley_depth = (min(p1['price'], p2['price']) - valley['price']) / min(p1['price'], p2['price'])
                    
                    if valley_depth > 0.03:
                        confidence = 0.90 - height_diff * 10
                        patterns.append({
                            'type': 'Double Top',
                            'start': p1['index'],
                            'end': p2['index'],
                            'confidence': confidence,
                            'bearish': True,
                            'key_points': [p1, valley, p2]
                        })
        
        # Double Bottom detection
        for i in range(len(self.valleys) - 1):
            v1, v2 = self.valleys[i], self.valleys[i + 1]
            
            height_diff = abs(v1['price'] - v2['price']) / v1['price']
            time_separation = v2['index'] - v1['index']
            
            if height_diff < tolerance and 10 < time_separation < 50:
                # Find peak between valleys
                peaks_between = [p for p in self.peaks if v1['index'] < p['index'] < v2['index']]
                
                if peaks_between:
                    peak = max(peaks_between, key=lambda x: x['price'])
                    peak_height = (peak['price'] - max(v1['price'], v2['price'])) / max(v1['price'], v2['price'])
                    
                    if peak_height > 0.03:
                        confidence = 0.90 - height_diff * 10
                        patterns.append({
                            'type': 'Double Bottom',
                            'start': v1['index'],
                            'end': v2['index'],
                            'confidence': confidence,
                            'bullish': True,
                            'key_points': [v1, peak, v2]
                        })
        
        return patterns
    
    def detect_triangles(self, window_size=30):
        """
        Detect Triangle patterns using trend line convergence - FIXED to use dictionary structure
        """
        patterns = []
        
        for i in range(window_size, len(self.smoothed_prices) - window_size):
            window_data = self.smoothed_prices[i-window_size:i+window_size]
            window_indices = np.arange(i-window_size, i+window_size)
            
            # Find peaks and valleys in window - FIXED to use dictionary structure
            window_peaks = [p for p in self.peaks if i-window_size <= p['index'] < i+window_size]
            window_valleys = [v for v in self.valleys if i-window_size <= v['index'] < i+window_size]
            
            if len(window_peaks) >= 2 and len(window_valleys) >= 2:
                # Calculate trend lines
                upper_slope, _ = self.calculate_trend_line(window_peaks)
                lower_slope, _ = self.calculate_trend_line(window_valleys)
                
                # Ascending Triangle: flat top, rising bottom
                if abs(upper_slope) < 0.1 and lower_slope > 0.2:
                    patterns.append({
                        'type': 'Ascending Triangle',
                        'start': i - window_size,
                        'end': i + window_size,
                        'confidence': 0.88,
                        'bullish': True
                    })
                
                # Descending Triangle: falling top, flat bottom
                elif upper_slope < -0.2 and abs(lower_slope) < 0.1:
                    patterns.append({
                        'type': 'Descending Triangle',
                        'start': i - window_size,
                        'end': i + window_size,
                        'confidence': 0.88,
                        'bearish': True
                    })
        
        return patterns
    
    def detect_wedges(self, window_size=25):
        """
        Detect Rising and Falling Wedge patterns - FIXED to use dictionary structure
        """
        patterns = []
        
        for i in range(window_size, len(self.smoothed_prices) - window_size):
            window_peaks = [p for p in self.peaks if i-window_size <= p['index'] < i+window_size]
            window_valleys = [v for v in self.valleys if i-window_size <= v['index'] < i+window_size]
            
            if len(window_peaks) >= 3 and len(window_valleys) >= 3:
                upper_slope, _ = self.calculate_trend_line(window_peaks)
                lower_slope, _ = self.calculate_trend_line(window_valleys)
                
                # Rising Wedge: both slopes positive, converging upward
                if upper_slope > 0 and lower_slope > 0 and lower_slope > upper_slope:
                    patterns.append({
                        'type': 'Rising Wedge',
                        'start': i - window_size,
                        'end': i + window_size,
                        'confidence': 0.85,
                        'bearish': True
                    })
                
                # Falling Wedge: both slopes negative, converging downward
                elif upper_slope < 0 and lower_slope < 0 and upper_slope > lower_slope:
                    patterns.append({
                        'type': 'Falling Wedge',
                        'start': i - window_size,
                        'end': i + window_size,
                        'confidence': 0.85,
                        'bullish': True
                    })
        
        return patterns
    
    def detect_flags(self, pre_flag_window=20, flag_window=15):
        """
        Detect Flag patterns: strong move + counter-trend consolidation
        """
        patterns = []
        
        for i in range(pre_flag_window, len(self.smoothed_prices) - flag_window):
            # Analyze pre-flag momentum
            pre_flag_data = self.smoothed_prices[i-pre_flag_window:i]
            flag_data = self.smoothed_prices[i:i+flag_window]
            
            # Calculate momentum
            pre_flag_slope = (pre_flag_data[-1] - pre_flag_data[0]) / pre_flag_window
            flag_slope = (flag_data[-1] - flag_data[0]) / flag_window
            
            # Volatility calculations
            pre_flag_volatility = np.std(pre_flag_data)
            flag_volatility = np.std(flag_data)
            
            # Deterministic criteria
            strong_move = abs(pre_flag_slope) > 1.0
            consolidation = abs(flag_slope) < abs(pre_flag_slope) * 0.3
            lower_volatility = flag_volatility < pre_flag_volatility * 0.7
            
            if strong_move and consolidation and lower_volatility:
                pattern_type = 'Bull Flag' if pre_flag_slope > 0 else 'Bear Flag'
                patterns.append({
                    'type': pattern_type,
                    'start': i - pre_flag_window,
                    'end': i + flag_window,
                    'confidence': 0.87,
                    'bullish': pre_flag_slope > 0,
                    'bearish': pre_flag_slope < 0
                })
        
        return patterns
    
    def detect_cup_and_handle(self):
        """
        Detect Cup and Handle pattern using geometric analysis - FIXED to use dictionary structure
        """
        patterns = []
        
        for i in range(len(self.peaks) - 1):
            left_peak = self.peaks[i]
            right_peak = self.peaks[i + 1]
            
            # Find valleys between peaks (cup bottom)
            valleys_between = [v for v in self.valleys 
                              if left_peak['index'] < v['index'] < right_peak['index']]
            
            if valleys_between:
                cup_bottom = min(valleys_between, key=lambda x: x['price'])
                
                # Cup criteria
                cup_depth = (min(left_peak['price'], right_peak['price']) - cup_bottom['price']) / min(left_peak['price'], right_peak['price'])
                cup_symmetry = abs(left_peak['price'] - right_peak['price']) / left_peak['price']
                cup_duration = right_peak['index'] - left_peak['index']
                
                if 0.1 < cup_depth < 0.5 and cup_symmetry < 0.05 and cup_duration > 20:
                    # Look for handle after right peak
                    handle_start = right_peak['index']
                    handle_end = min(handle_start + 15, len(self.smoothed_prices) - 1)
                    
                    if handle_end > handle_start + 5:
                        handle_data = self.smoothed_prices[handle_start:handle_end]
                        handle_depth = (right_peak['price'] - handle_data.min()) / right_peak['price']
                        
                        if 0.02 < handle_depth < 0.15:
                            patterns.append({
                                'type': 'Cup with Handle',
                                'start': left_peak['index'],
                                'end': handle_end,
                                'confidence': 0.83,
                                'bullish': True,
                                'key_points': [left_peak, cup_bottom, right_peak]
                            })
        
        return patterns
    
    def detect_rounding_patterns(self, window_size=30):
        """
        Detect Rounding Top/Bottom using curvature analysis - FIXED to use dictionary structure
        """
        patterns = []
        
        for i in range(window_size, len(self.smoothed_prices) - window_size):
            window_data = self.smoothed_prices[i-window_size:i+window_size]
            window_curvature = self.curvature[i-window_size:i+window_size]
            
            # Check for consistent curvature (rounding)
            avg_curvature = np.mean(window_curvature)
            curvature_consistency = np.std(window_curvature)
            
            # Rounding Top: negative curvature, consistent shape
            if avg_curvature < -0.1 and curvature_consistency < 0.3:
                peak_in_window = any(p['index'] for p in self.peaks if i-window_size <= p['index'] <= i+window_size)
                if peak_in_window:
                    patterns.append({
                        'type': 'Rounding Top',
                        'start': i - window_size,
                        'end': i + window_size,
                        'confidence': 0.80,
                        'bearish': True
                    })
            
            # Rounding Bottom: positive curvature, consistent shape
            elif avg_curvature > 0.1 and curvature_consistency < 0.3:
                valley_in_window = any(v['index'] for v in self.valleys if i-window_size <= v['index'] <= i+window_size)
                if valley_in_window:
                    patterns.append({
                        'type': 'Rounding Bottom',
                        'start': i - window_size,
                        'end': i + window_size,
                        'confidence': 0.80,
                        'bullish': True
                    })
        
        return patterns
    
    def fourier_analysis(self, n_components=10):
        """
        Perform Fourier analysis to detect cyclical patterns
        """
        # Apply FFT
        fft_result = np.fft.fft(self.smoothed_prices)
        frequencies = np.fft.fftfreq(len(self.smoothed_prices))
        
        # Get dominant frequencies
        magnitudes = np.abs(fft_result)
        dominant_indices = np.argsort(magnitudes)[-n_components-1:-1]
        
        cycles = []
        for idx in dominant_indices:
            if frequencies[idx] != 0:
                period = 1 / abs(frequencies[idx])
                cycles.append({
                    'frequency': frequencies[idx],
                    'period': period,
                    'magnitude': magnitudes[idx]
                })
        
        return sorted(cycles, key=lambda x: x['magnitude'], reverse=True)
    
    def run_full_analysis(self):
        """
        Run complete deterministic pattern analysis
        """
        print("🔍 Starting Deterministic Pattern Analysis...")
        
        # Step 1: Gaussian Smoothing
        print("📊 Applying Gaussian smoothing...")
        self.gaussian_smooth(sigma=2)
        
        # Step 2: Calculate derivatives
        print("📈 Calculating slopes and curvature...")
        self.calculate_derivatives()
        
        # Step 3: Find peaks and valleys
        print("🏔️ Finding peaks and valleys...")
        self.find_peaks_valleys()
        
        # Step 4: Pattern detection
        print("🔎 Detecting patterns...")
        
        patterns = []
        # Note: detect_head_and_shoulders now returns (valid_patterns, failed_patterns)
        valid_hs, failed_hs = self.detect_head_and_shoulders()
        patterns.extend(valid_hs)
        
        patterns.extend(self.detect_double_top_bottom())
        patterns.extend(self.detect_triangles())
        patterns.extend(self.detect_wedges())
        patterns.extend(self.detect_flags())
        patterns.extend(self.detect_cup_and_handle())
        patterns.extend(self.detect_rounding_patterns())
        
        self.patterns = patterns
        
        # Step 5: Fourier analysis
        print("🌊 Performing Fourier analysis...")
        cycles = self.fourier_analysis()
        
        # Results summary
        print(f"\n✅ Analysis Complete!")
        print(f"📊 Data points analyzed: {len(self.prices)}")
        print(f"🏔️ Peaks found: {len(self.peaks)}")
        print(f"🏞️ Valleys found: {len(self.valleys)}")
        print(f"📈 Patterns detected: {len(patterns)}")
        
        if cycles:
            print(f"🌊 Dominant cycle: {cycles[0]['period']:.1f} periods")
        
        return {
            'patterns': patterns,
            'peaks': self.peaks,
            'valleys': self.valleys,
            'cycles': cycles,
            'smoothed_prices': self.smoothed_prices,
            'slopes': self.slopes,
            'curvature': self.curvature
        }
    
    def plot_results(self, figsize=(15, 10)):
        """
        Plot the analysis results - FIXED to use dictionary structure
        """
        fig, axes = plt.subplots(3, 1, figsize=figsize)
        
        # Main price chart
        x = np.arange(len(self.prices))
        axes[0].plot(x, self.prices, 'lightgray', alpha=0.7, label='Original Price')
        axes[0].plot(x, self.smoothed_prices, 'blue', linewidth=2, label='Smoothed Price')
        
        # Plot peaks and valleys - FIXED to use dictionary structure
        if self.peaks:
            peak_x = [p['index'] for p in self.peaks]
            peak_y = [p['price'] for p in self.peaks]
            axes[0].scatter(peak_x, peak_y, color='red', s=50, zorder=5, label='Peaks')
        
        if self.valleys:
            valley_x = [v['index'] for v in self.valleys]
            valley_y = [v['price'] for v in self.valleys]
            axes[0].scatter(valley_x, valley_y, color='green', s=50, zorder=5, label='Valleys')
        
        # Highlight patterns
        colors = plt.cm.Set3(np.linspace(0, 1, len(self.patterns)))
        for pattern, color in zip(self.patterns, colors):
            axes[0].axvspan(pattern['start'], pattern['end'], 
                           alpha=0.3, color=color, 
                           label=f"{pattern['type']} ({pattern['confidence']:.2f})")
        
        axes[0].set_title('Stock Price with Detected Patterns')
        axes[0].set_ylabel('Price')
        axes[0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[0].grid(True, alpha=0.3)
        
        # Slope (First Derivative)
        axes[1].plot(x[1:-1], self.slopes[1:-1], 'orange', linewidth=1)
        axes[1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[1].set_title('First Derivative (Slope/Momentum)')
        axes[1].set_ylabel('Slope')
        axes[1].grid(True, alpha=0.3)
        
        # Curvature (Second Derivative)
        axes[2].plot(x[1:-1], self.curvature[1:-1], 'purple', linewidth=1)
        axes[2].axhline(y=0, color='black', linestyle='--', alpha=0.5)
        axes[2].set_title('Second Derivative (Curvature/Acceleration)')
        axes[2].set_ylabel('Curvature')
        axes[2].set_xlabel('Time')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        return fig
    
    def pattern_summary(self):
        """
        Print detailed pattern analysis summary
        """
        print("\n" + "="*60)
        print("📋 PATTERN DETECTION SUMMARY")
        print("="*60)
        
        if not self.patterns:
            print("❌ No patterns detected with current criteria")
            return
        
        # Group patterns by type
        pattern_counts = {}
        for pattern in self.patterns:
            ptype = pattern['type']
            if ptype not in pattern_counts:
                pattern_counts[ptype] = []
            pattern_counts[ptype].append(pattern)
        
        for ptype, plist in pattern_counts.items():
            print(f"\n📊 {ptype}: {len(plist)} detected")
            for i, pattern in enumerate(plist):
                bias = "📈 Bullish" if pattern.get('bullish') else "📉 Bearish" if pattern.get('bearish') else "⚪ Neutral"
                print(f"   #{i+1}: Days {pattern['start']}-{pattern['end']}, "
                      f"Confidence: {pattern['confidence']:.1%}, {bias}")
        
        print(f"\n📊 Total Patterns: {len(self.patterns)}")
        bullish = len([p for p in self.patterns if p.get('bullish')])
        bearish = len([p for p in self.patterns if p.get('bearish')])
        print(f"📈 Bullish: {bullish} | 📉 Bearish: {bearish}")

# Example usage and testing
def generate_sample_data():
    """Generate sample stock data with embedded patterns"""
    np.random.seed(42)  # For reproducible results
    data = []
    price = 100
    
    for i in range(300):
        # Base trend and noise
        trend = np.sin(i * 0.03) * 1.5
        noise = np.random.normal(0, 2)
        
        # Embed specific patterns
        if 50 <= i <= 80:  # Head and Shoulders
            pattern_pos = (i - 50) / 30
            pattern_effect = np.sin(pattern_pos * np.pi * 3) * 8
            price += pattern_effect + trend + noise
        elif 150 <= i <= 180:  # Double Top
            pattern_pos = (i - 150) / 30
            pattern_effect = np.sin(pattern_pos * np.pi * 2) * 6
            price += pattern_effect + trend + noise
        elif 220 <= i <= 260:  # Cup and Handle
            if i <= 250:  # Cup part
                pattern_pos = (i - 220) / 30
                pattern_effect = -np.cos(pattern_pos * np.pi) * 5
            else:  # Handle part
                pattern_effect = -2
            price += pattern_effect + trend + noise
        else:
            price += trend + noise
        
        data.append(max(price, 50))  # Ensure positive prices
    
    return np.array(data)

# Main execution
if __name__ == "__main__":
    # Generate or load your stock data
    stock_prices = generate_sample_data()
    
    # Initialize detector
    detector = DeterministicPatternDetector(stock_prices)
    
    # Run full analysis
    results = detector.run_full_analysis()
    
    # Print detailed summary
    detector.pattern_summary()
    
    # Create visualization
    detector.plot_results()
    
    # Access individual results
    print(f"\n🔧 Mathematical Analysis Results:")
    print(f"   Smoothed prices shape: {detector.smoothed_prices.shape}")
    print(f"   Slopes calculated: {len(detector.slopes)}")
    print(f"   Curvature points: {len(detector.curvature)}")
    
    # Fourier analysis results
    cycles = detector.fourier_analysis()
    if cycles:
        print(f"   Dominant cycle period: {cycles[0]['period']:.1f}")
        print(f"   Cycle strength: {cycles[0]['magnitude']:.1f}")

# Advanced Pattern Template Matching
class PatternTemplates:
    """
    Deterministic pattern matching using mathematical templates
    """
    
    @staticmethod
    def head_shoulders_template(length=21):
        """Mathematical template for Head and Shoulders"""
        x = np.linspace(0, 4*np.pi, length)
        # Create three peaks with middle one higher
        template = np.sin(x) + 0.5 * np.sin(x/2) 
        template[length//2-2:length//2+3] += 0.3  # Boost the head
        return template
    
    @staticmethod
    def double_top_template(length=21):
        """Mathematical template for Double Top"""
        x = np.linspace(0, 2*np.pi, length)
        return np.sin(x) + 0.1 * np.sin(2*x)
    
    @staticmethod
    def triangle_template(length=21, ascending=True):
        """Mathematical template for triangles"""
        x = np.linspace(0, 1, length)
        if ascending:
            return x * 0.5 + np.sin(x * np.pi * 3) * (1 - x) * 0.3
        else:
            return (1 - x) * 0.5 + np.sin(x * np.pi * 3) * x * 0.3
    
    def match_pattern_to_template(self, data_segment, template, threshold=0.3):
        """
        Match data segment to pattern template using correlation
        """
        if len(data_segment) != len(template):
            # Interpolate to match lengths
            from scipy.interpolate import interp1d
            x_old = np.linspace(0, 1, len(data_segment))
            x_new = np.linspace(0, 1, len(template))
            f = interp1d(x_old, data_segment, kind='cubic')
            data_segment = f(x_new)
        
        # Normalize both patterns
        norm_data = self.normalize_pattern(data_segment)
        norm_template = self.normalize_pattern(template)
        
        # Calculate correlation coefficient
        correlation = np.corrcoef(norm_data, norm_template)[0, 1]
        
        return correlation > threshold, correlation

# Usage example for template matching
def advanced_pattern_matching():
    """
    Example of using template matching for pattern detection
    """
    stock_prices = generate_sample_data()
    detector = DeterministicPatternDetector(stock_prices)
    detector.gaussian_smooth()
    
    templates = PatternTemplates()
    
    # Test different window sizes for pattern matching
    window_size = 21
    matches = []
    
    for i in range(len(detector.smoothed_prices) - window_size):
        segment = detector.smoothed_prices[i:i + window_size]
        
        # Test against different templates
        hs_template = templates.head_shoulders_template(window_size)
        dt_template = templates.double_top_template(window_size)
        
        # Check Head & Shoulders match
        is_hs_match, hs_corr = templates.match_pattern_to_template(segment, hs_template)
        if is_hs_match:
            matches.append({
                'type': 'Head & Shoulders (Template)',
                'start': i,
                'end': i + window_size,
                'correlation': hs_corr,
                'confidence': min(hs_corr, 1.0)
            })
        
        # Check Double Top match
        is_dt_match, dt_corr = templates.match_pattern_to_template(segment, dt_template)
        if is_dt_match:
            matches.append({
                'type': 'Double Top (Template)',
                'start': i,
                'end': i + window_size,
                'correlation': dt_corr,
                'confidence': min(dt_corr, 1.0)
            })
    
    print(f"Template matching found {len(matches)} pattern matches")
    return matches

# Advanced Mathematical Indicators
class MathematicalIndicators:
    """
    Mathematical indicators for pattern confirmation
    """
    
    @staticmethod
    def hurst_exponent(prices, lags=range(2, 100)):
        """
        Calculate Hurst exponent to measure trend persistence
        H > 0.5: Trending (persistent)
        H < 0.5: Mean reverting (anti-persistent) 
        H = 0.5: Random walk
        """
        tau = []
        lagvec = []
        
        for lag in lags:
            # Calculate the variance of the differenced series
            pp = np.subtract(prices[lag:], prices[:-lag])
            tau.append(np.sqrt(np.std(pp)))
            lagvec.append(lag)
        
        # Linear fit to log-log plot
        m = np.polyfit(np.log(lagvec), np.log(tau), 1)
        hurst = m[0] * 2.0
        
        return hurst
    
    @staticmethod
    def fractal_dimension(prices):
        """
        Calculate fractal dimension using Higuchi's method
        FD close to 1: Smooth, trending
        FD close to 2: Rough, random
        """
        N = len(prices)
        L = []
        x = []
        
        for k in range(1, 20):
            Lk = 0
            for m in range(k):
                Lmk = 0
                for i in range(1, int((N-m)/k)):
                    Lmk += abs(prices[m+i*k] - prices[m+(i-1)*k])
                Lmk = Lmk * (N-1) / (((N-m)/k) * k)
                Lk += Lmk
            
            L.append(np.log(Lk/k))
            x.append(np.log(1.0/k))
        
        # Linear regression
        coeffs = np.polyfit(x, L, 1)
        return coeffs[0]  # Slope is the fractal dimension
    
    @staticmethod
    def entropy(prices, bins=50):
        """
        Calculate Shannon entropy of price returns
        High entropy = High randomness
        Low entropy = More predictable patterns
        """
        returns = np.diff(np.log(prices))
        hist, _ = np.histogram(returns, bins=bins)
        hist = hist[hist > 0]  # Remove zero bins
        prob = hist / hist.sum()
        
        return -np.sum(prob * np.log2(prob))
    
    @staticmethod
    def lyapunov_exponent(prices, embed_dim=3, lag=1, steps=50):
        """
        Estimate largest Lyapunov exponent for chaos detection
        Positive: Chaotic behavior
        Negative: Stable/periodic behavior
        """
        # Embed the time series
        N = len(prices)
        embedded = np.zeros((N - (embed_dim - 1) * lag, embed_dim))
        
        for i in range(embed_dim):
            embedded[:, i] = prices[i * lag:N - (embed_dim - 1 - i) * lag]
        
        # Calculate divergence
        divergences = []
        
        for i in range(len(embedded) - steps):
            # Find nearest neighbor
            distances = np.linalg.norm(embedded[i+1:] - embedded[i], axis=1)
            if len(distances) == 0:
                continue
                
            nearest_idx = np.argmin(distances) + i + 1
            
            if nearest_idx + steps >= len(embedded):
                continue
            
            # Track divergence over time
            initial_dist = distances[nearest_idx - i - 1]
            if initial_dist == 0:
                continue
                
            final_dist = np.linalg.norm(embedded[nearest_idx + steps] - embedded[i + steps])
            
            if final_dist > 0 and initial_dist > 0:
                divergences.append(np.log(final_dist / initial_dist))
        
        return np.mean(divergences) if divergences else 0
    
    @staticmethod
    def detrended_fluctuation_analysis(prices, scales=range(10, 100, 5)):
        """
        DFA for detecting long-range correlations
        α > 1: Persistent long-range correlations
        α ≈ 0.5: Random walk (no correlations)
        α < 0.5: Anti-persistent correlations
        """
        # Integrate the series
        y = np.cumsum(prices - np.mean(prices))
        
        fluctuations = []
        
        for scale in scales:
            # Divide into non-overlapping segments
            segments = len(y) // scale
            
            # Detrend each segment
            F2 = 0
            for v in range(segments):
                segment = y[v*scale:(v+1)*scale]
                coeffs = np.polyfit(range(scale), segment, 1)
                trend = np.polyval(coeffs, range(scale))
                F2 += np.mean((segment - trend)**2)
            
            fluctuations.append(np.sqrt(F2 / segments))
        
        # Linear fit in log-log scale
        coeffs = np.polyfit(np.log(scales), np.log(fluctuations), 1)
        return coeffs[0]  # DFA exponent

# In detector.py or a new TrendlineEngine class
from itertools import combinations
import numpy as np

# ADD THE FOLLOWING NEW CLASS:
class TrendlineEngine:
    """
    Finds the most significant trendlines by connecting combinations of pivots.
    This is the core improvement for accurate trendline and pattern detection.
    """
    def __init__(self, peaks, valleys, prices):
        self.peaks = sorted(peaks, key=lambda x: x['index'])
        self.valleys = sorted(valleys, key=lambda x: x['index'])
        self.prices = prices

    def _calculate_line_equation(self, point1, point2):
        """Calculates y = mx + c for a line between two points."""
        # Handle dictionary format
        if isinstance(point1, dict):
            x1, y1 = point1['index'], point1['price']
            x2, y2 = point2['index'], point2['price']
        else:
            x1, y1 = point1
            x2, y2 = point2
            
        if x2 == x1: return np.inf, x1
        m = (y2 - y1) / (x2 - x1)
        c = y1 - m * x1
        return m, c

    def find_best_trendlines(self, is_resistance=True, min_touches=2, tolerance=0.015):
        """
        Finds the most significant trendlines by connecting combinations of pivots.
        """
        points_to_check = self.peaks if is_resistance else self.valleys
        if len(points_to_check) < 2: return []

        best_lines = []
        # Consider only the last 15 pivots to form initial lines for relevance
        recent_pivots = points_to_check[-15:]

        for p1, p2 in combinations(recent_pivots, 2):
            p1, p2 = sorted([p1, p2], key=lambda x: x['index'])
            m, c = self._calculate_line_equation(p1, p2)

            # Basic filtering for valid trendlines
            if is_resistance and m > 0.1: continue # Resistance shouldn't slope up sharply
            if not is_resistance and m < -0.1: continue # Support shouldn't slope down sharply

            # Validate against ALL historical pivots to find all touches
            touches = []
            for p in points_to_check:
                expected_price = m * p['index'] + c
                if abs(p['price'] - expected_price) / p['price'] < tolerance:
                    touches.append(p)

            if len(touches) >= min_touches:
                # Score the line based on touches and recency of the last touch
                recency_score = touches[-1]['index'] / len(self.prices) if touches else 0
                score = len(touches) + recency_score
                best_lines.append({
                    'slope': m,
                    'intercept': c,
                    'touches': touches,
                    'score': score
                })
        
        # Return the top-scoring candidate lines
        return sorted(best_lines, key=lambda x: x['score'], reverse=True)[:2]
    
# Complete Analysis Suite
class AdvancedPatternAnalyzer:
    """
    Complete mathematical pattern analysis suite
    """
    
    def __init__(self, prices):
        self.df = prices if isinstance(prices, pd.DataFrame) else pd.DataFrame(prices, columns=['close'])
        self.prices = self.df['close'].values
        self.detector = DeterministicPatternDetector(self.df)
        self.indicators = MathematicalIndicators()
        self.results = {}
    
    def _detect_trendline_patterns(self):
        """
        Private method to run the new TrendlineEngine and identify chart patterns.
        This replaces the old detect_triangles and detect_wedges methods.
        """
        print("📈 Phase 2: Detecting Trendline-Based Patterns using TrendlineEngine...")
        if not self.detector.peaks or not self.detector.valleys:
            logging.warning("Not enough peaks or valleys for trendline analysis.")
            return []

        self.trendline_engine = TrendlineEngine(self.detector.peaks, self.detector.valleys, self.prices)
        best_res_lines = self.trendline_engine.find_best_trendlines(is_resistance=True)
        best_sup_lines = self.trendline_engine.find_best_trendlines(is_resistance=False)

        if not best_res_lines or not best_sup_lines:
            return []

        # Use the top-scoring lines to check for patterns
        res_line, sup_line = best_res_lines[0], best_sup_lines[0]
        m_res, m_sup = res_line['slope'], sup_line['slope']

        pattern_type, is_bullish, is_bearish = "None", None, None
        flat_tolerance = abs(np.mean(self.prices) * 0.0005) # Relative tolerance for "flat"

        # Pattern classification logic
        if m_res < -flat_tolerance and m_sup > flat_tolerance:
            pattern_type = "Symmetrical Triangle"
        elif abs(m_res) < flat_tolerance and m_sup > flat_tolerance:
            pattern_type = "Ascending Triangle"; is_bullish = True
        elif m_res < -flat_tolerance and abs(m_sup) < flat_tolerance:
            pattern_type = "Descending Triangle"; is_bearish = True
        elif m_res > 0 and m_sup > 0 and m_res < m_sup:
            pattern_type = "Rising Wedge"; is_bearish = True
        elif m_res < 0 and m_sup < 0 and m_res < m_sup:
            pattern_type = "Falling Wedge"; is_bullish = True

        if pattern_type == "None": return []

        # Apex calculation for relevance
        apex_x, apex_y, time_to_apex = None, None, np.inf
        if m_res != m_sup:
            apex_x = (sup_line['intercept'] - res_line['intercept']) / (m_res - m_sup)
            apex_y = m_res * apex_x + res_line['intercept']
            time_to_apex = apex_x - (len(self.prices) - 1)

        # A pattern is only valid if its apex is in the future
        if time_to_apex < 0: return []

        all_touches = res_line['touches'] + sup_line['touches']
        start_date = min(p['index'] for p in all_touches)
        end_date = max(p['index'] for p in all_touches)

        return [{
            'type': pattern_type, 'start': start_date, 'end': end_date,
            'confidence': 0.80 + min(len(all_touches) / 10, 0.15),
            'bullish': is_bullish, 'bearish': is_bearish,
            'resistance_line': res_line, 'support_line': sup_line,
            'apex_point': (apex_x, apex_y),
            'time_to_apex': time_to_apex,
            'is_active': 0 < time_to_apex < (end_date - start_date) * 1.5
        }]
    
    # REPLACE THIS ENTIRE METHOD
    def comprehensive_analysis(self, symbol="Unknown Stock"):
        """
        Run comprehensive mathematical analysis, orchestrating all components.
        """
        print(f"🚀 Starting Comprehensive Analysis for: {symbol}")

        # Phase 1: Run the original detector for base patterns, peaks, and valleys
        print("🔍 Phase 1: Deterministic Pattern Detection (Base Patterns)")
        self.detector.gaussian_smooth()
        self.detector.calculate_derivatives()
        self.detector.find_peaks_valleys()
        base_results = self.detector.run_full_analysis()

        # Phase 2: Use the results of Phase 1 to run the new TrendlineEngine
        all_valid_patterns, all_failed_patterns = [], []
        
        hs_valid, hs_failed = self.detector.detect_head_and_shoulders()
        all_valid_patterns.extend(hs_valid)
        all_failed_patterns.extend(hs_failed)
        trendline_patterns = self._detect_trendline_patterns()
        all_valid_patterns.extend(trendline_patterns)

        # Phase 3: Run the original mathematical indicators
        print("📊 Phase 3: Advanced Mathematical Indicators")
        indicator_results = {
            "hurst_exponent": self.indicators.hurst_exponent(self.prices),
            "fractal_dimension": self.indicators.fractal_dimension(self.prices),
            "shannon_entropy": self.indicators.entropy(self.prices),
            "lyapunov_exponent": self.indicators.lyapunov_exponent(self.prices),
            "dfa_exponent": self.indicators.detrended_fluctuation_analysis(self.prices)
        }
        
        print("📈 Phase 3.5: Market Regime Analysis")
        regime_analysis = self.analyze_market_regimes()

        # Phase 4: Score all found patterns for reliability
        print("🎯 Phase 4: Pattern Reliability Scoring")
        reliability_scores = self.calculate_pattern_reliability(all_valid_patterns)

        self.results = {
            "analysis_metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "symbol": symbol,
                "data_points": len(self.df),
                "analysis_period": {"start_date": self.df.index[0], "end_date": self.df.index[-1]},
                "mathematical_parameters": self.detector.params
            },
            "swing_points": {"swing_highs": self.detector.peaks, "swing_lows": self.detector.valleys},
            "detected_patterns": all_valid_patterns,
            "failed_patterns": all_failed_patterns,
            "mathematical_indicators": indicator_results,
            "market_regimes": regime_analysis,
            "pattern_reliability": reliability_scores
        }
        print(f"✅ Analysis Complete for {symbol}. Found {len(all_valid_patterns)} valid patterns.")
        return self.results
    
    def analyze_market_regimes(self):
        """
        Identify different market regimes using mathematical criteria
        """
        window_size = 50
        regimes = []
        
        for i in range(window_size, len(self.prices) - window_size):
            window = self.prices[i-window_size:i+window_size]
            
            # Calculate regime indicators
            trend_slope = (window[-1] - window[0]) / len(window)
            volatility = np.std(window)
            momentum = np.mean(np.diff(window))
            
            # Classify regime
            if abs(trend_slope) > 0.5 and momentum > 0:
                regime = "Strong Bull"
            elif abs(trend_slope) > 0.5 and momentum < 0:
                regime = "Strong Bear" 
            elif volatility < np.std(self.prices) * 0.7:
                regime = "Low Volatility"
            elif volatility > np.std(self.prices) * 1.3:
                regime = "High Volatility"
            else:
                regime = "Sideways"
            
            regimes.append({
                'position': i,
                'regime': regime,
                'trend_slope': trend_slope,
                'volatility': volatility,
                'momentum': momentum
            })
        
        return regimes
    
    def calculate_pattern_reliability(self, patterns):
        """
        Calculate reliability scores for detected patterns
        """
        reliability_scores = []
        
        for pattern in patterns:
            # Extract pattern segment
            start, end = pattern['start'], pattern['end']
            segment = self.prices[start:end]
            
            # Calculate reliability factors
            volatility_factor = 1.0 - min(np.std(segment) / np.std(self.prices), 1.0)
            length_factor = min(len(segment) / 30, 1.0)  # Prefer longer patterns
            position_factor = 1.0 - abs(start - len(self.prices)/2) / (len(self.prices)/2)
            
            # Volume factor (simulated - in real use, incorporate actual volume)
            volume_factor = 0.8  # Placeholder
            
            # Combined reliability score
            reliability = (
                pattern['confidence'] * 0.4 +
                volatility_factor * 0.2 +
                length_factor * 0.2 + 
                position_factor * 0.1 +
                volume_factor * 0.1
            )
            
            reliability_scores.append({
                'pattern': pattern,
                'reliability_score': reliability,
                'factors': {
                    'base_confidence': pattern['confidence'],
                    'volatility_factor': volatility_factor,
                    'length_factor': length_factor,
                    'position_factor': position_factor,
                    'volume_factor': volume_factor
                }
            })
        
        return sorted(reliability_scores, key=lambda x: x['reliability_score'], reverse=True)
    
    def print_comprehensive_summary(self, symbol="Unknown Stock"):
        """
        Print detailed comprehensive analysis summary
        """
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE PATTERN ANALYSIS REPORT")
        print("="*80)
        
        # Basic stats
        patterns = self.results['detected_patterns']
        indicators = self.results['mathematical_indicators']
        
        print(f"\n📊 DATASET OVERVIEW:")
        print(f"   Total data points: {len(self.prices)}")
        print(f"   Price range: ${self.prices.min():.2f} - ${self.prices.max():.2f}")
        print(f"   Total return: {((self.prices[-1]/self.prices[0])-1)*100:.1f}%")
        
        print(f"\n🔍 PATTERN DETECTION RESULTS:")
        print(f"   Total patterns found: {len(patterns)}")
        bullish_count = sum(1 for p in patterns if p.get('bullish'))
        bearish_count = sum(1 for p in patterns if p.get('bearish'))
        print(f"   Bullish patterns: {bullish_count}")
        print(f"   Bearish patterns: {bearish_count}")
        
        if patterns:
            avg_confidence = np.mean([p['confidence'] for p in patterns])
            print(f"   Average confidence: {avg_confidence:.1%}")
        
        print(f"\n🧮 MATHEMATICAL INDICATORS:")
        print(f"   Hurst Exponent: {indicators['hurst_exponent']:.3f}", end="")
        if indicators['hurst_exponent'] > 0.5:
            print(" (Trending/Persistent)")
        elif indicators['hurst_exponent'] < 0.5:
            print(" (Mean-reverting)")
        else:
            print(" (Random walk)")
            
        print(f"   Fractal Dimension: {indicators['fractal_dimension']:.3f}", end="")
        if indicators['fractal_dimension'] < 1.5:
            print(" (Smooth/Trending)")
        else:
            print(" (Rough/Random)")
            
        print(f"   Shannon Entropy: {indicators['shannon_entropy']:.3f}", end="")
        if indicators['shannon_entropy'] < 3:
            print(" (Low randomness)")
        else:
            print(" (High randomness)")
            
        print(f"   Lyapunov Exponent: {indicators['lyapunov_exponent']:.3f}", end="")
        if indicators['lyapunov_exponent'] > 0:
            print(" (Chaotic)")
        else:
            print(" (Stable)")
            
        print(f"   DFA Exponent: {indicators['dfa_exponent']:.3f}", end="")
        if indicators['dfa_exponent'] > 1:
            print(" (Long-range correlations)")
        elif indicators['dfa_exponent'] < 0.5:
            print(" (Anti-correlations)")
        else:
            print(" (No long-range correlations)")
        
        # Top reliable patterns
        print(f"\n🏆 TOP RELIABLE PATTERNS:")
        top_patterns = self.results['pattern_reliability'][:5]
        
        for i, item in enumerate(top_patterns, 1):
            pattern = item['pattern']
            score = item['reliability_score']
            bias = "📈" if pattern.get('bullish') else "📉" if pattern.get('bearish') else "⚪"
            print(f"   #{i}: {pattern['type']} {bias}")
            print(f"       Reliability: {score:.1%} | Days {pattern['start']}-{pattern['end']}")
        
        # Market regime summary
        regimes = self.results['market_regimes']
        if regimes:
            regime_counts = {}
            for r in regimes:
                regime_type = r['regime']
                regime_counts[regime_type] = regime_counts.get(regime_type, 0) + 1
            
            print(f"\n🌊 MARKET REGIME ANALYSIS:")
            for regime, count in sorted(regime_counts.items(), key=lambda x: x[1], reverse=True):
                pct = count / len(regimes) * 100
                print(f"   {regime}: {pct:.1f}% of time")
        
        print("\n" + "="*80)
        

# Example usage with real-world application
def run_complete_example():
    """
    Complete example showing all features
    """
    print("💡 DETERMINISTIC CHART PATTERN DETECTION SYSTEM")
    print("=" * 50)
    
    # Generate sample data (replace with your actual stock data)
    stock_data = generate_sample_data()
    
    # Convert to DataFrame format as expected by the detector
    df = pd.DataFrame({'close': stock_data})
    df.index = pd.date_range(start='2024-01-01', periods=len(stock_data), freq='D')
    
    # Run comprehensive analysis
    analyzer = AdvancedPatternAnalyzer(df)
    results = analyzer.comprehensive_analysis()
    
    # Create visualizations
    analyzer.detector.plot_results()
    
    # Save results (optional)
    # import pickle
    # with open('pattern_analysis_results.pkl', 'wb') as f:
    #     pickle.dump(results, f)
    
    return results

# Run the complete analysis
# REPLACE the final __main__ block with this:

if __name__ == "__main__":
    """
    Complete example showing the new, integrated analysis workflow.
    """
    print("💡 DETERMINISTIC CHART PATTERN DETECTION SYSTEM")
    print("=" * 50)
    
    # Generate sample data with a clear triangle pattern to test the new engine
    def generate_triangle_data():
        np.random.seed(101)
        data = np.full(300, 100.0)
        # Base noise and trend
        data += np.random.normal(0, 1.5, 300).cumsum()
        data[:150] += np.linspace(0, -10, 150)
        
        # Create a clear ascending triangle
        support_slope = 0.2
        for i in range(150, 280):
            t = i - 150
            resistance_level = 115
            support_level = 90 + t * support_slope
            
            # Oscillate between support and resistance
            oscillation = np.sin(t * np.pi / 20) * (resistance_level - support_level) / 2
            mid_point = (resistance_level + support_level) / 2
            data[i] = mid_point + oscillation + np.random.normal(0, 1)

        # Breakout
        data[280:] += np.linspace(0, 15, 20)
        return data

    stock_data = generate_triangle_data()
    
    # Convert to DataFrame format as expected by the detector
    df = pd.DataFrame({'close': stock_data})
    df.index = pd.date_range(start='2024-01-01', periods=len(stock_data), freq='D')
    
    # 1. Initialize and run the main analyzer
    analyzer = AdvancedPatternAnalyzer(df)
    results = analyzer.comprehensive_analysis()
    
    # 2. Create visualizations using the detector's plot method
    analyzer.detector.plot_results()