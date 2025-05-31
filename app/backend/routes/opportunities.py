#!/usr/bin/env python
"""
Opportunities API Routes: Expose AI stock screening and opportunity discovery.
"""
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
import json
from loguru import logger

from src.agents.stock_screener import (
    get_stock_screener, 
    StockOpportunity, 
    ScreenerSignal,
    AIStockScreener
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

# Global cache for opportunities
_opportunities_cache: List[StockOpportunity] = []
_last_scan_time: Optional[datetime] = None
_scan_in_progress = False

@router.get("/scan")
async def scan_opportunities(
    background_tasks: BackgroundTasks,
    max_stocks: int = Query(default=20, ge=5, le=100, description="Maximum stocks to scan"),
    force_refresh: bool = Query(default=False, description="Force fresh scan ignoring cache")
):
    """
    Trigger AI stock screening for opportunities
    
    Returns immediately with scan status, actual scanning happens in background
    """
    global _scan_in_progress, _last_scan_time
    
    try:
        # Check if scan is already in progress
        if _scan_in_progress:
            return {
                "status": "scan_in_progress",
                "message": "Stock screening already in progress",
                "last_scan": _last_scan_time.isoformat() if _last_scan_time else None
            }
        
        # Check cache validity (5 minutes)
        if not force_refresh and _last_scan_time:
            time_since_scan = (datetime.now() - _last_scan_time).total_seconds()
            if time_since_scan < 300:  # 5 minutes
                return {
                    "status": "using_cache",
                    "message": f"Using cached results from {time_since_scan:.0f} seconds ago",
                    "opportunities_count": len(_opportunities_cache),
                    "last_scan": _last_scan_time.isoformat()
                }
        
        # Start background scanning
        background_tasks.add_task(_background_scan, max_stocks)
        
        return {
            "status": "scan_started",
            "message": f"AI stock screening started for {max_stocks} stocks",
            "estimated_time": f"{max_stocks * 2} seconds"
        }
        
    except Exception as e:
        logger.error(f"Failed to start opportunity scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")

async def _background_scan(max_stocks: int):
    """Background task to scan for opportunities"""
    global _opportunities_cache, _last_scan_time, _scan_in_progress
    
    try:
        _scan_in_progress = True
        logger.info(f"Starting background opportunity scan for {max_stocks} stocks")
        
        screener = get_stock_screener()
        opportunities = await screener.scan_opportunities(max_stocks=max_stocks)
        
        _opportunities_cache = opportunities
        _last_scan_time = datetime.now()
        
        logger.info(f"Background scan completed: {len(opportunities)} opportunities found")
        
    except Exception as e:
        logger.error(f"Background scan failed: {e}")
    finally:
        _scan_in_progress = False

@router.get("/list")
async def list_opportunities(
    signal: Optional[str] = Query(default=None, description="Filter by signal (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)"),
    min_score: float = Query(default=60.0, ge=0, le=100, description="Minimum overall score"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
    sector: Optional[str] = Query(default=None, description="Filter by sector")
):
    """
    Get list of current opportunities with filtering
    """
    try:
        if not _opportunities_cache:
            return {
                "opportunities": [],
                "message": "No opportunities available. Run /scan first.",
                "last_scan": None
            }
        
        # Apply filters
        filtered_opportunities = _opportunities_cache
        
        # Filter by signal
        if signal:
            try:
                signal_enum = ScreenerSignal(signal.upper())
                filtered_opportunities = [
                    opp for opp in filtered_opportunities 
                    if opp.signal == signal_enum
                ]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid signal: {signal}")
        
        # Filter by minimum score
        filtered_opportunities = [
            opp for opp in filtered_opportunities 
            if opp.overall_score >= min_score
        ]
        
        # Filter by sector
        if sector:
            filtered_opportunities = [
                opp for opp in filtered_opportunities 
                if sector.lower() in opp.sector.lower()
            ]
        
        # Apply limit
        filtered_opportunities = filtered_opportunities[:limit]
        
        return {
            "opportunities": [opp.to_dict() for opp in filtered_opportunities],
            "total_found": len(filtered_opportunities),
            "total_scanned": len(_opportunities_cache),
            "last_scan": _last_scan_time.isoformat() if _last_scan_time else None,
            "filters_applied": {
                "signal": signal,
                "min_score": min_score,
                "sector": sector,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list opportunities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list opportunities: {str(e)}")

@router.get("/top")
async def get_top_opportunities(
    count: int = Query(default=5, ge=1, le=20, description="Number of top opportunities")
):
    """
    Get top opportunities by overall score
    """
    try:
        if not _opportunities_cache:
            return {
                "top_opportunities": [],
                "message": "No opportunities available. Run /scan first."
            }
        
        # Get top opportunities (already sorted by score)
        top_opportunities = _opportunities_cache[:count]
        
        return {
            "top_opportunities": [opp.to_dict() for opp in top_opportunities],
            "count": len(top_opportunities),
            "last_scan": _last_scan_time.isoformat() if _last_scan_time else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get top opportunities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get top opportunities: {str(e)}")

@router.get("/analyze/{ticker}")
async def analyze_single_stock(ticker: str):
    """
    Analyze a single stock for opportunities
    """
    try:
        screener = get_stock_screener()
        opportunity = await screener.screen_stock(ticker.upper())
        
        if not opportunity:
            raise HTTPException(status_code=404, detail=f"Could not analyze stock: {ticker}")
        
        return {
            "analysis": opportunity.to_dict(),
            "analyzed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze stock {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze stock: {str(e)}")

@router.get("/status")
async def get_scan_status():
    """
    Get current scanning status and cache info
    """
    return {
        "scan_in_progress": _scan_in_progress,
        "opportunities_cached": len(_opportunities_cache),
        "last_scan": _last_scan_time.isoformat() if _last_scan_time else None,
        "cache_age_seconds": (
            (datetime.now() - _last_scan_time).total_seconds() 
            if _last_scan_time else None
        )
    }

@router.get("/signals")
async def get_signal_distribution():
    """
    Get distribution of signals across all opportunities
    """
    try:
        if not _opportunities_cache:
            return {"message": "No opportunities available"}
        
        signal_counts = {}
        for signal in ScreenerSignal:
            signal_counts[signal.value] = len([
                opp for opp in _opportunities_cache 
                if opp.signal == signal
            ])
        
        return {
            "signal_distribution": signal_counts,
            "total_opportunities": len(_opportunities_cache),
            "last_scan": _last_scan_time.isoformat() if _last_scan_time else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get signal distribution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get signal distribution: {str(e)}")

@router.get("/stream")
async def stream_opportunities():
    """
    Stream opportunities as Server-Sent Events
    """
    async def event_generator():
        while True:
            try:
                # Send current opportunities
                if _opportunities_cache:
                    data = {
                        "opportunities": [opp.to_dict() for opp in _opportunities_cache[:10]],
                        "total_count": len(_opportunities_cache),
                        "last_scan": _last_scan_time.isoformat() if _last_scan_time else None,
                        "scan_in_progress": _scan_in_progress,
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in opportunities stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    ) 