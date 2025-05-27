# Portfolio Monitoring System

A real-time portfolio monitoring system for the AI Hedge Fund that tracks your Zerodha account, providing live updates on cash, positions, P&L, and portfolio analytics.

## 🚀 Features

### Real-time Portfolio Tracking
- **Live Cash Balance**: Monitor available cash in your Zerodha account
- **Position Monitoring**: Track all your stock positions with current prices
- **P&L Tracking**: Real-time profit/loss calculations for individual positions and total portfolio
- **Portfolio Analytics**: Weight distribution, concentration risk, and diversification metrics

### Web Interface
- **Live Dashboard**: Real-time portfolio overview with auto-updating data
- **Position Details**: Detailed view of all holdings with current market values
- **Performance Metrics**: Portfolio analytics and risk metrics
- **Responsive Design**: Works on desktop and mobile devices

### API Integration
- **RESTful API**: Complete API for portfolio data access
- **Server-Sent Events (SSE)**: Real-time streaming updates
- **Health Monitoring**: System health checks and connection status

## 📋 Prerequisites

1. **Zerodha Account**: Active Zerodha trading account
2. **API Credentials**: Zerodha API key and secret from [Kite Connect](https://kite.trade/)
3. **Python 3.11+**: For backend services
4. **Node.js**: For frontend development

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
# Install Python dependencies
poetry install

# Install frontend dependencies
cd app/frontend
npm install
```

### 2. Configure Zerodha Credentials

```bash
# Generate access token (valid for 1 day)
python generate_zerodha_token.py

# This will automatically update your .env file with:
# ZERODHA_API_KEY=your_api_key
# ZERODHA_ACCESS_TOKEN=your_access_token
```

### 3. Test Portfolio Connection

```bash
# Run the test suite to verify everything works
python test_portfolio_monitor.py
```

Expected output:
```
🚀 AI Hedge Fund Portfolio Monitor Test Suite
============================================================
🔧 Environment Check
====================
✅ ZERODHA_API_KEY: abc12...xyz89
✅ ZERODHA_ACCESS_TOKEN: def34...uvw67

🧪 Testing Portfolio Monitoring System
==================================================
1. Initializing portfolio monitor...
✅ Portfolio monitor initialized successfully

2. Testing cash balance fetch...
✅ Cash balance: ₹1,25,000.00

3. Testing positions fetch...
✅ Found 5 positions
   - RELIANCE: 10 shares
   - INFY: 25 shares
   - HDFCBANK: 15 shares

4. Testing portfolio snapshot...
✅ Portfolio snapshot generated:
   - Total Value: ₹2,45,000.00
   - Cash: ₹1,25,000.00
   - Invested: ₹1,20,000.00
   - Total P&L: ₹5,000.00
   - Positions: 5

5. Testing portfolio scheduler...
✅ Scheduler started, waiting for updates...
   📊 Received update #1: portfolio_update
   📊 Received update #2: portfolio_update
✅ Scheduler test completed - received 2 updates

==================================================
🎉 All portfolio monitoring tests passed!
```

## 🖥️ Running the Application

### Backend (API Server)

```bash
cd app/backend
poetry run uvicorn main:app --reload
```

The backend will start on `http://localhost:8000` with:
- **API Documentation**: http://localhost:8000/docs
- **Portfolio Health**: http://localhost:8000/portfolio/health
- **Live Portfolio Stream**: http://localhost:8000/portfolio/stream

### Frontend (Web Interface)

```bash
cd app/frontend
npm run dev
```

The frontend will start on `http://localhost:5173` with:
- **Portfolio Monitor Tab**: Real-time portfolio dashboard
- **AI Agents Flow Tab**: Existing agent workflow interface

## 📊 API Endpoints

### Portfolio Data
- `GET /portfolio/summary` - Portfolio summary with key metrics
- `GET /portfolio/positions` - Detailed position information
- `GET /portfolio/cash` - Current cash balance
- `GET /portfolio/analytics` - Portfolio analytics and risk metrics

### Real-time Updates
- `GET /portfolio/stream` - Server-Sent Events stream for live updates
- `POST /portfolio/refresh` - Force refresh portfolio data

### System Health
- `GET /portfolio/health` - System health check and connection status

## 🔧 Configuration

### Environment Variables

```bash
# Required for portfolio monitoring
ZERODHA_API_KEY=your_zerodha_api_key
ZERODHA_ACCESS_TOKEN=your_zerodha_access_token

# Optional: AI model API keys (for future rebalancing features)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
```

### Portfolio Monitor Settings

```python
# In src/tools/zerodha_portfolio.py
cache_duration = 60  # Cache portfolio data for 60 seconds

# In app/backend/services/scheduler.py
interval_seconds = 30  # Update portfolio every 30 seconds
```

## 📱 Web Interface Features

### Portfolio Overview
- **Total Portfolio Value**: Combined cash + invested value
- **Cash Balance**: Available cash with percentage of portfolio
- **Invested Value**: Total market value of all positions
- **Day P&L**: Today's profit/loss with trend indicators

### Position Details
- **Holdings Table**: All positions with quantity, prices, and P&L
- **Top Holdings**: Largest positions by portfolio weight
- **Real-time Updates**: Live price updates and P&L changes

### System Status
- **Connection Status**: Live/Disconnected indicator
- **Last Update Time**: When data was last refreshed
- **Refresh Button**: Manual data refresh option

## 🔍 Troubleshooting

### Common Issues

1. **"Zerodha connection failed"**
   ```bash
   # Regenerate access token (expires daily)
   python generate_zerodha_token.py
   ```

2. **"Portfolio scheduler not started"**
   ```bash
   # Check environment variables
   echo $ZERODHA_API_KEY
   echo $ZERODHA_ACCESS_TOKEN
   ```

3. **"Connection to portfolio stream lost"**
   - Check if backend is running on port 8000
   - Verify CORS settings allow frontend origin
   - Check network connectivity

### Debug Mode

```bash
# Run with debug logging
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.tools.zerodha_portfolio import get_portfolio_monitor
monitor = get_portfolio_monitor()
snapshot = monitor.get_portfolio_snapshot()
print(snapshot)
"
```

## 🔮 Next Steps (Week 2+)

This portfolio monitoring system is the foundation for:

1. **AI-Powered Rebalancing**: Agents that analyze portfolio and suggest rebalancing
2. **Opportunity Scanner**: AI agents scanning mid/small-cap opportunities
3. **Risk Management**: Automated position sizing and risk controls
4. **Trade Execution**: Automated trade placement with approval workflow

## 📝 Technical Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   Zerodha API   │
│   (React)       │◄──►│   (FastAPI)      │◄──►│   (KiteConnect) │
│                 │    │                  │    │                 │
│ • Portfolio UI  │    │ • REST API       │    │ • Positions     │
│ • Real-time SSE │    │ • SSE Streaming  │    │ • Cash Balance  │
│ • Charts/Tables │    │ • Scheduler      │    │ • Market Data   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow
1. **Scheduler** fetches portfolio data from Zerodha every 30 seconds
2. **Portfolio Monitor** processes and caches the data
3. **SSE Stream** broadcasts updates to connected frontend clients
4. **React Components** update the UI in real-time

## 🤝 Contributing

To extend the portfolio monitoring system:

1. **Add New Metrics**: Extend `PortfolioSnapshot` class
2. **New API Endpoints**: Add routes in `app/backend/routes/portfolio.py`
3. **Frontend Components**: Create new React components in `app/frontend/src/components/`
4. **Schedulers**: Add new background tasks in `app/backend/services/scheduler.py`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 