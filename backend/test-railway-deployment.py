#!/usr/bin/env python3
"""
Test script for Railway deployment
Tests the deployed backend to ensure everything is working correctly
"""

import requests
import json
import time
import sys

def test_railway_deployment(base_url):
    """Test the Railway deployment"""
    print(f"🧪 Testing Railway deployment at: {base_url}")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/api/performance", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Optimizations: {data.get('optimizations', {})}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Simple chat request
    print("\n2. Testing simple chat request...")
    try:
        payload = {
            "message": "Hello, how are you?",
            "model": "openai/gpt-5",
            "use_rag": False,
            "use_web_search": False
        }
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            response_time = time.time() - start_time
            print(f"✅ Chat request successful ({response_time:.2f}s)")
            
            # Check if we get streaming response
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    if chunk_count >= 3:  # Check first few chunks
                        break
            
            print(f"   Received {chunk_count} response chunks")
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chat request failed: {e}")
        return False
    
    # Test 3: Performance test
    print("\n3. Testing performance...")
    try:
        payload = {
            "message": "Write a simple Python function",
            "model": "deepseek/deepseek-chat-v3.1",
            "use_rag": False,
            "use_web_search": False
        }
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=60,
            stream=True
        )
        
        if response.status_code == 200:
            response_time = time.time() - start_time
            print(f"✅ Performance test successful ({response_time:.2f}s)")
            
            if response_time < 10:
                print("   🚀 Excellent performance!")
            elif response_time < 20:
                print("   ✅ Good performance")
            else:
                print("   ⚠️  Performance could be improved")
        else:
            print(f"❌ Performance test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Your Railway deployment is working correctly.")
    return True

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python test-railway-deployment.py <railway-url>")
        print("Example: python test-railway-deployment.py https://your-app.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🚀 Railway Deployment Test")
    print("=" * 30)
    print(f"Testing: {base_url}")
    print()
    
    success = test_railway_deployment(base_url)
    
    if success:
        print("\n✅ Deployment test completed successfully!")
        print("\n📋 Your backend is ready for production!")
        print("🔗 Share your API URL with your frontend")
        print("📊 Monitor performance at /api/performance")
    else:
        print("\n❌ Deployment test failed!")
        print("🔍 Check Railway dashboard for logs and errors")
        sys.exit(1)

if __name__ == "__main__":
    main()
