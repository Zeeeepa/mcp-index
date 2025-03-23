#!/usr/bin/env python
"""
Test API Connection
Tests connection to the DeepInfra API
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    print("=== Testing DeepInfra API Connection ===")
    
    api_key = os.environ.get("DEEPINFRA_API_KEY")
    if not api_key:
        print("❌ Error: DEEPINFRA_API_KEY not set")
        return False
    
    base_url = os.environ.get("EMBEDDING_BASE_URL", "https://api.deepinfra.com/v1/openai")
    model = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")
    
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    
    # Test request
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "input": ["Test embedding request"],
            "model": model
        }
        
        print("\nSending request...")
        response = requests.post(
            f"{base_url}/embeddings",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("data", [])
            
            if data and len(data) > 0:
                embedding = data[0].get("embedding", [])
                print(f"\n✅ Success! Generated embedding with {len(embedding)} dimensions")
                print(f"First 5 values: {embedding[:5]}")
                return True
            else:
                print("\n❌ Error: No embedding data returned")
                return False
        else:
            print(f"\n❌ Error: API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 