"""
Stock-related routes for search, quotes, and market data
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
import asyncio

from ..routes.auth import get_current_user
from ..auth.kite_client import AsyncKiteClient
from ..core.config import settings
from ..core.logging_config import get_context_logger
from ..core.rate_limiter import rate_limit
from ..models.stocks import (
    StockSearchRequest,
    StockSearchResponse,
    StockQuote,
    HistoricalDataRequest,
    HistoricalDataResponse,
    WatchlistResponse,
    AddToWatchlistRequest,
    RemoveFromWatchlistRequest,
    MarketStatusResponse,
    TopMoversResponse
)

router = APIRouter()
logger = get_context_logger(__name__)

# Add portfolio/holdings routes
@router.get("/holdings")
@rate_limit("stocks")
async def get_user_holdings(
    current_user: dict = Depends(get_current_user),
    kite_client: AsyncKiteClient = Depends(get_kite_client)
):
    """Get user's holdings from Kite Connect"""
    user_id = current_user.get("user_id")
    
    logger.info(f"📊 Fetching holdings", extra={"user_id": user_id})
    
    try:
        holdings = await kite_client.get_holdings()
        
        logger.info(
            f"✅ Holdings fetched successfully",
            extra={
                "user_id": user_id,
                "holdings_count": len(holdings)
            }
        )
        
        return holdings
        
    except Exception as e:
        logger.error(
            f"❌ Failed to fetch holdings",
            extra={
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch portfolio holdings"
        )

@router.get("/positions")
@rate_limit("stocks")
async def get_user_positions(
    current_user: dict = Depends(get_current_user),
    kite_client: AsyncKiteClient = Depends(get_kite_client)
):
    """Get user's positions from Kite Connect"""
    user_id = current_user.get("user_id")
    
    logger.info(f"📈 Fetching positions", extra={"user_id": user_id})
    
    try:
        positions_data = await kite_client.get_positions()
        
        # Extract day positions (most relevant for UI)
        day_positions = positions_data.get("day", []) if positions_data else []
        net_positions = positions_data.get("net", []) if positions_data else []
        
        # Combine both day and net positions, prioritizing day positions
        all_positions = []
        
        # Add day positions first
        for pos in day_positions:
            if pos.get("quantity", 0) != 0:  # Only positions with actual quantity
                all_positions.append({
                    **pos,
                    "position_type": "day"
                })
        
        # Add net positions that aren't already in day positions
        day_symbols = {pos.get("tradingsymbol") for pos in day_positions}
        for pos in net_positions:
            if pos.get("quantity", 0) != 0 and pos.get("tradingsymbol") not in day_symbols:
                all_positions.append({
                    **pos,
                    "position_type": "net"
                })
        
        logger.info(
            f"✅ Positions fetched successfully", 
            extra={
                "user_id": user_id,
                "day_positions": len(day_positions),
                "net_positions": len(net_positions),
                "total_active": len(all_positions)
            }
        )
        
        return all_positions
        
    except Exception as e:
        logger.error(
            f"❌ Failed to fetch positions",
            extra={
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trading positions"
        )


async def get_kite_client(current_user: dict = Depends(get_current_user)) -> AsyncKiteClient:
    """Get authenticated Kite client for current user"""
    
    kite_client = AsyncKiteClient()
    
    # Get Kite access token from user data
    kite_access_token = current_user.get("kite_access_token")
    user_id = current_user.get("user_id")
    
    if not kite_access_token:
        logger.error(
            "❌ No Kite access token found for user",
            extra={"user_id": user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kite access token not found. Please re-authenticate."
        )
    
    # Set access token
    kite_client.set_access_token(kite_access_token, user_id)
    
    return kite_client


@router.get("/search", response_model=StockSearchResponse)
@rate_limit("general")
async def search_stocks(
    query: str = Query(..., min_length=1, max_length=50, description="Search query"),
    exchange: str = Query("NSE", description="Exchange to search in"),
    instrument_type: str = Query("EQ", description="Instrument type"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    kite_client: AsyncKiteClient = Depends(get_kite_client),
    current_user: dict = Depends(get_current_user)
):
    """Search for stocks by symbol or company name"""
    
    user_id = current_user.get("user_id")
    
    logger.info(
        f"🔍 Stock search",
        extra={
            "query": query,
            "exchange": exchange,
            "user_id": user_id,
            "limit": limit
        }
    )
    
    try:
        # Search instruments using Kite client
        results = await kite_client.search_instruments(
            query=query,
            exchange=exchange,
            instrument_type=instrument_type,
            limit=limit
        )
        
        logger.info(
            f"✅ Stock search completed",
            extra={
                "query": query,
                "user_id": user_id,
                "results_count": len(results)
            }
        )
        
        return StockSearchResponse(
            query=query,
            results=results,
            count=len(results),
            total_matches=len(results)  # In a full implementation, this would be the total available
        )
        
    except Exception as e:
        logger.error(
            f"❌ Stock search failed",
            extra={
                "query": query,
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stock search failed"
        )


@router.get("/quote/{symbol}")
@rate_limit("general")
async def get_stock_quote(
    symbol: str,
    kite_client: AsyncKiteClient = Depends(get_kite_client),
    current_user: dict = Depends(get_current_user)
):
    """Get real-time quote for a stock symbol"""
    
    user_id = current_user.get("user_id")
    symbol = symbol.upper()
    
    logger.info(
        f"📈 Fetching quote",
        extra={
            "symbol": symbol,
            "user_id": user_id
        }
    )
    
    try:
        # Get quote using Kite client
        quotes = await kite_client.get_quote([f"NSE:{symbol}"])
        
        if not quotes or f"NSE:{symbol}" not in quotes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote not found for symbol {symbol}"
            )
        
        quote_data = quotes[f"NSE:{symbol}"]
        
        # Format quote response
        quote = {
            "symbol": symbol,
            "last_price": quote_data.get("last_price", 0),
            "change": quote_data.get("net_change", 0),
            "change_percent": quote_data.get("change", 0),
            "volume": quote_data.get("volume", 0),
            "average_price": quote_data.get("average_price", 0),
            "open": quote_data.get("open", 0),
            "high": quote_data.get("high", 0),
            "low": quote_data.get("low", 0),
            "close": quote_data.get("close", 0),
            "bid_price": quote_data.get("bid", {}).get("price"),
            "ask_price": quote_data.get("offer", {}).get("price"),
            "bid_quantity": quote_data.get("bid", {}).get("quantity"),
            "ask_quantity": quote_data.get("offer", {}).get("quantity"),
            "timestamp": quote_data.get("timestamp")
        }
        
        logger.info(
            f"✅ Quote fetched",
            extra={
                "symbol": symbol,
                "user_id": user_id,
                "last_price": quote["last_price"]
            }
        )
        
        return quote
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Failed to fetch quote",
            extra={
                "symbol": symbol,
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quote"
        )


@router.get("/quotes")
@rate_limit("general")
async def get_multiple_quotes(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    kite_client: AsyncKiteClient = Depends(get_kite_client),
    current_user: dict = Depends(get_current_user)
):
    """Get real-time quotes for multiple symbols"""
    
    user_id = current_user.get("user_id")
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    
    if len(symbol_list) > 20:  # Limit to prevent abuse
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 symbols allowed"
        )
    
    logger.info(
        f"📈 Fetching multiple quotes",
        extra={
            "symbols": symbol_list,
            "user_id": user_id,
            "count": len(symbol_list)
        }
    )
    
    try:
        # Format symbols for Kite API
        kite_symbols = [f"NSE:{symbol}" for symbol in symbol_list]
        
        # Get quotes using Kite client
        quotes = await kite_client.get_quote(kite_symbols)
        
        # Format responses
        formatted_quotes = {}
        for symbol in symbol_list:
            kite_symbol = f"NSE:{symbol}"
            if kite_symbol in quotes:
                quote_data = quotes[kite_symbol]
                formatted_quotes[symbol] = {
                    "symbol": symbol,
                    "last_price": quote_data.get("last_price", 0),
                    "change": quote_data.get("net_change", 0),
                    "change_percent": quote_data.get("change", 0),
                    "volume": quote_data.get("volume", 0),
                    "open": quote_data.get("open", 0),
                    "high": quote_data.get("high", 0),
                    "low": quote_data.get("low", 0),
                    "timestamp": quote_data.get("timestamp")
                }
        
        logger.info(
            f"✅ Multiple quotes fetched",
            extra={
                "user_id": user_id,
                "requested": len(symbol_list),
                "found": len(formatted_quotes)
            }
        )
        
        return formatted_quotes
        
    except Exception as e:
        logger.error(
            f"❌ Failed to fetch multiple quotes",
            extra={
                "symbols": symbol_list,
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch quotes"
        )


@router.get("/market-status", response_model=MarketStatusResponse)
@rate_limit("general")
async def get_market_status(
    kite_client: AsyncKiteClient = Depends(get_kite_client),
    current_user: dict = Depends(get_current_user)
):
    """Get current market status"""
    
    user_id = current_user.get("user_id")
    
    logger.info(
        f"📊 Fetching market status",
        extra={"user_id": user_id}
    )
    
    try:
        market_status = await kite_client.get_market_status()
        
        # Format market status response
        nse_status = {}
        bse_status = {}
        
        for status_item in market_status:
            exchange = status_item.get("exchange", "").upper()
            if exchange == "NSE":
                nse_status = status_item
            elif exchange == "BSE":
                bse_status = status_item
        
        logger.info(
            f"✅ Market status fetched",
            extra={"user_id": user_id}
        )
        
        return MarketStatusResponse(
            nse=nse_status,
            bse=bse_status
        )
        
    except Exception as e:
        logger.error(
            f"❌ Failed to fetch market status",
            extra={
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch market status"
        )


@router.get("/watchlist", response_model=WatchlistResponse)
async def get_user_watchlist(
    current_user: dict = Depends(get_current_user)
):
    """Get user's watchlist"""
    
    user_id = current_user.get("user_id")
    
    logger.info(
        f"📋 Fetching watchlist",
        extra={"user_id": user_id}
    )
    
    try:
        # TODO: Implement database query for user's watchlist
        # For now, return empty watchlist
        
        return WatchlistResponse(
            items=[],
            count=0
        )
        
    except Exception as e:
        logger.error(
            f"❌ Failed to fetch watchlist",
            extra={
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch watchlist"
        )


@router.post("/watchlist")
async def add_to_watchlist(
    request: AddToWatchlistRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add symbol to user's watchlist"""
    
    user_id = current_user.get("user_id")
    
    logger.info(
        f"➕ Adding to watchlist",
        extra={
            "symbol": request.symbol,
            "user_id": user_id
        }
    )
    
    try:
        # TODO: Implement database insert for watchlist
        # For now, just return success message
        
        logger.info(
            f"✅ Added to watchlist",
            extra={
                "symbol": request.symbol,
                "user_id": user_id
            }
        )
        
        return {
            "message": f"Added {request.symbol} to watchlist",
            "symbol": request.symbol
        }
        
    except Exception as e:
        logger.error(
            f"❌ Failed to add to watchlist",
            extra={
                "symbol": request.symbol,
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add to watchlist"
        )


@router.delete("/watchlist")
async def remove_from_watchlist(
    request: RemoveFromWatchlistRequest,
    current_user: dict = Depends(get_current_user)
):
    """Remove symbol from user's watchlist"""
    
    user_id = current_user.get("user_id")
    
    logger.info(
        f"➖ Removing from watchlist",
        extra={
            "symbol": request.symbol,
            "user_id": user_id
        }
    )
    
    try:
        # TODO: Implement database delete for watchlist
        # For now, just return success message
        
        logger.info(
            f"✅ Removed from watchlist",
            extra={
                "symbol": request.symbol,
                "user_id": user_id
            }
        )
        
        return {
            "message": f"Removed {request.symbol} from watchlist",
            "symbol": request.symbol
        }
        
    except Exception as e:
        logger.error(
            f"❌ Failed to remove from watchlist",
            extra={
                "symbol": request.symbol,
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove from watchlist"
        )