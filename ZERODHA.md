# Zerodha Integration for AI Hedge Fund

This guide explains how to set up and use the Zerodha integration for trading Indian stocks with the AI Hedge Fund.

## Prerequisites

1. A Zerodha Kite account
2. API key and secret from Zerodha Developer Console (https://kite.trade/)
3. Python 3.11+ with Poetry installed

## Setup Steps

### 1. Generate Zerodha Access Token

The access token is required for API access and is valid for one day. You need to regenerate it daily.

```bash
# Run the token generator script
python generate_zerodha_token.py
```

The script will:
1. Prompt for your API key and secret (if not in environment)
2. Open a browser window to authenticate with Zerodha
3. Generate an access token
4. Automatically update your `.env` file with the credentials

### 2. Run the AI Hedge Fund with Zerodha

```bash
# Run with default tickers (RELIANCE, INFY)
./run_with_zerodha.sh

# Run with specific tickers
./run_with_zerodha.sh --tickers "SBIN,HDFCBANK,TCS"

# Run with local LLM via Ollama (to avoid API costs)
./run_with_zerodha.sh --ollama
```

## Environment Variables

The system uses these environment variables:

- `ZERODHA_API_KEY`: Your Zerodha API key
- `ZERODHA_API_SECRET`: Your Zerodha API secret
- `ZERODHA_ACCESS_TOKEN`: The access token generated daily
- `ANTHROPIC_API_KEY`: Your Anthropic Claude API key (for AI analysis)

All these variables can be stored in your `.env` file.

## Troubleshooting

1. **Access token errors**: Run `generate_zerodha_token.py` to refresh your token.
2. **LLM errors**: Use the `--ollama` flag to use local models instead of API.
3. **Missing data**: Ensure you're using valid NSE ticker symbols. 