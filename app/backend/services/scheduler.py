#!/usr/bin/env python
"""
Scheduler service for continuous portfolio monitoring and broadcasting updates.
Uses APScheduler to run background tasks and FastAPI SSE for real-time updates.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.tools.zerodha_portfolio import get_portfolio_monitor, PortfolioSnapshot

class PortfolioScheduler:
    """Scheduler for continuous portfolio monitoring and updates"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.portfolio_monitor = get_portfolio_monitor()
        self.subscribers: List[Callable] = []
        self.is_running = False
        self.last_snapshot: Optional[PortfolioSnapshot] = None
        
    def add_subscriber(self, callback: Callable):
        """Add a callback function to receive portfolio updates"""
        self.subscribers.append(callback)
        logger.info(f"Added portfolio subscriber. Total subscribers: {len(self.subscribers)}")
    
    def remove_subscriber(self, callback: Callable):
        """Remove a callback function from portfolio updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.info(f"Removed portfolio subscriber. Total subscribers: {len(self.subscribers)}")
    
    async def fetch_and_broadcast_portfolio(self):
        """Fetch portfolio data and broadcast to all subscribers"""
        try:
            # Get fresh portfolio snapshot
            snapshot = self.portfolio_monitor.get_portfolio_snapshot(force_refresh=True)
            
            if snapshot:
                self.last_snapshot = snapshot
                
                # Broadcast to all subscribers
                if self.subscribers:
                    logger.debug(f"Broadcasting portfolio update to {len(self.subscribers)} subscribers")
                    
                    # Create update message
                    update_data = {
                        "type": "portfolio_update",
                        "data": snapshot.to_dict()
                    }
                    
                    # Send to all subscribers
                    for callback in self.subscribers.copy():  # Copy to avoid modification during iteration
                        try:
                            await callback(update_data)
                        except Exception as e:
                            logger.error(f"Error sending portfolio update to subscriber: {e}")
                            # Remove failed subscriber
                            self.remove_subscriber(callback)
                else:
                    logger.debug("No subscribers for portfolio updates")
            else:
                logger.warning("Failed to get portfolio snapshot")
                
        except Exception as e:
            logger.error(f"Error in fetch_and_broadcast_portfolio: {e}")
    
    async def start(self, interval_seconds: int = 30):
        """Start the portfolio monitoring scheduler"""
        if self.is_running:
            logger.warning("Portfolio scheduler is already running")
            return
        
        try:
            # Add the portfolio monitoring job
            self.scheduler.add_job(
                self.fetch_and_broadcast_portfolio,
                trigger=IntervalTrigger(seconds=interval_seconds),
                id='portfolio_monitor',
                name='Portfolio Monitor',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"Portfolio scheduler started with {interval_seconds}s interval")
            
            # Fetch initial portfolio data
            await self.fetch_and_broadcast_portfolio()
            
        except Exception as e:
            logger.error(f"Failed to start portfolio scheduler: {e}")
            self.is_running = False
    
    async def stop(self):
        """Stop the portfolio monitoring scheduler"""
        if not self.is_running:
            logger.warning("Portfolio scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            self.subscribers.clear()
            logger.info("Portfolio scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping portfolio scheduler: {e}")
    
    def get_last_snapshot(self) -> Optional[Dict]:
        """Get the last portfolio snapshot as dictionary"""
        if self.last_snapshot:
            return self.last_snapshot.to_dict()
        return None
    
    async def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        try:
            return self.portfolio_monitor.get_portfolio_summary()
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global scheduler instance
_portfolio_scheduler = None

def get_portfolio_scheduler() -> PortfolioScheduler:
    """Get singleton instance of portfolio scheduler"""
    global _portfolio_scheduler
    if _portfolio_scheduler is None:
        _portfolio_scheduler = PortfolioScheduler()
    return _portfolio_scheduler

# SSE Event formatting utilities
class SSEEvent:
    """Server-Sent Event formatter"""
    
    def __init__(self, data: Dict, event_type: str = "message", event_id: Optional[str] = None):
        self.data = data
        self.event_type = event_type
        self.event_id = event_id or str(int(datetime.now().timestamp() * 1000))
    
    def format(self) -> str:
        """Format as SSE event string"""
        lines = []
        
        if self.event_id:
            lines.append(f"id: {self.event_id}")
        
        lines.append(f"event: {self.event_type}")
        lines.append(f"data: {json.dumps(self.data)}")
        lines.append("")  # Empty line to end event
        
        return "\n".join(lines)

async def portfolio_sse_generator():
    """Generator for portfolio SSE events"""
    scheduler = get_portfolio_scheduler()
    
    # Queue to collect events
    event_queue = asyncio.Queue()
    
    async def event_callback(update_data: Dict):
        """Callback to add events to queue"""
        await event_queue.put(update_data)
    
    # Subscribe to portfolio updates
    scheduler.add_subscriber(event_callback)
    
    try:
        # Send initial portfolio data if available
        last_snapshot = scheduler.get_last_snapshot()
        if last_snapshot:
            initial_event = SSEEvent(
                data={
                    "type": "portfolio_update",
                    "data": last_snapshot
                },
                event_type="portfolio_update"
            )
            yield initial_event.format()
        
        # Stream updates
        while True:
            try:
                # Wait for next update with timeout
                update_data = await asyncio.wait_for(event_queue.get(), timeout=60.0)
                
                event = SSEEvent(
                    data=update_data,
                    event_type=update_data.get("type", "message")
                )
                
                yield event.format()
                
            except asyncio.TimeoutError:
                # Send keepalive
                keepalive = SSEEvent(
                    data={"type": "keepalive", "timestamp": datetime.now().isoformat()},
                    event_type="keepalive"
                )
                yield keepalive.format()
                
    except asyncio.CancelledError:
        logger.info("Portfolio SSE generator cancelled")
    except Exception as e:
        logger.error(f"Error in portfolio SSE generator: {e}")
    finally:
        # Cleanup
        scheduler.remove_subscriber(event_callback) 