#!/usr/bin/env python
"""
Test script for verifying the LineItem validation fix.
"""
import sys
from loguru import logger
import datetime
from src.tools.zerodha_api import search_line_items
from src.data.models import LineItem

# Set up logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Define test tickers and line items
TEST_TICKERS = ["SWSOLAR", "IDFCFIRSTB"]
TEST_LINE_ITEMS = [
    "earnings_per_share", 
    "book_value_per_share", 
    "revenue", 
    "net_income", 
    "operating_income", 
    "return_on_invested_capital"
]

def main():
    """Test the LineItem validation fix with search_line_items function"""
    logger.info("Testing LineItem validation fix...")
    
    today = datetime.date.today()
    end_date = today.isoformat()
    
    for ticker in TEST_TICKERS:
        logger.info(f"\n\n{'='*50}\nTesting search_line_items for {ticker}\n{'='*50}")
        
        try:
            # Call search_line_items to test LineItem creation
            results = search_line_items(
                ticker=ticker,
                line_items=TEST_LINE_ITEMS,
                end_date=end_date,
                period="annual",
                limit=3
            )
            
            if not results:
                logger.warning(f"No results returned for {ticker}")
                continue
                
            # Verify that we got valid LineItem objects back
            logger.info(f"Received {len(results)} LineItem objects")
            
            # Check the first result to validate its contents
            first_item = results[0]
            logger.info(f"First LineItem object details:")
            logger.info(f"  ticker: {first_item.ticker}")
            logger.info(f"  report_period: {first_item.report_period}")
            logger.info(f"  period: {first_item.period}")
            logger.info(f"  currency: {first_item.currency}")
            
            # Check for presence of requested line items
            for item_name in TEST_LINE_ITEMS:
                if hasattr(first_item, item_name):
                    logger.info(f"  {item_name}: {getattr(first_item, item_name)}")
                else:
                    logger.warning(f"  {item_name} not found in LineItem")
                    
            logger.info(f"LineItem validation successful for {ticker}! ✓")
            
        except Exception as e:
            logger.error(f"Error testing search_line_items for {ticker}: {e}")
    
    logger.info("\nLineItem validation test completed")

if __name__ == "__main__":
    main() 