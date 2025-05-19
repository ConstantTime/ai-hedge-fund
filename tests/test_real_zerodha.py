#!/usr/bin/env python
"""
Test script for the real ZerodhaAdapter.get_fundamentals method
"""
import sys
from loguru import logger
import json
from pathlib import Path

# Import the ZerodhaAdapter class
from src.tools.zerodha_api import ZerodhaAdapter

# Set up logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Define test tickers
TEST_TICKERS = ["TATASTEEL", "RELIANCE", "HDFCBANK", "INFY"]

def main():
    # Create a ZerodhaAdapter instance
    adapter = ZerodhaAdapter()
    
    results = {}
    
    # Test each ticker
    for ticker in TEST_TICKERS:
        logger.info(f"\n\n{'='*50}\nTesting ZerodhaAdapter.get_fundamentals for {ticker}\n{'='*50}")
        
        try:
            # Call the get_fundamentals method
            fundamentals = adapter.get_fundamentals(ticker)
            
            # Check if we got any data
            if not fundamentals:
                logger.error(f"No fundamentals data returned for {ticker}")
                results[ticker] = {"status": "error", "message": "No data returned"}
                continue
                
            # Check for error
            if "error" in fundamentals:
                logger.error(f"Error fetching fundamentals for {ticker}: {fundamentals['error']}")
                results[ticker] = {"status": "error", "message": fundamentals["error"]}
                continue
                
            # Check critical fields
            critical_fields = ["market_cap", "book_value_per_share", "earnings_per_share"]
            missing_fields = [field for field in critical_fields if field not in fundamentals or fundamentals.get(field) is None]
            
            if missing_fields:
                logger.warning(f"Missing critical fields for {ticker}: {missing_fields}")
                results[ticker] = {"status": "incomplete", "missing_fields": missing_fields}
            else:
                logger.info(f"All critical fields found for {ticker}")
                results[ticker] = {"status": "success"}
                
            # Log key metrics
            logger.info(f"Market Cap: {fundamentals.get('market_cap')}")
            logger.info(f"Current Price: {fundamentals.get('price')}")
            logger.info(f"P/E Ratio: {fundamentals.get('pe_ratio')}")
            logger.info(f"Book Value: {fundamentals.get('book_value_per_share')}")
            logger.info(f"EPS: {fundamentals.get('earnings_per_share')}")
            logger.info(f"ROE: {fundamentals.get('roe')}")
            
        except Exception as e:
            logger.error(f"Exception testing {ticker}: {e}")
            results[ticker] = {"status": "exception", "message": str(e)}
    
    # Print summary
    logger.info("\n\n=== SUMMARY ===")
    for ticker, result in results.items():
        status = result["status"]
        if status == "success":
            logger.info(f"{ticker}: SUCCESS - All critical fields found")
        elif status == "incomplete":
            logger.warning(f"{ticker}: INCOMPLETE - Missing fields: {result['missing_fields']}")
        else:
            logger.error(f"{ticker}: {status.upper()} - {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main() 