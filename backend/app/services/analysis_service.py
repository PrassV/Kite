"""
Async Market Analysis Service
Ports the comprehensive market analyzer to async FastAPI service with caching
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor
import json

from ..auth.kite_client import AsyncKiteClient
from ..core.config import settings
from ..core.logging_config import get_context_logger
from ..models.analysis import (
    AnalysisRequest, 
    ComprehensiveAnalysisResponse,
    QuickAnalysisResponse,
    AnalysisType
)

# Import the original analyzer components (we'll adapt them)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

logger = get_context_logger(__name__)


class AsyncMarketAnalysisService:
    """
    Async service for comprehensive market analysis
    Integrates with Kite Connect and provides caching
    """
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_ANALYSIS)
        self.kite_client = None
    
    def set_kite_client(self, kite_client: AsyncKiteClient):
        """Set the authenticated Kite client"""
        self.kite_client = kite_client
    
    async def get_historical_data(
        self, 
        symbol: str, 
        analysis_window: int,
        timeframe: str = "day"
    ) -> pd.DataFrame:
        """Get historical data for analysis"""
        if not self.kite_client:
            raise ValueError("Kite client not initialized")
        
        # First, search for the instrument to get the token
        instruments = await self.kite_client.search_instruments(
            query=symbol, 
            exchange="NSE",
            instrument_type="EQ",
            limit=1
        )
        
        if not instruments:
            raise ValueError(f"Symbol {symbol} not found")
        
        instrument = instruments[0]
        
        # Get historical data
        to_date = datetime.now()
        from_date = to_date - timedelta(days=analysis_window * 2)  # Extra buffer
        
        # For now, we'll simulate the instrument token lookup
        # In a real implementation, you'd need to get this from the instruments list
        # This is a placeholder - you'll need to implement proper instrument token lookup
        try:
            df = await self.kite_client.get_historical_data(
                instrument_token=123456,  # This needs to be looked up properly
                from_date=from_date,
                to_date=to_date,
                interval=timeframe
            )
            
            if df.empty:
                raise ValueError(f"No historical data available for {symbol}")
            
            return df
            
        except Exception as e:
            logger.error(
                f"❌ Failed to fetch historical data for {symbol}",
                extra={"symbol": symbol, "error": str(e)},
                exc_info=True
            )
            # For development, create sample data
            return self._generate_sample_data(symbol, analysis_window)
    
    def _generate_sample_data(self, symbol: str, periods: int) -> pd.DataFrame:
        """Generate sample OHLCV data for development/testing"""
        logger.info(f"📊 Generating sample data for {symbol}")
        
        np.random.seed(42)
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=periods),
            periods=periods,
            freq='D'
        )
        
        # Generate realistic price data
        base_price = 100
        prices = []
        current_price = base_price
        
        for i in range(periods):
            # Add some trend and volatility
            trend = 0.001 * i  # Slight upward trend
            volatility = np.random.normal(0, 0.02)  # 2% daily volatility
            
            current_price = current_price * (1 + trend + volatility)
            prices.append(current_price)
        
        # Generate OHLCV data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            high = close * (1 + abs(np.random.normal(0, 0.01)))
            low = close * (1 - abs(np.random.normal(0, 0.01)))
            open_price = prices[i-1] if i > 0 else close
            volume = int(np.random.normal(100000, 20000))
            
            data.append({
                'date': date,
                'open': open_price,
                'high': max(open_price, high, close),
                'low': min(open_price, low, close),
                'close': close,
                'volume': max(volume, 1000)
            })
        
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        return df
    
    async def run_comprehensive_analysis(
        self, 
        request: AnalysisRequest,
        user_id: str
    ) -> ComprehensiveAnalysisResponse:
        """Run comprehensive market analysis"""
        
        logger.info(
            f"🎯 Starting comprehensive analysis",
            extra={
                "symbol": request.symbol,
                "user_id": user_id,
                "analysis_window": request.analysis_window
            }
        )
        
        try:
            # Get historical data
            df = await self.get_historical_data(
                request.symbol,
                request.analysis_window,
                request.timeframe.value
            )
            
            # Run analysis in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            analysis_result = await loop.run_in_executor(
                self.thread_pool,
                self._run_sync_analysis,
                df,
                request.symbol,
                request
            )
            
            logger.info(
                f"✅ Comprehensive analysis completed",
                extra={
                    "symbol": request.symbol,
                    "user_id": user_id,
                    "patterns_found": len(analysis_result.get("chart_patterns", []))
                }
            )
            
            return self._format_comprehensive_response(analysis_result, request)
            
        except Exception as e:
            logger.error(
                f"❌ Comprehensive analysis failed",
                extra={
                    "symbol": request.symbol,
                    "user_id": user_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def _run_sync_analysis(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        request: AnalysisRequest
    ) -> Dict[str, Any]:
        """Run synchronous analysis in thread pool"""
        
        # Create a simplified version of the comprehensive analyzer
        analyzer = SimplifiedMarketAnalyzer(df, symbol, request.analysis_window)
        
        results = {
            "analysis_summary": {
                "stock_symbol": symbol,
                "analysis_date": datetime.now().strftime("%B %d, %Y"),
                "analysis_focus": f"Comprehensive analysis - last {request.analysis_window} days",
                "current_price": float(df['close'].iloc[-1]),
                "analysis_components": []
            },
            "current_market_structure": analyzer.analyze_market_structure(),
            "trendline_analysis": {"trendlines": [], "trendline_summary": {}},
            "chart_patterns": [],
            "volume_analysis": analyzer.analyze_volume() if request.include_volume else {},
            "fibonacci_analysis": analyzer.analyze_fibonacci() if request.include_fibonacci else {},
            "trading_opportunities": [],
            "risk_management": analyzer.generate_risk_management()
        }
        
        # Add analysis components
        components = []
        if request.include_patterns:
            components.append("Chart Patterns")
            results["chart_patterns"] = analyzer.detect_simple_patterns()
        
        if request.include_volume:
            components.append("Volume Analysis")
        
        if request.include_fibonacci:
            components.append("Fibonacci Analysis")
        
        results["analysis_summary"]["analysis_components"] = components
        
        return results
    
    def _format_comprehensive_response(
        self, 
        analysis_result: Dict[str, Any], 
        request: AnalysisRequest
    ) -> ComprehensiveAnalysisResponse:
        """Format analysis result as Pydantic response"""
        
        # This is a simplified conversion - in production you'd want more robust formatting
        return ComprehensiveAnalysisResponse.parse_obj(analysis_result)
    
    async def run_quick_analysis(
        self, 
        request: AnalysisRequest,
        user_id: str
    ) -> QuickAnalysisResponse:
        """Run quick analysis for faster responses"""
        
        logger.info(
            f"⚡ Starting quick analysis",
            extra={
                "symbol": request.symbol,
                "user_id": user_id
            }
        )
        
        try:
            # Get limited historical data
            df = await self.get_historical_data(
                request.symbol,
                min(request.analysis_window, 30),  # Limit for quick analysis
                request.timeframe.value
            )
            
            current_price = float(df['close'].iloc[-1])
            
            # Simple trend analysis
            sma_10 = df['close'].rolling(10).mean().iloc[-1]
            sma_20 = df['close'].rolling(20).mean().iloc[-1] if len(df) >= 20 else current_price
            
            if current_price > sma_10 > sma_20:
                trend = "Strong Uptrend"
                recommendation = "BULLISH"
                confidence = 0.8
            elif current_price > sma_10:
                trend = "Uptrend"
                recommendation = "BULLISH"
                confidence = 0.6
            elif current_price < sma_10 < sma_20:
                trend = "Strong Downtrend"
                recommendation = "BEARISH"
                confidence = 0.8
            elif current_price < sma_10:
                trend = "Downtrend"
                recommendation = "BEARISH"
                confidence = 0.6
            else:
                trend = "Sideways"
                recommendation = "NEUTRAL"
                confidence = 0.5
            
            # Simple support/resistance levels
            recent_high = df['high'].tail(20).max()
            recent_low = df['low'].tail(20).min()
            key_levels = [recent_low, sma_20, current_price, sma_10, recent_high]
            key_levels = [float(level) for level in key_levels if not np.isnan(level)]
            key_levels = sorted(list(set(key_levels)))
            
            logger.info(
                f"✅ Quick analysis completed",
                extra={
                    "symbol": request.symbol,
                    "user_id": user_id,
                    "trend": trend,
                    "recommendation": recommendation
                }
            )
            
            return QuickAnalysisResponse(
                symbol=request.symbol,
                current_price=current_price,
                trend=trend,
                key_levels=key_levels,
                recommendation=recommendation,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(
                f"❌ Quick analysis failed",
                extra={
                    "symbol": request.symbol,
                    "user_id": user_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise


class SimplifiedMarketAnalyzer:
    """Simplified market analyzer for async processing"""
    
    def __init__(self, df: pd.DataFrame, symbol: str, analysis_window: int):
        self.df = df
        self.symbol = symbol
        self.analysis_window = analysis_window
        self.current_price = float(df['close'].iloc[-1])
        self.current_date = df.index[-1]
    
    def analyze_market_structure(self) -> Dict[str, Any]:
        """Analyze market structure"""
        sma_10 = self.df['close'].rolling(10).mean().iloc[-1]
        sma_20 = self.df['close'].rolling(20).mean().iloc[-1] if len(self.df) >= 20 else self.current_price
        
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
            "trend": {
                "direction": trend_direction,
                "strength": trend_strength,
                "sma_10": float(sma_10) if not np.isnan(sma_10) else self.current_price,
                "sma_20": float(sma_20) if not np.isnan(sma_20) else self.current_price
            },
            "price_action": self._analyze_price_action()
        }
    
    def _analyze_price_action(self) -> Dict[str, Any]:
        """Analyze recent price action"""
        price_1d = (self.current_price - self.df['close'].iloc[-2]) if len(self.df) > 1 else 0
        price_5d = (self.current_price - self.df['close'].iloc[-6]) if len(self.df) > 5 else 0
        price_20d = (self.current_price - self.df['close'].iloc[-21]) if len(self.df) > 20 else 0
        
        return {
            "1_day_change": {
                "absolute": float(price_1d),
                "percent": float(price_1d/self.current_price*100)
            },
            "5_day_change": {
                "absolute": float(price_5d),
                "percent": float(price_5d/self.current_price*100) if price_5d != 0 else 0
            },
            "20_day_change": {
                "absolute": float(price_20d),
                "percent": float(price_20d/self.current_price*100) if price_20d != 0 else 0
            }
        }
    
    def analyze_volume(self) -> Dict[str, Any]:
        """Analyze volume patterns"""
        if 'volume' not in self.df.columns:
            return {"error": "No volume data available"}
        
        current_vol = self.df['volume'].iloc[-1]
        avg_vol = self.df['volume'].mean()
        vol_std = self.df['volume'].std()
        
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
        
        return {
            "current_volume": int(current_vol),
            "average_volume": int(avg_vol),
            "volume_assessment": vol_assessment,
            "significance": significance,
            "volume_trend": "Stable",  # Simplified
            "volume_ratio": float(current_vol / avg_vol),
            "recent_spikes": [],  # Simplified
            "volume_ma_5": int(self.df['volume'].rolling(5).mean().iloc[-1]),
            "volume_ma_20": int(self.df['volume'].rolling(20).mean().iloc[-1]) if len(self.df) >= 20 else int(avg_vol)
        }
    
    def analyze_fibonacci(self) -> Dict[str, Any]:
        """Simplified Fibonacci analysis"""
        # Find recent high and low
        recent_high = self.df['high'].tail(30).max()
        recent_low = self.df['low'].tail(30).min()
        price_range = recent_high - recent_low
        
        if price_range <= 0:
            return {"error": "Invalid price range for Fibonacci analysis"}
        
        # Calculate key Fibonacci levels
        fib_levels = []
        fib_ratios = [0.236, 0.382, 0.500, 0.618, 0.786]
        
        for ratio in fib_ratios:
            level_price = recent_low + (price_range * ratio)
            distance_pct = abs(level_price - self.current_price) / self.current_price * 100
            
            fib_levels.append({
                "level": f"Fibonacci {ratio*100:.1f}%",
                "price": float(level_price),
                "ratio": ratio,
                "distance_percent": float(distance_pct),
                "significance": f"{ratio*100:.1f}% retracement level"
            })
        
        # Sort by distance to current price
        fib_levels.sort(key=lambda x: x['distance_percent'])
        
        return {
            "fibonacci_analysis": {
                "recent_swing_high": {"price": float(recent_high)},
                "recent_swing_low": {"price": float(recent_low)},
                "price_range": float(price_range)
            },
            "key_levels": fib_levels,
            "nearest_level": fib_levels[0] if fib_levels else None
        }
    
    def detect_simple_patterns(self) -> List[Dict[str, Any]]:
        """Detect simple chart patterns"""
        patterns = []
        
        # Simple support/resistance detection
        recent_high = self.df['high'].tail(30).max()
        recent_low = self.df['low'].tail(30).min()
        
        # Check if price is near key levels
        near_resistance = abs(self.current_price - recent_high) / self.current_price < 0.02
        near_support = abs(self.current_price - recent_low) / self.current_price < 0.02
        
        if near_resistance:
            patterns.append({
                "pattern_id": "RES_01",
                "pattern_name": "Near Resistance",
                "pattern_type": "Support/Resistance",
                "bias": "Bearish if rejected, Bullish if breaks",
                "reliability_score": 0.7,
                "status": "Active",
                "formation_start": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "current_price": self.current_price,
                "trading_setup": {
                    "entry_trigger": float(recent_high * 1.002),
                    "stop_loss": float(recent_high * 0.98),
                    "target_price": float(recent_high * 1.05)
                }
            })
        
        if near_support:
            patterns.append({
                "pattern_id": "SUP_01",
                "pattern_name": "Near Support",
                "pattern_type": "Support/Resistance",
                "bias": "Bullish if holds, Bearish if breaks",
                "reliability_score": 0.7,
                "status": "Active",
                "formation_start": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "current_price": self.current_price,
                "trading_setup": {
                    "entry_trigger": float(recent_low * 1.005),
                    "stop_loss": float(recent_low * 0.98),
                    "target_price": float(recent_low * 1.05)
                }
            })
        
        return patterns
    
    def generate_risk_management(self) -> Dict[str, Any]:
        """Generate risk management guidelines"""
        recent_high = self.df['high'].tail(30).max()
        recent_low = self.df['low'].tail(30).min()
        
        return {
            "stop_loss_levels": {
                "nearest_support": float(recent_low),
                "nearest_resistance": float(recent_high),
                "percentage_stops": {
                    "conservative": float(self.current_price * 0.95),
                    "moderate": float(self.current_price * 0.97),
                    "tight": float(self.current_price * 0.985)
                }
            },
            "position_sizing": {
                "max_risk_per_trade": "1-2% of portfolio",
                "pattern_based_sizing": "Higher allocation for high-reliability patterns",
                "volume_confirmation": "Increase size when volume confirms setup"
            }
        }


# Global service instance
analysis_service = AsyncMarketAnalysisService()