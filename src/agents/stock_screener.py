#!/usr/bin/env python
"""
AI Stock Screener Agent: Intelligent scanning of NSE mid/small cap opportunities.
Uses technical analysis, fundamental metrics, and AI reasoning to identify high-potential stocks.
"""
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from loguru import logger
from kiteconnect import KiteConnect

# Import data source functions directly
from src.tools import data_source
from src.tools.zerodha_api import ZerodhaAdapter

class ScreenerSignal(Enum):
    """Stock screening signals"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

@dataclass
class StockOpportunity:
    """Represents a screened stock opportunity"""
    ticker: str
    company_name: str
    current_price: float
    market_cap: float
    sector: str
    
    # Technical indicators
    rsi: float
    macd_signal: str
    moving_avg_trend: str
    volume_surge: bool
    
    # Fundamental metrics
    pe_ratio: float
    debt_to_equity: float
    roe: float
    revenue_growth: float
    
    # AI scoring
    technical_score: float  # 0-100
    fundamental_score: float  # 0-100
    overall_score: float  # 0-100
    signal: ScreenerSignal
    confidence: float  # 0-1
    
    # Reasoning
    buy_reasons: List[str]
    risk_factors: List[str]
    target_price: float
    stop_loss: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "ticker": str(self.ticker),
            "company_name": str(self.company_name),
            "current_price": float(self.current_price),
            "market_cap": float(self.market_cap),
            "sector": str(self.sector),
            "technical_indicators": {
                "rsi": float(self.rsi),
                "macd_signal": str(self.macd_signal),
                "moving_avg_trend": str(self.moving_avg_trend),
                "volume_surge": bool(self.volume_surge)  # Convert numpy.bool_ to Python bool
            },
            "fundamental_metrics": {
                "pe_ratio": float(self.pe_ratio),
                "debt_to_equity": float(self.debt_to_equity),
                "roe": float(self.roe),
                "revenue_growth": float(self.revenue_growth)
            },
            "ai_analysis": {
                "technical_score": float(self.technical_score),
                "fundamental_score": float(self.fundamental_score),
                "overall_score": float(self.overall_score),
                "signal": str(self.signal.value),
                "confidence": float(self.confidence),
                "target_price": float(self.target_price),
                "stop_loss": float(self.stop_loss)
            },
            "reasoning": {
                "buy_reasons": [str(reason) for reason in self.buy_reasons],
                "risk_factors": [str(risk) for risk in self.risk_factors]
            }
        }

class AIStockScreener:
    """AI-powered stock screener for NSE mid/small cap opportunities"""
    
    def __init__(self):
        """Initialize the stock screener"""
        self.data_source = data_source
        self.zerodha_api = ZerodhaAdapter()
        
        # Screening criteria
        self.market_cap_range = (500, 50000)  # 500Cr to 50,000Cr (mid/small cap)
        self.min_volume = 100000  # Minimum daily volume
        self.sectors_to_focus = [
            "Technology", "Healthcare", "Consumer Goods", "Financial Services",
            "Industrial", "Energy", "Materials", "Real Estate"
        ]
        
        logger.info("AIStockScreener initialized")
    
    def get_nse_universe(self) -> List[Dict]:
        """Get NSE stock universe for screening"""
        try:
            # Get all NSE instruments from Zerodha
            if hasattr(self.zerodha_api, 'kite') and self.zerodha_api.kite:
                instruments = self.zerodha_api.kite.instruments("NSE")
                
                # Filter for equity stocks only
                equity_stocks = [
                    inst for inst in instruments 
                    if inst['instrument_type'] == 'EQ' and 
                    inst['segment'] == 'NSE'
                ]
                
                logger.info(f"Found {len(equity_stocks)} NSE equity stocks")
                return equity_stocks
            else:
                logger.warning("Zerodha API not available, using fallback stock list")
                return self._get_fallback_stock_list()
                
        except Exception as e:
            logger.error(f"Failed to fetch NSE universe: {e}")
            return self._get_fallback_stock_list()
    
    def _get_fallback_stock_list(self) -> List[Dict]:
        """Fallback list of popular NSE mid/small cap stocks"""
        return [
            {"tradingsymbol": "TATAMOTORS", "name": "Tata Motors Ltd"},
            {"tradingsymbol": "BAJFINANCE", "name": "Bajaj Finance Ltd"},
            {"tradingsymbol": "HDFCBANK", "name": "HDFC Bank Ltd"},
            {"tradingsymbol": "INFY", "name": "Infosys Ltd"},
            {"tradingsymbol": "TCS", "name": "Tata Consultancy Services"},
            {"tradingsymbol": "WIPRO", "name": "Wipro Ltd"},
            {"tradingsymbol": "TECHM", "name": "Tech Mahindra Ltd"},
            {"tradingsymbol": "MARUTI", "name": "Maruti Suzuki India Ltd"},
            {"tradingsymbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries"},
            {"tradingsymbol": "DRREDDY", "name": "Dr Reddy's Laboratories"},
            {"tradingsymbol": "CIPLA", "name": "Cipla Ltd"},
            {"tradingsymbol": "DIVISLAB", "name": "Divi's Laboratories Ltd"},
            {"tradingsymbol": "PIDILITIND", "name": "Pidilite Industries Ltd"},
            {"tradingsymbol": "DABUR", "name": "Dabur India Ltd"},
            {"tradingsymbol": "GODREJCP", "name": "Godrej Consumer Products"},
        ]
    
    def calculate_technical_indicators(self, ticker: str, price_data: pd.DataFrame) -> Dict:
        """Calculate technical indicators for a stock"""
        try:
            if price_data.empty or len(price_data) < 20:
                return self._default_technical_indicators()
            
            # Ensure we have the required columns
            if 'close' not in price_data.columns:
                price_data['close'] = price_data.get('Close', price_data.iloc[:, -1])
            if 'volume' not in price_data.columns:
                price_data['volume'] = price_data.get('Volume', 0)
            
            # RSI calculation
            rsi = self._calculate_rsi(price_data['close'])
            
            # MACD calculation
            macd_signal = self._calculate_macd_signal(price_data['close'])
            
            # Moving average trend
            ma_trend = self._calculate_ma_trend(price_data['close'])
            
            # Volume surge detection
            volume_surge = self._detect_volume_surge(price_data['volume'])
            
            return {
                "rsi": rsi,
                "macd_signal": macd_signal,
                "moving_avg_trend": ma_trend,
                "volume_surge": volume_surge
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate technical indicators for {ticker}: {e}")
            return self._default_technical_indicators()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1]) if not rsi.empty else 50.0
        except:
            return 50.0
    
    def _calculate_macd_signal(self, prices: pd.Series) -> str:
        """Calculate MACD signal"""
        try:
            ema12 = prices.ewm(span=12).mean()
            ema26 = prices.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            
            if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
                return "BULLISH_CROSSOVER"
            elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
                return "BEARISH_CROSSOVER"
            elif macd.iloc[-1] > signal.iloc[-1]:
                return "BULLISH"
            else:
                return "BEARISH"
        except:
            return "NEUTRAL"
    
    def _calculate_ma_trend(self, prices: pd.Series) -> str:
        """Calculate moving average trend"""
        try:
            ma20 = prices.rolling(window=20).mean()
            ma50 = prices.rolling(window=50).mean()
            
            current_price = prices.iloc[-1]
            ma20_current = ma20.iloc[-1]
            ma50_current = ma50.iloc[-1]
            
            if current_price > ma20_current > ma50_current:
                return "STRONG_UPTREND"
            elif current_price > ma20_current:
                return "UPTREND"
            elif current_price < ma20_current < ma50_current:
                return "STRONG_DOWNTREND"
            elif current_price < ma20_current:
                return "DOWNTREND"
            else:
                return "SIDEWAYS"
        except:
            return "NEUTRAL"
    
    def _detect_volume_surge(self, volume: pd.Series) -> bool:
        """Detect if there's a volume surge"""
        try:
            if len(volume) < 20:
                return False
            
            avg_volume = volume.rolling(window=20).mean().iloc[-2]
            current_volume = volume.iloc[-1]
            
            return bool(current_volume > (avg_volume * 1.5))  # Convert to Python bool
        except:
            return False
    
    def _default_technical_indicators(self) -> Dict:
        """Default technical indicators when calculation fails"""
        return {
            "rsi": 50.0,
            "macd_signal": "NEUTRAL",
            "moving_avg_trend": "NEUTRAL",
            "volume_surge": False
        }
    
    def get_fundamental_metrics(self, ticker: str) -> Dict:
        """Get fundamental metrics for a stock"""
        try:
            # Try to get fundamental data from data source
            # This is a placeholder - in real implementation, you'd fetch from
            # financial data APIs like Alpha Vantage, Yahoo Finance, etc.
            
            # For now, return mock data with realistic ranges
            import random
            
            return {
                "pe_ratio": round(random.uniform(10, 30), 2),
                "debt_to_equity": round(random.uniform(0.1, 2.0), 2),
                "roe": round(random.uniform(5, 25), 2),
                "revenue_growth": round(random.uniform(-10, 30), 2),
                "market_cap": round(random.uniform(500, 50000), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get fundamental metrics for {ticker}: {e}")
            return {
                "pe_ratio": 20.0,
                "debt_to_equity": 0.5,
                "roe": 15.0,
                "revenue_growth": 10.0,
                "market_cap": 5000.0
            }
    
    def calculate_ai_scores(self, technical_data: Dict, fundamental_data: Dict) -> Tuple[float, float, float]:
        """Calculate AI-powered technical, fundamental, and overall scores"""
        
        # Technical Score (0-100)
        technical_score = 50.0  # Base score
        
        # RSI scoring
        rsi = technical_data.get("rsi", 50)
        if 30 <= rsi <= 70:  # Good range
            technical_score += 20
        elif rsi < 30:  # Oversold (potential buy)
            technical_score += 15
        elif rsi > 70:  # Overbought (potential sell)
            technical_score -= 15
        
        # MACD scoring
        macd = technical_data.get("macd_signal", "NEUTRAL")
        if macd in ["BULLISH_CROSSOVER", "BULLISH"]:
            technical_score += 15
        elif macd in ["BEARISH_CROSSOVER", "BEARISH"]:
            technical_score -= 15
        
        # Moving average trend scoring
        ma_trend = technical_data.get("moving_avg_trend", "NEUTRAL")
        if ma_trend in ["STRONG_UPTREND", "UPTREND"]:
            technical_score += 15
        elif ma_trend in ["STRONG_DOWNTREND", "DOWNTREND"]:
            technical_score -= 15
        
        # Volume surge bonus
        if technical_data.get("volume_surge", False):
            technical_score += 10
        
        # Fundamental Score (0-100)
        fundamental_score = 50.0  # Base score
        
        # P/E ratio scoring
        pe = fundamental_data.get("pe_ratio", 20)
        if 10 <= pe <= 20:  # Good value range
            fundamental_score += 20
        elif pe < 10:  # Very cheap
            fundamental_score += 15
        elif pe > 30:  # Expensive
            fundamental_score -= 15
        
        # ROE scoring
        roe = fundamental_data.get("roe", 15)
        if roe > 20:
            fundamental_score += 20
        elif roe > 15:
            fundamental_score += 10
        elif roe < 10:
            fundamental_score -= 10
        
        # Debt-to-equity scoring
        de = fundamental_data.get("debt_to_equity", 0.5)
        if de < 0.5:
            fundamental_score += 15
        elif de > 1.5:
            fundamental_score -= 15
        
        # Revenue growth scoring
        growth = fundamental_data.get("revenue_growth", 10)
        if growth > 20:
            fundamental_score += 15
        elif growth > 10:
            fundamental_score += 10
        elif growth < 0:
            fundamental_score -= 20
        
        # Overall score (weighted average)
        overall_score = (technical_score * 0.4) + (fundamental_score * 0.6)
        
        # Clamp scores to 0-100 range
        technical_score = max(0, min(100, technical_score))
        fundamental_score = max(0, min(100, fundamental_score))
        overall_score = max(0, min(100, overall_score))
        
        return technical_score, fundamental_score, overall_score
    
    def generate_signal_and_reasoning(self, ticker: str, technical_data: Dict, 
                                    fundamental_data: Dict, overall_score: float) -> Tuple[ScreenerSignal, float, List[str], List[str], float, float]:
        """Generate trading signal and AI reasoning"""
        
        buy_reasons = []
        risk_factors = []
        
        # Determine signal based on overall score
        if overall_score >= 80:
            signal = ScreenerSignal.STRONG_BUY
            confidence = 0.9
        elif overall_score >= 65:
            signal = ScreenerSignal.BUY
            confidence = 0.7
        elif overall_score >= 35:
            signal = ScreenerSignal.HOLD
            confidence = 0.5
        elif overall_score >= 20:
            signal = ScreenerSignal.SELL
            confidence = 0.7
        else:
            signal = ScreenerSignal.STRONG_SELL
            confidence = 0.9
        
        # Generate buy reasons
        if technical_data.get("rsi", 50) < 35:
            buy_reasons.append("RSI indicates oversold condition - potential reversal")
        
        if technical_data.get("macd_signal") in ["BULLISH_CROSSOVER", "BULLISH"]:
            buy_reasons.append("MACD showing bullish momentum")
        
        if technical_data.get("moving_avg_trend") in ["STRONG_UPTREND", "UPTREND"]:
            buy_reasons.append("Strong upward price trend")
        
        if technical_data.get("volume_surge"):
            buy_reasons.append("Unusual volume surge indicates institutional interest")
        
        if fundamental_data.get("pe_ratio", 20) < 15:
            buy_reasons.append("Attractive valuation with low P/E ratio")
        
        if fundamental_data.get("roe", 15) > 18:
            buy_reasons.append("Strong return on equity indicates efficient management")
        
        if fundamental_data.get("revenue_growth", 10) > 15:
            buy_reasons.append("Strong revenue growth trajectory")
        
        # Generate risk factors
        if technical_data.get("rsi", 50) > 75:
            risk_factors.append("RSI indicates overbought condition - potential correction")
        
        if fundamental_data.get("debt_to_equity", 0.5) > 1.0:
            risk_factors.append("High debt levels may impact financial stability")
        
        if fundamental_data.get("pe_ratio", 20) > 25:
            risk_factors.append("High valuation may limit upside potential")
        
        if fundamental_data.get("revenue_growth", 10) < 5:
            risk_factors.append("Slow revenue growth may indicate business challenges")
        
        # Calculate target price and stop loss (simplified)
        current_price = 100.0  # Placeholder - would get from market data
        
        if signal in [ScreenerSignal.STRONG_BUY, ScreenerSignal.BUY]:
            target_price = current_price * 1.15  # 15% upside target
            stop_loss = current_price * 0.92     # 8% stop loss
        else:
            target_price = current_price * 0.95  # 5% downside target
            stop_loss = current_price * 1.05     # 5% stop loss
        
        return signal, confidence, buy_reasons, risk_factors, target_price, stop_loss
    
    async def screen_stock(self, ticker: str, company_name: str = "") -> Optional[StockOpportunity]:
        """Screen a single stock for opportunities"""
        try:
            logger.info(f"Screening stock: {ticker}")
            
            # Get price data (last 100 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=100)
            
            try:
                price_data = data_source.get_price_data(
                    ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
                )
            except Exception as e:
                logger.warning(f"Failed to get price data for {ticker}: {e}")
                price_data = pd.DataFrame()
            
            # Calculate technical indicators
            technical_data = self.calculate_technical_indicators(ticker, price_data)
            
            # Get fundamental metrics
            fundamental_data = self.get_fundamental_metrics(ticker)
            
            # Calculate AI scores
            technical_score, fundamental_score, overall_score = self.calculate_ai_scores(
                technical_data, fundamental_data
            )
            
            # Generate signal and reasoning
            signal, confidence, buy_reasons, risk_factors, target_price, stop_loss = self.generate_signal_and_reasoning(
                ticker, technical_data, fundamental_data, overall_score
            )
            
            # Get current price (placeholder)
            current_price = 100.0  # Would get from live market data
            
            opportunity = StockOpportunity(
                ticker=ticker,
                company_name=company_name or ticker,
                current_price=current_price,
                market_cap=fundamental_data.get("market_cap", 5000),
                sector="Technology",  # Placeholder
                rsi=technical_data.get("rsi", 50),
                macd_signal=technical_data.get("macd_signal", "NEUTRAL"),
                moving_avg_trend=technical_data.get("moving_avg_trend", "NEUTRAL"),
                volume_surge=technical_data.get("volume_surge", False),
                pe_ratio=fundamental_data.get("pe_ratio", 20),
                debt_to_equity=fundamental_data.get("debt_to_equity", 0.5),
                roe=fundamental_data.get("roe", 15),
                revenue_growth=fundamental_data.get("revenue_growth", 10),
                technical_score=technical_score,
                fundamental_score=fundamental_score,
                overall_score=overall_score,
                signal=signal,
                confidence=confidence,
                buy_reasons=buy_reasons,
                risk_factors=risk_factors,
                target_price=target_price,
                stop_loss=stop_loss
            )
            
            logger.info(f"Screened {ticker}: Score {overall_score:.1f}, Signal {signal.value}")
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to screen stock {ticker}: {e}")
            return None
    
    async def scan_opportunities(self, max_stocks: int = 50) -> List[StockOpportunity]:
        """Scan NSE stocks for opportunities"""
        logger.info(f"Starting AI stock screening for top {max_stocks} opportunities")
        
        # Get stock universe
        stock_universe = self.get_nse_universe()
        
        # Limit to max_stocks for performance
        stocks_to_screen = stock_universe[:max_stocks]
        
        opportunities = []
        
        # Screen stocks concurrently (but with rate limiting)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
        async def screen_with_semaphore(stock):
            async with semaphore:
                return await self.screen_stock(
                    stock.get("tradingsymbol", ""),
                    stock.get("name", "")
                )
        
        # Execute screening
        tasks = [screen_with_semaphore(stock) for stock in stocks_to_screen]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        for result in results:
            if isinstance(result, StockOpportunity):
                opportunities.append(result)
        
        # Sort by overall score (best opportunities first)
        opportunities.sort(key=lambda x: x.overall_score, reverse=True)
        
        logger.info(f"Found {len(opportunities)} stock opportunities")
        return opportunities
    
    def get_top_opportunities(self, opportunities: List[StockOpportunity], 
                            signal_filter: Optional[ScreenerSignal] = None,
                            min_score: float = 60.0,
                            limit: int = 10) -> List[StockOpportunity]:
        """Get top opportunities with filtering"""
        
        filtered = opportunities
        
        # Filter by signal
        if signal_filter:
            filtered = [opp for opp in filtered if opp.signal == signal_filter]
        
        # Filter by minimum score
        filtered = [opp for opp in filtered if opp.overall_score >= min_score]
        
        # Return top N
        return filtered[:limit]

# Global instance
_stock_screener = None

def get_stock_screener() -> AIStockScreener:
    """Get singleton instance of stock screener"""
    global _stock_screener
    if _stock_screener is None:
        _stock_screener = AIStockScreener()
    return _stock_screener 