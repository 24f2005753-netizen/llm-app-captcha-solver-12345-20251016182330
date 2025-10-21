"""
Example client script for testing the LLM Code Deployment API
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
SHARED_SECRET = "your_shared_secret_here"  # Replace with your actual secret

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_app_generation():
    """Test the main app generation endpoint"""
    # Generate a unique nonce
    nonce = f"test_{int(time.time())}"
    
    request_data = {
        "email": "test@example.com",
        "secret": SHARED_SECRET,
        "task": "Create a simple calculator",
        "round": 1,
        "nonce": nonce,
        "brief": "Create a basic calculator web app with addition, subtraction, multiplication, and division. Include a clean, modern interface with a display and number/operation buttons.",
        "evaluation_url": "https://httpbin.org/post",  # Test URL that echoes back requests
        "attachments": []
    }
    
    try:
        print("🚀 Sending app generation request...")
        response = requests.post(
            f"{API_BASE_URL}/api/request",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ App generation successful!")
            print(f"Repository: {result['deployment']['repo_name']}")
            print(f"Repository URL: {result['deployment']['repo_url']}")
            print(f"GitHub Pages: {result['deployment']['pages_url']}")
            print(f"Commit SHA: {result['deployment']['commit_sha']}")
            return result
        else:
            print(f"❌ App generation failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

def test_evaluation_endpoint():
    """Test the evaluation endpoint"""
    evaluation_data = {
        "email": "test@example.com",
        "task": "Create a simple calculator",
        "round": 1,
        "nonce": f"test_{int(time.time())}",
        "evaluation_data": {
            "score": 85,
            "feedback": "Good functionality, clean interface",
            "suggestions": ["Add keyboard support", "Improve mobile responsiveness"]
        }
    }
    
    try:
        print("📊 Sending evaluation data...")
        response = requests.post(
            f"{API_BASE_URL}/api/evaluate",
            json=evaluation_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Evaluation data received successfully!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Evaluation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Evaluation error: {e}")
        return False

def main():
    """Run example client tests"""
    print("🧪 LLM Code Deployment API Test Client")
    print("=" * 50)
    
    # Check if server is running
    if not test_health_check():
        print("\n❌ Server is not running or not accessible")
        print("Please start the server with: python main.py")
        return
    
    print("\n" + "=" * 50)
    
    # Test app generation
    result = test_app_generation()
    
    if result:
        print("\n" + "=" * 50)
        
        # Test evaluation endpoint
        test_evaluation_endpoint()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed!")
        
        if result.get('deployment', {}).get('pages_url'):
            print(f"\n🌐 Your generated app is available at:")
            print(f"   {result['deployment']['pages_url']}")
            print(f"\n📁 Repository: {result['deployment']['repo_url']}")
    else:
        print("\n❌ Tests failed. Please check your configuration.")

if __name__ == "__main__":
    print("⚠️  Make sure to update SHARED_SECRET in this script!")
    print("⚠️  Make sure the server is running on http://localhost:8000")
    print()
    
    # Uncomment the line below to run the tests
    # main()
    
    print("To run the tests, uncomment the main() call at the bottom of this file")
    print("and update the SHARED_SECRET variable with your actual secret.")
