#!/bin/bash

# This script runs the AI Hedge Fund with Zerodha as the data source for Indian stocks

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found"
fi

# Set environment variables
export AI_HEDGE_FUND_DATA_SOURCE="zerodha"

# Check if ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN are set
if [ -z "$ZERODHA_API_KEY" ] || [ -z "$ZERODHA_ACCESS_TOKEN" ]; then
    echo "Warning: ZERODHA_API_KEY or ZERODHA_ACCESS_TOKEN not set."
    echo "Will run in dry-run mode without API access."
fi

# Parse command line arguments
TICKERS="RELIANCE,INFY"  # Default tickers
OLLAMA=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --ticker|--tickers)
            TICKERS="$2"
            shift
            shift
            ;;
        --ollama)
            OLLAMA="--ollama"
            shift
            ;;
        --backtest)
            MODE="backtest"
            shift
            ;;
        *)
            # Unknown option
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set mode, default to main if not specified
if [ -z "$MODE" ]; then
    MODE="main"
fi

# Debug: Print environment variables for debugging
echo "Using the following configuration:"
echo "ZERODHA_API_KEY: ${ZERODHA_API_KEY:0:5}... (truncated)"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:5}... (truncated)" 
echo "Mode: $MODE"
echo "Tickers: $TICKERS"
echo "Ollama: ${OLLAMA:-Not enabled}"

# Run the appropriate mode
if [ "$MODE" = "backtest" ]; then
    echo "Running backtester with Zerodha data source for Indian stocks"
    
    poetry run python src/backtester.py --tickers "$TICKERS" $OLLAMA
else
    echo "Running main with Zerodha data source for Indian stocks"
    
    poetry run python src/main.py --tickers "$TICKERS" $OLLAMA
fi 