#!/usr/bin/env python
"""
Script to generate a Zerodha access token.

This token is required for API access and is valid for one day.
"""

import os
import re
import webbrowser
import argparse
from pathlib import Path
from dotenv import load_dotenv
from kiteconnect import KiteConnect

def update_env_file(api_key, access_token, env_file=".env"):
    """Update .env file with Zerodha API key and access token."""
    env_path = Path(env_file)
    
    # Create .env file if it doesn't exist
    if not env_path.exists():
        env_path.touch()
        print(f"Created new {env_file} file")
    
    # Read current .env content
    try:
        with open(env_path, 'r') as f:
            content = f.read()
    except:
        content = ""
    
    # Update or add API key
    if api_key:
        if "ZERODHA_API_KEY" in content:
            content = re.sub(
                r'ZERODHA_API_KEY=.*',
                f'ZERODHA_API_KEY={api_key}',
                content
            )
        else:
            content += f'\nZERODHA_API_KEY={api_key}\n'
    
    # Update or add access token
    if access_token:
        if "ZERODHA_ACCESS_TOKEN" in content:
            content = re.sub(
                r'ZERODHA_ACCESS_TOKEN=.*',
                f'ZERODHA_ACCESS_TOKEN={access_token}',
                content
            )
        else:
            content += f'\nZERODHA_ACCESS_TOKEN={access_token}\n'
    
    # Write updated content back to .env
    with open(env_path, 'w') as f:
        f.write(content)
    
    print(f"Updated {env_file} with Zerodha credentials")

def generate_token():
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Generate Zerodha access token')
    parser.add_argument('--api-key', type=str, help='Zerodha API key')
    parser.add_argument('--api-secret', type=str, help='Zerodha API secret')
    parser.add_argument('--no-update-env', action='store_true', help='Do not update .env file')
    args = parser.parse_args()
    
    # Print environment variables for debugging
    print(f"ZERODHA_API_KEY environment variable: {'Set' if os.environ.get('ZERODHA_API_KEY') else 'Not set'}")
    print(f"ZERODHA_API_SECRET environment variable: {'Set' if os.environ.get('ZERODHA_API_SECRET') else 'Not set'}")
    
    # Get API key and secret from args or environment variables
    api_key = args.api_key or os.environ.get('ZERODHA_API_KEY')
    api_secret = args.api_secret or os.environ.get('ZERODHA_API_SECRET')
    
    if not api_key:
        api_key = input("Enter your Zerodha API key: ")
    
    if not api_secret:
        api_secret = input("Enter your Zerodha API secret: ")
    
    # Initialize Kite Connect
    kite = KiteConnect(api_key=api_key)
    
    # Get login URL
    login_url = kite.login_url()
    print(f"\nPlease visit this URL to log in and obtain the request token:\n{login_url}")
    
    # Open browser automatically if possible
    try:
        webbrowser.open(login_url)
    except:
        pass
    
    # Get request token from user
    request_token = input("\nAfter logging in, enter the request token from the redirect URL: ")
    
    # Generate session
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        print("\nAccess token generated successfully!")
        print(f"\nAccess Token: {access_token}")
        
        # Update .env file if not disabled
        if not args.no_update_env:
            update_env_file(api_key, access_token)
            print("\nYour .env file has been updated with the new token!")
            print("You can now run the application with ./run_with_zerodha.sh")
        else:
            print("\nTo use this token, set these environment variables:")
            print(f"export ZERODHA_API_KEY='{api_key}'")
            print(f"export ZERODHA_ACCESS_TOKEN='{access_token}'")
        
    except Exception as e:
        print(f"\nError generating access token: {e}")
        print("Please ensure you're using the correct API key and secret.")

if __name__ == "__main__":
    generate_token() 