#!/usr/bin/env python
"""
Basic API Configuration Check
Checks environment variables for API embedding setup
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_config():
    print("=== API Embedding Configuration Check ===")
    
    # Important variables to check
    variables = [
        "MCP_EMBEDDING_ENGINE",
        "MCP_EMBEDDING_PROVIDER",
        "DEEPINFRA_API_KEY",
        "EMBEDDING_BASE_URL",
        "EMBEDDING_MODEL"
    ]
    
    all_set = True
    for var in variables:
        value = os.environ.get(var)
        if value:
            # Mask API keys in output
            if "API_KEY" in var:
                masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                print(f"✓ {var} = {masked}")
            else:
                print(f"✓ {var} = {value}")
        else:
            all_set = False
            print(f"✗ {var} is not set")
    
    if all_set:
        print("\n✓ All API variables are set")
    else:
        print("\n✗ Some variables are missing")
        print("  Please update your .env file with the missing variables")
    
    return all_set

if __name__ == "__main__":
    check_config() 