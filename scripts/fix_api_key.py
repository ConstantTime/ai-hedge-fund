#!/usr/bin/env python
"""
Script to fix the Anthropic API key in the .env file.
"""

import os
import re
from pathlib import Path

def fix_api_key():
    """Fix the Anthropic API key in the .env file."""
    # Define the .env file path
    env_path = Path(".env")
    
    if not env_path.exists():
        print("Error: .env file not found.")
        return False
    
    # Read the .env file
    with open(env_path, "r") as f:
        content = f.read()
    
    # Extract the Anthropic API key
    api_key_match = re.search(r'ANTHROPIC_API_KEY=(sk-ant-api[^\n]+)', content, re.DOTALL)
    
    if not api_key_match:
        print("Error: Could not find ANTHROPIC_API_KEY in .env file.")
        return False
    
    # Get the API key with all line breaks removed
    original_key = api_key_match.group(1)
    fixed_key = original_key.replace("\n", "")
    
    # Replace the API key in the content
    new_content = content.replace(original_key, fixed_key)
    
    # Write the updated content back to the .env file
    with open(env_path, "w") as f:
        f.write(new_content)
    
    # Print the result
    print(f"Fixed API key in .env file.")
    print(f"Original length: {len(original_key)}, Fixed length: {len(fixed_key)}")
    
    return True

if __name__ == "__main__":
    fix_api_key() 