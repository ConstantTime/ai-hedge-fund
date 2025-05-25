"""
Data source selector module for the AI Hedge Fund.
Allows switching between financialdatasets.ai API and Zerodha API.
"""

import os
import pandas as pd
from typing import List, Optional
import logging
from loguru import logger
from dotenv import load_dotenv

# Import data models
from src.data.models import (
    Price,
    FinancialMetrics,
    CompanyNews,
    InsiderTrade,
    LineItem
)

# Always load environment variables at the start of this module
load_dotenv()

# Initialize the selected data source based on environment variable
data_source = os.environ.get("AI_HEDGE_FUND_DATA_SOURCE", "financial_datasets")
logger.info(f"Using data source: {data_source}")

# Import the appropriate data source module
if data_source == "zerodha":
    logger.info("Using Zerodha API for Indian stocks")
    try:
        from src.tools.zerodha_api import (
            get_prices as zerodha_get_prices,
            get_financial_metrics as zerodha_get_financial_metrics,
            prices_to_df as zerodha_prices_to_df,
            get_price_data as zerodha_get_price_data,
            search_line_items as zerodha_search_line_items,
            ZerodhaAdapter
        )
        # Other functions will be missing for Zerodha
        HAS_ZERODHA = True
        
        # Make sure we initialize the adapter once with the correct environment variables
        # Force reinitialization to ensure we use the most up-to-date environment variables
        zerodha_adapter = ZerodhaAdapter.get_instance(force_reinit=True)
        
        def get_market_cap(ticker: str, end_date: str) -> float:
            """Get market cap for a ticker using Zerodha data."""
            fundamentals = zerodha_adapter.get_fundamentals(ticker)
            return fundamentals.get("market_cap", 0)
        
        def get_insider_trades(ticker: str, end_date: str, start_date: Optional[str] = None, limit: int = 10) -> List[dict]:
            """Get insider trades data - not available with Zerodha yet."""
            logger.warning("Insider trades not available with Zerodha data source")
            return []
        
        def get_company_news(ticker: str, end_date: str, start_date: Optional[str] = None, limit: int = 10) -> List[dict]:
            """Get company news - not available with Zerodha yet."""
            logger.warning("Company news not available with Zerodha data source")
            return []
    except ImportError as e:
        logger.error(f"Error importing Zerodha API: {e}")
        logger.warning("Falling back to financialdatasets.ai API")
        from src.tools.api import (
            get_prices as api_get_prices,
            get_financial_metrics as api_get_financial_metrics,
            prices_to_df as api_prices_to_df,
            get_price_data as api_get_price_data,
            get_company_news as api_get_company_news,
            get_insider_trades as api_get_insider_trades,
            search_line_items as api_search_line_items,
            get_market_cap as api_get_market_cap
        )
        HAS_ZERODHA = False
else:
    logger.info("Using financialdatasets.ai API")
    from src.tools.api import (
        get_prices as api_get_prices,
        get_financial_metrics as api_get_financial_metrics,
        prices_to_df as api_prices_to_df,
        get_price_data as api_get_price_data,
        get_company_news as api_get_company_news,
        get_insider_trades as api_get_insider_trades,
        search_line_items as api_search_line_items,
        get_market_cap as api_get_market_cap
    )
    HAS_ZERODHA = False

def get_prices(
    ticker: str,
    start_date: str,
    end_date: str,
) -> List[Price]:
    """Get prices from the selected data source."""
    if data_source == "zerodha" and HAS_ZERODHA:
        return zerodha_get_prices(ticker, start_date, end_date)
    else:
        return api_get_prices(ticker, start_date, end_date)

def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[FinancialMetrics]:
    """Get financial metrics from the selected data source."""
    if data_source == "zerodha" and HAS_ZERODHA:
        return zerodha_get_financial_metrics(ticker, end_date, period, limit)
    else:
        return api_get_financial_metrics(ticker, end_date, period, limit)

def prices_to_df(prices: List[Price]) -> pd.DataFrame:
    """Convert prices to DataFrame."""
    if data_source == "zerodha" and HAS_ZERODHA:
        return zerodha_prices_to_df(prices)
    else:
        return api_prices_to_df(prices)

def get_price_data(
    ticker: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Get price data from the selected data source."""
    if data_source == "zerodha" and HAS_ZERODHA:
        return zerodha_get_price_data(ticker, start_date, end_date)
    else:
        return api_get_price_data(ticker, start_date, end_date)

def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str = None,
    limit: int = 1000,
) -> List[CompanyNews]:
    """Get company news from the selected data source."""
    if data_source == "zerodha" and HAS_ZERODHA:
        logger.warning("Company news not available with Zerodha data source")
        return []
    else:
        return api_get_company_news(ticker, end_date, start_date, limit)

def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str = None,
    limit: int = 1000,
) -> List[InsiderTrade]:
    """Get insider trades from the selected data source."""
    if data_source == "zerodha" and HAS_ZERODHA:
        logger.warning("Insider trades not available with Zerodha data source")
        return []
    else:
        return api_get_insider_trades(ticker, end_date, start_date, limit)

def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> List[LineItem]:
    """Search line items from the selected data source."""
    if data_source == "zerodha" and HAS_ZERODHA:
        # Use the new mock implementation in zerodha_api
        return zerodha_search_line_items(ticker, line_items, end_date, period, limit)
    else:
        return api_search_line_items(ticker, line_items, end_date, period, limit)

def get_market_cap(
    ticker: str,
    end_date: str,
) -> float:
    """Get market cap from the selected data source."""
    if data_source == "zerodha" and HAS_ZERODHA:
        # Try to get market cap from financial metrics in Zerodha
        try:
            metrics = zerodha_get_financial_metrics(ticker, end_date)
            if metrics and metrics[0].market_cap:
                return metrics[0].market_cap
            logger.warning(f"Market cap not available for {ticker} with Zerodha data source")
            return None
        except Exception as e:
            logger.error(f"Error getting market cap for {ticker}: {e}")
            return None
    else:
        return api_get_market_cap(ticker, end_date) 