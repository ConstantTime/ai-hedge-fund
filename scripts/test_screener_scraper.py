import requests
from bs4 import BeautifulSoup
import json
import datetime
from pathlib import Path
from loguru import logger
import re
import math

# Cache base directory
CACHE_DIR = Path("../cache") 
FUNDAMENTALS_CACHE_DIR = CACHE_DIR / "fundamentals"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
FUNDAMENTALS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Helper to parse numeric strings from Screener

def _parse_number(value_text: str) -> float | None:
    """Convert Screener number text to float.
    Handles crores (Cr.), percentages, and keeps decimals."""
    if not value_text:
        return None
    value_text = value_text.strip()
    percent = value_text.endswith('%') or '%' in value_text
    # Remove rupee symbol and commas
    clean = value_text.replace('₹', '').replace(',', '').replace('%', '').strip()
    crore_multiplier = 1.0
    if 'Cr.' in clean or 'Cr' in clean:
        clean = clean.replace('Cr.', '').replace('Cr', '')
        crore_multiplier = 1e7
    try:
        num = float(clean)
        num *= crore_multiplier
        if percent:
            num /= 100.0
        return num
    except ValueError:
        return None

def get_screener_data(ticker: str, use_cache: bool = True) -> dict:
    cache_suffix = "consolidated" 
    cache_file = FUNDAMENTALS_CACHE_DIR / f"{ticker}_fundamentals_{cache_suffix}_test.json"

    if use_cache and cache_file.exists():
        try:
            logger.info(f"Loading fundamentals for {ticker} from test cache: {cache_file}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading fundamentals cache file {cache_file}: {e}. Will fetch fresh data.")

    logger.info(f"Fetching fundamental data for {ticker} from screener.in")
    fundamentals_data = {"ticker": ticker}
    url_tried = "N/A"

    try:
        url = f"https://www.screener.in/company/{ticker}/consolidated/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
        }
        url_tried = url
        response = requests.get(url, headers=headers, timeout=20)
        logger.info(f"Screener.in response status for {ticker} (consolidated): {response.status_code}")
        
        if response.status_code == 404:
            logger.warning(f"Consolidated view not found for {ticker} (HTTP 404). Trying standalone.")
            url = f"https://www.screener.in/company/{ticker}/"
            url_tried = url
            response = requests.get(url, headers=headers, timeout=20)
            logger.info(f"Screener.in response status for {ticker} (standalone): {response.status_code}")

        if response.status_code != 200:
            logger.error(f"Failed to fetch data for {ticker} from screener.in: HTTP {response.status_code} at {url_tried}")
            return {"error": f"HTTP {response.status_code}", "ticker": ticker, "url_tried": url_tried}

        soup = BeautifulSoup(response.text, 'html.parser')
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
                            name = name_s.text.strip().replace(":","")
                            value_text = value_s.text.strip()
                            parsed_val = _parse_number(value_text)
                            if parsed_val is not None:
                                top_ratios[name] = parsed_val
                            else:
                                top_ratios[name] = value_text
                else:
                    logger.warning(f"Found 'Market Cap' but could not find parent UL for {ticker}.")
            else:
                 logger.warning(f"Found 'Market Cap' but could not find parent LI for {ticker}.")
        else:
            logger.warning(f"Could not find 'Market Cap' span to anchor ratio search for {ticker}.")
            company_info_div = soup.find("div", class_="company-info")
            if company_info_div:
                logger.debug(f"HTML snippet from company-info for {ticker}: {str(company_info_div)[:500]}")
            else:
                top_section_div = soup.find("div", id="top")
                if top_section_div:
                    logger.debug(f"HTML snippet from #top for {ticker}: {str(top_section_div)[:500]}")

        fundamentals_data["ratios"] = top_ratios
        field_map = {
            "Market Cap": "market_cap", "Current Price": "price", "High / Low": "high_low_52_week", 
            "Stock P/E": "pe_ratio", "Book Value": "book_value_per_share", "Dividend Yield": "dividend_yield", 
            "ROCE": "roce", "ROE": "roe", "Face Value": "face_value", "Debt to equity": "debt_to_equity",
            "Piotroski score": "piotroski_score", "PEG Ratio": "peg_ratio", "OPM": "operating_margin", 
            "NPM": "net_profit_margin", "Price to book value": "price_to_book_value",
            "EPS": "earnings_per_share_ttm",
            "Sales CAGR 3Yrs": "sales_cagr_3y",
            "Profit CAGR 3Yrs": "profit_cagr_3y"
        }
        for screener_name, our_name in field_map.items():
            found_val = top_ratios.get(screener_name)
            if found_val is None:
                for r_name, r_val in top_ratios.items():
                    if r_name.lower() == screener_name.lower():
                        found_val = r_val
                        break
            if found_val is None and screener_name.replace(" ", "") in top_ratios:
                 found_val = top_ratios[screener_name.replace(" ", "")]
            if found_val is not None:
                fundamentals_data[our_name] = found_val

        def extract_table_data(soup_section_id: str, target_rows: dict, period_preference: list = None):
            section = soup.find("section", id=soup_section_id)
            table_data = {}
            if not section: 
                logger.warning(f"Section '{soup_section_id}' not found for {ticker}.")
                return table_data
            table = section.find("table", class_="data-table")
            if not table: 
                logger.warning(f"Data table not found in section '{soup_section_id}' for {ticker}.")
                return table_data
            thead = table.find("thead")
            if not thead: 
                logger.warning(f"Thead not found in table for {soup_section_id}")
                return table_data
            headers = [th.text.strip() for th in thead.select("tr th")][1:] 
            if not headers: 
                logger.warning(f"No headers found in table for section '{soup_section_id}' for {ticker}")
                return table_data

            col_idx_to_extract = len(headers) - 1  # pick latest by default
            if period_preference:
                for i, header_text in enumerate(headers):
                    if any(pref.lower() in header_text.lower() for pref in period_preference):
                        col_idx_to_extract = i
                        logger.info(f"Found preferred period '{headers[col_idx_to_extract]}' at index {col_idx_to_extract} for {soup_section_id}")
                        break
                else: 
                    default_header_msg = headers[0] if headers else "N/A"
                    logger.info(f'No preferred period found in {headers} for {soup_section_id}. Using first data column: "{default_header_msg}"')
            else:
                 default_header_msg = headers[0] if headers else "N/A"
                 logger.info(f'No period preference for {soup_section_id}. Using first data column: "{default_header_msg}"')

            tbody = table.find("tbody")
            if not tbody: 
                logger.warning(f"Tbody not found for {soup_section_id}")
                return table_data
            for row in tbody.select("tr"):
                cells = row.find_all("td")
                if not cells or len(cells) <= col_idx_to_extract + 1: continue
                row_name_cell = cells[0].text.strip().replace(":", "").replace("+", "").strip()
                if row_name_cell in target_rows:
                    our_field_name = target_rows[row_name_cell]
                    value_text = cells[col_idx_to_extract + 1].text.strip()
                    try:
                        parsed_val = _parse_number(value_text)
                        table_data[our_field_name] = parsed_val
                    except Exception:
                        table_data[our_field_name] = value_text
            return table_data

        first_header_quarters, first_header_pl, first_header_bs = "", "", ""
        temp_q_table = soup.find("section", id="quarters")
        if temp_q_table and temp_q_table.find("table", class_="data-table") and temp_q_table.find("table", class_="data-table").find("thead"):
            q_headers = [th.text.strip() for th in temp_q_table.find("table", class_="data-table").find("thead").select("tr th")][1:]
            if q_headers: first_header_quarters = q_headers[0]
        temp_pl_table = soup.find("section", id="profit-loss")
        if temp_pl_table and temp_pl_table.find("table", class_="data-table") and temp_pl_table.find("table", class_="data-table").find("thead"):
            pl_headers = [th.text.strip() for th in temp_pl_table.find("table", class_="data-table").find("thead").select("tr th")][1:]
            if pl_headers: first_header_pl = pl_headers[0]
        temp_bs_table = soup.find("section", id="balance-sheet")
        if temp_bs_table and temp_bs_table.find("table", class_="data-table") and temp_bs_table.find("table", class_="data-table").find("thead"):
            bs_headers = [th.text.strip() for th in temp_bs_table.find("table", class_="data-table").find("thead").select("tr th")][1:]
            if bs_headers: first_header_bs = bs_headers[0]

        quarterly_targets = {"EPS (Rs)": "earnings_per_share", "EPS in Rs": "earnings_per_share", "EPS": "earnings_per_share"}
        quarterly_data = extract_table_data("quarters", quarterly_targets, period_preference=["latest", first_header_quarters])
        if not quarterly_data or "earnings_per_share" not in quarterly_data or quarterly_data["earnings_per_share"] is None:
            logger.info("Did not find EPS in section 'quarters', trying 'quarterly-results'...")
            quarterly_data = extract_table_data("quarterly-results", quarterly_targets, period_preference=["latest", first_header_quarters])
        if quarterly_data and quarterly_data.get("earnings_per_share") is not None:
             fundamentals_data["earnings_per_share"] = quarterly_data["earnings_per_share"]
        elif fundamentals_data.get("earnings_per_share_ttm") is not None:
            fundamentals_data["earnings_per_share"] = fundamentals_data["earnings_per_share_ttm"]
            logger.info(f"Using EPS (TTM) from ratios for {ticker} as quarterly EPS not found/None.")
        else:
            logger.warning(f"EPS not found or is None in quarterly results or TTM ratios for {ticker}.")

        pl_targets = {"Sales": "sales", "Net Profit": "net_profit"}
        pl_data = extract_table_data("profit-loss", pl_targets, period_preference=["TTM", "Trailing 12M", first_header_pl]) 
        fundamentals_data.update(pl_data)

        bs_targets = {
            "Total Liabilities": "total_liabilities", "Total Assets": "total_assets",
            "Share Capital": "share_capital", "Reserves": "reserves", "Borrowings": "total_debt", 
            "Total Current Assets": "current_assets", "Total Current Liabilities": "current_liabilities",
            "Equity Share Capital": "share_capital"
        }
        bs_data = extract_table_data("balance-sheet", bs_targets, period_preference=["latest", first_header_bs]) 
        fundamentals_data.update(bs_data)
        if fundamentals_data.get("share_capital") is not None and fundamentals_data.get("reserves") is not None:
            sc = fundamentals_data["share_capital"]
            rs = fundamentals_data["reserves"]
            if isinstance(sc, (int,float)) and isinstance(rs, (int,float)): fundamentals_data["total_equity"] = sc + rs
        if fundamentals_data.get("current_assets") is not None and fundamentals_data.get("current_liabilities") is not None:
            ca = fundamentals_data["current_assets"]
            cl = fundamentals_data["current_liabilities"]
            if isinstance(ca, (int,float)) and isinstance(cl, (int,float)): fundamentals_data["working_capital"] = ca - cl
        if "earnings_per_share" not in fundamentals_data or fundamentals_data["earnings_per_share"] is None:
            if fundamentals_data.get("earnings_per_share_ttm") is not None:
                 fundamentals_data["earnings_per_share"] = fundamentals_data["earnings_per_share_ttm"]

        if use_cache:
            try:
                with open(cache_file, 'w') as f: json.dump(fundamentals_data, f, indent=4)
                logger.info(f"Saved fundamentals for {ticker} to test cache: {cache_file}")
            except Exception as e: logger.error(f"Failed to save fundamentals to test cache: {e}")
        return fundamentals_data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching data for {ticker} from screener.in")
        return {"error": "Timeout", "ticker": ticker, "url_tried": url_tried}
    except Exception as e:
        logger.error(f"Error in get_screener_data for {ticker}: {e} at url {url_tried}", exc_info=True)
        return {"error": str(e), "ticker": ticker, "url_tried": url_tried}

if __name__ == "__main__":
    import sys
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    tickers_to_test = ["RELIANCE", "FEDERALBNK", "IDFCFIRSTB", "HDFCBANK", "TATAMOTORS", "ITC"]
    test_use_cache = False 

    all_results = {}
    for test_ticker in tickers_to_test:
        logger.info(f"--- Testing Ticker: {test_ticker} ---")
        data = get_screener_data(test_ticker, use_cache=test_use_cache)
        all_results[test_ticker] = data
        print(f"--- Results for {test_ticker} ---")
        print(json.dumps(data, indent=4))
        print("\n--- End of Results for {test_ticker} ---\n")
    
    logger.info("Completed all ticker tests.")
    for ticker, result in all_results.items():
        if "error" in result:
            logger.error(f"Test for {ticker} resulted in an error: {result['error']}")
        else:
            required_fields = ["market_cap", "price", "earnings_per_share", "sales", "net_profit", "book_value_per_share"]
            missing_or_problematic_fields = []
            for field in required_fields:
                value = result.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing_or_problematic_fields.append(field)
            if missing_or_problematic_fields:
                logger.warning(f"For {ticker}, missing or problematic critical fields: {missing_or_problematic_fields}.")
            else:
                logger.success(f"Successfully fetched and parsed critical fields for {ticker}.") 