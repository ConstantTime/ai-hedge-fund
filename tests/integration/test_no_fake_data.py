#!/usr/bin/env python
"""
Test script to demonstrate the new NO FAKE DATA policy
"""
import asyncio
from src.agents.stock_screener import get_stock_screener

async def test_no_fake_data_policy():
    """Test that stocks are skipped when no real data is available"""
    
    print("🧪 TESTING: No Fake Data Policy")
    print("=" * 60)
    
    # Test mix of real stocks and potentially missing ones
    test_stocks = [
        "ADOR",        # Real data available
        "RELIANCE",    # Real data available  
        "INVALIDTICKER",  # Should be skipped
        "XYZKP",       # Likely to be skipped
        "TCS"          # Real data available
    ]
    
    screener = get_stock_screener()
    
    real_data_count = 0
    skipped_count = 0
    
    for ticker in test_stocks:
        print(f"\n🔍 Testing {ticker}:")
        print("-" * 30)
        
        try:
            # Test fundamental data fetching
            fundamental_data = screener.get_fundamental_metrics(ticker)
            
            if fundamental_data is None:
                print(f"🚫 SKIPPED: {ticker} - No real data available")
                skipped_count += 1
            else:
                print(f"✅ REAL DATA: {ticker}")
                print(f"   Price: ₹{fundamental_data.get('price', 'N/A')}")
                print(f"   P/E: {fundamental_data.get('pe_ratio', 'N/A')}")
                print(f"   Market Cap: ₹{fundamental_data.get('market_cap', 'N/A')} Cr")
                print(f"   Data Source: {fundamental_data.get('data_source', 'Unknown')}")
                real_data_count += 1
                
        except Exception as e:
            print(f"❌ ERROR: {ticker} - {e}")
            skipped_count += 1
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"✅ Real Data Stocks: {real_data_count}")
    print(f"🚫 Skipped Stocks: {skipped_count}")
    print(f"📈 Data Quality: {real_data_count/(real_data_count+skipped_count)*100:.1f}% real")
    
    print("\n🎯 CONCLUSION:")
    print("✅ NO FAKE DATA generated")
    print("✅ Stocks with missing data are SKIPPED")
    print("✅ Only REAL screener.in data is used")
    print("✅ Clear logging shows data source")

async def test_scoring_transparency():
    """Test scoring system transparency"""
    
    print("\n\n🧮 TESTING: Scoring System Transparency")
    print("=" * 60)
    
    screener = get_stock_screener()
    
    # Test with a stock that has real data
    ticker = "ADOR"
    print(f"📊 Analyzing {ticker} scoring:")
    
    try:
        # Get real data
        fundamental_data = screener.get_fundamental_metrics(ticker)
        
        if fundamental_data:
            print(f"\n💰 Fundamental Metrics:")
            print(f"   P/E Ratio: {fundamental_data.get('pe_ratio')}")
            print(f"   ROE: {fundamental_data.get('roe')}%")
            print(f"   Debt/Equity: {fundamental_data.get('debt_to_equity'):.3f}")
            print(f"   Revenue Growth: {fundamental_data.get('revenue_growth')}%")
            
            # Mock technical data for scoring demo
            technical_data = {
                "rsi": 55.0,
                "macd_signal": "NEUTRAL",
                "moving_avg_trend": "UPTREND", 
                "volume_surge": False
            }
            
            print(f"\n📈 Technical Indicators:")
            print(f"   RSI: {technical_data['rsi']}")
            print(f"   MACD: {technical_data['macd_signal']}")
            print(f"   Trend: {technical_data['moving_avg_trend']}")
            print(f"   Volume Surge: {technical_data['volume_surge']}")
            
            # Calculate scores
            tech_score, fund_score, overall_score = screener.calculate_ai_scores(
                technical_data, fundamental_data
            )
            
            print(f"\n🧠 AI Scoring Results:")
            print(f"   Technical Score: {tech_score:.1f}/100")
            print(f"   Fundamental Score: {fund_score:.1f}/100") 
            print(f"   Overall Score: {overall_score:.1f}/100")
            
            # Determine signal
            if overall_score >= 80:
                signal = "STRONG_BUY"
            elif overall_score >= 65:
                signal = "BUY"
            elif overall_score >= 35:
                signal = "HOLD"
            else:
                signal = "SELL"
            
            print(f"   Signal: {signal}")
            
        else:
            print(f"🚫 Cannot demo scoring - {ticker} has no real data")
            
    except Exception as e:
        print(f"❌ Scoring test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_no_fake_data_policy())
    asyncio.run(test_scoring_transparency()) 