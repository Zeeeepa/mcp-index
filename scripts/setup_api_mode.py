#!/usr/bin/env python
"""
Setup API Mode
Main script to set up and test API embedding mode
"""

import os
import sys
import importlib.util
import subprocess

def run_script(script_name):
    """Run another script and return its module"""
    script_path = os.path.join("scripts", f"{script_name}.py")
    
    if not os.path.exists(script_path):
        print(f"❌ Error: Script {script_path} not found")
        return None
    
    # Import the script as a module
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module

def main():
    print("=== Setting Up API Embedding Mode ===\n")
    
    # Step 1: Update .env file
    print("Step 1: Updating .env file")
    env_updater = run_script("update_env")
    if env_updater:
        env_updater.update_env_file()
    print()
    
    # Step 2: Create batch file
    print("Step 2: Creating API batch file")
    bat_creator = run_script("create_api_bat")
    if bat_creator:
        bat_creator.create_batch_file()
    print()
    
    # Step 3: Check configuration
    print("Step 3: Checking API configuration")
    config_checker = run_script("check_api_config")
    if config_checker:
        config_ok = config_checker.check_config()
    else:
        config_ok = False
    print()
    
    # Step 4: Test API if config is OK
    if config_ok:
        print("Step 4: Testing API connection")
        api_tester = run_script("test_api")
        if api_tester:
            api_ok = api_tester.test_connection()
        else:
            api_ok = False
    else:
        print("Step 4: Skipping API test (configuration incomplete)")
        api_ok = False
    print()
    
    # Print summary
    print("=== Setup Summary ===")
    print(f"Configuration: {'✓ OK' if config_ok else '❌ Incomplete'}")
    if config_ok:
        print(f"API Connection: {'✓ OK' if api_ok else '❌ Failed'}")
    
    print("\n=== Next Steps ===")
    if not config_ok:
        print("1. Update your .env file with the required variables")
        print("2. Run this script again to test the configuration")
    elif not api_ok:
        print("1. Check your API credentials and connection")
        print("2. Run scripts/test_api.py to test the API directly")
    else:
        print("1. Run the server with API embeddings: run_api_mode.bat")
        print("2. Test the server with: python scripts/test_full.py")

if __name__ == "__main__":
    main() 