"""
JWT token handling with secure refresh token management
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
from passlib.context import CryptContext
import secrets
import json
import logging

from ..core.config import settings
from ..core.logging_config import get_context_logger

logger = get_context_logger(__name__)

# Password context for hashing refresh tokens
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTHandler:
    """JWT token handler with access and refresh token support"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
    
    def create_access_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create JWT access token with user data"""
        to_encode = data.copy()
        
        # Add standard JWT claims
        now = datetime.utcnow()
        expire = now + self.access_token_expire
        
        to_encode.update({
            "iat": now,
            "exp": expire,
            "type": "access"
        })
        
        # Create token
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        logger.info(
            "🎟️  Access token created",
            extra={
                "user_id": data.get("user_id"),
                "expires_at": expire.isoformat()
            }
        )
        
        return {
            "access_token": encoded_jwt,
            "token_type": "bearer",
            "expires_in": int(self.access_token_expire.total_seconds()),
            "expires_at": expire
        }
    
    def create_refresh_token(self, user_id: str) -> Dict[str, Any]:
        """Create secure refresh token"""
        # Generate random token
        raw_token = secrets.token_urlsafe(32)
        
        # Create JWT wrapper with minimal data
        now = datetime.utcnow()
        expire = now + self.refresh_token_expire
        
        token_data = {
            "user_id": user_id,
            "token_id": raw_token,
            "iat": now,
            "exp": expire,
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            token_data,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        # Hash the raw token for storage
        hashed_token = pwd_context.hash(raw_token)
        
        logger.info(
            "🔄 Refresh token created",
            extra={
                "user_id": user_id,
                "token_id": raw_token[:8] + "...",
                "expires_at": expire.isoformat()
            }
        )
        
        return {
            "refresh_token": encoded_jwt,
            "hashed_token": hashed_token,
            "token_id": raw_token,
            "expires_at": expire
        }
    
    def create_token_pair(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create both access and refresh tokens"""
        user_id = user_data["user_id"]
        
        # Create access token
        access_token_data = self.create_access_token(user_data)
        
        # Create refresh token
        refresh_token_data = self.create_refresh_token(user_id)
        
        logger.info(
            "👥 Token pair created",
            extra={"user_id": user_id}
        )
        
        return {
            "access_token": access_token_data["access_token"],
            "refresh_token": refresh_token_data["refresh_token"],
            "token_type": "bearer",
            "expires_in": access_token_data["expires_in"],
            "expires_at": access_token_data["expires_at"],
            "refresh_expires_at": refresh_token_data["expires_at"],
            # These are for backend storage, not returned to client
            "_hashed_refresh_token": refresh_token_data["hashed_token"],
            "_refresh_token_id": refresh_token_data["token_id"]
        }
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(
                    "⚠️  Token type mismatch",
                    extra={
                        "expected": token_type,
                        "received": payload.get("type")
                    }
                )
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                logger.warning(
                    "⏰ Token expired",
                    extra={
                        "token_type": token_type,
                        "expired_at": datetime.utcfromtimestamp(exp).isoformat()
                    }
                )
                return None
            
            logger.debug(
                "✅ Token verified",
                extra={
                    "token_type": token_type,
                    "user_id": payload.get("user_id")
                }
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("⏰ Token signature expired")
            return None
        except jwt.JWTError as e:
            logger.warning(
                "❌ JWT verification failed",
                extra={"error": str(e)}
            )
            return None
        except Exception as e:
            logger.error(
                "❌ Unexpected error during token verification",
                extra={"error": str(e)},
                exc_info=True
            )
            return None
    
    def verify_refresh_token(self, token: str, stored_hash: str) -> Optional[Dict[str, Any]]:
        """Verify refresh token against stored hash"""
        # First verify JWT structure
        payload = self.verify_token(token, "refresh")
        if not payload:
            return None
        
        # Get the raw token ID from payload
        token_id = payload.get("token_id")
        if not token_id:
            logger.warning("🔍 Refresh token missing token_id")
            return None
        
        # Verify against stored hash
        try:
            if pwd_context.verify(token_id, stored_hash):
                logger.info(
                    "✅ Refresh token verified",
                    extra={"user_id": payload.get("user_id")}
                )
                return payload
            else:
                logger.warning(
                    "❌ Refresh token hash mismatch",
                    extra={"user_id": payload.get("user_id")}
                )
                return None
                
        except Exception as e:
            logger.error(
                "❌ Error verifying refresh token hash",
                extra={"error": str(e)},
                exc_info=True
            )
            return None
    
    def refresh_access_token(self, refresh_token: str, stored_hash: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new access token from valid refresh token"""
        # Verify refresh token
        refresh_payload = self.verify_refresh_token(refresh_token, stored_hash)
        if not refresh_payload:
            return None
        
        # Ensure user IDs match
        if refresh_payload.get("user_id") != user_data.get("user_id"):
            logger.warning(
                "❌ User ID mismatch in refresh token",
                extra={
                    "refresh_user_id": refresh_payload.get("user_id"),
                    "provided_user_id": user_data.get("user_id")
                }
            )
            return None
        
        # Create new access token
        access_token_data = self.create_access_token(user_data)
        
        logger.info(
            "🔄 Access token refreshed",
            extra={"user_id": user_data.get("user_id")}
        )
        
        return access_token_data
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode token without verification (for debugging/logging)"""
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except Exception:
            return None


# Global JWT handler instance
jwt_handler = JWTHandler()