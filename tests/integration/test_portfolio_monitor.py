#!/usr/bin/env python
"""
Test script for portfolio monitoring system.
Tests the Zerodha portfolio integration and real-time monitoring capabilities.
"""
import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append('src')

from src.tools.zerodha_portfolio import get_portfolio_monitor
from app.backend.services.scheduler import get_portfolio_scheduler

async def test_portfolio_monitor():
    """Test the portfolio monitoring system"""
    print("🧪 Testing Portfolio Monitoring System")
    print("=" * 50)
    
    # Test 1: Initialize portfolio monitor
    print("\n1. Initializing portfolio monitor...")
    portfolio_monitor = get_portfolio_monitor()
    
    if not portfolio_monitor.kite:
        print("❌ Zerodha connection failed - check your credentials")
        print("   Make sure ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN are set")
        return False
    
    print("✅ Portfolio monitor initialized successfully")
    
    # Test 2: Get cash balance
    print("\n2. Testing cash balance fetch...")
    try:
        cash = portfolio_monitor.get_cash()
        print(f"✅ Cash balance: ₹{cash:,.2f}")
    except Exception as e:
        print(f"❌ Failed to get cash balance: {e}")
        return False
    
    # Test 3: Get positions
    print("\n3. Testing positions fetch...")
    try:
        positions = portfolio_monitor.get_positions()
        print(f"✅ Found {len(positions)} positions")
        for pos in positions[:3]:  # Show first 3 positions
            print(f"   - {pos.get('tradingsymbol', 'Unknown')}: {pos.get('quantity', 0)} shares")
    except Exception as e:
        print(f"❌ Failed to get positions: {e}")
        return False
    
    # Test 4: Get portfolio snapshot
    print("\n4. Testing portfolio snapshot...")
    try:
        snapshot = portfolio_monitor.get_portfolio_snapshot()
        if snapshot:
            print(f"✅ Portfolio snapshot generated:")
            print(f"   - Total Value: ₹{snapshot.total_value:,.2f}")
            print(f"   - Cash: ₹{snapshot.cash:,.2f}")
            print(f"   - Invested: ₹{snapshot.invested_value:,.2f}")
            print(f"   - Total P&L: ₹{snapshot.total_pnl:,.2f}")
            print(f"   - Positions: {len(snapshot.positions)}")
        else:
            print("❌ Failed to generate portfolio snapshot")
            return False
    except Exception as e:
        print(f"❌ Failed to get portfolio snapshot: {e}")
        return False
    
    # Test 5: Test scheduler
    print("\n5. Testing portfolio scheduler...")
    try:
        scheduler = get_portfolio_scheduler()
        
        # Test callback function
        update_count = 0
        async def test_callback(update_data):
            nonlocal update_count
            update_count += 1
            print(f"   📊 Received update #{update_count}: {update_data['type']}")
        
        # Start scheduler for a short test
        await scheduler.start(interval_seconds=5)
        scheduler.add_subscriber(test_callback)
        
        print("✅ Scheduler started, waiting for updates...")
        await asyncio.sleep(12)  # Wait for 2 updates
        
        await scheduler.stop()
        print(f"✅ Scheduler test completed - received {update_count} updates")
        
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All portfolio monitoring tests passed!")
    return True

async def test_api_endpoints():
    """Test the API endpoints (requires running backend)"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 30)
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            print("1. Testing portfolio health endpoint...")
            response = await client.get(f"{base_url}/portfolio/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check: {health_data.get('status', 'unknown')}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
            
            # Test summary endpoint
            print("2. Testing portfolio summary endpoint...")
            response = await client.get(f"{base_url}/portfolio/summary")
            if response.status_code == 200:
                summary_data = response.json()
                print(f"✅ Summary: ₹{summary_data.get('total_value', 0):,.2f} total value")
            else:
                print(f"❌ Summary failed: {response.status_code}")
                
    except ImportError:
        print("⚠️  httpx not available - skipping API tests")
        print("   Install with: pip install httpx")
    except Exception as e:
        print(f"❌ API tests failed: {e}")
        print("   Make sure the backend is running: cd app/backend && uvicorn main:app --reload")

def check_environment():
    """Check if environment is properly configured"""
    print("🔧 Environment Check")
    print("=" * 20)
    
    required_vars = ["ZERODHA_API_KEY", "ZERODHA_ACCESS_TOKEN"]
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value[:5]}...{value[-5:] if len(value) > 10 else value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Run: python generate_zerodha_token.py to set them up")
        return False
    
    return True

async def main():
    """Main test function"""
    print("🚀 AI Hedge Fund Portfolio Monitor Test Suite")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed - fix the issues above and try again")
        return
    
    # Test portfolio monitoring
    success = await test_portfolio_monitor()
    
    if success:
        # Test API endpoints (optional)
        await test_api_endpoints()
    
    print("\n🏁 Test suite completed!")

if __name__ == "__main__":
    asyncio.run(main()) 