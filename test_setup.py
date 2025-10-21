"""
Simple test script to verify the LLM Code Deployment setup
"""

import os
import sys
from dotenv import load_dotenv

def test_environment_variables():
    """Test if all required environment variables are set"""
    load_dotenv()
    
    required_vars = [
        "OPENAI_API_KEY",
        "GITHUB_TOKEN", 
        "GITHUB_USERNAME",
        "SHARED_SECRET"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    else:
        print("All required environment variables are set")
        return True

def test_imports():
    """Test if all required modules can be imported"""
    try:
        import fastapi
        import uvicorn
        import openai  # Still using openai package for Groq API
        import github
        import httpx
        import pydantic
        print("All required packages are installed")
        return True
    except ImportError as e:
        print(f"Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def test_module_imports():
    """Test if our custom modules can be imported"""
    try:
        from llm_helper import LLMHelper
        from github_helper import GitHubHelper
        from deploy_helper import DeployHelper
        print("All custom modules can be imported")
        return True
    except ImportError as e:
        print(f"Error importing custom modules: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing LLM Code Deployment Setup")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_environment_variables,
        test_module_imports
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    if passed == total:
        print(f"All tests passed! ({passed}/{total})")
        print("Your LLM Code Deployment system is ready to use!")
        print("\nTo start the server, run:")
        print("python main.py")
    else:
        print(f"{passed}/{total} tests passed")
        print("Please fix the issues above before running the server")
        sys.exit(1)

if __name__ == "__main__":
    main()
