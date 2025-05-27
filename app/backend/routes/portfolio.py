#!/usr/bin/env python
"""
Portfolio API routes for real-time portfolio monitoring and management.
Provides endpoints for portfolio data, streaming updates, and portfolio analytics.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Optional
import asyncio
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.backend.services.scheduler import (
    get_portfolio_scheduler, 
    portfolio_sse_generator
)
from src.tools.zerodha_portfolio import get_portfolio_monitor

router = APIRouter(prefix="/portfolio")

@router.get("/summary")
async def get_portfolio_summary() -> Dict:
    """
    Get current portfolio summary including cash, positions, and PnL
    """
    try:
        scheduler = get_portfolio_scheduler()
        summary = await scheduler.get_portfolio_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio summary: {str(e)}")

@router.get("/positions")
async def get_portfolio_positions() -> Dict:
    """
    Get detailed portfolio positions
    """
    try:
        portfolio_monitor = get_portfolio_monitor()
        snapshot = portfolio_monitor.get_portfolio_snapshot()
        
        if not snapshot:
            raise HTTPException(status_code=500, detail="Failed to fetch portfolio data")
        
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "positions": [
                {
                    "ticker": pos.ticker,
                    "quantity": pos.quantity,
                    "average_price": pos.average_price,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "pnl": pos.pnl,
                    "day_pnl": pos.day_pnl,
                    "weight": pos.weight
                }
                for pos in snapshot.positions
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio positions: {str(e)}")

@router.get("/cash")
async def get_cash_balance() -> Dict:
    """
    Get current cash balance
    """
    try:
        portfolio_monitor = get_portfolio_monitor()
        cash = portfolio_monitor.get_cash()
        
        return {
            "cash": cash,
            "currency": "INR",
            "timestamp": portfolio_monitor._last_fetch_time.isoformat() if portfolio_monitor._last_fetch_time else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cash balance: {str(e)}")

@router.get("/stream")
async def stream_portfolio_updates():
    """
    Stream real-time portfolio updates via Server-Sent Events (SSE)
    """
    try:
        # Start the scheduler if not already running
        scheduler = get_portfolio_scheduler()
        if not scheduler.is_running:
            await scheduler.start(interval_seconds=30)
        
        return StreamingResponse(
            portfolio_sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start portfolio stream: {str(e)}")

@router.post("/refresh")
async def refresh_portfolio() -> Dict:
    """
    Force refresh portfolio data
    """
    try:
        portfolio_monitor = get_portfolio_monitor()
        snapshot = portfolio_monitor.get_portfolio_snapshot(force_refresh=True)
        
        if not snapshot:
            raise HTTPException(status_code=500, detail="Failed to refresh portfolio data")
        
        return {
            "message": "Portfolio refreshed successfully",
            "timestamp": snapshot.timestamp.isoformat(),
            "total_value": snapshot.total_value,
            "cash": snapshot.cash,
            "invested_value": snapshot.invested_value,
            "total_pnl": snapshot.total_pnl
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh portfolio: {str(e)}")

@router.get("/analytics")
async def get_portfolio_analytics() -> Dict:
    """
    Get portfolio analytics and metrics
    """
    try:
        portfolio_monitor = get_portfolio_monitor()
        snapshot = portfolio_monitor.get_portfolio_snapshot()
        
        if not snapshot:
            raise HTTPException(status_code=500, detail="Failed to fetch portfolio data")
        
        # Calculate analytics
        total_value = snapshot.total_value
        cash_percentage = (snapshot.cash / total_value * 100) if total_value > 0 else 100
        invested_percentage = 100 - cash_percentage
        
        # Position analytics
        position_count = len(snapshot.positions)
        avg_position_size = (snapshot.invested_value / position_count) if position_count > 0 else 0
        
        # Top positions by weight
        top_positions = sorted(snapshot.positions, key=lambda x: abs(x.weight), reverse=True)[:5]
        
        # Sector concentration (simplified - would need sector mapping)
        largest_position_weight = top_positions[0].weight if top_positions else 0
        
        # PnL analytics
        total_return_pct = (snapshot.total_pnl / (total_value - snapshot.total_pnl) * 100) if (total_value - snapshot.total_pnl) > 0 else 0
        
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "portfolio_metrics": {
                "total_value": total_value,
                "cash_percentage": cash_percentage,
                "invested_percentage": invested_percentage,
                "position_count": position_count,
                "avg_position_size": avg_position_size,
                "largest_position_weight": largest_position_weight,
                "total_return_percentage": total_return_pct
            },
            "top_positions": [
                {
                    "ticker": pos.ticker,
                    "weight": pos.weight,
                    "pnl": pos.pnl,
                    "market_value": pos.market_value
                }
                for pos in top_positions
            ],
            "risk_metrics": {
                "cash_buffer": cash_percentage,
                "concentration_risk": largest_position_weight,
                "diversification_score": min(100, position_count * 10)  # Simple score
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio analytics: {str(e)}")

@router.get("/health")
async def portfolio_health_check() -> Dict:
    """
    Health check for portfolio monitoring system
    """
    try:
        portfolio_monitor = get_portfolio_monitor()
        scheduler = get_portfolio_scheduler()
        
        # Test Zerodha connection
        zerodha_connected = portfolio_monitor.kite is not None
        
        # Check scheduler status
        scheduler_running = scheduler.is_running
        
        # Test portfolio data fetch
        try:
            cash = portfolio_monitor.get_cash()
            data_accessible = True
        except:
            data_accessible = False
        
        return {
            "status": "healthy" if (zerodha_connected and data_accessible) else "degraded",
            "zerodha_connected": zerodha_connected,
            "scheduler_running": scheduler_running,
            "data_accessible": data_accessible,
            "timestamp": portfolio_monitor._last_fetch_time.isoformat() if portfolio_monitor._last_fetch_time else None,
            "subscribers": len(scheduler.subscribers)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "zerodha_connected": False,
            "scheduler_running": False,
            "data_accessible": False
        } 