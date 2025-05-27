from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.backend.routes import api_router
from app.backend.services.scheduler import get_portfolio_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    scheduler = get_portfolio_scheduler()
    
    # Check if we have Zerodha credentials before starting scheduler
    api_key = os.environ.get("ZERODHA_API_KEY")
    access_token = os.environ.get("ZERODHA_ACCESS_TOKEN")
    
    if api_key and access_token:
        await scheduler.start(interval_seconds=30)
        print("✅ Portfolio scheduler started successfully")
    else:
        print("⚠️  Portfolio scheduler not started - missing Zerodha credentials")
        print("   Set ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN to enable portfolio monitoring")
    
    yield
    
    # Shutdown
    await scheduler.stop()
    print("🛑 Portfolio scheduler stopped")

app = FastAPI(
    title="AI Hedge Fund API", 
    description="Backend API for AI Hedge Fund with Portfolio Monitoring", 
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(api_router)
