#!/usr/bin/env python
"""
ZerodhaPortfolio: Real-time portfolio monitoring and cash management via Zerodha KiteConnect.
Provides live portfolio snapshot including cash, positions, PnL, and portfolio metrics.
"""
import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from kiteconnect import KiteConnect
from loguru import logger
import pandas as pd
import json
from threading import Lock

@dataclass
class PortfolioPosition:
    """Represents a single position in the portfolio"""
    ticker: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    day_pnl: float
    market_value: float
    weight: float  # % of total portfolio
    
@dataclass
class PortfolioSnapshot:
    """Complete portfolio snapshot at a point in time"""
    timestamp: datetime
    cash: float
    invested_value: float
    total_value: float
    total_pnl: float
    day_pnl: float
    positions: List[PortfolioPosition]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cash": self.cash,
            "invested_value": self.invested_value,
            "total_value": self.total_value,
            "total_pnl": self.total_pnl,
            "day_pnl": self.day_pnl,
            "positions": [
                {
                    "ticker": pos.ticker,
                    "quantity": pos.quantity,
                    "average_price": pos.average_price,
                    "current_price": pos.current_price,
                    "pnl": pos.pnl,
                    "day_pnl": pos.day_pnl,
                    "market_value": pos.market_value,
                    "weight": pos.weight
                }
                for pos in self.positions
            ]
        }

class ZerodhaPortfolioMonitor:
    """Real-time portfolio monitoring system using Zerodha KiteConnect API"""
    
    def __init__(self, cache_duration: int = 60):
        """
        Initialize portfolio monitor
        
        Args:
            cache_duration: Cache duration in seconds (default 60s)
        """
        self.cache_duration = cache_duration
        self._cache_lock = Lock()
        self._last_snapshot: Optional[PortfolioSnapshot] = None
        self._last_fetch_time: Optional[datetime] = None
        
        # Initialize Zerodha connection
        api_key = os.environ.get("ZERODHA_API_KEY")
        access_token = os.environ.get("ZERODHA_ACCESS_TOKEN")
        
        if not api_key or not access_token:
            logger.error("ZerodhaPortfolioMonitor: Missing Zerodha credentials")
            logger.error("Make sure ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN are set")
            self.kite = None
        else:
            try:
                self.kite = KiteConnect(api_key=api_key)
                self.kite.set_access_token(access_token)
                logger.info("ZerodhaPortfolioMonitor: KiteConnect initialized successfully")
            except Exception as e:
                logger.error(f"ZerodhaPortfolioMonitor: Failed to init KiteConnect: {e}")
                self.kite = None
    
    def get_cash(self) -> float:
        """Get available cash balance"""
        if not self.kite:
            logger.error("Kite client not initialized")
            return 0.0
            
        try:
            margins = self.kite.margins()
            # Use live_balance which includes all available funds (cash + recent deposits)
            equity_margin = margins.get('equity', {})
            available_cash = equity_margin.get('available', {}).get('live_balance', 0.0)
            logger.info(f"Available cash: ₹{available_cash:,.2f}")
            return float(available_cash)
        except Exception as e:
            logger.error(f"Failed to fetch cash balance: {e}")
            return 0.0
    
    def get_positions(self) -> List[Dict]:
        """Get current positions from Zerodha"""
        if not self.kite:
            logger.error("Kite client not initialized")
            return []
            
        try:
            positions = self.kite.positions()
            # Return net positions (consolidated view)
            net_positions = positions.get('net', [])
            
            # Filter out zero quantity positions
            active_positions = [
                pos for pos in net_positions 
                if pos.get('quantity', 0) != 0
            ]
            
            logger.info(f"Found {len(active_positions)} active positions")
            return active_positions
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return []
    
    def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get current market prices for given tickers"""
        if not self.kite or not tickers:
            return {}
            
        try:
            # Get instrument tokens for tickers
            instruments = self.kite.instruments("NSE")
            ticker_to_token = {}
            
            for instrument in instruments:
                if instrument['tradingsymbol'] in tickers:
                    ticker_to_token[instrument['tradingsymbol']] = instrument['instrument_token']
            
            if not ticker_to_token:
                logger.warning(f"No instrument tokens found for tickers: {tickers}")
                return {}
            
            # Get LTP (Last Traded Price) for all tokens
            tokens = list(ticker_to_token.values())
            ltp_data = self.kite.ltp([f"NSE:{token}" for token in tokens])
            
            # Map back to ticker symbols
            prices = {}
            for ticker, token in ticker_to_token.items():
                token_key = f"NSE:{token}"
                if token_key in ltp_data:
                    prices[ticker] = ltp_data[token_key]['last_price']
            
            logger.info(f"Fetched current prices for {len(prices)} tickers")
            return prices
            
        except Exception as e:
            logger.error(f"Failed to fetch current prices: {e}")
            return {}
    
    def calculate_portfolio_snapshot(self) -> Optional[PortfolioSnapshot]:
        """Calculate complete portfolio snapshot"""
        try:
            # Get cash balance
            cash = self.get_cash()
            
            # Get positions
            raw_positions = self.get_positions()
            
            if not raw_positions:
                # Portfolio with only cash
                return PortfolioSnapshot(
                    timestamp=datetime.now(),
                    cash=cash,
                    invested_value=0.0,
                    total_value=cash,
                    total_pnl=0.0,
                    day_pnl=0.0,
                    positions=[]
                )
            
            # Get current prices for all position tickers
            tickers = [pos['tradingsymbol'] for pos in raw_positions]
            current_prices = self.get_current_prices(tickers)
            
            # Calculate position metrics
            portfolio_positions = []
            total_invested_value = 0.0
            total_pnl = 0.0
            total_day_pnl = 0.0
            
            for pos in raw_positions:
                ticker = pos['tradingsymbol']
                quantity = pos['quantity']
                avg_price = pos['average_price']
                current_price = current_prices.get(ticker, avg_price)  # Fallback to avg_price
                
                market_value = quantity * current_price
                pnl = pos.get('pnl', 0.0)
                day_pnl = pos.get('day_pnl', 0.0)
                
                total_invested_value += abs(market_value)
                total_pnl += pnl
                total_day_pnl += day_pnl
                
                portfolio_positions.append(PortfolioPosition(
                    ticker=ticker,
                    quantity=quantity,
                    average_price=avg_price,
                    current_price=current_price,
                    pnl=pnl,
                    day_pnl=day_pnl,
                    market_value=market_value,
                    weight=0.0  # Will calculate after total_value
                ))
            
            total_value = cash + total_invested_value
            
            # Calculate position weights
            for pos in portfolio_positions:
                pos.weight = (abs(pos.market_value) / total_value) * 100 if total_value > 0 else 0.0
            
            snapshot = PortfolioSnapshot(
                timestamp=datetime.now(),
                cash=cash,
                invested_value=total_invested_value,
                total_value=total_value,
                total_pnl=total_pnl,
                day_pnl=total_day_pnl,
                positions=portfolio_positions
            )
            
            logger.info(f"Portfolio snapshot: Total value ₹{total_value:,.2f}, Cash ₹{cash:,.2f}, Invested ₹{total_invested_value:,.2f}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to calculate portfolio snapshot: {e}")
            return None
    
    def get_portfolio_snapshot(self, force_refresh: bool = False) -> Optional[PortfolioSnapshot]:
        """
        Get portfolio snapshot with caching
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
        """
        with self._cache_lock:
            now = datetime.now()
            
            # Check if we have cached data and it's still valid
            if (not force_refresh and 
                self._last_snapshot and 
                self._last_fetch_time and 
                (now - self._last_fetch_time).total_seconds() < self.cache_duration):
                
                logger.debug("Returning cached portfolio snapshot")
                return self._last_snapshot
            
            # Fetch fresh data
            logger.info("Fetching fresh portfolio snapshot")
            snapshot = self.calculate_portfolio_snapshot()
            
            if snapshot:
                self._last_snapshot = snapshot
                self._last_fetch_time = now
            
            return snapshot
    
    def get_portfolio_summary(self) -> Dict:
        """Get a summary of portfolio metrics"""
        snapshot = self.get_portfolio_snapshot()
        
        if not snapshot:
            return {
                "error": "Failed to fetch portfolio data",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "total_value": snapshot.total_value,
            "cash": snapshot.cash,
            "invested_value": snapshot.invested_value,
            "total_pnl": snapshot.total_pnl,
            "day_pnl": snapshot.day_pnl,
            "cash_percentage": (snapshot.cash / snapshot.total_value * 100) if snapshot.total_value > 0 else 100,
            "position_count": len(snapshot.positions),
            "top_positions": [
                {
                    "ticker": pos.ticker,
                    "weight": pos.weight,
                    "pnl": pos.pnl,
                    "market_value": pos.market_value
                }
                for pos in sorted(snapshot.positions, key=lambda x: abs(x.market_value), reverse=True)[:5]
            ]
        }
    
    async def stream_portfolio_updates(self, callback, interval: int = 30):
        """
        Stream portfolio updates at regular intervals
        
        Args:
            callback: Function to call with each portfolio snapshot
            interval: Update interval in seconds
        """
        logger.info(f"Starting portfolio streaming with {interval}s interval")
        
        while True:
            try:
                snapshot = self.get_portfolio_snapshot(force_refresh=True)
                if snapshot:
                    await callback(snapshot)
                else:
                    logger.warning("Failed to get portfolio snapshot for streaming")
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("Portfolio streaming cancelled")
                break
            except Exception as e:
                logger.error(f"Error in portfolio streaming: {e}")
                await asyncio.sleep(interval)  # Continue streaming despite errors

# Global instance for easy access
_portfolio_monitor = None

def get_portfolio_monitor() -> ZerodhaPortfolioMonitor:
    """Get singleton instance of portfolio monitor"""
    global _portfolio_monitor
    if _portfolio_monitor is None:
        _portfolio_monitor = ZerodhaPortfolioMonitor()
    return _portfolio_monitor 