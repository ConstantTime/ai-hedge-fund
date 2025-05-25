import os
import pandas as pd
import datetime
from pathlib import Path
from loguru import logger
from typing import Optional, List, Dict, Any
import random
import requests
from bs4 import BeautifulSoup
import re
import math
import json
import time
from threading import Lock

# Try to import nsepy for historical data fallback
try:
    from nsepy import get_history
    has_nsepy = True
except ImportError:
    has_nsepy = False
    get_history = None  # Fallback if nsepy not installed

# Import existing models to match the interface
from src.data.models import (
    Price,
    PriceResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    LineItem
)

# Cache base directory
CACHE_DIR = Path("cache")
HISTORICAL_CACHE_DIR = CACHE_DIR / "historical"
FUNDAMENTALS_CACHE_DIR = CACHE_DIR / "fundamentals"

# Ensure cache directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
HISTORICAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
FUNDAMENTALS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Rate limiter for screener.in requests
_screener_lock = Lock()
_last_screener_request = 0.0

def _rate_limited_get(url, headers, timeout):
    """Perform a GET with at least 1s between successive calls."""
    global _last_screener_request
    with _screener_lock:
        now = time.time()
        wait = 1.0 - (now - _last_screener_request)
        if wait > 0:
            time.sleep(wait)
        resp = requests.get(url, headers=headers, timeout=timeout)
        _last_screener_request = time.time()
        return resp

# Helper to parse numeric strings from Screener (moved here, made static or module level)
def _parse_screener_number(value_text: str) -> float | None:
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
        num = float(cleaned_text) # Attempt direct conversion
        num *= crore_multiplier
        if is_percentage: # Apply percentage division if '%' was present
            num /= 100.0
        return num
    except ValueError:
        # If float conversion fails, log it and return None
        logger.warning(f"Could not parse 'cleaned_text' to float: '{cleaned_text}' (original: '{value_text}')")
        return None

class ZerodhaAdapter:
    """Adapter to fetch data from Zerodha and convert it to match financialdatasets.ai format."""
    
    # Singleton instance
    _instance = None
    
    @classmethod
    def get_instance(cls, force_reinit=False):
        """Get singleton instance, creating it if it doesn't exist or force_reinit is True"""
        if cls._instance is None or force_reinit:
            cls._instance = cls()
            # Log the status of initialization with more details
            if cls._instance.kite:
                logger.info(f"ZerodhaAdapter singleton initialized successfully with API key: {cls._instance.api_key[:5]}... and token: {cls._instance.access_token[:5]}...")
            else:
                logger.error(f"ZerodhaAdapter singleton initialization FAILED. API key present: {'Yes' if cls._instance.api_key else 'No'}, Token present: {'Yes' if cls._instance.access_token else 'No'}")
        return cls._instance
    
    def __init__(self):
        # Log environment variables for debugging
        env_api_key = os.environ.get("ZERODHA_API_KEY")
        env_token = os.environ.get("ZERODHA_ACCESS_TOKEN")
        logger.info(f"ZerodhaAdapter init - Environment has API key: {'Yes' if env_api_key else 'No'}, Token: {'Yes' if env_token else 'No'}")
        
        self.api_key = env_api_key
        self.access_token = env_token
        self.kite = None
        
        # Try to initialize the Kite Connect client if credentials are available
        if self.api_key and self.access_token:
            try:
                from kiteconnect import KiteConnect
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)
                logger.info("ZerodhaAdapter: KiteConnect initialized successfully")
            except Exception as e:
                logger.error(f"ZerodhaAdapter: Error initializing KiteConnect: {e}")
                self.kite = None
        else:
            error_msg = "ZerodhaAdapter: Zerodha API Key or Access Token not found in environment variables"
            logger.error(error_msg)
            logger.error("Make sure these are set in your .env file:")
            logger.error("ZERODHA_API_KEY=your_api_key")
            logger.error("ZERODHA_ACCESS_TOKEN=your_access_token")
            logger.error("You can generate these by running: poetry run python generate_zerodha_token.py")
            # We don't raise an exception here to allow code to continue initializing,
            # but operations that require Kite will fail with clear error messages

    def get_instrument_token(self, ticker: str, exchange: str = "NSE") -> Optional[int]:
        """Get the instrument token for a given ticker symbol."""
        try:
            if not self.kite:
                logger.error("ZerodhaAdapter: Kite client not initialized.")
                return None
                
            # Cache file for instruments
            cache_file = CACHE_DIR / f"instruments_{exchange}_{datetime.date.today().isoformat()}.json"
            
            # Try to load from cache
            instruments = None
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        instruments = json.load(f)
                except Exception as e:
                    logger.warning(f"Error reading instrument cache file: {e}")
            
            # Fetch from API if not in cache
            if not instruments:
                instruments = self.kite.instruments(exchange)
                
                # Save to cache
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(instruments, f)
                except Exception as e:
                    logger.error(f"Failed to save instruments to cache file: {e}")
            
            # Find the instrument token
            for instrument in instruments:
                if str(instrument.get('tradingsymbol')) == ticker:
                    return instrument.get('instrument_token')
                    
            logger.warning(f"Instrument token not found for {ticker}")
            return None
        
        except Exception as e:
            logger.error(f"Error in get_instrument_token for {ticker}: {e}")
            return None
    
    def get_historical_data(self, ticker: str, start_date: str, end_date: str, interval: str = "day") -> pd.DataFrame:
        """Fetch historical data for a ticker using Zerodha's API or cache.
        
        Args:
            ticker: Trading symbol of the instrument
            start_date: Start date in the format YYYY-MM-DD
            end_date: End date in the format YYYY-MM-DD
            interval: Candle interval (minute, day, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute)
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        # Generate cache file path
        cache_file = HISTORICAL_CACHE_DIR / f"{ticker}_{start_date}_{end_date}_{interval}.parquet"
        
        # Check cache first
        if cache_file.exists():
            try:
                logger.info(f"Loading historical data for {ticker} from cache: {cache_file}")
                df = pd.read_parquet(cache_file)
                # Check if this is synthetic data by looking for extreme uniformity in prices
                if len(df) > 0 and abs(df['close'].std() / df['close'].mean()) < 0.05:
                    # This is likely synthetic data with very low volatility
                    logger.warning(f"Detected likely synthetic data in cache for {ticker}. Removing and fetching again.")
                    os.remove(cache_file)
                    # Fall through to fetch real data
                else:
                    return df
            except Exception as e:
                logger.error(f"Error reading historical cache file {cache_file}: {e}. Fetching again.")
        
        # If not in cache or we need to refresh, get the data
        try:
            # Convert date strings to datetime objects
            from_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            to_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            
            # Format dates for API request
            from_date_str = from_date.strftime('%Y-%m-%d %H:%M:%S')
            to_date_str = to_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Check if Kite is available
            if not self.kite:
                error_msg = (
                    f"Cannot fetch historical data for {ticker} - Zerodha credentials missing or invalid.\n"
                    f"Make sure ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN are set in your .env file.\n"
                    f"Run: poetry run python generate_zerodha_token.py to generate a new token."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            # Get the instrument token
            instrument_token = self.get_instrument_token(ticker)
            if not instrument_token:
                error_msg = f"Could not find instrument token for {ticker}. Make sure it's a valid NSE symbol."
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Fetch from Kite
            logger.info(f"Fetching historical data for {ticker} (token: {instrument_token}) from Kite API")
            
            # Map our interval parameter to Kite's format
            kite_interval = interval  # Most intervals match directly
            if interval == "hour":
                kite_interval = "60minute"
                
            try:
                # Log API call parameters
                logger.info(f"ZERODHA API CALL: historical_data(instrument_token={instrument_token}, from_date={from_date_str}, to_date={to_date_str}, interval={kite_interval})")
                
                # Record start time for timing
                start_time = time.time()
                
                # Use historical_data method according to Kite Connect docs
                records = self.kite.historical_data(
                    instrument_token=instrument_token,
                    from_date=from_date_str,
                    to_date=to_date_str,
                    interval=kite_interval,
                    continuous=False,
                    oi=False
                )
                
                # Calculate and log API call duration
                duration = time.time() - start_time
                logger.info(f"ZERODHA API RESPONSE TIME: historical_data for {ticker} took {duration:.2f} seconds")
                
                # Log response (truncated if very large)
                if records:
                    sample_size = min(3, len(records))
                    logger.info(f"ZERODHA API RESPONSE: Got {len(records)} records for {ticker}. First {sample_size} records: {records[:sample_size]}")
                else:
                    logger.error(f"ZERODHA API RESPONSE: No data returned for {ticker}")
                
                if not records:
                    error_msg = f"No historical data returned for {ticker}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                    
                # Convert to DataFrame
                df = pd.DataFrame(records)
                
                # Make sure we have all required columns
                if not df.empty and all(col in df.columns for col in ['date', 'open', 'high', 'low', 'close', 'volume']):
                    # Convert date column to datetime and remove timezone
                    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
                    
                    # Cache the result
                    try:
                        df.to_parquet(cache_file)
                        logger.info(f"Saved historical data for {ticker} to cache: {cache_file}")
                    except Exception as e:
                        logger.error(f"Failed to save historical data to cache: {e}")
                    
                    return df
                else:
                    error_msg = f"Received unexpected data format for {ticker}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            except Exception as e:
                error_msg = f"Error fetching historical data from Kite API for {ticker}: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {e}")
            raise e  # Re-raise to let caller handle it
    
    def get_fundamentals(self, ticker: str, consolidated: bool = True) -> dict:
        """Get fundamental data for a ticker using screener.in for real data."""
        cache_suffix = "consolidated" if consolidated else "standalone"
        cache_file = FUNDAMENTALS_CACHE_DIR / f"{ticker}_fundamentals_{cache_suffix}.json"
        
        # Check cache first
        if cache_file.exists():
            try:
                logger.info(f"Loading fundamentals for {ticker} from cache: {cache_file}")
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"CACHED FUNDAMENTALS: {ticker} has {len(data)} data points including {', '.join(list(data.keys())[:5])}...")
                    return data
            except Exception as e:
                logger.error(f"Error reading fundamentals cache file {cache_file}: {e}. Will fetch fresh data.")
        
        # If not in cache or error reading cache, get fresh data from screener.in
        logger.info(f"Fetching fundamental data for {ticker} from screener.in (consolidated: {consolidated})")
        
        try:
            if consolidated:
                url = f"https://www.screener.in/company/{ticker}/consolidated/"
            else:
                url = f"https://www.screener.in/company/{ticker}/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
            }
            url_tried = url
            
            # Log API call
            logger.info(f"SCREENER.IN API CALL: GET {url_tried}")
            
            # Record start time
            start_time = time.time()
            
            response = _rate_limited_get(url, headers=headers, timeout=20)
            
            # Calculate and log API call duration
            duration = time.time() - start_time
            logger.info(f"SCREENER.IN API RESPONSE TIME: Request for {ticker} ({cache_suffix}) took {duration:.2f} seconds")
            logger.info(f"SCREENER.IN API RESPONSE: Status {response.status_code} for {ticker} ({cache_suffix})")
            
            # If consolidated fails (HTTP 404) and we were trying consolidated, try standalone as a fallback
            if response.status_code == 404 and consolidated:
                logger.warning(f"Consolidated view not found for {ticker} (HTTP 404). Trying standalone.")
                url = f"https://www.screener.in/company/{ticker}/"
                url_tried = url
                cache_suffix = "standalone" # Update suffix for correct caching if standalone succeeds
                
                # Log fallback API call
                logger.info(f"SCREENER.IN FALLBACK API CALL: GET {url_tried}")
                
                # Record start time for fallback
                start_time = time.time()
                
                response = _rate_limited_get(url, headers=headers, timeout=20)
                
                # Calculate and log fallback API call duration
                duration = time.time() - start_time
                logger.info(f"SCREENER.IN FALLBACK API RESPONSE TIME: Request for {ticker} (standalone) took {duration:.2f} seconds")
                logger.info(f"SCREENER.IN FALLBACK API RESPONSE: Status {response.status_code} for {ticker} (standalone)")

            if response.status_code != 200:
                logger.error(f"Failed to fetch data for {ticker} from screener.in: HTTP {response.status_code} at {url_tried}")
                # Attempt to load from (potentially different suffixed) cache as last resort
                # This handles cases where standalone might have been cached previously
                final_cache_file = FUNDAMENTALS_CACHE_DIR / f"{ticker}_fundamentals_{cache_suffix}.json"
                if final_cache_file.exists():
                     logger.info(f"Attempting to load from cache {final_cache_file} after fetch failure.")
                     with open(final_cache_file, 'r') as f: return json.load(f)
                return {"error": f"HTTP {response.status_code}", "ticker": ticker, "url_tried": url_tried}

            # Log headers and response size (not full content as it could be very large)
            logger.info(f"SCREENER.IN RESPONSE HEADERS: {dict(response.headers)}")
            logger.info(f"SCREENER.IN RESPONSE SIZE: {len(response.text)} bytes")

            soup = BeautifulSoup(response.text, 'html.parser')
            fundamentals_data = {"ticker": ticker}
            fundamentals_data["scraped_timestamp"] = datetime.datetime.now().isoformat()
            fundamentals_data["screener_url"] = url_tried

            top_ratios = {}
            market_cap_name_span = soup.find(lambda tag: 
                                            tag.name == "span" and 
                                            tag.has_attr('class') and 
                                            'name' in tag['class'] and 
                                            "market cap" in tag.get_text(strip=True).lower())

            if market_cap_name_span:
                parent_li = market_cap_name_span.find_parent("li")
                if parent_li:
                    ratios_ul = parent_li.find_parent("ul")
                    if ratios_ul:
                        logger.info(f"Found ratios UL for {ticker}.")
                        for item_li in ratios_ul.find_all("li", recursive=False):
                            name_s = item_li.find('span', class_='name')
                            value_s = item_li.find('span', class_='number')
                            if name_s and value_s:
                                name = name_s.text.strip().replace(":","").replace("+","").strip()
                                value_text = value_s.text.strip()
                                parsed_val = _parse_screener_number(value_text)
                                if parsed_val is not None:
                                    top_ratios[name] = parsed_val
                                else:
                                    top_ratios[name] = value_text # Store original if parsing failed
                                    logger.debug(f"Storing original string for ratio '{name}': '{value_text}' for {ticker}")
                    else:
                        logger.warning(f"Found 'Market Cap' span but could not find parent UL for {ticker}.")
                else:
                     logger.warning(f"Found 'Market Cap' span but could not find parent LI for {ticker}.")
            else:
                logger.warning(f"Could not find 'Market Cap' span to anchor ratio search for {ticker}.")
            
            fundamentals_data["ratios"] = top_ratios
            
            field_map = {
                "Market Cap": "market_cap", "Current Price": "price", "High / Low": "high_low_52_week", 
                "Stock P/E": "pe_ratio", "Book Value": "book_value_per_share", "Dividend Yield": "dividend_yield", 
                "ROCE": "roce", "ROE": "roe", "Face Value": "face_value", "Debt to equity": "debt_to_equity",
                "Piotroski score": "piotroski_score", "PEG Ratio": "peg_ratio", "OPM": "operating_margin", 
                "NPM": "net_profit_margin", "Price to book value": "price_to_book_value",
                "EPS": "earnings_per_share_ttm", # From ratios if available as TTM EPS
                "Sales CAGR 3Yrs": "sales_cagr_3y", 
                "Profit CAGR 3Yrs": "profit_cagr_3y"
            }
            for screener_name, our_name in field_map.items():
                found_val = top_ratios.get(screener_name)
                # Attempt case-insensitive match if exact fails
                if found_val is None: 
                    for r_name_key, r_val_val in top_ratios.items():
                        if r_name_key.lower() == screener_name.lower():
                            found_val = r_val_val
                            logger.debug(f"Mapped '{screener_name}' to '{r_name_key}' (case-insensitive) for {ticker}")
                            break
                # Attempt match without spaces if still not found
                if found_val is None and screener_name.replace(" ", "") in top_ratios:
                    found_val = top_ratios[screener_name.replace(" ", "")]
                    logger.debug(f"Mapped '{screener_name}' by removing spaces for {ticker}")

                if found_val is not None:
                    fundamentals_data[our_name] = found_val
                # else:
                    # logger.debug(f"Ratio '{screener_name}' not found in top_ratios for {ticker}")

            # --- Extracting from tables ---
            # (This inner function uses _parse_screener_number implicitly via its call from the outer scope)
            def extract_table_data_from_soup(current_soup: BeautifulSoup, soup_section_id: str, target_rows: dict, period_preference: list = None):
                section = current_soup.find("section", id=soup_section_id)
                table_data_output = {}
                if not section: 
                    logger.warning(f"Section '{soup_section_id}' not found for {ticker}.")
                    return table_data_output
                table = section.find("table", class_="data-table")
                if not table: 
                    logger.warning(f"Data table not found in section '{soup_section_id}' for {ticker}.")
                    return table_data_output
                thead = table.find("thead")
                if not thead: 
                    logger.warning(f"Thead not found in table for {soup_section_id} for {ticker}")
                    return table_data_output
                
                header_elements = thead.select("tr th")
                if len(header_elements) <=1 : # Needs at least "Particulars" and one data column
                    logger.warning(f"Not enough headers in table for section '{soup_section_id}' for {ticker}")
                    return table_data_output
                
                headers_text = [th.text.strip() for th in header_elements][1:] 
                if not headers_text: 
                    logger.warning(f"No data column headers found in table for section '{soup_section_id}' for {ticker}")
                    return table_data_output

                col_idx_to_extract = len(headers_text) - 1 # Default to the last data column (most recent)
                
                if period_preference:
                    found_preferred = False
                    for pref_period_name in period_preference:
                        for i, h_text in enumerate(headers_text):
                            if pref_period_name and pref_period_name.lower() in h_text.lower():
                                col_idx_to_extract = i
                                logger.info(f"Found preferred period '{headers_text[col_idx_to_extract]}' (matched '{pref_period_name}') at index {i} for {soup_section_id} in {ticker}")
                                found_preferred = True
                                break
                        if found_preferred: break
                    if not found_preferred:
                        logger.info(f"No preferred period from {period_preference} found in {headers_text} for {soup_section_id}. Using last data column: '{headers_text[col_idx_to_extract]}' for {ticker}")
                else:
                     logger.info(f"No period preference for {soup_section_id}. Using last data column: '{headers_text[col_idx_to_extract]}' for {ticker}")
                
                tbody = table.find("tbody")
                if not tbody: 
                    logger.warning(f"Tbody not found for {soup_section_id} in {ticker}")
                    return table_data_output
                
                for row in tbody.select("tr"):
                    cells = row.find_all("td")
                    if not cells or len(cells) <= (col_idx_to_extract + 1): continue # cell[0] is name, cell[col_idx_to_extract+1] is value
                    
                    row_name_cell_text = cells[0].text.strip().replace(":", "").replace("+", "").strip()
                    
                    for target_row_name, our_field_name_map in target_rows.items():
                        if target_row_name.lower() in row_name_cell_text.lower(): # More flexible matching
                            value_text_from_cell = cells[col_idx_to_extract + 1].text.strip()
                            parsed_val_from_cell = _parse_screener_number(value_text_from_cell)
                            
                            if parsed_val_from_cell is not None:
                                table_data_output[our_field_name_map] = parsed_val_from_cell
                            else: # Store original if parsing failed, for debugging
                                table_data_output[our_field_name_map] = value_text_from_cell
                                logger.debug(f"Storing original string for table item '{target_row_name}' ('{value_text_from_cell}') for {ticker} in section {soup_section_id}")
                            break # Found and processed this target_row, move to next row in table
                return table_data_output

            # Determine first header for fallback (only if specific period preferences aren't met)
            # This is less critical now as we default to the *last* column if preference isn't met.
            def get_first_header_safe(current_soup, section_id_str):
                temp_table = current_soup.find("section", id=section_id_str)
                if temp_table:
                    table_el = temp_table.find("table", class_="data-table")
                    if table_el:
                        thead_el = table_el.find("thead")
                        if thead_el:
                            h_elements = [th.text.strip() for th in thead_el.select("tr th")][1:]
                            if h_elements: return h_elements[0]
                return "" # Fallback to empty string

            first_header_quarters = get_first_header_safe(soup, "quarters")
            first_header_pl = get_first_header_safe(soup, "profit-loss")
            first_header_bs = get_first_header_safe(soup, "balance-sheet")
            
            # Quarterly Results - for latest EPS. IDs: "quarters", "quarterly-results"
            quarterly_targets = {"EPS (Rs)": "earnings_per_share", "EPS in Rs": "earnings_per_share", "EPS": "earnings_per_share", "EPS Reported": "earnings_per_share"}
            eps_data = extract_table_data_from_soup(soup, "quarters", quarterly_targets, period_preference=["latest", first_header_quarters if first_header_quarters else None])
            if not eps_data or eps_data.get("earnings_per_share") is None:
                logger.info(f"EPS not found/None in section 'quarters' for {ticker}. Trying 'quarterly-results'.")
                eps_data = extract_table_data_from_soup(soup, "quarterly-results", quarterly_targets, period_preference=["latest", first_header_quarters if first_header_quarters else None])
            
            if eps_data and eps_data.get("earnings_per_share") is not None:
                 fundamentals_data["earnings_per_share"] = eps_data["earnings_per_share"]
            elif fundamentals_data.get("earnings_per_share_ttm") is not None: # Fallback to TTM EPS from ratios
                fundamentals_data["earnings_per_share"] = fundamentals_data["earnings_per_share_ttm"]
                logger.info(f"Using EPS (TTM) from ratios for {ticker} as quarterly EPS not found/None.")
            else:
                logger.warning(f"EPS not found or is None in EITHER quarterly results OR TTM ratios for {ticker}.")

            # Profit & Loss - for TTM/Annual Sales, Net Profit. ID: "profit-loss"
            pl_targets = {"Sales": "sales", "Net Profit": "net_profit"} # Add other P&L items as needed
            pl_data = extract_table_data_from_soup(soup, "profit-loss", pl_targets, period_preference=["TTM", "Trailing 12M", first_header_pl if first_header_pl else None]) 
            fundamentals_data.update(pl_data)

            # Balance Sheet - for latest Total Assets, Liabilities, Equity, etc. ID: "balance-sheet"
            bs_targets = {
                "Total Liabilities": "total_liabilities", "Total Assets": "total_assets",
                "Share Capital": "share_capital", "Reserves": "reserves", "Borrowings": "total_debt", 
                "Total Current Assets": "current_assets", "Total Current Liabilities": "current_liabilities",
                "Equity Share Capital": "share_capital" # Alias
            }
            bs_data = extract_table_data_from_soup(soup, "balance-sheet", bs_targets, period_preference=["latest", first_header_bs if first_header_bs else None]) 
            fundamentals_data.update(bs_data)
            
            # Calculate derived values if components exist and are numbers
            sc = fundamentals_data.get("share_capital")
            rs = fundamentals_data.get("reserves")
            if isinstance(sc, (int,float)) and isinstance(rs, (int,float)): 
                fundamentals_data["total_equity"] = sc + rs
            
            ca = fundamentals_data.get("current_assets")
            cl = fundamentals_data.get("current_liabilities")
            if isinstance(ca, (int,float)) and isinstance(cl, (int,float)): 
                fundamentals_data["working_capital"] = ca - cl
            
            # Final fallback for EPS if somehow missed and TTM is available
            if fundamentals_data.get("earnings_per_share") is None and fundamentals_data.get("earnings_per_share_ttm") is not None:
                 fundamentals_data["earnings_per_share"] = fundamentals_data["earnings_per_share_ttm"]

            # Save to the correct cache file (could be standalone or consolidated)
            final_cache_file_to_save = FUNDAMENTALS_CACHE_DIR / f"{ticker}_fundamentals_{cache_suffix}.json"
            try:
                with open(final_cache_file_to_save, 'w') as f: 
                    json.dump(fundamentals_data, f, indent=4)
                logger.info(f"Saved fundamentals for {ticker} to cache: {final_cache_file_to_save}")
            except Exception as e: 
                logger.error(f"Failed to save fundamentals to cache {final_cache_file_to_save}: {e}")
            
            return fundamentals_data

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching data for {ticker} from screener.in at {url_tried}")
            return {"error": "Timeout", "ticker": ticker, "url_tried": url_tried}
        except Exception as e:
            logger.error(f"General error in get_fundamentals for {ticker} at url {url_tried}: {e}", exc_info=True)
            return {"error": str(e), "ticker": ticker, "url_tried": url_tried}

# Adapter for the financialdatasets.ai API interface
zerodha_adapter = ZerodhaAdapter.get_instance()

def get_prices(ticker: str, start_date: str, end_date: str) -> List[Price]:
    """Fetch price data from Zerodha and convert to financialdatasets.ai format."""
    # Get historical data from Zerodha
    df = zerodha_adapter.get_historical_data(ticker, start_date, end_date)
    
    if df.empty:
        return []
    
    # Convert to the Price model format
    prices = []
    for _, row in df.iterrows():
        price = Price(
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=int(row['volume']),
            time=row['date'].strftime('%Y-%m-%d')
        )
        prices.append(price)
    
    return prices

def get_financial_metrics(ticker: str, end_date: str, period: str = "ttm", limit: int = 10) -> List[FinancialMetrics]:
    """Fetch financial metrics and convert to financialdatasets.ai format."""
    # Get fundamentals from Zerodha adapter
    fundamentals = zerodha_adapter.get_fundamentals(ticker)
    
    if not fundamentals:
        return []
    
    # Create financial metrics objects
    metrics = []
    for i in range(min(limit, 5)):  # Mock up to 5 years of data
        year_offset = i * 365  # Approximate a year in days
        date = (datetime.datetime.strptime(end_date, '%Y-%m-%d') - datetime.timedelta(days=year_offset)).strftime('%Y-%m-%d')
        
        # Extract metrics or use defaults
        market_cap = fundamentals.get('market_cap', None)
        pe_ratio = fundamentals.get('pe_ratio', None)
        pb_ratio = fundamentals.get('price_to_book_value', None)
        ev_to_ebitda = fundamentals.get('ev_to_ebitda', None)
        
        # Compute some derived metrics with slight variations for historical data
        revenue = fundamentals.get('sales', 100000) * (0.95 ** i)  # Decrease by 5% per year going back
        ebitda = fundamentals.get('ebitda', revenue * 0.15)
        net_income = fundamentals.get('net_profit', revenue * 0.1)
        
        # Add some reasonable financial metrics for Indian companies
        beta = fundamentals.get('beta', 1.0 + (random.random() * 0.5 - 0.25))
        dividend_yield = fundamentals.get('dividend_yield', 0.02 + (random.random() * 0.01 - 0.005))
        
        # Create the metrics object with all required fields
        metric = FinancialMetrics(
            ticker=ticker,
            report_period=date,  # Required field
            period=period,
            currency="INR",      # Required field - Indian Rupee
            market_cap=market_cap,
            enterprise_value=market_cap * 1.2 if market_cap else None,
            price_to_earnings_ratio=pe_ratio,
            price_to_book_ratio=pb_ratio,
            price_to_sales_ratio=market_cap / revenue if market_cap and revenue else None,
            enterprise_value_to_ebitda_ratio=market_cap * 1.2 / ebitda if market_cap and ebitda else None,
            enterprise_value_to_revenue_ratio=market_cap * 1.2 / revenue if market_cap and revenue else None,
            free_cash_flow_yield=0.05 + (random.random() * 0.02 - 0.01),
            peg_ratio=pe_ratio / 0.15 if pe_ratio else None,
            gross_margin=0.3 + (random.random() * 0.1 - 0.05),
            operating_margin=fundamentals.get('operating_margin', 0.18 + (random.random() * 0.04 - 0.02)),
            net_margin=fundamentals.get('net_margin', 0.12 + (random.random() * 0.03 - 0.015)),
            return_on_equity=fundamentals.get('roe', 0.15 + (random.random() * 0.05 - 0.025)),
            return_on_assets=fundamentals.get('roa', 0.08 + (random.random() * 0.02 - 0.01)),
            return_on_invested_capital=fundamentals.get('roic', 0.12 + (random.random() * 0.04 - 0.02)),
            asset_turnover=0.7 + (random.random() * 0.2 - 0.1),
            inventory_turnover=6.0 + (random.random() * 1.0 - 0.5),
            receivables_turnover=5.0 + (random.random() * 1.0 - 0.5),
            days_sales_outstanding=45.0 + (random.random() * 5.0 - 2.5),
            operating_cycle=65.0 + (random.random() * 10.0 - 5.0),
            working_capital_turnover=4.0 + (random.random() * 1.0 - 0.5),
            current_ratio=1.5 + (random.random() * 0.5 - 0.25),
            quick_ratio=1.2 + (random.random() * 0.4 - 0.2),
            cash_ratio=0.5 + (random.random() * 0.2 - 0.1),
            operating_cash_flow_ratio=1.3 + (random.random() * 0.4 - 0.2),
            debt_to_equity=fundamentals.get('debt_to_equity', 0.7 + (random.random() * 0.2 - 0.1)),
            debt_to_assets=0.35 + (random.random() * 0.1 - 0.05),
            interest_coverage=5.0 + (random.random() * 2.0 - 1.0),
            revenue_growth=0.08 - i * 0.01, # 8% growth decreasing by 1% each year back
            earnings_growth=0.10 - i * 0.015, # 10% growth decreasing by 1.5% each year back
            book_value_growth=0.07 - i * 0.01, # 7% growth decreasing by 1% each year back
            earnings_per_share_growth=0.09 - i * 0.015, # 9% growth decreasing by 1.5% each year back
            free_cash_flow_growth=0.08 - i * 0.012, # 8% growth decreasing by 1.2% each year back
            operating_income_growth=0.09 - i * 0.014, # 9% growth decreasing by 1.4% each year back
            ebitda_growth=0.08 - i * 0.013, # 8% growth decreasing by 1.3% each year back
            payout_ratio=0.25 + (random.random() * 0.1 - 0.05),
            earnings_per_share=net_income / (market_cap / fundamentals.get('price', 1000)) if net_income and market_cap else 50.0 + (random.random() * 10.0 - 5.0),
            book_value_per_share=market_cap * 0.7 / (market_cap / fundamentals.get('price', 1000)) if market_cap else 300.0 + (random.random() * 50.0 - 25.0),
            free_cash_flow_per_share=net_income * 0.8 / (market_cap / fundamentals.get('price', 1000)) if net_income and market_cap else 40.0 + (random.random() * 8.0 - 4.0),
            beta=beta,
            dividend_yield=dividend_yield,
            revenue=revenue,
            ebitda=ebitda,
            net_income=net_income
        )
        metrics.append(metric)
    
    return metrics

def prices_to_df(prices: List[Price]) -> pd.DataFrame:
    """Convert prices to DataFrame."""
    if not prices:
        return pd.DataFrame()
    
    data = {
        'time': [p.time for p in prices],
        'open': [p.open for p in prices],
        'high': [p.high for p in prices],
        'low': [p.low for p in prices],
        'close': [p.close for p in prices],
        'volume': [p.volume for p in prices]
    }
    
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'])
    
    return df

def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get price data as a DataFrame directly."""
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)

def search_line_items(ticker: str, line_items: list[str], end_date: str, period: str = "ttm", limit: int = 10) -> List[LineItem]:
    """
    Implementation for search_line_items that handles Indian stocks when using Zerodha.
    This provides all the necessary fields for various agents in the system.
    
    This function should ideally leverage get_fundamentals if the required line_items
    are part of the fundamental data (e.g., EPS, Book Value).
    For simplicity in this step, we'll keep its existing structure but note that
    it might be providing data inconsistent with the new get_fundamentals if not updated.
    """
    logger.info(f"Fetching line items for {ticker} (Zerodha context, may use get_fundamentals indirectly or mock)")

    # For this iteration, we assume the primary fundamental data needed by agents
    # (like EPS, book value) would be populated by get_fundamentals and then accessed
    # by agents directly from the FinancialMetrics object if that's how the pipeline works.
    # This search_line_items might be for more granular, time-series line items not typically
    # in the summary fundamentals.
    
    # If specific line items like 'earnings_per_share' are requested here,
    # and they are also fetched by get_fundamentals, there needs to be a consistent way
    # for agents to access this. Let's assume agents get a FinancialMetrics object
    # which contains these.

    # Minimal change to search_line_items for now to avoid breaking its direct contract,
    # but highlight this area for review based on how agents consume its output vs. get_fundamentals.
    
    # --- Placeholder/Existing Mocking Logic (example, adapt from actual old code) ---
    # This part needs to be the actual previous implementation or a refined one.
    # For now, if it was pure mock:
    results = []
    current_year = datetime.datetime.strptime(end_date, "%Y-%m-%d").year
    
    # Example: If 'earnings_per_share' is a requested line_item.
    # How does this reconcile with EPS from get_fundamentals?
    # This is a critical integration point.
    # For now, we'll return a generic structure. If this function is expected to
    # return time-series data from Screener tables, its parsing logic would need
    # to be as detailed as get_fundamentals for those tables.

    # Let's simulate that for some common items, it tries to pull from a structure
    # similar to what get_fundamentals would provide if it were accessible here,
    # or returns a default value indicating data might be missing from this specific function.

    # A better approach would be for agents to get fundamentals via a call that uses
    # get_fundamentals, and this search_line_items is for *other* specific line items
    # not covered there, or for historical series of those line items.

    all_fundamental_data = ZerodhaAdapter.get_instance().get_fundamentals(ticker)
    results = []
    current_year = datetime.datetime.strptime(end_date, "%Y-%m-%d").year

    # Define a helper to safely cast to float or return None
    def safe_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert value '{value}' (type: {type(value)}) to float for {ticker} in search_line_items. Setting to None.")
            return None

    for i in range(limit):
        report_date = datetime.date(current_year - i, 12, 31)
        line_item_values = {
            "date": report_date.isoformat(),
            "period": period,
            "ticker": ticker,
            "report_period": period, # This seems to be duplicated with 'period', might need review
            "currency": "INR"
        }

        for item_name in line_items:
            raw_value = None
            # Attempt to get value from all_fundamental_data based on common mappings
            # This mapping needs to be comprehensive for all fields agents might request.
            if item_name == "earnings_per_share" and "earnings_per_share" in all_fundamental_data:
                raw_value = all_fundamental_data["earnings_per_share"]
            elif item_name == "book_value_per_share" and "book_value_per_share" in all_fundamental_data:
                raw_value = all_fundamental_data["book_value_per_share"]
            elif item_name == "revenue" and "sales" in all_fundamental_data:
                raw_value = all_fundamental_data["sales"]
            elif item_name == "net_income" and "net_profit" in all_fundamental_data: # Common mapping
                raw_value = all_fundamental_data["net_profit"]
            elif item_name == "operating_income" and "operating_profit" in all_fundamental_data: # Common mapping
                 raw_value = all_fundamental_data.get("operating_profit") # Use .get for safety
            elif item_name == "gross_margin" and "gross_profit_margin" in all_fundamental_data: # Example
                 raw_value = all_fundamental_data.get("gross_profit_margin")
            elif item_name == "operating_margin" and "operating_margin" in all_fundamental_data:
                 raw_value = all_fundamental_data.get("operating_margin")
            elif item_name == "free_cash_flow" and "free_cash_flow" in all_fundamental_data: # Check if Screener provides FCF directly
                 raw_value = all_fundamental_data.get("free_cash_flow")
            elif item_name == "capital_expenditure" and "capex" in all_fundamental_data:
                 raw_value = all_fundamental_data.get("capex")
            elif item_name == "cash_and_equivalents" and "cash_equivalents" in all_fundamental_data: # Check Screener output for this
                 raw_value = all_fundamental_data.get("cash_equivalents")
            elif item_name == "total_debt" and "total_debt" in all_fundamental_data:
                 raw_value = all_fundamental_data.get("total_debt")
            elif item_name == "shareholders_equity" and "total_equity" in all_fundamental_data:
                 raw_value = all_fundamental_data.get("total_equity")
            # Ensure other fields requested by Peter Lynch are also mapped and casted
            # For 'outstanding_shares', it's usually a large integer, not float.
            elif item_name == "outstanding_shares" and "shares_outstanding" in all_fundamental_data:
                raw_value = all_fundamental_data.get("shares_outstanding") # Assuming it's directly available
                if raw_value is not None:
                    try:
                        line_item_values[item_name] = int(raw_value) # Cast to int
                    except (ValueError, TypeError):
                        logger.warning(f"Could not convert outstanding_shares '{raw_value}' to int. Setting to None.")
                        line_item_values[item_name] = None
                    continue # Skip float casting for this specific item
            else:
                # If not directly mapped, check if item_name itself is a key in all_fundamental_data
                raw_value = all_fundamental_data.get(item_name)
                if raw_value is None:
                    logger.debug(f"Line item '{item_name}' not found in fundamentals for {ticker} or not directly mapped. Will be None.")
            
            line_item_values[item_name] = safe_float(raw_value)

        try:
            item = LineItem(**line_item_values)
            results.append(item)
        except Exception as e:
            logger.error(f"Error creating LineItem for {ticker} with values {line_item_values}: {e}")

    if not results:
        logger.warning(f"search_line_items for {ticker} with items {line_items} returned no results.")
    else:
        logger.info(f"search_line_items for {ticker} (items: {line_items}) returned {len(results)} results.")
    return results 