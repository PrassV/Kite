"""
Stock-related Pydantic models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Exchange(str, Enum):
    """Supported exchanges"""
    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"
    NFO = "NFO"
    BFO = "BFO"


class InstrumentType(str, Enum):
    """Supported instrument types"""
    EQ = "EQ"  # Equity
    FUT = "FUT"  # Futures
    CE = "CE"  # Call Option
    PE = "PE"  # Put Option


class StockSearchRequest(BaseModel):
    """Stock search request model"""
    query: str = Field(
        description="Search query (symbol or company name)",
        min_length=1,
        max_length=50
    )
    exchange: Optional[Exchange] = Field(
        default=Exchange.NSE,
        description="Exchange to search in"
    )
    instrument_type: Optional[InstrumentType] = Field(
        default=InstrumentType.EQ,
        description="Instrument type filter"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results (1-50)"
    )

    @validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip().upper()


class StockInfo(BaseModel):
    """Basic stock information model"""
    symbol: str = Field(description="Stock trading symbol")
    name: str = Field(description="Company name")
    exchange: str = Field(description="Exchange name")
    instrument_type: str = Field(description="Instrument type")
    lot_size: Optional[int] = Field(None, description="Lot size for F&O")
    tick_size: Optional[float] = Field(None, description="Minimum price tick")
    expiry: Optional[datetime] = Field(None, description="Expiry date for derivatives")
    strike: Optional[float] = Field(None, description="Strike price for options")
    segment: str = Field(description="Market segment")


class StockQuote(BaseModel):
    """Stock quote model"""
    symbol: str = Field(description="Stock symbol")
    last_price: float = Field(description="Last traded price")
    change: float = Field(description="Price change")
    change_percent: float = Field(description="Percentage change")
    volume: int = Field(description="Trading volume")
    average_price: float = Field(description="Average price")
    open: float = Field(description="Opening price")
    high: float = Field(description="Day's high")
    low: float = Field(description="Day's low")
    close: float = Field(description="Previous close")
    bid_price: Optional[float] = Field(None, description="Bid price")
    ask_price: Optional[float] = Field(None, description="Ask price")
    bid_quantity: Optional[int] = Field(None, description="Bid quantity")
    ask_quantity: Optional[int] = Field(None, description="Ask quantity")
    timestamp: datetime = Field(description="Quote timestamp")


class OHLCV(BaseModel):
    """OHLCV data point model"""
    date: datetime = Field(description="Date/time of the data point")
    open: float = Field(description="Opening price")
    high: float = Field(description="High price")
    low: float = Field(description="Low price")
    close: float = Field(description="Closing price")
    volume: int = Field(description="Trading volume")


class HistoricalDataRequest(BaseModel):
    """Historical data request model"""
    symbol: str = Field(description="Stock symbol")
    from_date: datetime = Field(description="Start date for historical data")
    to_date: datetime = Field(description="End date for historical data")
    interval: str = Field(
        default="day",
        description="Data interval (minute, day, etc.)"
    )
    continuous: bool = Field(
        default=False,
        description="Continuous contract for futures"
    )

    @validator('to_date')
    def validate_date_range(cls, v, values):
        """Validate that to_date is after from_date"""
        if 'from_date' in values and v <= values['from_date']:
            raise ValueError('to_date must be after from_date')
        return v


class HistoricalDataResponse(BaseModel):
    """Historical data response model"""
    symbol: str = Field(description="Stock symbol")
    interval: str = Field(description="Data interval")
    data: List[OHLCV] = Field(description="Historical OHLCV data")
    from_date: datetime = Field(description="Start date of data")
    to_date: datetime = Field(description="End date of data")
    count: int = Field(description="Number of data points")


class StockSearchResponse(BaseModel):
    """Stock search response model"""
    query: str = Field(description="Original search query")
    results: List[StockInfo] = Field(description="Search results")
    count: int = Field(description="Number of results")
    total_matches: Optional[int] = Field(None, description="Total matches in database")


class WatchlistItem(BaseModel):
    """Watchlist item model"""
    symbol: str = Field(description="Stock symbol")
    name: str = Field(description="Company name")
    added_at: datetime = Field(description="Date added to watchlist")
    alerts_enabled: bool = Field(default=False, description="Whether alerts are enabled")
    target_price: Optional[float] = Field(None, description="Target price alert")
    stop_loss: Optional[float] = Field(None, description="Stop loss alert")


class WatchlistResponse(BaseModel):
    """Watchlist response model"""
    items: List[WatchlistItem] = Field(description="Watchlist items")
    count: int = Field(description="Number of items in watchlist")
    last_updated: datetime = Field(description="Last update timestamp")


class AddToWatchlistRequest(BaseModel):
    """Add to watchlist request model"""
    symbol: str = Field(description="Stock symbol to add")
    target_price: Optional[float] = Field(None, description="Optional target price alert")
    stop_loss: Optional[float] = Field(None, description="Optional stop loss alert")

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format"""
        if not v.replace('-', '').replace('&', '').isalnum():
            raise ValueError('Symbol must contain only alphanumeric characters, hyphens, and ampersands')
        return v.upper()


class RemoveFromWatchlistRequest(BaseModel):
    """Remove from watchlist request model"""
    symbol: str = Field(description="Stock symbol to remove")

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate stock symbol format"""
        return v.upper()


class MarketStatusResponse(BaseModel):
    """Market status response model"""
    nse: Dict[str, Any] = Field(description="NSE market status")
    bse: Dict[str, Any] = Field(description="BSE market status")
    timestamp: datetime = Field(description="Status timestamp")


class TopMoversResponse(BaseModel):
    """Top movers response model"""
    gainers: List[StockQuote] = Field(description="Top gaining stocks")
    losers: List[StockQuote] = Field(description="Top losing stocks")
    most_active: List[StockQuote] = Field(description="Most active stocks by volume")
    timestamp: datetime = Field(description="Data timestamp")