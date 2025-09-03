"""
Analysis-related Pydantic models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class AnalysisType(str, Enum):
    """Available analysis types"""
    COMPREHENSIVE = "comprehensive"
    QUICK = "quick"
    PATTERNS = "patterns"
    FIBONACCI = "fibonacci"
    VOLUME = "volume"
    TRENDLINES = "trendlines"


class TimeFrame(str, Enum):
    """Available timeframes for analysis"""
    MINUTE = "minute"
    FIVE_MINUTE = "5minute"
    FIFTEEN_MINUTE = "15minute"
    THIRTY_MINUTE = "30minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class AnalysisRequest(BaseModel):
    """Request model for stock analysis"""
    symbol: str = Field(
        description="Stock symbol (e.g., RELIANCE, TCS)",
        min_length=1,
        max_length=20
    )
    analysis_type: AnalysisType = Field(
        default=AnalysisType.COMPREHENSIVE,
        description="Type of analysis to perform"
    )
    timeframe: TimeFrame = Field(
        default=TimeFrame.DAY,
        description="Timeframe for analysis"
    )
    analysis_window: int = Field(
        default=60,
        ge=20,
        le=365,
        description="Number of periods to analyze (20-365)"
    )
    include_volume: bool = Field(
        default=True,
        description="Include volume analysis"
    )
    include_patterns: bool = Field(
        default=True,
        description="Include chart pattern detection"
    )
    include_fibonacci: bool = Field(
        default=True,
        description="Include Fibonacci analysis"
    )
    cache_duration: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Cache duration in seconds (60-3600)"
    )

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format"""
        if not v.replace('-', '').replace('&', '').isalnum():
            raise ValueError('Symbol must contain only alphanumeric characters, hyphens, and ampersands')
        return v.upper()


class TrendlinePoint(BaseModel):
    """Trendline touch point model"""
    date: datetime = Field(description="Date of the touch point")
    price: float = Field(description="Price at the touch point")
    index: int = Field(description="Index position in the dataset")


class TrendlineData(BaseModel):
    """Trendline data model"""
    trendline_id: str = Field(description="Unique trendline identifier")
    type: str = Field(description="Trendline type (Support/Resistance)")
    direction: str = Field(description="Trendline direction (Rising/Falling/Flat)")
    current_value: float = Field(description="Current trendline value")
    slope: float = Field(description="Trendline slope")
    touches: int = Field(description="Number of touch points")
    strength: str = Field(description="Trendline strength (Strong/Medium/Weak)")
    touch_points: List[TrendlinePoint] = Field(description="Touch points on the trendline")
    distance_from_current: float = Field(description="Distance from current price")
    distance_percent: float = Field(description="Distance as percentage")
    trading_relevance: str = Field(description="Trading relevance (High/Medium/Low)")
    forward_projections: Dict[str, float] = Field(description="Future price projections")
    days_to_intersection: Optional[int] = Field(None, description="Days until price intersection")
    significance: str = Field(description="Trendline significance description")


class TrendlineAnalysis(BaseModel):
    """Trendline analysis results"""
    trendlines: List[TrendlineData] = Field(description="Detected trendlines")
    trendline_summary: Dict[str, int] = Field(description="Trendline summary statistics")


class PatternTradingSetup(BaseModel):
    """Trading setup for patterns"""
    entry_trigger: Optional[float] = Field(None, description="Entry trigger price")
    target_1: Optional[float] = Field(None, description="First target price")
    target_2: Optional[float] = Field(None, description="Second target price")
    target_price: Optional[float] = Field(None, description="Target price")
    stop_loss: float = Field(description="Stop loss price")
    risk_reward_ratio: Optional[str] = Field(None, description="Risk reward ratio")
    volume_confirmation_needed: Optional[bool] = Field(None, description="Volume confirmation required")


class ChartPattern(BaseModel):
    """Chart pattern model"""
    pattern_id: str = Field(description="Unique pattern identifier")
    pattern_name: str = Field(description="Pattern name")
    pattern_type: str = Field(description="Pattern type category")
    bias: str = Field(description="Pattern bias (Bullish/Bearish/Neutral)")
    reliability_score: float = Field(ge=0, le=1, description="Pattern reliability (0-1)")
    status: str = Field(description="Pattern status")
    formation_start: str = Field(description="Pattern formation start date")
    formation_end: Optional[str] = Field(None, description="Pattern formation end date")
    trading_setup: Optional[PatternTradingSetup] = Field(None, description="Trading setup details")
    key_points: Optional[Dict[str, Any]] = Field(None, description="Key pattern points")
    analysis_date: str = Field(description="Analysis date")
    current_price: float = Field(description="Current price during analysis")


class VolumeAnalysis(BaseModel):
    """Volume analysis results"""
    current_volume: int = Field(description="Current trading volume")
    average_volume: int = Field(description="Average trading volume")
    volume_assessment: str = Field(description="Volume assessment (High/Normal/Low)")
    significance: str = Field(description="Volume significance description")
    volume_trend: str = Field(description="Volume trend")
    volume_ratio: float = Field(description="Current volume to average ratio")
    recent_spikes: List[Dict[str, Any]] = Field(description="Recent volume spikes")
    volume_ma_5: int = Field(description="5-day volume moving average")
    volume_ma_20: int = Field(description="20-day volume moving average")


class FibonacciLevel(BaseModel):
    """Fibonacci level model"""
    level: str = Field(description="Fibonacci level name")
    price: float = Field(description="Fibonacci price level")
    ratio: float = Field(description="Fibonacci ratio")
    distance_percent: float = Field(description="Distance from current price (percentage)")
    significance: str = Field(description="Level significance description")


class FibonacciAnalysis(BaseModel):
    """Fibonacci analysis results"""
    fibonacci_analysis: Dict[str, Any] = Field(description="Fibonacci analysis metadata")
    key_levels: List[FibonacciLevel] = Field(description="Key Fibonacci levels")
    nearest_level: Optional[FibonacciLevel] = Field(None, description="Nearest Fibonacci level")


class MarketStructure(BaseModel):
    """Market structure analysis"""
    trend: Dict[str, Any] = Field(description="Current trend analysis")
    price_action: Dict[str, Any] = Field(description="Recent price action analysis")


class TradingOpportunity(BaseModel):
    """Trading opportunity model"""
    type: str = Field(description="Opportunity type")
    pattern_name: Optional[str] = Field(None, description="Associated pattern name")
    bias: str = Field(description="Trading bias")
    reliability: float = Field(description="Reliability score")
    setup: Dict[str, Any] = Field(description="Trading setup details")
    volume_confirmation: Optional[str] = Field(None, description="Volume confirmation status")
    fibonacci_confirmation: Optional[str] = Field(None, description="Fibonacci confirmation status")


class RiskManagement(BaseModel):
    """Risk management guidelines"""
    stop_loss_levels: Dict[str, Any] = Field(description="Stop loss level recommendations")
    position_sizing: Dict[str, Any] = Field(description="Position sizing guidelines")


class AnalysisSummary(BaseModel):
    """Analysis summary model"""
    stock_symbol: str = Field(description="Analyzed stock symbol")
    analysis_date: str = Field(description="Analysis date")
    analysis_focus: str = Field(description="Analysis focus description")
    current_price: float = Field(description="Current stock price")
    analysis_components: List[str] = Field(description="Included analysis components")


class ComprehensiveAnalysisResponse(BaseModel):
    """Comprehensive analysis response model"""
    analysis_summary: AnalysisSummary = Field(description="Analysis summary")
    current_market_structure: MarketStructure = Field(description="Current market structure")
    trendline_analysis: TrendlineAnalysis = Field(description="Trendline analysis results")
    chart_patterns: List[ChartPattern] = Field(description="Detected chart patterns")
    volume_analysis: VolumeAnalysis = Field(description="Volume analysis results")
    fibonacci_analysis: FibonacciAnalysis = Field(description="Fibonacci analysis results")
    trading_opportunities: List[TradingOpportunity] = Field(description="Identified trading opportunities")
    risk_management: RiskManagement = Field(description="Risk management guidelines")


class QuickAnalysisResponse(BaseModel):
    """Quick analysis response model"""
    symbol: str = Field(description="Stock symbol")
    current_price: float = Field(description="Current price")
    trend: str = Field(description="Current trend")
    key_levels: List[float] = Field(description="Key support/resistance levels")
    recommendation: str = Field(description="Quick recommendation")
    confidence: float = Field(description="Recommendation confidence")


class AnalysisResponse(BaseModel):
    """Generic analysis response model"""
    analysis_type: AnalysisType = Field(description="Type of analysis performed")
    symbol: str = Field(description="Analyzed symbol")
    timeframe: TimeFrame = Field(description="Analysis timeframe")
    analysis_window: int = Field(description="Analysis window period")
    cached: bool = Field(description="Whether result was cached")
    cache_expires_at: Optional[datetime] = Field(None, description="Cache expiration time")
    processing_time: float = Field(description="Analysis processing time in seconds")
    comprehensive_data: Optional[ComprehensiveAnalysisResponse] = Field(None, description="Comprehensive analysis data")
    quick_data: Optional[QuickAnalysisResponse] = Field(None, description="Quick analysis data")


class AnalysisHistoryResponse(BaseModel):
    """Analysis history response model"""
    analyses: List[Dict[str, Any]] = Field(description="Historical analyses")
    total: int = Field(description="Total number of analyses")
    symbols_analyzed: List[str] = Field(description="List of analyzed symbols")
    most_analyzed_symbol: Optional[str] = Field(None, description="Most frequently analyzed symbol")