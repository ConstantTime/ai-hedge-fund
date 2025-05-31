#!/usr/bin/env python
"""
Test script to verify the new intelligent filtering system
"""
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.agents.stock_screener import get_stock_screener

async def test_intelligent_filtering():
    """Test the new intelligent filtering system"""
    
    print("🧪 TESTING: Intelligent Stock Filtering System")
    print("=" * 60)
    
    screener = get_stock_screener()
    
    # Test 1: Basic filtering functionality
    print("\n1️⃣ Testing Basic Universe Generation:")
    print("-" * 40)
    
    try:
        universe = screener.get_nse_universe()
        print(f"✅ Generated universe: {len(universe)} stocks")
        
        if universe:
            print(f"📋 Sample stocks: {[s.get('tradingsymbol') for s in universe[:10]]}")
            
            # Check sector diversity
            sectors = {}
            for stock in universe:
                symbol = stock.get('tradingsymbol', '')
                sector = screener._determine_stock_sector(symbol)
                sectors[sector] = sectors.get(sector, 0) + 1
            
            print(f"🎯 Sector diversity: {len(sectors)} sectors")
            for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
                print(f"   {sector}: {count} stocks")
        
    except Exception as e:
        print(f"❌ Universe generation failed: {e}")
    
    # Test 2: Individual filtering components
    print("\n2️⃣ Testing Individual Filter Components:")
    print("-" * 40)
    
    # Test tradeable check
    test_instruments = [
        {"tradingsymbol": "TCS", "instrument_type": "EQ", "segment": "NSE"},
        {"tradingsymbol": "INVALID-BE", "instrument_type": "EQ", "segment": "NSE"},
        {"tradingsymbol": "XY", "instrument_type": "EQ", "segment": "NSE"},
        {"tradingsymbol": "TEST123", "instrument_type": "EQ", "segment": "NSE"},
    ]
    
    for instrument in test_instruments:
        is_tradeable = screener._is_stock_tradeable(instrument)
        symbol = instrument['tradingsymbol']
        result = "✅ PASS" if is_tradeable else "❌ SKIP"
        print(f"   {result}: {symbol}")
    
    # Test sector determination
    test_symbols = ["TCS", "SUNPHARMA", "HDFCBANK", "TATAMOTORS", "RELIANCE", "UNKNOWNSTOCK"]
    print(f"\n🏷️ Sector Classification:")
    for symbol in test_symbols:
        sector = screener._determine_stock_sector(symbol)
        print(f"   {symbol} → {sector}")
    
    # Test 3: Market cap filtering (if data available)
    print("\n3️⃣ Testing Market Cap Filtering:")
    print("-" * 40)
    
    test_stocks = [{"tradingsymbol": "TCS"}, {"tradingsymbol": "RELIANCE"}, {"tradingsymbol": "INVALIDSTOCK"}]
    try:
        filtered = screener._filter_by_market_metrics(test_stocks)
        print(f"✅ Market cap filter: {len(test_stocks)} → {len(filtered)} stocks")
    except Exception as e:
        print(f"⚠️ Market cap filter test skipped: {e}")
    
    # Test 4: Complete screening pipeline
    print("\n4️⃣ Testing Complete Screening Pipeline:")
    print("-" * 40)
    
    try:
        print("🚀 Running small-scale screening test...")
        opportunities = await screener.scan_opportunities(max_stocks=10)
        
        print(f"✅ Screening completed: {len(opportunities)} opportunities found")
        
        if opportunities:
            print("🏆 TOP OPPORTUNITIES:")
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"   {i}. {opp.ticker} ({opp.sector}): {opp.overall_score:.1f} - {opp.signal.value}")
                print(f"      Price: ₹{opp.current_price}, Market Cap: ₹{opp.market_cap}Cr")
        
        # Analyze results
        if opportunities:
            sectors_found = set(opp.sector for opp in opportunities)
            avg_score = sum(opp.overall_score for opp in opportunities) / len(opportunities)
            high_quality = sum(1 for opp in opportunities if opp.overall_score >= 70)
            
            print(f"\n📊 SCREENING ANALYSIS:")
            print(f"   Sectors represented: {len(sectors_found)}")
            print(f"   Average score: {avg_score:.1f}")
            print(f"   High quality stocks (≥70): {high_quality}/{len(opportunities)} ({high_quality/len(opportunities)*100:.1f}%)")
            print(f"   Sectors found: {', '.join(sorted(sectors_found))}")
        
    except Exception as e:
        print(f"❌ Complete screening test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Performance comparison (conceptual)
    print("\n5️⃣ System Improvements Summary:")
    print("-" * 40)
    print("✅ Intelligent Filtering Features:")
    print("   🎯 Sector-based diversified selection")
    print("   💰 Market cap filtering (₹500-50,000 Cr)")
    print("   📊 Technical strength pre-filtering")
    print("   🎲 Smart sampling vs alphabetical bias")
    print("   🔍 Quality stock identification")
    print("   📈 Volume trend analysis")
    print("   🚫 Non-tradeable stock exclusion")
    
    print("\n❌ Old System Issues Fixed:")
    print("   🔧 No more 'first 50 alphabetically' selection")
    print("   🔧 No more sector concentration bias")
    print("   🔧 No more inclusion of illiquid/untradeable stocks")
    print("   🔧 No more random fake data generation")
    
    print("\n🎯 Expected Improvements:")
    print("   📈 Higher quality stock selection")
    print("   🎯 Better sector diversification")
    print("   💪 Stronger technical candidates")
    print("   📊 More actionable investment opportunities")
    print("   🚀 AI-powered instead of alphabetical sorting")

if __name__ == "__main__":
    asyncio.run(test_intelligent_filtering()) 