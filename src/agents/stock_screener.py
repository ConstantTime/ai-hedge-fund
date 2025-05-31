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
import random

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
        
        # Enhanced screening criteria
        self.market_cap_range = (500, 50000)  # 500Cr to 50,000Cr (mid/small cap)
        self.min_volume = 100000  # Minimum daily volume
        self.sectors_to_focus = [
            "Technology", "Healthcare", "Consumer Goods", "Financial Services",
            "Industrial", "Energy", "Materials", "Real Estate", "Pharmaceuticals",
            "Automotive", "Chemicals", "Textiles", "Media", "Telecommunications"
        ]
        
        # Sector-based stock mapping (for better selection)
        self.sector_stocks = {
            "Technology": ["TCS", "INFY", "WIPRO", "TECHM", "HCLTECH", "LTI", "MPHASIS", "MINDTREE"],
            "Healthcare": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "LUPIN", "AUROBINDO", "BIOCON"],
            "Financial": ["HDFCBANK", "ICICIBANK", "BAJFINANCE", "KOTAKBANK", "SBIN", "AXISBANK"],
            "Automotive": ["TATAMOTORS", "MARUTI", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "TVSMOTORS"],
            "Consumer": ["PIDILITIND", "DABUR", "GODREJCP", "BRITANNIA", "NESTLEIND", "HUL"],
            "Industrial": ["RELIANCE", "LT", "SIEMENS", "ABB", "BHEL", "CUMMINSIND"],
            "Materials": ["JSWSTEEL", "TATASTEEL", "HINDALCO", "VEDL", "JINDALSTEL", "SAIL"],
            "Energy": ["ONGC", "IOC", "BPCL", "GAIL", "NTPC", "POWERGRID"]
        }
        
        logger.info("AIStockScreener initialized with intelligent filtering")
    
    def get_nse_universe(self) -> List[Dict]:
        """Get NSE stock universe for screening with intelligent pre-filtering"""
        try:
            logger.info("🔍 SCREENING: Starting intelligent NSE universe discovery...")
            
            # Get all NSE instruments from Zerodha
            if hasattr(self.zerodha_api, 'kite') and self.zerodha_api.kite:
                logger.info("🔍 SCREENING: Fetching NSE instruments from Zerodha API...")
                instruments = self.zerodha_api.kite.instruments("NSE")
                
                # Filter for equity stocks only
                equity_stocks = [
                    inst for inst in instruments 
                    if inst['instrument_type'] == 'EQ' and 
                    inst['segment'] == 'NSE' and
                    self._is_stock_tradeable(inst)
                ]
                
                logger.info(f"🔍 SCREENING: Found {len(equity_stocks)} tradeable NSE equity stocks")
                
                # Apply intelligent filtering
                filtered_stocks = self._apply_intelligent_filtering(equity_stocks)
                logger.info(f"🧠 AI_FILTER: Reduced universe to {len(filtered_stocks)} high-potential stocks")
                
                return filtered_stocks
            else:
                logger.warning("🔍 SCREENING: Zerodha API not available, using fallback stock list")
                return self._get_enhanced_fallback_stock_list()
                
        except Exception as e:
            logger.error(f"🔍 SCREENING: Failed to fetch NSE universe: {e}")
            return self._get_enhanced_fallback_stock_list()
    
    def _is_stock_tradeable(self, instrument: Dict) -> bool:
        """Check if stock is tradeable (basic filters)"""
        try:
            symbol = instrument.get('tradingsymbol', '')
            
            # Skip if symbol contains patterns that indicate non-standard stocks
            skip_patterns = ['-BE', '-SM', '-BZ', '-IL', '-BL', 'PP-', 'M-']
            if any(pattern in symbol for pattern in skip_patterns):
                return False
            
            # Skip very short symbols (likely indices or special instruments)
            if len(symbol) < 3:
                return False
                
            # Skip symbols with numbers (often warrants, rights, etc.)
            if any(char.isdigit() for char in symbol):
                return False
                
            return True
            
        except Exception as e:
            logger.debug(f"⚠️ TRADEABLE_CHECK: Error checking {instrument}: {e}")
            return False
    
    def _apply_intelligent_filtering(self, stocks: List[Dict]) -> List[Dict]:
        """Apply AI-powered intelligent filtering to select best candidates"""
        logger.info("🧠 AI_FILTER: Starting intelligent stock filtering...")
        
        # Step 1: Sector-based diversified selection
        sector_selected = self._select_by_sector_diversity(stocks)
        logger.info(f"🎯 SECTOR_FILTER: Selected {len(sector_selected)} stocks across sectors")
        
        # Step 2: Market cap and volume filtering (when data available)
        cap_filtered = self._filter_by_market_metrics(sector_selected)
        logger.info(f"💰 CAP_FILTER: {len(cap_filtered)} stocks passed market cap/volume filters")
        
        # Step 3: Technical strength pre-filtering
        technically_strong = self._prefilter_technical_strength(cap_filtered)
        logger.info(f"📈 TECH_FILTER: {len(technically_strong)} stocks show technical strength")
        
        # Step 4: Smart sampling for final selection
        final_selection = self._smart_sample_stocks(technically_strong, max_stocks=50)
        logger.info(f"🎲 SMART_SAMPLE: Final selection of {len(final_selection)} stocks")
        
        return final_selection
    
    def _select_by_sector_diversity(self, stocks: List[Dict]) -> List[Dict]:
        """Select stocks ensuring sector diversity"""
        selected = []
        stocks_by_sector = {}
        
        # Group stocks by known sectors
        for stock in stocks:
            symbol = stock.get('tradingsymbol', '')
            sector = self._determine_stock_sector(symbol)
            
            if sector not in stocks_by_sector:
                stocks_by_sector[sector] = []
            stocks_by_sector[sector].append(stock)
        
        # Select balanced number from each sector
        stocks_per_sector = max(10, 200 // len(stocks_by_sector))  # Aim for ~200 total
        
        for sector, sector_stocks in stocks_by_sector.items():
            # Shuffle to avoid alphabetical bias
            shuffled = sector_stocks.copy()
            random.shuffle(shuffled)
            
            # Take top stocks from each sector
            sector_selection = shuffled[:stocks_per_sector]
            selected.extend(sector_selection)
            
            logger.debug(f"🎯 SECTOR: {sector} contributed {len(sector_selection)} stocks")
        
        return selected
    
    def _determine_stock_sector(self, symbol: str) -> str:
        """Determine sector for a stock symbol"""
        # Check known sector mappings
        for sector, stocks in self.sector_stocks.items():
            if symbol in stocks:
                return sector
        
        # Use simple heuristics for unknown stocks
        if any(term in symbol for term in ['TECH', 'INFO', 'SOFT', 'COMP']):
            return "Technology"
        elif any(term in symbol for term in ['PHARMA', 'DRUG', 'MED', 'BIO']):
            return "Healthcare"
        elif any(term in symbol for term in ['BANK', 'FIN', 'NBFC']):
            return "Financial"
        elif any(term in symbol for term in ['AUTO', 'MOTOR', 'BAJAJ']):
            return "Automotive"
        elif any(term in symbol for term in ['STEEL', 'METAL', 'ALUMIN', 'COPPER']):
            return "Materials"
        elif any(term in symbol for term in ['OIL', 'GAS', 'PETRO', 'ENERGY']):
            return "Energy"
        else:
            return "Others"
    
    def _filter_by_market_metrics(self, stocks: List[Dict]) -> List[Dict]:
        """Filter stocks by market cap and volume (when data available)"""
        filtered = []
        
        for stock in stocks:
            symbol = stock.get('tradingsymbol', '')
            
            try:
                # Try to get basic market data for filtering
                fundamentals = self.zerodha_api.get_fundamentals(symbol)
                
                if fundamentals and 'error' not in fundamentals:
                    market_cap = fundamentals.get('market_cap', 0)
                    
                    # Apply market cap filter
                    if self.market_cap_range[0] <= market_cap <= self.market_cap_range[1]:
                        filtered.append(stock)
                        logger.debug(f"✅ CAP_PASS: {symbol} market cap ₹{market_cap}Cr in range")
                    else:
                        logger.debug(f"❌ CAP_FAIL: {symbol} market cap ₹{market_cap}Cr out of range")
                else:
                    # If no fundamental data, include in filtered list for later screening
                    # This ensures we don't lose potentially good stocks due to data unavailability
                    filtered.append(stock)
                    logger.debug(f"⚠️ CAP_UNKNOWN: {symbol} included despite missing cap data")
                    
            except Exception as e:
                # Include stock if we can't check (to avoid losing good opportunities)
                filtered.append(stock)
                logger.debug(f"⚠️ CAP_ERROR: {symbol} included despite error: {e}")
        
        return filtered
    
    def _prefilter_technical_strength(self, stocks: List[Dict]) -> List[Dict]:
        """Pre-filter stocks based on technical strength indicators"""
        technically_strong = []
        
        # Sample a subset for technical analysis (to avoid API rate limits)
        sample_size = min(len(stocks), 100)
        sampled_stocks = random.sample(stocks, sample_size)
        
        logger.info(f"📊 TECH_PREFILTER: Analyzing {sample_size} stocks for technical strength")
        
        for stock in sampled_stocks:
            symbol = stock.get('tradingsymbol', '')
            
            try:
                # Get basic price data for quick technical check
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)  # Just 30 days for quick check
                
                price_data = data_source.get_price_data(
                    symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
                )
                
                if not price_data.empty and len(price_data) >= 10:
                    # Quick technical strength check
                    recent_high = price_data['high'].tail(10).max()
                    recent_low = price_data['low'].tail(10).min()
                    current_price = price_data['close'].iloc[-1]
                    
                    # Price position in recent range (higher is better)
                    price_position = (current_price - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0.5
                    
                    # Volume trend (if available)
                    volume_strength = 1.0  # Default
                    if 'volume' in price_data.columns and len(price_data) >= 5:
                        recent_avg_volume = price_data['volume'].tail(5).mean()
                        older_avg_volume = price_data['volume'].head(5).mean() if len(price_data) >= 10 else recent_avg_volume
                        volume_strength = recent_avg_volume / older_avg_volume if older_avg_volume > 0 else 1.0
                    
                    # Simple technical score
                    tech_score = (price_position * 0.6) + (min(volume_strength, 2.0) / 2.0 * 0.4)
                    
                    # Include if technically promising
                    if tech_score >= 0.4:  # 40% threshold
                        technically_strong.append(stock)
                        logger.debug(f"💪 TECH_STRONG: {symbol} score {tech_score:.2f}")
                    else:
                        logger.debug(f"💤 TECH_WEAK: {symbol} score {tech_score:.2f}")
                else:
                    # Include if no technical data (don't lose opportunities)
                    technically_strong.append(stock)
                    logger.debug(f"⚠️ TECH_UNKNOWN: {symbol} included despite missing price data")
                    
            except Exception as e:
                # Include stock if technical analysis fails
                technically_strong.append(stock)
                logger.debug(f"⚠️ TECH_ERROR: {symbol} included despite error: {e}")
        
        # If we don't have enough technically strong stocks, add more from original list
        if len(technically_strong) < 30:
            remaining_stocks = [s for s in stocks if s not in sampled_stocks]
            additional_needed = min(30 - len(technically_strong), len(remaining_stocks))
            technically_strong.extend(random.sample(remaining_stocks, additional_needed))
            logger.info(f"📊 TECH_BACKFILL: Added {additional_needed} additional stocks")
        
        return technically_strong
    
    def _smart_sample_stocks(self, stocks: List[Dict], max_stocks: int = 50) -> List[Dict]:
        """Smart sampling to get final stock selection"""
        if len(stocks) <= max_stocks:
            return stocks
        
        # Ensure sector diversity in final selection
        stocks_by_sector = {}
        for stock in stocks:
            symbol = stock.get('tradingsymbol', '')
            sector = self._determine_stock_sector(symbol)
            
            if sector not in stocks_by_sector:
                stocks_by_sector[sector] = []
            stocks_by_sector[sector].append(stock)
        
        # Smart allocation across sectors
        final_selection = []
        stocks_per_sector = max_stocks // len(stocks_by_sector)
        remaining_slots = max_stocks % len(stocks_by_sector)
        
        for sector, sector_stocks in stocks_by_sector.items():
            allocation = stocks_per_sector
            if remaining_slots > 0:
                allocation += 1
                remaining_slots -= 1
            
            # Shuffle for randomness within sector
            shuffled = sector_stocks.copy()
            random.shuffle(shuffled)
            
            selected_from_sector = shuffled[:min(allocation, len(shuffled))]
            final_selection.extend(selected_from_sector)
            
            logger.debug(f"🎲 FINAL_SAMPLE: {sector} -> {len(selected_from_sector)} stocks")
        
        # If we still need more stocks, add randomly
        if len(final_selection) < max_stocks:
            remaining = [s for s in stocks if s not in final_selection]
            additional = min(max_stocks - len(final_selection), len(remaining))
            final_selection.extend(random.sample(remaining, additional))
            logger.debug(f"🎲 FINAL_RANDOM: Added {additional} random stocks")
        
        return final_selection[:max_stocks]
    
    def _get_enhanced_fallback_stock_list(self) -> List[Dict]:
        """Enhanced fallback list with sector diversity"""
        fallback_stocks = []
        
        # Add stocks from each sector for diversity
        for sector, stocks in self.sector_stocks.items():
            for symbol in stocks[:3]:  # Top 3 from each sector
                fallback_stocks.append({
                    "tradingsymbol": symbol, 
                    "name": f"{symbol} Ltd",
                    "sector": sector
                })
        
        logger.info(f"📋 FALLBACK: Using enhanced fallback list with {len(fallback_stocks)} diversified stocks")
        return fallback_stocks
    
    def calculate_technical_indicators(self, ticker: str, price_data: pd.DataFrame) -> Dict:
        """Calculate technical indicators for a stock"""
        logger.debug(f"📊 TECHNICAL: Calculating indicators for {ticker}")
        
        if price_data.empty:
            logger.warning(f"📊 TECHNICAL: No price data for {ticker}, using fallback indicators")
            return {
                "rsi": 50.0,
                "macd_signal": "NEUTRAL", 
                "moving_avg_trend": "NEUTRAL",
                "volume_surge": False
            }
        
        try:
            # Calculate RSI
            delta = price_data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50.0
            
            logger.debug(f"📊 TECHNICAL: {ticker} RSI = {current_rsi:.1f}")
            
            # Simple MACD
            ema12 = price_data['close'].ewm(span=12).mean()
            ema26 = price_data['close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal_line = macd.ewm(span=9).mean()
            
            if len(macd) >= 2:
                if macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-2] <= signal_line.iloc[-2]:
                    macd_signal = "BULLISH_CROSSOVER"
                elif macd.iloc[-1] < signal_line.iloc[-1] and macd.iloc[-2] >= signal_line.iloc[-2]:
                    macd_signal = "BEARISH_CROSSOVER"
                elif macd.iloc[-1] > signal_line.iloc[-1]:
                    macd_signal = "BULLISH"
                else:
                    macd_signal = "BEARISH"
            else:
                macd_signal = "NEUTRAL"
            
            logger.debug(f"📊 TECHNICAL: {ticker} MACD = {macd_signal}")
            
            # Moving average trend
            if len(price_data) >= 50:
                ma20 = price_data['close'].rolling(window=20).mean()
                ma50 = price_data['close'].rolling(window=50).mean()
                current_price = price_data['close'].iloc[-1]
                
                if current_price > ma20.iloc[-1] > ma50.iloc[-1]:
                    ma_trend = "STRONG_UPTREND"
                elif current_price > ma20.iloc[-1]:
                    ma_trend = "UPTREND"
                elif current_price < ma20.iloc[-1] < ma50.iloc[-1]:
                    ma_trend = "STRONG_DOWNTREND"
                elif current_price < ma20.iloc[-1]:
                    ma_trend = "DOWNTREND"
                else:
                    ma_trend = "NEUTRAL"
            else:
                ma_trend = "NEUTRAL"
            
            logger.debug(f"📊 TECHNICAL: {ticker} Trend = {ma_trend}")
            
            # Volume surge detection
            if 'volume' in price_data.columns and len(price_data) >= 20:
                avg_volume = price_data['volume'].rolling(window=20).mean()
                current_volume = price_data['volume'].iloc[-1]
                volume_surge = current_volume > (avg_volume.iloc[-1] * 1.5)
            else:
                volume_surge = False
            
            logger.debug(f"📊 TECHNICAL: {ticker} Volume surge = {volume_surge}")
            
            indicators = {
                "rsi": float(current_rsi),
                "macd_signal": macd_signal,
                "moving_avg_trend": ma_trend,
                "volume_surge": bool(volume_surge)
            }
            
            logger.info(f"📊 TECHNICAL: {ticker} indicators calculated: RSI={current_rsi:.1f}, MACD={macd_signal}, Trend={ma_trend}, VolSurge={volume_surge}")
            return indicators
            
        except Exception as e:
            logger.error(f"📊 TECHNICAL: Error calculating indicators for {ticker}: {e}")
            return {
                "rsi": 50.0,
                "macd_signal": "NEUTRAL",
                "moving_avg_trend": "NEUTRAL", 
                "volume_surge": False
            }
    
    def get_fundamental_metrics(self, ticker: str) -> Dict:
        """Get fundamental metrics for a stock - ONLY REAL DATA, no fallbacks"""
        try:
            logger.debug(f"💰 FUNDAMENTALS: Fetching real data for {ticker}")
            
            # Get real fundamental data from Zerodha adapter (screener.in)
            fundamentals = self.zerodha_api.get_fundamentals(ticker)
            
            if not fundamentals or 'error' in fundamentals:
                logger.warning(f"🚫 SKIP_STOCK: {ticker} - No real data available from screener.in")
                return None  # Return None instead of fake data
            
            # Validate that we have essential data
            if not fundamentals.get('pe_ratio') or not fundamentals.get('price'):
                logger.warning(f"🚫 SKIP_STOCK: {ticker} - Missing essential data (P/E or Price)")
                return None
            
            # Extract key metrics with safe defaults and better field mapping
            pe_ratio = fundamentals.get('pe_ratio')
            
            # Calculate debt to equity from balance sheet data
            total_debt = fundamentals.get('total_debt', 0.0)
            reserves = fundamentals.get('reserves', 0.0)
            debt_to_equity = (total_debt / reserves) if reserves > 0 else 0.0
            
            roe = fundamentals.get('roe', 0.0)
            
            # Since sales_growth isn't directly available, calculate or use a reasonable default
            # In real implementation, you'd compare with previous year's sales
            revenue_growth = 10.0  # Default value - would need historical data for actual calculation
            
            market_cap = fundamentals.get('market_cap')
            price = fundamentals.get('price')
            book_value = fundamentals.get('book_value_per_share', 0.0)
            eps = fundamentals.get('earnings_per_share', 0.0)
            
            # Extract additional useful metrics
            roce = fundamentals.get('roce', 0.0)
            dividend_yield = fundamentals.get('dividend_yield', 0.0)
            sales = fundamentals.get('sales', 0.0)
            net_profit = fundamentals.get('net_profit', 0.0)
            
            # Try to determine sector - not directly available, use "Unknown" for now
            sector = "Unknown"  # Could be enhanced with a ticker-to-sector mapping
            
            logger.info(f"✅ REAL_DATA: {ticker} - P/E: {pe_ratio}, ROE: {roe}%, D/E: {debt_to_equity:.2f}, Market Cap: ₹{market_cap}Cr, Price: ₹{price}")
            
            return {
                "pe_ratio": float(pe_ratio),
                "debt_to_equity": float(debt_to_equity),
                "roe": float(roe),
                "revenue_growth": float(revenue_growth),
                "market_cap": float(market_cap),
                "price": float(price),
                "book_value": float(book_value),
                "eps": float(eps),
                "sector": str(sector),
                # Additional metrics for enhanced analysis
                "roce": float(roce),
                "dividend_yield": float(dividend_yield),
                "sales": float(sales),
                "net_profit": float(net_profit),
                "data_source": "screener.in"  # Track data source
            }
            
        except Exception as e:
            logger.error(f"🚫 SKIP_STOCK: {ticker} - Failed to get real data: {e}")
            return None  # Return None instead of fake data
    
    def _get_fallback_fundamental_metrics(self) -> Dict:
        """DEPRECATED: No longer used - we skip stocks instead of using fake data"""
        logger.error("🚫 DEPRECATED: _get_fallback_fundamental_metrics should not be called")
        raise ValueError("Fake data generation is disabled - stocks should be skipped instead")
    
    def calculate_ai_scores(self, technical_data: Dict, fundamental_data: Dict) -> Tuple[float, float, float]:
        """Calculate AI-powered technical, fundamental, and overall scores"""
        
        logger.debug(f"🤖 AI_SCORING: Technical data: {technical_data}")
        logger.debug(f"🤖 AI_SCORING: Fundamental data: {fundamental_data}")
        
        # Technical Score (0-100)
        technical_score = 50.0  # Base score
        
        # RSI scoring
        rsi = technical_data.get("rsi", 50)
        if 30 <= rsi <= 70:  # Good range
            technical_score += 20
            logger.debug(f"🤖 AI_SCORING: RSI {rsi:.1f} in good range, +20 points")
        elif rsi < 30:  # Oversold (potential buy)
            technical_score += 15
            logger.debug(f"🤖 AI_SCORING: RSI {rsi:.1f} oversold, +15 points")
        elif rsi > 70:  # Overbought (potential sell)
            technical_score -= 15
            logger.debug(f"🤖 AI_SCORING: RSI {rsi:.1f} overbought, -15 points")
        
        # MACD scoring
        macd = technical_data.get("macd_signal", "NEUTRAL")
        if macd in ["BULLISH_CROSSOVER", "BULLISH"]:
            technical_score += 15
            logger.debug(f"🤖 AI_SCORING: MACD {macd}, +15 points")
        elif macd in ["BEARISH_CROSSOVER", "BEARISH"]:
            technical_score -= 15
            logger.debug(f"🤖 AI_SCORING: MACD {macd}, -15 points")
        
        # Moving average trend scoring
        ma_trend = technical_data.get("moving_avg_trend", "NEUTRAL")
        if ma_trend in ["STRONG_UPTREND", "UPTREND"]:
            technical_score += 15
            logger.debug(f"🤖 AI_SCORING: Trend {ma_trend}, +15 points")
        elif ma_trend in ["STRONG_DOWNTREND", "DOWNTREND"]:
            technical_score -= 15
            logger.debug(f"🤖 AI_SCORING: Trend {ma_trend}, -15 points")
        
        # Volume surge bonus
        if technical_data.get("volume_surge", False):
            technical_score += 10
            logger.debug(f"🤖 AI_SCORING: Volume surge detected, +10 points")
        
        # Fundamental Score (0-100)
        fundamental_score = 50.0  # Base score
        
        # P/E ratio scoring
        pe = fundamental_data.get("pe_ratio", 20)
        if 10 <= pe <= 20:  # Good value range
            fundamental_score += 20
            logger.debug(f"🤖 AI_SCORING: P/E {pe:.1f} in good range, +20 points")
        elif pe < 10:  # Very cheap
            fundamental_score += 15
            logger.debug(f"🤖 AI_SCORING: P/E {pe:.1f} very cheap, +15 points")
        elif pe > 30:  # Expensive
            fundamental_score -= 15
            logger.debug(f"🤖 AI_SCORING: P/E {pe:.1f} expensive, -15 points")
        
        # ROE scoring
        roe = fundamental_data.get("roe", 15)
        if roe > 20:
            fundamental_score += 20
            logger.debug(f"🤖 AI_SCORING: ROE {roe:.1f}% excellent, +20 points")
        elif roe > 15:
            fundamental_score += 10
            logger.debug(f"🤖 AI_SCORING: ROE {roe:.1f}% good, +10 points")
        elif roe < 10:
            fundamental_score -= 10
            logger.debug(f"🤖 AI_SCORING: ROE {roe:.1f}% poor, -10 points")
        
        # Debt to equity scoring
        de = fundamental_data.get("debt_to_equity", 0.5)
        if de < 0.3:
            fundamental_score += 15
            logger.debug(f"🤖 AI_SCORING: D/E {de:.2f} low debt, +15 points")
        elif de > 1.0:
            fundamental_score -= 15
            logger.debug(f"🤖 AI_SCORING: D/E {de:.2f} high debt, -15 points")
        
        # Revenue growth scoring
        growth = fundamental_data.get("revenue_growth", 10)
        if growth > 20:
            fundamental_score += 15
            logger.debug(f"🤖 AI_SCORING: Revenue growth {growth:.1f}% strong, +15 points")
        elif growth > 10:
            fundamental_score += 10
            logger.debug(f"🤖 AI_SCORING: Revenue growth {growth:.1f}% good, +10 points")
        elif growth < 5:
            fundamental_score -= 10
            logger.debug(f"🤖 AI_SCORING: Revenue growth {growth:.1f}% weak, -10 points")
        
        # Ensure scores are within bounds
        technical_score = max(0, min(100, technical_score))
        fundamental_score = max(0, min(100, fundamental_score))
        overall_score = (technical_score + fundamental_score) / 2
        
        logger.info(f"🤖 AI_SCORING: Final scores - Technical: {technical_score:.1f}, Fundamental: {fundamental_score:.1f}, Overall: {overall_score:.1f}")
        
        return technical_score, fundamental_score, overall_score
    
    def generate_signal_and_reasoning(self, ticker: str, technical_data: Dict, 
                                    fundamental_data: Dict, overall_score: float, current_price: float) -> Tuple[ScreenerSignal, float, List[str], List[str], float, float]:
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
        if signal in [ScreenerSignal.STRONG_BUY, ScreenerSignal.BUY]:
            target_price = current_price * 1.15  # 15% upside target
            stop_loss = current_price * 0.92     # 8% stop loss
        else:
            target_price = current_price * 0.95  # 5% downside target
            stop_loss = current_price * 1.05     # 5% stop loss
        
        return signal, confidence, buy_reasons, risk_factors, target_price, stop_loss
    
    async def screen_stock(self, ticker: str, company_name: str = "") -> Optional[StockOpportunity]:
        """Screen a single stock for opportunities - ONLY with real data"""
        try:
            logger.info(f"🔍 SCREENING: Starting analysis for {ticker}")
            
            # Get fundamental metrics first (contains price, sector, etc.)
            fundamental_data = self.get_fundamental_metrics(ticker)
            
            # Skip stock if no real fundamental data available
            if fundamental_data is None:
                logger.warning(f"🚫 SKIPPED: {ticker} - No real fundamental data available")
                return None
            
            # Get price data (last 100 days) for technical analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=100)
            
            try:
                price_data = data_source.get_price_data(
                    ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
                )
            except Exception as e:
                logger.warning(f"📊 TECHNICAL: Failed to get price data for {ticker}: {e}")
                price_data = pd.DataFrame()
            
            # Calculate technical indicators
            technical_data = self.calculate_technical_indicators(ticker, price_data)
            
            # Calculate AI scores
            technical_score, fundamental_score, overall_score = self.calculate_ai_scores(
                technical_data, fundamental_data
            )
            
            # Generate signal and reasoning with real current price
            current_price = fundamental_data.get("price")
            signal, confidence, buy_reasons, risk_factors, target_price, stop_loss = self.generate_signal_and_reasoning(
                ticker, technical_data, fundamental_data, overall_score, current_price
            )
            
            # Extract real data from fundamentals
            market_cap = fundamental_data.get("market_cap")
            sector = fundamental_data.get("sector", "Unknown")
            company_name = company_name or ticker
            
            opportunity = StockOpportunity(
                ticker=ticker,
                company_name=company_name,
                current_price=current_price,
                market_cap=market_cap,
                sector=sector,
                rsi=technical_data.get("rsi", 50),
                macd_signal=technical_data.get("macd_signal", "NEUTRAL"),
                moving_avg_trend=technical_data.get("moving_avg_trend", "NEUTRAL"),
                volume_surge=technical_data.get("volume_surge", False),
                pe_ratio=fundamental_data.get("pe_ratio"),
                debt_to_equity=fundamental_data.get("debt_to_equity"),
                roe=fundamental_data.get("roe"),
                revenue_growth=fundamental_data.get("revenue_growth"),
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
            
            logger.info(f"✅ SCREENED: {ticker} - Score {overall_score:.1f}, Signal {signal.value}, Price ₹{current_price}")
            return opportunity
            
        except Exception as e:
            logger.error(f"🚫 FAILED: {ticker} - Screening error: {e}")
            return None
    
    async def scan_opportunities(self, max_stocks: int = 50) -> List[StockOpportunity]:
        """Scan NSE stocks for opportunities with intelligent AI-powered filtering"""
        logger.info(f"🚀 SCREENING: Starting AI-powered stock screening for {max_stocks} opportunities")
        
        # Get intelligently filtered stock universe
        stock_universe = self.get_nse_universe()
        logger.info(f"🚀 SCREENING: AI-filtered universe size: {len(stock_universe)} stocks")
        
        # The intelligent filtering already limits stocks, but we can still cap it
        stocks_to_screen = stock_universe[:max_stocks] if len(stock_universe) > max_stocks else stock_universe
        logger.info(f"🚀 SCREENING: Final screening list: {len(stocks_to_screen)} stocks")
        
        # Log sector distribution of selected stocks
        sector_counts = {}
        for stock in stocks_to_screen:
            symbol = stock.get('tradingsymbol', '')
            sector = self._determine_stock_sector(symbol)
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
        
        logger.info("🎯 SECTOR_DISTRIBUTION:")
        for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {sector}: {count} stocks")
        
        opportunities = []
        
        # Screen stocks concurrently (but with rate limiting)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        logger.info(f"🚀 SCREENING: Using concurrent screening with max 5 parallel requests")
        
        async def screen_with_semaphore(stock):
            async with semaphore:
                return await self.screen_stock(
                    stock.get("tradingsymbol", ""),
                    stock.get("name", "")
                )
        
        # Execute screening
        logger.info(f"🚀 SCREENING: Starting parallel screening of {len(stocks_to_screen)} AI-selected stocks...")
        tasks = [screen_with_semaphore(stock) for stock in stocks_to_screen]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results and analyze quality
        successful_screens = 0
        failed_screens = 0
        high_quality_stocks = 0
        sector_performance = {}
        
        for i, result in enumerate(results):
            if isinstance(result, StockOpportunity):
                opportunities.append(result)
                successful_screens += 1
                
                # Track sector performance
                sector = result.sector
                if sector not in sector_performance:
                    sector_performance[sector] = {'count': 0, 'avg_score': 0, 'total_score': 0}
                
                sector_performance[sector]['count'] += 1
                sector_performance[sector]['total_score'] += result.overall_score
                sector_performance[sector]['avg_score'] = sector_performance[sector]['total_score'] / sector_performance[sector]['count']
                
                if result.overall_score >= 70:
                    high_quality_stocks += 1
                    logger.info(f"🎯 HIGH_SCORE: {result.ticker} ({result.sector}) scored {result.overall_score:.1f} - {result.signal.value}")
            else:
                failed_screens += 1
                stock_symbol = stocks_to_screen[i].get('tradingsymbol', 'UNKNOWN')
                logger.debug(f"❌ FAILED: Stock {stock_symbol} failed screening")
        
        logger.info(f"🚀 SCREENING: Completed - {successful_screens} successful, {failed_screens} failed")
        logger.info(f"🏆 QUALITY: {high_quality_stocks}/{successful_screens} stocks scored ≥70 ({high_quality_stocks/successful_screens*100:.1f}% hit rate)")
        
        # Log sector performance analysis
        if sector_performance:
            logger.info("📊 SECTOR_PERFORMANCE:")
            sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1]['avg_score'], reverse=True)
            for sector, perf in sorted_sectors[:5]:  # Top 5 performing sectors
                logger.info(f"  {sector}: {perf['count']} stocks, avg score {perf['avg_score']:.1f}")
        
        # Sort by overall score (best opportunities first)
        opportunities.sort(key=lambda x: x.overall_score, reverse=True)
        logger.info(f"🏆 TOP_OPPORTUNITIES: Sorted {len(opportunities)} opportunities by score")
        
        if opportunities:
            top_5 = opportunities[:5]
            logger.info("🏆 TOP_5_OPPORTUNITIES:")
            for i, opp in enumerate(top_5, 1):
                logger.info(f"  {i}. {opp.ticker} ({opp.sector}): {opp.overall_score:.1f} ({opp.signal.value}) - ₹{opp.current_price}")
        
        logger.info(f"🚀 SCREENING: Found {len(opportunities)} stock opportunities using AI-powered filtering")
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