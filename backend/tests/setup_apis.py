#!/usr/bin/env python3
"""
Setup script for API integrations
This script helps configure the API keys and test the setup
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ env_example.txt not found")
        return False
    
    # Copy template to .env
    with open(env_example, 'r') as src, open(env_file, 'w') as dst:
        dst.write(src.read())
    
    print("✅ Created .env file from template")
    print("📝 Please edit .env and add your API keys")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'openai',
        'anthropic',
        'httpx',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def get_api_key_info():
    """Display information about getting API keys"""
    print("\n🔑 API Key Information:")
    print("=" * 50)
    
    print("\n1. Perplexity Sonar API:")
    print("   • URL: https://www.perplexity.ai/settings/api")
    print("   • Cost: Pay-per-request (~$0.01-0.05 per generation)")
    print("   • Purpose: Research agent for key concepts")
    
    print("\n2. OpenAI API:")
    print("   • URL: https://platform.openai.com/api-keys")
    print("   • Cost: Pay-per-token (~$0.01-0.03 per generation)")
    print("   • Purpose: Concept explanations and learning suggestions")
    
    print("\n3. Anthropic API (Optional):")
    print("   • URL: https://console.anthropic.com/")
    print("   • Cost: Pay-per-token (~$0.005-0.015 per generation)")
    print("   • Purpose: Fallback LLM service")

def main():
    """Main setup function"""
    print("🚀 Leo Learning Platform - API Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        sys.exit(1)
    
    # Create .env file
    print("\n📝 Setting up environment file...")
    if not create_env_file():
        print("❌ Failed to create .env file")
        sys.exit(1)
    
    # Show API key information
    get_api_key_info()
    
    print("\n🎯 Next Steps:")
    print("1. Edit .env file and add your API keys")
    print("2. Run: python test_api_integration.py")
    print("3. Start the server: python main.py")
    
    print("\n💡 Tips:")
    print("• You only need Perplexity + OpenAI for full functionality")
    print("• Anthropic is optional (used as fallback)")
    print("• The system will work with mock data if APIs are unavailable")

if __name__ == "__main__":
    main()
