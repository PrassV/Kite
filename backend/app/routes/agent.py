"""
LivePositionalAgent API routes for web interface integration
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from ..routes.auth import get_current_user
from ..core.logging_config import get_context_logger
from ..core.rate_limiter import rate_limit

# Import the LivePositionalAgent
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from agent_action import LivePositionalAgent
except ImportError:
    LivePositionalAgent = None
    logging.warning("LivePositionalAgent not available - agent routes disabled")

router = APIRouter()
logger = get_context_logger(__name__)

# Global agent instance
_agent_instance = None
_agent_status = {
    "status": "stopped",
    "started_at": None,
    "last_analysis": None,
    "analysis_count": 0,
    "error": None
}

@router.get("/status")
@rate_limit("agent")
async def get_agent_status(current_user: dict = Depends(get_current_user)):
    """Get current status of the LivePositionalAgent"""
    user_id = current_user.get("user_id")
    
    logger.info(f"📊 Agent status requested", extra={"user_id": user_id})
    
    return {
        "agent_available": LivePositionalAgent is not None,
        "status": _agent_status["status"],
        "started_at": _agent_status["started_at"],
        "last_analysis": _agent_status["last_analysis"],
        "analysis_count": _agent_status["analysis_count"],
        "error": _agent_status["error"],
        "mathematical_engine": "Advanced Pattern Detection with 13+ Indicators",
        "features": [
            "Real-time Portfolio Analysis",
            "Advanced Pattern Detection", 
            "Fibonacci Analysis",
            "Volume Profile Analysis",
            "Mathematical Indicators (Hurst, Fractal, Shannon Entropy)",
            "Live Market Monitoring",
            "Automated Risk Management"
        ]
    }

@router.post("/start")
@rate_limit("agent")
async def start_agent(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start the LivePositionalAgent"""
    global _agent_instance, _agent_status
    
    user_id = current_user.get("user_id")
    
    logger.info(f"🚀 Starting LivePositionalAgent", extra={"user_id": user_id})
    
    if not LivePositionalAgent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LivePositionalAgent is not available. Check mathematical components."
        )
    
    if _agent_status["status"] == "running":
        logger.info(f"⚠️ Agent already running", extra={"user_id": user_id})
        return {
            "message": "Agent is already running",
            "status": "running",
            "started_at": _agent_status["started_at"]
        }
    
    try:
        # Start agent in background
        background_tasks.add_task(run_agent_background, user_id)
        
        _agent_status.update({
            "status": "starting",
            "started_at": datetime.now().isoformat(),
            "error": None
        })
        
        logger.info(f"✅ Agent start initiated", extra={"user_id": user_id})
        
        return {
            "message": "LivePositionalAgent starting...",
            "status": "starting",
            "started_at": _agent_status["started_at"],
            "note": "Agent will begin mathematical analysis of your portfolio holdings"
        }
        
    except Exception as e:
        logger.error(
            f"❌ Failed to start agent",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        
        _agent_status.update({
            "status": "error",
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start agent: {str(e)}"
        )

@router.post("/stop")
@rate_limit("agent")
async def stop_agent(current_user: dict = Depends(get_current_user)):
    """Stop the LivePositionalAgent"""
    global _agent_instance, _agent_status
    
    user_id = current_user.get("user_id")
    
    logger.info(f"🛑 Stopping LivePositionalAgent", extra={"user_id": user_id})
    
    if _agent_status["status"] != "running":
        logger.info(f"⚠️ Agent not running", extra={"user_id": user_id})
        return {
            "message": "Agent is not currently running",
            "status": _agent_status["status"]
        }
    
    try:
        # Set status to stopping
        _agent_status["status"] = "stopping"
        
        # Clean up agent instance
        if _agent_instance:
            # Note: The actual LivePositionalAgent doesn't have a clean stop method
            # so we'll just mark it as stopped and let it finish its current cycle
            _agent_instance = None
        
        _agent_status.update({
            "status": "stopped",
            "error": None
        })
        
        logger.info(f"✅ Agent stopped", extra={"user_id": user_id})
        
        return {
            "message": "LivePositionalAgent stopped",
            "status": "stopped",
            "analysis_count": _agent_status["analysis_count"]
        }
        
    except Exception as e:
        logger.error(
            f"❌ Failed to stop agent",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop agent: {str(e)}"
        )

@router.get("/results")
@rate_limit("agent")
async def get_agent_results(current_user: dict = Depends(get_current_user)):
    """Get latest analysis results from the agent"""
    global _agent_instance
    
    user_id = current_user.get("user_id")
    
    logger.info(f"📊 Agent results requested", extra={"user_id": user_id})
    
    if not _agent_instance or _agent_status["status"] != "running":
        return {
            "status": "no_results",
            "message": "Agent is not running or no results available yet",
            "agent_status": _agent_status["status"]
        }
    
    try:
        # Get analysis results from agent instance
        if hasattr(_agent_instance, 'analysis_results') and _agent_instance.analysis_results:
            results = {}
            for symbol, analysis in _agent_instance.analysis_results.items():
                # Simplify the complex agent results for API consumption
                if isinstance(analysis, dict) and 'current_analysis' in analysis:
                    current = analysis['current_analysis']
                    results[symbol] = {
                        "symbol": symbol,
                        "analysis_date": current.get('analysis_summary', {}).get('analysis_date', 'N/A'),
                        "current_price": current.get('analysis_summary', {}).get('current_price', 0),
                        "trend": current.get('current_market_structure', {}).get('trend', {}).get('direction', 'N/A'),
                        "patterns_found": len(current.get('chart_patterns', [])),
                        "fibonacci_levels": len(current.get('fibonacci_analysis', {}).get('key_levels', [])),
                        "trading_opportunities": len(current.get('trading_opportunities', [])),
                        "risk_level": current.get('risk_management', {}).get('overall_risk', 'Medium')
                    }
                
            return {
                "status": "success",
                "results_count": len(results),
                "analysis": results,
                "last_updated": _agent_status["last_analysis"],
                "agent_status": _agent_status["status"]
            }
        else:
            return {
                "status": "no_results",
                "message": "Analysis in progress...",
                "agent_status": _agent_status["status"]
            }
            
    except Exception as e:
        logger.error(
            f"❌ Failed to get agent results",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent results: {str(e)}"
        )

async def run_agent_background(user_id: str):
    """Run the LivePositionalAgent in background"""
    global _agent_instance, _agent_status
    
    logger.info(f"🔄 Starting agent background task", extra={"user_id": user_id})
    
    try:
        # Update status to running
        _agent_status.update({
            "status": "running",
            "error": None
        })
        
        # Initialize the agent
        _agent_instance = LivePositionalAgent()
        
        logger.info(f"🎯 LivePositionalAgent initialized", extra={"user_id": user_id})
        
        # Run initial analysis (this is what the original agent does)
        _agent_instance._perform_initial_analysis()
        
        # Update status
        _agent_status.update({
            "last_analysis": datetime.now().isoformat(),
            "analysis_count": _agent_status["analysis_count"] + 1
        })
        
        logger.info(
            f"✅ Agent analysis completed",
            extra={
                "user_id": user_id,
                "symbols_analyzed": len(_agent_instance.analysis_results) if hasattr(_agent_instance, 'analysis_results') else 0
            }
        )
        
        # Note: The original agent runs indefinitely with live monitoring
        # For web integration, we'll run one analysis cycle and then stop
        # In production, you might want to run this periodically or keep it running
        
        _agent_status["status"] = "completed"
        
    except Exception as e:
        logger.error(
            f"❌ Agent background task failed",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        
        _agent_status.update({
            "status": "error",
            "error": str(e)
        })
        
        _agent_instance = None

@router.get("/mathematical-indicators")
@rate_limit("agent")
async def get_mathematical_indicators(current_user: dict = Depends(get_current_user)):
    """Get information about mathematical indicators used by the agent"""
    return {
        "mathematical_indicators": [
            {
                "name": "Hurst Exponent",
                "description": "Measures trend persistence and mean reversion tendencies",
                "range": "0.0 - 1.0",
                "interpretation": "> 0.5 = Trending, < 0.5 = Mean Reverting"
            },
            {
                "name": "Fractal Dimension", 
                "description": "Quantifies market roughness and complexity",
                "range": "1.0 - 2.0",
                "interpretation": "Higher values = More complex price movements"
            },
            {
                "name": "Shannon Entropy",
                "description": "Measures randomness and information content",
                "range": "0.0 - ∞",
                "interpretation": "Higher values = More unpredictable movements"
            },
            {
                "name": "Lyapunov Exponent",
                "description": "Detects chaos and sensitive dependence",
                "range": "Real numbers",
                "interpretation": "> 0 = Chaotic behavior, < 0 = Stable"
            },
            {
                "name": "DFA (Detrended Fluctuation Analysis)",
                "description": "Analyzes long-range correlations",
                "range": "0.0 - 2.0", 
                "interpretation": "> 1.0 = Long-term persistence"
            }
        ],
        "pattern_detection": [
            "Head & Shoulders",
            "Double Top/Bottom", 
            "Triangles (Ascending, Descending, Symmetrical)",
            "Wedges (Rising, Falling)",
            "Flags & Pennants",
            "Cup & Handle",
            "Rounding Patterns"
        ],
        "technical_analysis": [
            "Fibonacci Retracements & Extensions",
            "Volume Profile Analysis", 
            "Support & Resistance Levels",
            "Trendline Detection",
            "Moving Average Analysis",
            "RSI & MACD Indicators"
        ]
    }