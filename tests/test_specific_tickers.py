#!/usr/bin/env python
"""
End-to-end test for specific tickers (SWSOLAR and IDFCFIRSTB) using the ZerodhaAdapter.
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

# Define the specific tickers to test
TEST_TICKERS = ["SWSOLAR", "IDFCFIRSTB"]

def test_ticker(ticker):
    """Test a specific ticker with the ZerodhaAdapter"""
    logger.info(f"\n\n{'='*50}\nTesting ticker: {ticker}\n{'='*50}")
    
    # Create a fresh adapter instance
    adapter = ZerodhaAdapter()
    
    # Clear any existing cache for this ticker to ensure fresh data
    cache_file = Path(f"cache/fundamentals/{ticker}_fundamentals_consolidated.json")
    if cache_file.exists():
        logger.info(f"Removing existing cache file: {cache_file}")
        cache_file.unlink()
    
    # Fetch fresh data
    try:
        logger.info(f"Fetching fundamentals for {ticker}...")
        fundamentals = adapter.get_fundamentals(ticker)
        
        if not fundamentals:
            logger.error(f"No fundamentals data returned for {ticker}")
            return {"ticker": ticker, "status": "error", "message": "No data returned"}
            
        if "error" in fundamentals:
            logger.error(f"Error fetching fundamentals for {ticker}: {fundamentals['error']}")
            return {"ticker": ticker, "status": "error", "message": fundamentals["error"]}
        
        # Check critical fields
        critical_fields = ["market_cap", "book_value_per_share", "earnings_per_share"]
        missing_fields = [field for field in critical_fields if field not in fundamentals or fundamentals.get(field) is None]
        
        if missing_fields:
            logger.warning(f"Missing critical fields for {ticker}: {missing_fields}")
            status = "incomplete"
        else:
            logger.info(f"All critical fields found for {ticker}")
            status = "success"
        
        # Log detailed information about key fields
        key_fields = {
            "market_cap": fundamentals.get("market_cap"),
            "price": fundamentals.get("price"),
            "pe_ratio": fundamentals.get("pe_ratio"),
            "book_value_per_share": fundamentals.get("book_value_per_share"),
            "earnings_per_share": fundamentals.get("earnings_per_share"),
            "roe": fundamentals.get("roe"),
            "dividend_yield": fundamentals.get("dividend_yield")
        }
        
        logger.info("Key financial metrics:")
        for field, value in key_fields.items():
            logger.info(f"  {field}: {value}")
        
        # Log all available ratios for debugging
        logger.info("\nAll available ratios:")
        for name, value in fundamentals.get("ratios", {}).items():
            logger.info(f"  {name}: {value}")
        
        return {
            "ticker": ticker,
            "status": status,
            "missing_fields": missing_fields if missing_fields else [],
            "metrics": key_fields
        }
        
    except Exception as e:
        logger.error(f"Exception testing {ticker}: {e}")
        return {"ticker": ticker, "status": "exception", "message": str(e)}

def main():
    """Run tests for the specified tickers"""
    results = []
    
    for ticker in TEST_TICKERS:
        result = test_ticker(ticker)
        results.append(result)
        
        # Be nice to the website - add a small delay between requests
        if ticker != TEST_TICKERS[-1]:  # Don't delay after the last ticker
            time.sleep(2)
    
    # Print summary
    logger.info("\n\n=== SUMMARY ===")
    for result in results:
        ticker = result["ticker"]
        status = result["status"]
        
        if status == "success":
            logger.info(f"{ticker}: SUCCESS - All critical fields found")
        elif status == "incomplete":
            logger.warning(f"{ticker}: INCOMPLETE - Missing fields: {result['missing_fields']}")
        else:
            logger.error(f"{ticker}: {status.upper()} - {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main() 