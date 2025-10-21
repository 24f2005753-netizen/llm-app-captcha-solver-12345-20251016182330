"""
Startup script for LLM Code Deployment
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please copy env.template to .env and configure your settings")
        return False
    print("✅ .env file found")
    return True

def install_dependencies():
    """Install required dependencies"""
    try:
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_setup_test():
    """Run the setup test"""
    try:
        print("🧪 Running setup test...")
        result = subprocess.run([sys.executable, "test_setup.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Setup test passed")
            return True
        else:
            print("❌ Setup test failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Setup test error: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    try:
        print("🚀 Starting LLM Code Deployment server...")
        print("Server will be available at: http://localhost:8000")
        print("API documentation: http://localhost:8000/docs")
        print("Press Ctrl+C to stop the server")
        print("-" * 50)
        
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

def main():
    """Main startup function"""
    print("🚀 LLM Code Deployment Startup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_env_file():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Run setup test
    if not run_setup_test():
        print("\n⚠️  Setup test failed, but continuing...")
        print("You may need to configure your .env file properly")
    
    print("\n" + "=" * 40)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
