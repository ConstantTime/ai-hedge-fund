#!/usr/bin/env python
"""
Clear Cache Script: Clear all cached data for AI hedge fund system
"""
import requests
import asyncio
from src.data.cache import get_cache

def clear_data_cache():
    """Clear the global data cache"""
    print("🧹 Clearing data cache...")
    cache = get_cache()
    cache._prices_cache.clear()
    cache._financial_metrics_cache.clear()
    cache._line_items_cache.clear()
    cache._insider_trades_cache.clear()
    cache._company_news_cache.clear()
    print("✅ Data cache cleared")

def clear_opportunities_cache():
    """Clear opportunities cache via API"""
    print("🧹 Clearing opportunities cache...")
    try:
        # Call the backend to clear opportunities cache
        response = requests.delete("http://localhost:8000/opportunities/cache")
        if response.status_code == 200:
            print("✅ Opportunities cache cleared")
        else:
            print(f"❌ Failed to clear opportunities cache: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to clear opportunities cache: {e}")

def refresh_portfolio():
    """Refresh portfolio data"""
    print("🔄 Refreshing portfolio data...")
    try:
        response = requests.post("http://localhost:8000/portfolio/refresh")
        if response.status_code == 200:
            print("✅ Portfolio data refreshed")
        else:
            print(f"❌ Failed to refresh portfolio: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to refresh portfolio: {e}")

if __name__ == "__main__":
    print("🚀 AI Hedge Fund Cache Cleaner")
    print("=" * 40)
    
    clear_data_cache()
    clear_opportunities_cache()
    refresh_portfolio()
    
    print("=" * 40)
    print("🎉 Cache cleared! System is reset.")
    print("\nNow you can:")
    print("1. Go to Portfolio Monitor tab - see live portfolio data")
    print("2. Go to AI Opportunities tab - run new stock scans")
    print("3. See AI agents analyze fresh data") 