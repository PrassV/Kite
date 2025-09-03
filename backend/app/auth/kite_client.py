"""
Enhanced Kite Connect client with async support and error handling
"""

import asyncio
from typing import Optional, Dict, Any, List
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import pandas as pd
import logging

from ..core.config import settings
from ..core.logging_config import get_context_logger

logger = get_context_logger(__name__)


class AsyncKiteClient:
    """Async wrapper for Kite Connect with enhanced error handling"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or settings.KITE_API_KEY
        self.api_secret = api_secret or settings.KITE_API_SECRET
        self._kite = None
        self._access_token = None
        self._user_id = None
        
    def _get_kite_instance(self) -> KiteConnect:
        """Get KiteConnect instance"""
        if not self._kite:
            self._kite = KiteConnect(api_key=self.api_key)
            if self._access_token:
                self._kite.set_access_token(self._access_token)
        return self._kite
    
    def get_login_url(self, redirect_url: str = None) -> str:
        """Get Kite Connect login URL"""
        redirect_url = redirect_url or settings.KITE_REDIRECT_URL
        kite = self._get_kite_instance()
        
        logger.info(
            "🔐 Generating Kite login URL",
            extra={"redirect_url": redirect_url}
        )
        
        return kite.login_url(redirect_url=redirect_url)
    
    async def generate_session(self, request_token: str) -> Dict[str, Any]:
        """Generate session from request token"""
        logger.info(
            "🔑 Generating Kite session",
            extra={"request_token": request_token[:10] + "..."}
        )
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            session_data = await loop.run_in_executor(
                None,
                lambda: self._get_kite_instance().generate_session(
                    request_token, 
                    api_secret=self.api_secret
                )
            )
            
            # Store session data
            self._access_token = session_data["access_token"]
            self._user_id = session_data["user_id"]
            self._get_kite_instance().set_access_token(self._access_token)
            
            logger.info(
                "✅ Kite session generated successfully",
                extra={
                    "user_id": self._user_id,
                    "access_token": self._access_token[:10] + "..."
                }
            )
            
            return session_data
            
        except Exception as e:
            logger.error(
                "❌ Failed to generate Kite session",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def set_access_token(self, access_token: str, user_id: str = None):
        """Set access token for authenticated requests"""
        self._access_token = access_token
        self._user_id = user_id
        if self._kite:
            self._kite.set_access_token(access_token)
        
        logger.info(
            "🔐 Access token set",
            extra={
                "user_id": user_id,
                "token_length": len(access_token)
            }
        )
    
    async def get_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        if not self._access_token:
            raise ValueError("Access token not set")
        
        try:
            loop = asyncio.get_event_loop()
            profile = await loop.run_in_executor(
                None,
                self._get_kite_instance().profile
            )
            
            logger.info(
                "👤 User profile fetched",
                extra={
                    "user_id": profile.get("user_id"),
                    "user_name": profile.get("user_name")
                }
            )
            
            return profile
            
        except Exception as e:
            logger.error(
                "❌ Failed to fetch user profile",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def get_instruments(self, exchange: str = None) -> List[Dict[str, Any]]:
        """Get instruments list"""
        if not self._access_token:
            raise ValueError("Access token not set")
        
        try:
            loop = asyncio.get_event_loop()
            
            if exchange:
                instruments = await loop.run_in_executor(
                    None,
                    self._get_kite_instance().instruments,
                    exchange
                )
            else:
                instruments = await loop.run_in_executor(
                    None,
                    self._get_kite_instance().instruments
                )
            
            logger.info(
                "📋 Instruments fetched",
                extra={
                    "exchange": exchange,
                    "count": len(instruments)
                }
            )
            
            return instruments
            
        except Exception as e:
            logger.error(
                "❌ Failed to fetch instruments",
                extra={"error": str(e), "exchange": exchange},
                exc_info=True
            )
            raise
    
    async def search_instruments(
        self, 
        query: str, 
        exchange: str = "NSE",
        instrument_type: str = "EQ",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search instruments by symbol or name"""
        instruments = await self.get_instruments(exchange)
        
        query_upper = query.upper()
        matches = []
        
        for instrument in instruments:
            if (instrument.get('instrument_type') == instrument_type and
                (query_upper in instrument.get('tradingsymbol', '').upper() or
                 query_upper in instrument.get('name', '').upper())):
                
                matches.append({
                    'symbol': instrument['tradingsymbol'],
                    'name': instrument['name'],
                    'exchange': instrument['exchange'],
                    'instrument_type': instrument['instrument_type'],
                    'segment': instrument.get('segment', ''),
                    'lot_size': instrument.get('lot_size'),
                    'tick_size': instrument.get('tick_size'),
                    'expiry': instrument.get('expiry'),
                    'strike': instrument.get('strike')
                })
                
                if len(matches) >= limit:
                    break
        
        logger.info(
            "🔍 Instrument search completed",
            extra={
                "query": query,
                "exchange": exchange,
                "matches": len(matches)
            }
        )
        
        return matches
    
    async def get_quote(self, symbols: List[str]) -> Dict[str, Any]:
        """Get real-time quotes for symbols"""
        if not self._access_token:
            raise ValueError("Access token not set")
        
        try:
            loop = asyncio.get_event_loop()
            quotes = await loop.run_in_executor(
                None,
                self._get_kite_instance().quote,
                symbols
            )
            
            logger.info(
                "📈 Quotes fetched",
                extra={
                    "symbols": symbols,
                    "count": len(quotes)
                }
            )
            
            return quotes
            
        except Exception as e:
            logger.error(
                "❌ Failed to fetch quotes",
                extra={"error": str(e), "symbols": symbols},
                exc_info=True
            )
            raise
    
    async def get_historical_data(
        self,
        instrument_token: int,
        from_date: datetime,
        to_date: datetime,
        interval: str = "day",
        continuous: bool = False
    ) -> pd.DataFrame:
        """Get historical OHLCV data"""
        if not self._access_token:
            raise ValueError("Access token not set")
        
        try:
            loop = asyncio.get_event_loop()
            historical_data = await loop.run_in_executor(
                None,
                self._get_kite_instance().historical_data,
                instrument_token,
                from_date,
                to_date,
                interval,
                continuous
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            if not df.empty:
                df.set_index('date', inplace=True)
            
            logger.info(
                "📊 Historical data fetched",
                extra={
                    "instrument_token": instrument_token,
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat(),
                    "interval": interval,
                    "records": len(df)
                }
            )
            
            return df
            
        except Exception as e:
            logger.error(
                "❌ Failed to fetch historical data",
                extra={
                    "error": str(e),
                    "instrument_token": instrument_token,
                    "interval": interval
                },
                exc_info=True
            )
            raise
    
    async def get_holdings(self) -> List[Dict[str, Any]]:
        """Get user's holdings"""
        if not self._access_token:
            raise ValueError("Access token not set")
        
        try:
            loop = asyncio.get_event_loop()
            holdings = await loop.run_in_executor(
                None,
                self._get_kite_instance().holdings
            )
            
            logger.info(
                "💼 Holdings fetched",
                extra={"count": len(holdings)}
            )
            
            return holdings
            
        except Exception as e:
            logger.error(
                "❌ Failed to fetch holdings",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def get_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get user's positions"""
        if not self._access_token:
            raise ValueError("Access token not set")
        
        try:
            loop = asyncio.get_event_loop()
            positions = await loop.run_in_executor(
                None,
                self._get_kite_instance().positions
            )
            
            logger.info(
                "📊 Positions fetched",
                extra={
                    "day_positions": len(positions.get("day", [])),
                    "net_positions": len(positions.get("net", []))
                }
            )
            
            return positions
            
        except Exception as e:
            logger.error(
                "❌ Failed to fetch positions",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def get_market_status(self) -> List[Dict[str, Any]]:
        """Get market status"""
        try:
            loop = asyncio.get_event_loop()
            market_status = await loop.run_in_executor(
                None,
                self._get_kite_instance().market_status
            )
            
            logger.info("📊 Market status fetched")
            return market_status
            
        except Exception as e:
            logger.error(
                "❌ Failed to fetch market status",
                extra={"error": str(e)},
                exc_info=True
            )
            raise