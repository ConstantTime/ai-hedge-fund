#!/usr/bin/env python
"""
Simple end-to-end test that fetches fundamental data for our test tickers
and generates a basic analysis summary.
"""
import sys
from loguru import logger
import json
from pathlib import Path
import time

# Import the ZerodhaAdapter class
from src.tools.zerodha_api import ZerodhaAdapter

# Set up logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Define the tickers to test
TEST_TICKERS = ["SWSOLAR", "IDFCFIRSTB"]

def analyze_fundamentals(ticker, fundamentals):
    """Generate a simple analysis summary based on the fundamentals data"""
    analysis = {}
    
    # Extract key metrics
    market_cap = fundamentals.get("market_cap")
    price = fundamentals.get("price")
    pe_ratio = fundamentals.get("pe_ratio")
    book_value = fundamentals.get("book_value_per_share")
    eps = fundamentals.get("earnings_per_share")
    roe = fundamentals.get("roe")
    
    # Basic valuations
    if price and book_value:
        pb_ratio = price / book_value
        analysis["price_to_book"] = pb_ratio
        
        if pb_ratio < 1:
            analysis["pb_assessment"] = "Below book value - potentially undervalued"
        elif pb_ratio < 3:
            analysis["pb_assessment"] = "Reasonable price to book ratio"
        else:
            analysis["pb_assessment"] = "High price to book ratio - potentially expensive"
    
    if pe_ratio:
        analysis["pe_ratio"] = pe_ratio
        
        if pe_ratio < 15:
            analysis["pe_assessment"] = "Below market average - potentially undervalued"
        elif pe_ratio < 25:
            analysis["pe_assessment"] = "Around market average - fairly valued"
        else:
            analysis["pe_assessment"] = "Above market average - potentially expensive"
    
    if eps:
        analysis["eps"] = eps
        if eps <= 0:
            analysis["eps_assessment"] = "Negative earnings - company is not profitable"
        else:
            analysis["eps_assessment"] = "Positive earnings"
    
    if roe:
        analysis["roe"] = roe
        if roe < 10:
            analysis["roe_assessment"] = "Below average return on equity"
        elif roe < 15:
            analysis["roe_assessment"] = "Average return on equity"
        else:
            analysis["roe_assessment"] = "Above average return on equity"
    
    # Overall assessment
    strengths = []
    weaknesses = []
    
    if pe_ratio and pe_ratio < 15:
        strengths.append("Low P/E ratio")
    elif pe_ratio and pe_ratio > 25:
        weaknesses.append("High P/E ratio")
        
    if pb_ratio and pb_ratio < 1.5:
        strengths.append("Low P/B ratio")
    elif pb_ratio and pb_ratio > 3:
        weaknesses.append("High P/B ratio")
        
    if eps and eps > 0:
        strengths.append("Positive earnings")
    elif eps and eps <= 0:
        weaknesses.append("Negative earnings")
        
    if roe and roe > 15:
        strengths.append("Strong ROE")
    elif roe and roe < 10:
        weaknesses.append("Weak ROE")
    
    analysis["strengths"] = strengths
    analysis["weaknesses"] = weaknesses
    
    if len(strengths) > len(weaknesses):
        analysis["overall_assessment"] = "Generally positive outlook"
    elif len(strengths) < len(weaknesses):
        analysis["overall_assessment"] = "Generally negative outlook"
    else:
        analysis["overall_assessment"] = "Mixed outlook"
    
    return analysis

def main():
    """Run analysis for the test tickers"""
    adapter = ZerodhaAdapter()
    results = {}
    
    for ticker in TEST_TICKERS:
        logger.info(f"\n\n{'='*50}\nAnalyzing {ticker}\n{'='*50}")
        
        try:
            # Clear cache to ensure fresh data
            cache_file = Path(f"cache/fundamentals/{ticker}_fundamentals_consolidated.json")
            if cache_file.exists():
                logger.info(f"Removing existing cache file: {cache_file}")
                cache_file.unlink()
            
            # Fetch fresh data
            logger.info(f"Fetching fundamentals for {ticker}...")
            fundamentals = adapter.get_fundamentals(ticker)
            
            if not fundamentals:
                logger.error(f"No fundamentals data returned for {ticker}")
                continue
                
            if "error" in fundamentals:
                logger.error(f"Error fetching fundamentals for {ticker}: {fundamentals['error']}")
                continue
            
            # Display key metrics
            logger.info("Key Financial Metrics:")
            key_metrics = {
                "Market Cap": fundamentals.get("market_cap"),
                "Current Price": fundamentals.get("price"),
                "P/E Ratio": fundamentals.get("pe_ratio"),
                "Book Value Per Share": fundamentals.get("book_value_per_share"),
                "Earnings Per Share": fundamentals.get("earnings_per_share"),
                "ROE": fundamentals.get("roe"),
                "Dividend Yield": fundamentals.get("dividend_yield")
            }
            
            for name, value in key_metrics.items():
                logger.info(f"  {name}: {value}")
            
            # Generate analysis
            logger.info("\nAnalysis:")
            analysis = analyze_fundamentals(ticker, fundamentals)
            
            if "price_to_book" in analysis:
                logger.info(f"  Price/Book Ratio: {analysis['price_to_book']:.2f} - {analysis['pb_assessment']}")
                
            if "pe_ratio" in analysis:
                logger.info(f"  P/E Assessment: {analysis['pe_assessment']}")
                
            if "eps" in analysis:
                logger.info(f"  EPS Assessment: {analysis['eps_assessment']}")
                
            if "roe" in analysis:
                logger.info(f"  ROE Assessment: {analysis['roe_assessment']}")
            
            logger.info("\nStrengths:")
            for strength in analysis["strengths"]:
                logger.info(f"  + {strength}")
                
            logger.info("\nWeaknesses:")
            for weakness in analysis["weaknesses"]:
                logger.info(f"  - {weakness}")
            
            logger.info(f"\nOverall Assessment: {analysis['overall_assessment']}")
            
            # Store results
            results[ticker] = {
                "fundamentals": fundamentals,
                "analysis": analysis
            }
            
            # Be nice to the website - add a delay between requests
            if ticker != TEST_TICKERS[-1]:
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
    
    # Save results to file
    try:
        output_file = Path("analysis_results.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"\nAnalysis results saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")

if __name__ == "__main__":
    main() 