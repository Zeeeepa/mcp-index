#!/usr/bin/env python
"""
Update .env File
Adds or updates API embedding configuration in .env file
"""

import os
from pathlib import Path

def update_env_file():
    print("=== Updating .env File ===")
    
    # Path to .env file
    env_path = Path(".env")
    
    # Read existing content
    existing_content = ""
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
    
    # Variables to ensure are set
    api_vars = {
        "MCP_EMBEDDING_ENGINE": "api",
        "MCP_EMBEDDING_PROVIDER": "deepinfra"
    }
    
    # Check if variables already exist
    lines = existing_content.splitlines()
    updated_lines = []
    updated_vars = set()
    
    # Update existing variables
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            updated_lines.append(line)
            continue
        
        if "=" in line:
            key, _ = line.split("=", 1)
            key = key.strip()
            
            if key in api_vars:
                updated_lines.append(f"{key}={api_vars[key]}")
                updated_vars.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add missing variables
    if updated_lines and not updated_lines[-1].strip():
        updated_lines.append("")
    else:
        updated_lines.append("")
    
    updated_lines.append("# API Embedding Configuration")
    for key, value in api_vars.items():
        if key not in updated_vars:
            updated_lines.append(f"{key}={value}")
    
    # Write updated content
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines))
    
    print(f"✓ Updated {env_path}")
    print("  API embedding configuration has been added/updated")

if __name__ == "__main__":
    update_env_file() 