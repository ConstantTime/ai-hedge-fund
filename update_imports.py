#!/usr/bin/env python
"""
Script to update imports in all agent files from src.tools.api to src.tools.data_source
and also fix the wrapper function imports.
"""

import os
import re
import glob

def update_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    modified = content
    changes_made = False
    
    # Check if the file imports from src.tools.api
    if 'from src.tools.api import' in content:
        # Replace direct imports
        modified = re.sub(
            r'from src\.tools\.api import (.*?)$',
            r'from src.tools.data_source import \1',
            modified,
            flags=re.MULTILINE
        )
        changes_made = True
    
    # Update wrapper imports
    wrapper_patterns = [
        (r'from src\.tools\.data_source import (\w+_wrapper)', r'from src.tools.data_source import \1'),
        (r'search_line_items_wrapper', r'search_line_items'),
        (r'get_company_news_wrapper', r'get_company_news'),
        (r'get_insider_trades_wrapper', r'get_insider_trades'),
        (r'get_market_cap_wrapper', r'get_market_cap'),
    ]
    
    for pattern, replacement in wrapper_patterns:
        if re.search(pattern, modified):
            modified = re.sub(pattern, replacement, modified)
            changes_made = True
    
    # If the content was modified, write it back
    if changes_made:
        with open(file_path, 'w') as f:
            f.write(modified)
        return True
    
    return False

def main():
    # Get all Python files in the agents directory and their imports
    agent_files = glob.glob('src/agents/*.py')
    utils_files = glob.glob('src/utils/*.py')
    tools_files = glob.glob('src/tools/*.py')
    
    # Combine all files to check
    all_files = agent_files + utils_files + tools_files
    
    updated_files = []
    for file_path in all_files:
        if update_file(file_path):
            updated_files.append(os.path.basename(file_path))
    
    print(f"Updated {len(updated_files)} files:")
    for file in updated_files:
        print(f"- {file}")

if __name__ == '__main__':
    main() 