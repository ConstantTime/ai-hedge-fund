import os
from loguru import logger
from colorama import Fore, Style
import sys

# Find the function that loads data and add error handling around the Zerodha call
try:
    # Look for where get_prices or similar function is called for a ticker
    # Example (adjust based on actual code):
    prices = get_prices(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )
    
    # If you find this pattern or something similar, replace it with:
    try:
        prices = get_prices(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        # Print a clear error message and exit
        print(f"\n{Fore.RED}Error fetching price data for {ticker}: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}To fix this issue:{Style.RESET_ALL}")
        print(f"1. Make sure your {Fore.CYAN}.env{Style.RESET_ALL} file contains valid Zerodha credentials:")
        print(f"   {Fore.GREEN}ZERODHA_API_KEY{Style.RESET_ALL}=your_api_key")
        print(f"   {Fore.GREEN}ZERODHA_ACCESS_TOKEN{Style.RESET_ALL}=your_access_token")
        print(f"2. Run: {Fore.CYAN}poetry run python generate_zerodha_token.py{Style.RESET_ALL} to generate a fresh token")
        print(f"3. Try your command again\n")
        # Prevent moving forward with broken/missing data
        sys.exit(1)  # Exit with error code
        
except:
    # File doesn't exist or couldn't be found, that's okay
    pass 