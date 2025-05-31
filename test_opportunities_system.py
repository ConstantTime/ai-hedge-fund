#!/usr/bin/env python
"""
Comprehensive test script for AI Stock Opportunities System
Tests the complete pipeline: AI Screener -> API -> Frontend Integration
"""
import asyncio
import sys
import os
import requests
import time
from datetime import datetime

# Add src to path
sys.path.append('src')

def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:8000/api"
    
    print("🌐 Testing API Endpoints...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test 2: Opportunities status
    try:
        response = requests.get(f"{base_url}/opportunities/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working - Cached: {data.get('opportunities_cached', 0)}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
    
    # Test 3: Start scan
    try:
        response = requests.get(f"{base_url}/opportunities/scan?max_stocks=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Scan endpoint working - Status: {data.get('status')}")
            
            # Wait for scan to complete
            print("⏳ Waiting for scan to complete...")
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                status_response = requests.get(f"{base_url}/opportunities/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if not status_data.get('scan_in_progress', True):
                        print(f"✅ Scan completed! Found {status_data.get('opportunities_cached', 0)} opportunities")
                        break
                    if i % 5 == 0:
                        print(f"   Still scanning... ({i}s)")
            
        else:
            print(f"❌ Scan endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Scan endpoint error: {e}")
    
    # Test 4: List opportunities
    try:
        response = requests.get(f"{base_url}/opportunities/list?limit=3")
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunities', [])
            print(f"✅ List endpoint working - Found {len(opportunities)} opportunities")
            
            if opportunities:
                top_opp = opportunities[0]
                print(f"   Top opportunity: {top_opp.get('ticker')} - Score: {top_opp.get('ai_analysis', {}).get('overall_score', 0):.1f}")
        else:
            print(f"❌ List endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ List endpoint error: {e}")
    
    # Test 5: Analyze single stock
    try:
        response = requests.get(f"{base_url}/opportunities/analyze/RELIANCE")
        if response.status_code == 200:
            data = response.json()
            analysis = data.get('analysis', {})
            print(f"✅ Analyze endpoint working - RELIANCE score: {analysis.get('ai_analysis', {}).get('overall_score', 0):.1f}")
        else:
            print(f"❌ Analyze endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Analyze endpoint error: {e}")
    
    # Test 6: Signal distribution
    try:
        response = requests.get(f"{base_url}/opportunities/signals")
        if response.status_code == 200:
            data = response.json()
            signals = data.get('signal_distribution', {})
            print(f"✅ Signals endpoint working - Distribution: {signals}")
        else:
            print(f"❌ Signals endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Signals endpoint error: {e}")

async def test_ai_screener():
    """Test AI screener functionality"""
    print("\n🤖 Testing AI Stock Screener...")
    
    try:
        from src.agents.stock_screener import get_stock_screener, ScreenerSignal
        
        screener = get_stock_screener()
        print("✅ AI Screener initialized")
        
        # Test single stock analysis
        print("📊 Testing single stock analysis...")
        opportunity = await screener.screen_stock("RELIANCE", "Reliance Industries Ltd")
        
        if opportunity:
            print(f"✅ Stock analysis working!")
            print(f"   Ticker: {opportunity.ticker}")
            print(f"   Overall Score: {opportunity.overall_score:.1f}")
            print(f"   Signal: {opportunity.signal.value}")
            print(f"   Technical Score: {opportunity.technical_score:.1f}")
            print(f"   Fundamental Score: {opportunity.fundamental_score:.1f}")
            print(f"   Buy Reasons: {len(opportunity.buy_reasons)}")
            print(f"   Risk Factors: {len(opportunity.risk_factors)}")
            print(f"   Target Price: ₹{opportunity.target_price:.2f}")
            print(f"   Stop Loss: ₹{opportunity.stop_loss:.2f}")
        else:
            print("❌ Stock analysis failed")
        
        # Test batch scanning
        print("\n🔍 Testing batch scanning...")
        opportunities = await screener.scan_opportunities(max_stocks=3)
        
        if opportunities:
            print(f"✅ Batch scanning working! Found {len(opportunities)} opportunities")
            
            print("\n📈 Top Opportunities:")
            for i, opp in enumerate(opportunities, 1):
                print(f"   {i}. {opp.ticker} - Score: {opp.overall_score:.1f} - Signal: {opp.signal.value}")
            
            # Test filtering
            buy_opportunities = screener.get_top_opportunities(
                opportunities,
                signal_filter=ScreenerSignal.BUY,
                min_score=50.0,
                limit=5
            )
            print(f"\n💰 Buy signals (score > 50): {len(buy_opportunities)}")
            
        else:
            print("❌ Batch scanning failed")
            
    except Exception as e:
        print(f"❌ AI Screener error: {e}")
        import traceback
        traceback.print_exc()

def test_portfolio_integration():
    """Test portfolio integration"""
    print("\n💼 Testing Portfolio Integration...")
    
    try:
        # Test portfolio endpoints
        base_url = "http://localhost:8000/api"
        
        response = requests.get(f"{base_url}/portfolio/summary")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Portfolio integration working - Total value: ₹{data.get('total_value', 0):,.2f}")
        else:
            print(f"❌ Portfolio integration failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Portfolio integration error: {e}")

def test_frontend_readiness():
    """Test if frontend is ready"""
    print("\n🎨 Testing Frontend Readiness...")
    
    try:
        # Check if frontend server is running
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend server running on port 5173")
        else:
            print(f"❌ Frontend server issue: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Frontend server not running on port 5173")
        print("   Start with: cd app/frontend && npm run dev")
    except Exception as e:
        print(f"❌ Frontend test error: {e}")

def print_testing_instructions():
    """Print manual testing instructions"""
    print("\n" + "="*60)
    print("🧪 MANUAL TESTING INSTRUCTIONS")
    print("="*60)
    
    print("\n1. 🚀 START SERVERS:")
    print("   Backend:  cd app/backend && poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
    print("   Frontend: cd app/frontend && npm run dev")
    
    print("\n2. 🌐 TEST API ENDPOINTS:")
    print("   • http://localhost:8000/docs (Swagger UI)")
    print("   • GET /api/opportunities/status")
    print("   • GET /api/opportunities/scan?max_stocks=10")
    print("   • GET /api/opportunities/list")
    print("   • GET /api/opportunities/analyze/RELIANCE")
    
    print("\n3. 🎨 TEST FRONTEND:")
    print("   • Open http://localhost:5173")
    print("   • Navigate to 'AI Opportunities' tab")
    print("   • Click 'Scan 20 Stocks' button")
    print("   • Wait for scan completion")
    print("   • View opportunities with scores & signals")
    print("   • Test filters (signal, min score, sector)")
    print("   • Try 'Analyze Stock' tab with ticker like 'RELIANCE'")
    
    print("\n4. 🔍 VERIFY FEATURES:")
    print("   ✓ Real-time scan status updates")
    print("   ✓ AI scoring (Technical + Fundamental)")
    print("   ✓ Buy/Sell signals with confidence")
    print("   ✓ Target prices & stop losses")
    print("   ✓ Buy reasons & risk factors")
    print("   ✓ Filtering and sorting")
    print("   ✓ Individual stock analysis")
    
    print("\n5. 🎯 SUCCESS CRITERIA:")
    print("   ✓ Backend starts without errors")
    print("   ✓ Frontend loads AI Opportunities tab")
    print("   ✓ Scan completes and shows opportunities")
    print("   ✓ Opportunities display with scores 0-100")
    print("   ✓ Signals show (STRONG_BUY, BUY, HOLD, etc.)")
    print("   ✓ Technical & fundamental metrics visible")
    print("   ✓ AI reasoning (buy reasons + risk factors)")
    print("   ✓ Individual stock analysis works")

async def main():
    """Run comprehensive test suite"""
    print("🚀 AI STOCK OPPORTUNITIES - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test AI Screener Core
    await test_ai_screener()
    
    # Test API Endpoints
    test_api_endpoints()
    
    # Test Portfolio Integration
    test_portfolio_integration()
    
    # Test Frontend Readiness
    test_frontend_readiness()
    
    # Print manual testing instructions
    print_testing_instructions()
    
    print("\n" + "="*60)
    print("🎉 TEST SUITE COMPLETED!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Start both servers (backend + frontend)")
    print("2. Open http://localhost:5173")
    print("3. Test AI Opportunities tab")
    print("4. Verify all features working")
    print("\n🚀 Ready for Week 3: Portfolio Rebalancing Engine!")

if __name__ == "__main__":
    asyncio.run(main()) 