#!/usr/bin/env python
"""
Script to test the Anthropic API key.
"""

import os
import sys
import anthropic
from dotenv import load_dotenv

def test_anthropic_api():
    """Test the Anthropic API key."""
    # Load .env file
    load_dotenv()
    
    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        sys.exit(1)
    
    # Print first 10 chars of the API key (for debugging)
    print(f"Using API key: {api_key[:10]}...")
    
    try:
        # Create Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test message
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Hello, can you give me a quick test response?"}
            ]
        )
        
        # Print response
        print("\nAPI TEST SUCCESSFUL! Got response:")
        print(message.content[0].text)
        
        return True
    except Exception as e:
        print(f"\nAPI TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    test_anthropic_api() 