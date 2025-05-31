#!/usr/bin/env python
"""
Test script to demonstrate detailed AI screener logging
"""
import asyncio
import requests
from loguru import logger

async def test_detailed_screener():
    """Test the AI screener with detailed logging"""
    
    print("🚀 Testing AI Stock Screener with Detailed Logging")
    print("=" * 60)
    
    # Configure loguru to show detailed logs
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        level="DEBUG"
    )
    
    try:
        # Import the screener
        from src.agents.stock_screener import get_stock_screener
        
        print("\n1. 🤖 Initializing AI Stock Screener...")
        screener = get_stock_screener()
        
        print("\n2. 🔍 Testing single stock analysis...")
        opportunity = await screener.screen_stock("RELIANCE", "Reliance Industries Ltd")
        
        if opportunity:
            print(f"\n✅ Successfully analyzed RELIANCE:")
            print(f"   📊 Overall Score: {opportunity.overall_score:.1f}")
            print(f"   🎯 Signal: {opportunity.signal.value}")
            print(f"   📈 Technical Score: {opportunity.technical_score:.1f}")
            print(f"   💰 Fundamental Score: {opportunity.fundamental_score:.1f}")
            print(f"   🎯 Target Price: ₹{opportunity.target_price:.2f}")
            print(f"   🛡️ Stop Loss: ₹{opportunity.stop_loss:.2f}")
            print(f"   ✅ Buy Reasons: {len(opportunity.buy_reasons)}")
            print(f"   ⚠️ Risk Factors: {len(opportunity.risk_factors)}")
        
        print("\n3. 🔍 Testing opportunity scan (5 stocks)...")
        opportunities = await screener.scan_opportunities(max_stocks=5)
        
        print(f"\n📊 Scan Results:")
        print(f"   🎯 Total Opportunities: {len(opportunities)}")
        
        if opportunities:
            print("   🏆 Top Opportunities:")
            for i, opp in enumerate(opportunities[:3], 1):
                print(f"     {i}. {opp.ticker}: {opp.overall_score:.1f} ({opp.signal.value})")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n4. 🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/opportunities/status",
        "/portfolio/summary", 
        "/opportunities/scan?max_stocks=3"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"   📡 Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - OK")
            else:
                print(f"   ❌ {endpoint} - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {e}")

if __name__ == "__main__":
    print("🎯 Starting Detailed AI Screener Test")
    print("\nThis will show you exactly how the AI finds opportunities:")
    print("- 🔍 Stock universe discovery")
    print("- 📊 Technical analysis calculations")
    print("- 💰 Fundamental analysis scoring")
    print("- 🤖 AI scoring algorithm")
    print("- 🏆 Opportunity ranking")
    
    # Run async test
    asyncio.run(test_detailed_screener())
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("🎉 Test Complete!")
    print("\nNow check your web UI:")
    print("1. Portfolio Monitor - should show beautiful cards instead of JSON")
    print("2. AI Opportunities - click 'Scan 20 Stocks' to see detailed logs")
    print("3. Check terminal logs to see the detailed screening process") 