#!/usr/bin/env python
"""
Test script for validating screener.in scraping functionality in the ZerodhaAdapter.
This focuses on the specific scraping issues like missing EPS and market cap.
"""
import sys
import requests
from bs4 import BeautifulSoup
from loguru import logger
import json
from pathlib import Path
import re
import time

# Set up logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Define test tickers - including ones that had issues
TEST_TICKERS = ["TATASTEEL", "RELIANCE", "HDFCBANK", "INFY"]

def _parse_number(value_text: str) -> float | None:
    """Convert Screener number text to float.
    Handles crores (Cr.), percentages, and keeps decimals."""
    if not value_text:
        return None
    value_text = value_text.strip()
    # Check for percentage before removing it, to apply division later
    is_percentage = '%' in value_text
    
    # Remove currency symbols, commas, and the percentage sign for initial cleaning
    # Keep the decimal point for float conversion
    cleaned_text = value_text.replace('₹', '').replace(',', '').replace('%', '')
    
    # Handle 'Cr.' or 'Cr' for crores
    crore_multiplier = 1.0
    if "Cr." in cleaned_text:
        cleaned_text = cleaned_text.replace('Cr.', '').strip()
        crore_multiplier = 1e7
    elif "Cr" in cleaned_text: # Handle case where only "Cr" is present
        cleaned_text = cleaned_text.replace('Cr', '').strip()
        crore_multiplier = 1e7
        
    # Remove percentage sign after checking for it, before float conversion
    cleaned_text = cleaned_text.replace('%', '').strip()

    if not cleaned_text or cleaned_text == '--' or cleaned_text == '-': # Handle empty or placeholder strings
        return None
        
    try:
        num = float(cleaned_text)
        num *= crore_multiplier
        if is_percentage: # Apply percentage division if '%' was present
            num /= 100.0
        return num
    except ValueError:
        logger.warning(f"Could not parse number: '{value_text}' (cleaned: '{cleaned_text}')")
        return None

def test_scraper(ticker: str):
    """Test the screener.in scraper logic for a specific ticker"""
    url = f"https://www.screener.in/company/{ticker}/"
    
    logger.info(f"Testing scraper with ticker: {ticker}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=20)
    
    logger.info(f"Response status: {response.status_code}")
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch data: HTTP {response.status_code}")
        return {"ticker": ticker, "error": f"HTTP {response.status_code}"}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    fundamentals_data = {"ticker": ticker}
    
    # Test 1: Extract Market Cap and other top ratios
    logger.info("Test 1: Extracting top ratios (Market Cap, etc.)")
    top_ratios = {}
    
    # Find market cap element using case-insensitive search
    market_cap_name_span = soup.find(lambda tag: 
                                    tag.name == "span" and 
                                    tag.has_attr('class') and 
                                    'name' in tag['class'] and 
                                    "market cap" in tag.get_text(strip=True).lower())

    if market_cap_name_span:
        logger.info(f"Found market cap span: {market_cap_name_span.text}")
        parent_li = market_cap_name_span.find_parent("li")
        if parent_li:
            ratios_ul = parent_li.find_parent("ul")
            if ratios_ul:
                logger.info(f"Found ratios UL.")
                for item_li in ratios_ul.find_all("li", recursive=False):
                    name_s = item_li.find('span', class_='name')
                    value_s = item_li.find('span', class_='number')
                    if name_s and value_s:
                        name = name_s.text.strip().replace(":","").replace("+","").strip()
                        value_text = value_s.text.strip()
                        parsed_val = _parse_number(value_text)
                        if parsed_val is not None:
                            top_ratios[name] = parsed_val
                        else:
                            top_ratios[name] = value_text # Store original if parsing failed
                            logger.debug(f"Storing original string for ratio '{name}': '{value_text}'")
            else:
                logger.warning(f"Found 'Market Cap' span but could not find parent UL.")
        else:
             logger.warning(f"Found 'Market Cap' span but could not find parent LI.")
    else:
        logger.warning(f"Could not find 'Market Cap' span to anchor ratio search.")
    
    fundamentals_data["ratios"] = top_ratios
    
    # Test 2: Extract EPS from quarterly results
    logger.info("Test 2: Extracting EPS from quarterly results")
    
    # Try different section IDs for quarterly results
    quarters_section_ids = ["quarters", "quarterly-results"]
    eps_data = {}
    
    for section_id in quarters_section_ids:
        section = soup.find("section", id=section_id)
        if not section:
            logger.info(f"Section '{section_id}' not found.")
            continue
            
        logger.info(f"Found section '{section_id}'")
        table = section.find("table", class_="data-table")
        if not table:
            logger.info(f"Data table not found in section '{section_id}'.")
            continue
            
        thead = table.find("thead")
        if not thead:
            logger.info(f"Thead not found in table for {section_id}")
            continue
            
        header_elements = thead.select("tr th")
        if len(header_elements) <= 1:
            logger.info(f"Not enough headers in table for section '{section_id}'")
            continue
            
        headers_text = [th.text.strip() for th in header_elements][1:]
        if not headers_text:
            logger.info(f"No data column headers found in table for section '{section_id}'")
            continue
            
        logger.info(f"Headers: {headers_text}")
        
        # Default to the LAST column (most recent) rather than the first
        col_idx_to_extract = len(headers_text) - 1
        logger.info(f"Using column index {col_idx_to_extract}: '{headers_text[col_idx_to_extract]}'")
        
        tbody = table.find("tbody")
        if not tbody:
            logger.info(f"Tbody not found for {section_id}")
            continue
            
        # Look for EPS row with multiple possible name variations
        eps_row_names = ["EPS (Rs)", "EPS in Rs", "EPS", "EPS Reported"]
        
        for row in tbody.select("tr"):
            cells = row.find_all("td")
            if not cells or len(cells) <= (col_idx_to_extract + 1):
                continue
                
            row_name_cell_text = cells[0].text.strip().replace(":", "").replace("+", "").strip()
            
            for eps_row_name in eps_row_names:
                if eps_row_name.lower() in row_name_cell_text.lower():
                    value_text_from_cell = cells[col_idx_to_extract + 1].text.strip()
                    parsed_val = _parse_number(value_text_from_cell)
                    
                    if parsed_val is not None:
                        eps_data["earnings_per_share"] = parsed_val
                    else:
                        eps_data["earnings_per_share"] = value_text_from_cell
                        
                    logger.info(f"Found EPS row: '{row_name_cell_text}' = '{value_text_from_cell}' (parsed: {parsed_val})")
                    break
    
    # Test 3: Extract other important fields
    logger.info("Test 3: Extracting other important fields like Book Value, PE, etc.")
    
    # Map from Screener field names to our field names
    field_map = {
        "Market Cap": "market_cap", 
        "Current Price": "price", 
        "High / Low": "high_low_52_week", 
        "Stock P/E": "pe_ratio", 
        "Book Value": "book_value_per_share", 
        "Dividend Yield": "dividend_yield", 
        "ROCE": "roce", 
        "ROE": "roe", 
        "Face Value": "face_value", 
        "Debt to equity": "debt_to_equity",
        "EPS": "earnings_per_share_ttm"
    }
    
    mapped_fields = {}
    for screener_name, our_name in field_map.items():
        found_val = top_ratios.get(screener_name)
        
        # Attempt case-insensitive match if exact fails
        if found_val is None: 
            for r_name_key, r_val_val in top_ratios.items():
                if r_name_key.lower() == screener_name.lower():
                    found_val = r_val_val
                    logger.info(f"Mapped '{screener_name}' to '{r_name_key}' (case-insensitive)")
                    break
        
        # Attempt match without spaces if still not found
        if found_val is None and screener_name.replace(" ", "") in top_ratios:
            found_val = top_ratios[screener_name.replace(" ", "")]
            logger.info(f"Mapped '{screener_name}' by removing spaces")

        if found_val is not None:
            mapped_fields[our_name] = found_val
            logger.info(f"Mapped '{screener_name}' -> '{our_name}': {found_val}")
    
    # Combine all data and check for missing critical fields
    all_data = {**fundamentals_data, **eps_data, **mapped_fields}
    
    # Check critical fields
    critical_fields = ["market_cap", "book_value_per_share", "earnings_per_share"]
    missing_fields = [field for field in critical_fields if field not in all_data or all_data.get(field) is None]
    
    if missing_fields:
        logger.warning(f"Missing critical fields: {missing_fields}")
    else:
        logger.info("All critical fields were found!")
    
    # Print final results
    logger.info("\n=== RESULTS for {ticker} ===")
    for k, v in all_data.items():
        logger.info(f"{k}: {v}")
    
    return all_data

def main():
    """Run the test for multiple tickers"""
    results = []
    
    for ticker in TEST_TICKERS:
        try:
            logger.info(f"\n\n{'='*50}\nTesting ticker: {ticker}\n{'='*50}")
            result = test_scraper(ticker)
            results.append(result)
            
            # Be nice to the website - add a small delay between requests
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error testing ticker {ticker}: {e}")
            results.append({"ticker": ticker, "error": str(e)})
    
    # Summary
    logger.info("\n\n=== SUMMARY ===")
    for result in results:
        ticker = result.get("ticker", "Unknown")
        if "error" in result:
            logger.warning(f"{ticker}: Error - {result['error']}")
        elif "market_cap" not in result or result["market_cap"] is None:
            logger.warning(f"{ticker}: Missing market_cap")
        elif "book_value_per_share" not in result or result["book_value_per_share"] is None:
            logger.warning(f"{ticker}: Missing book_value_per_share")
        elif "earnings_per_share" not in result or result["earnings_per_share"] is None:
            logger.warning(f"{ticker}: Missing earnings_per_share")
        else:
            logger.info(f"{ticker}: All critical fields found")

if __name__ == "__main__":
    main() 