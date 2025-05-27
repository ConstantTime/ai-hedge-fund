# AI Hedge Fund

This is a proof of concept for an AI-powered hedge fund.  The goal of this project is to explore the use of AI to make trading decisions.  This project is for **educational** purposes only and is not intended for real trading or investment.

This system employs several agents working together:

1. Aswath Damodaran Agent - The Dean of Valuation, focuses on story, numbers, and disciplined valuation
2. Ben Graham Agent - The godfather of value investing, only buys hidden gems with a margin of safety
3. Bill Ackman Agent - An activist investor, takes bold positions and pushes for change
4. Cathie Wood Agent - The queen of growth investing, believes in the power of innovation and disruption
5. Charlie Munger Agent - Warren Buffett's partner, only buys wonderful businesses at fair prices
6. Michael Burry Agent - The Big Short contrarian who hunts for deep value
7. Peter Lynch Agent - Practical investor who seeks "ten-baggers" in everyday businesses
8. Phil Fisher Agent - Meticulous growth investor who uses deep "scuttlebutt" research 
9. Rakesh Jhunjhunwala Agent - The Big Bull of India
10. Stanley Druckenmiller Agent - Macro legend who hunts for asymmetric opportunities with growth potential
11. Warren Buffett Agent - The oracle of Omaha, seeks wonderful companies at a fair price
12. Valuation Agent - Calculates the intrinsic value of a stock and generates trading signals
13. Sentiment Agent - Analyzes market sentiment and generates trading signals
14. Fundamentals Agent - Analyzes fundamental data and generates trading signals
15. Technicals Agent - Analyzes technical indicators and generates trading signals
16. Risk Manager - Calculates risk metrics and sets position limits
17. Portfolio Manager - Makes final trading decisions and generates orders
    
<img width="1042" alt="Screenshot 2025-03-22 at 6 19 07 PM" src="https://github.com/user-attachments/assets/cbae3dcf-b571-490d-b0ad-3f0f035ac0d4" />


**Note**: the system simulates trading decisions, it does not actually trade.

[![Twitter Follow](https://img.shields.io/twitter/follow/virattt?style=social)](https://twitter.com/virattt)

## Disclaimer

This project is for **educational and research purposes only**.

- Not intended for real trading or investment
- No investment advice or guarantees provided
- Creator assumes no liability for financial losses
- Consult a financial advisor for investment decisions
- Past performance does not indicate future results

By using this software, you agree to use it solely for learning purposes.

## Table of Contents
- [🚀 New: Real-time Portfolio Monitoring](#-new-real-time-portfolio-monitoring)
- [Indian Stock Market Integration](#indian-stock-market-integration)
- [Setup](#setup)
  - [Using Poetry](#using-poetry)
  - [Using Docker](#using-docker)
- [Usage](#usage)
  - [Running the Hedge Fund](#running-the-hedge-fund)
  - [Running the Backtester](#running-the-backtester)
- [Contributing](#contributing)
- [Feature Requests](#feature-requests)
- [License](#license)

## Introduction

The AI Hedge Fund is a combination of multiple AI agents that analyze market data and collaborate to make investment decisions. Each AI agent is designed to mimic the trading style and strategies of a famous investor (like Warren Buffett, Michael Burry), or a specific trading approach (like technical analysis).

## 🚀 New: Real-time Portfolio Monitoring

This project now includes a **live portfolio monitoring system** that tracks your actual Zerodha account in real-time! Monitor your cash, positions, P&L, and get AI-powered insights on your portfolio.

### Quick Start - Portfolio Monitor

```bash
# 1. Set up Zerodha credentials
python generate_zerodha_token.py

# 2. Test the system
python test_portfolio_monitor.py

# 3. Start the web interface
./start_portfolio_monitor.sh
```

Then open http://localhost:5173 to see your live portfolio dashboard!

**Features:**
- 📊 **Real-time Portfolio Tracking**: Live cash, positions, and P&L updates
- 🌐 **Modern Web Interface**: Beautiful dashboard with live data streaming
- 📈 **Portfolio Analytics**: Risk metrics, concentration analysis, and performance tracking
- 🔄 **Auto-refresh**: Portfolio data updates every 30 seconds automatically
- 📱 **Responsive Design**: Works on desktop and mobile

For detailed setup instructions, see [PORTFOLIO_MONITOR.md](PORTFOLIO_MONITOR.md).

## Indian Stock Market Integration

In addition to US stocks through financialdatasets.ai, this project now supports Indian stocks via Zerodha integration. The system can fetch data from NSE (National Stock Exchange) and process it in the same format used by the AI agents.

### Using Zerodha Integration

To use the Zerodha integration for Indian stocks:

1. Ensure you have a Zerodha account and API credentials
2. Set the following environment variables:
   ```
   export ZERODHA_API_KEY="your_api_key"
   export ZERODHA_ACCESS_TOKEN="your_access_token"
   export AI_HEDGE_FUND_DATA_SOURCE="zerodha"
   ```
3. Run the hedge fund with Indian stock tickers:
   ```
   ./run_with_zerodha.sh --tickers RELIANCE,INFY,HDFCBANK
   ```

For a backtesting run:
```
./run_with_zerodha.sh --tickers RELIANCE,INFY --backtest
```

If you don't have LLM API keys, you can use Ollama for local inference:
```
./run_with_zerodha.sh --tickers RELIANCE,INFY --ollama
```

### Data Sources

The Zerodha integration provides:
- Historical OHLCV data via Kite Connect API
- Basic fundamental metrics via web scraping (Screener.in)

Note that some metrics available for US stocks may not be available for Indian stocks.

### Zerodha-specific Requirements

If you're using the Zerodha integration for Indian stocks, you'll need to install additional dependencies:

```bash
pip install -r requirements-zerodha.txt
```

Or with Poetry:

```bash
poetry add kiteconnect beautifulsoup4 python-dateutil pandas pyarrow fastparquet
```

### Generating Zerodha Access Token

The Zerodha API requires an access token that is valid for one day. To generate a token:

1. Make sure you have your Zerodha API key and secret from the [Kite Connect Developer Console](https://kite.trade/connect/login/)
2. Run the token generation script:

```bash
# Using Poetry (recommended)
poetry run python generate_zerodha_token.py

# Or with API credentials as arguments
poetry run python generate_zerodha_token.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET
```

The script will:
1. Open a browser window for you to log in to your Zerodha account
2. Ask you to paste the request token from the redirect URL
3. Generate and display your access token
4. Show the export commands to set the required environment variables

## Setup

### Using Poetry

Clone the repository:
```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
```

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Set up your environment variables:
```bash
# Create .env file for your API keys
cp .env.example .env
```

4. Set your API keys:
```bash
# For running LLMs hosted by openai (gpt-4o, gpt-4o-mini, etc.)
# Get your OpenAI API key from https://platform.openai.com/
OPENAI_API_KEY=your-openai-api-key

# For running LLMs hosted by groq (deepseek, llama3, etc.)
# Get your Groq API key from https://groq.com/
GROQ_API_KEY=your-groq-api-key

# For getting financial data to power the hedge fund
# Get your Financial Datasets API key from https://financialdatasets.ai/
FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key
```

### Using Docker

1. Make sure you have Docker installed on your system. If not, you can download it from [Docker's official website](https://www.docker.com/get-started).

2. Clone the repository:
```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
```

3. Set up your environment variables:
```bash
# Create .env file for your API keys
cp .env.example .env
```

4. Edit the .env file to add your API keys as described above.

5. Navigate to the docker directory:
```bash
cd docker
```

6. Build the Docker image:
```bash
# On Linux/Mac:
./run.sh build

# On Windows:
run.bat build
```

**Important**: You must set `OPENAI_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, or `DEEPSEEK_API_KEY` for the hedge fund to work.  If you want to use LLMs from all providers, you will need to set all API keys.

Financial data for AAPL, GOOGL, MSFT, NVDA, and TSLA is free and does not require an API key.

For any other ticker, you will need to set the `FINANCIAL_DATASETS_API_KEY` in the .env file.

## Usage

### Running the Hedge Fund

#### With Poetry
```bash
poetry run python src/main.py --ticker AAPL,MSFT,NVDA
```

#### With Docker
**Note**: All Docker commands must be run from the `docker/` directory.

```bash
# Navigate to the docker directory first
cd docker

# On Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA main

# On Windows:
run.bat --ticker AAPL,MSFT,NVDA main
```

**Example Output:**
<img width="992" alt="Screenshot 2025-01-06 at 5 50 17 PM" src="https://github.com/user-attachments/assets/e8ca04bf-9989-4a7d-a8b4-34e04666663b" />

You can also specify a `--ollama` flag to run the AI hedge fund using local LLMs.

```bash
# With Poetry:
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --ollama

# With Docker (from docker/ directory):
# On Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --ollama main

# On Windows:
run.bat --ticker AAPL,MSFT,NVDA --ollama main
```

You can also specify a `--show-reasoning` flag to print the reasoning of each agent to the console.

```bash
# With Poetry:
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --show-reasoning

# With Docker (from docker/ directory):
# On Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --show-reasoning main

# On Windows:
run.bat --ticker AAPL,MSFT,NVDA --show-reasoning main
```

You can optionally specify the start and end dates to make decisions for a specific time period.

```bash
# With Poetry:
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 

# With Docker (from docker/ directory):
# On Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 main

# On Windows:
run.bat --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 main
```

### Running the Backtester

#### With Poetry
```bash
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA
```

#### With Docker
**Note**: All Docker commands must be run from the `docker/` directory.

```bash
# Navigate to the docker directory first
cd docker

# On Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA backtest

# On Windows:
run.bat --ticker AAPL,MSFT,NVDA backtest
```

**Example Output:**
<img width="941" alt="Screenshot 2025-01-06 at 5 47 52 PM" src="https://github.com/user-attachments/assets/00e794ea-8628-44e6-9a84-8f8a31ad3b47" />


You can optionally specify the start and end dates to backtest over a specific time period.

```bash
# With Poetry:
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01

# With Docker (from docker/ directory):
# On Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 backtest

# On Windows:
run.bat --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 backtest
```

You can also specify a `--ollama` flag to run the backtester using local LLMs.
```bash
# With Poetry:
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA --ollama

# With Docker (from docker/ directory):
# On Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --ollama backtest

# On Windows:
run.bat --ticker AAPL,MSFT,NVDA --ollama backtest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

**Important**: Please keep your pull requests small and focused.  This will make it easier to review and merge.

## Feature Requests

If you have a feature request, please open an [issue](https://github.com/virattt/ai-hedge-fund/issues) and make sure it is tagged with `enhancement`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
