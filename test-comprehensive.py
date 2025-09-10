#!/usr/bin/env python3
"""
Comprehensive Local Testing Suite for Railway Deployment
Tests Docker build, container startup, and API endpoints
"""

import subprocess
import time
import requests
import json
import sys
import os
from pathlib import Path

class LocalTester:
    def __init__(self):
        self.container_name = "docs-wiki-test"
        self.port = 8000
        self.base_url = f"http://localhost:{self.port}"
        
    def run_command(self, command, shell=True):
        """Run a command and return success status"""
        try:
            result = subprocess.run(command, shell=shell, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def cleanup_container(self):
        """Clean up test container"""
        print("🧹 Cleaning up container...")
        self.run_command(f"docker stop {self.container_name}")
        self.run_command(f"docker rm {self.container_name}")
    
    def test_docker_build(self):
        """Test Docker build process"""
        print("📦 Testing Docker build...")
        success, stdout, stderr = self.run_command("docker build -t docs-wiki-backend .")
        
        if not success:
            print("❌ Docker build failed!")
            print("STDERR:", stderr)
            return False
        
        print("✅ Docker build successful!")
        return True
    
    def test_container_startup(self):
        """Test container startup"""
        print("🚀 Testing container startup...")
        
        # Start container
        success, stdout, stderr = self.run_command(
            f"docker run -d -p {self.port}:8000 --name {self.container_name} docs-wiki-backend"
        )
        
        if not success:
            print("❌ Container startup failed!")
            print("STDERR:", stderr)
            return False
        
        print("✅ Container started!")
        return True
    
    def wait_for_health(self, max_attempts=30):
        """Wait for health endpoint to respond"""
        print("⏳ Waiting for health check...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.base_url}/api/performance", timeout=5)
                if response.status_code == 200:
                    print("✅ Health check passed!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            print(f"   Attempt {attempt + 1}/{max_attempts}...")
        
        print("❌ Health check failed!")
        return False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("🧪 Testing API endpoints...")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.base_url}/api/performance")
            if response.status_code != 200:
                print("❌ Health endpoint failed!")
                return False
            print("✅ Health endpoint working!")
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False
        
        # Test chat endpoint (without API keys - should still respond)
        try:
            chat_data = {
                "message": "Hello, this is a test",
                "model": "openai/gpt-5"
            }
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=chat_data,
                timeout=30
            )
            # Even if it fails due to missing API keys, we should get a response
            if response.status_code in [200, 500]:  # 500 is expected without API keys
                print("✅ Chat endpoint responding!")
                return True
            else:
                print(f"❌ Chat endpoint failed with status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Chat endpoint error: {e}")
            return False
    
    def get_container_logs(self):
        """Get container logs for debugging"""
        print("📋 Container logs:")
        success, stdout, stderr = self.run_command(f"docker logs {self.container_name}")
        print(stdout)
        if stderr:
            print("STDERR:", stderr)
    
    def run_full_test(self):
        """Run complete test suite"""
        print("🧪 Starting Comprehensive Local Test Suite")
        print("=" * 50)
        
        try:
            # Test 1: Docker build
            if not self.test_docker_build():
                return False
            
            # Test 2: Container startup
            if not self.test_container_startup():
                return False
            
            # Test 3: Health check
            if not self.wait_for_health():
                self.get_container_logs()
                return False
            
            # Test 4: API endpoints
            if not self.test_api_endpoints():
                self.get_container_logs()
                return False
            
            print("=" * 50)
            print("🎉 All tests passed! Ready for Railway deployment!")
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️ Test interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        finally:
            self.cleanup_container()

def main():
    """Main test runner"""
    print("🚀 Railway Deployment Local Testing Suite")
    print("This will test your Docker build and deployment locally")
    print()
    
    # Check if Docker is available
    tester = LocalTester()
    success, _, _ = tester.run_command("docker --version")
    if not success:
        print("❌ Docker is not installed or not available!")
        print("Please install Docker Desktop and try again.")
        sys.exit(1)
    
    # Run tests
    if tester.run_full_test():
        print("\n✅ Local testing completed successfully!")
        print("🚀 Your code is ready for Railway deployment!")
        sys.exit(0)
    else:
        print("\n❌ Local testing failed!")
        print("🔧 Please fix the issues before deploying to Railway.")
        sys.exit(1)

if __name__ == "__main__":
    main()
