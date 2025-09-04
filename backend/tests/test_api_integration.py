#!/usr/bin/env python3
"""
Test script for API integrations
Run this to verify your API keys are working correctly
"""

import asyncio
import os
from dotenv import load_dotenv
from api_services import perplexity_service, llm_service

# Load environment variables
load_dotenv()

async def test_perplexity_integration():
    """Test Perplexity Sonar API integration"""
    print("🔍 Testing Perplexity Sonar API...")
    
    topic = "comp-sci"
    prompt = "I want to learn React hooks and state management"
    
    try:
        concepts = await perplexity_service.get_key_concepts(topic, prompt)
        print(f"✅ Retrieved {len(concepts)} concepts:")
        for i, concept in enumerate(concepts, 1):
            print(f"   {i}. {concept}")
        return True
    except Exception as e:
        print(f"❌ Perplexity API test failed: {e}")
        return False

async def test_llm_integration():
    """Test LLM API integration"""
    print("\n🤖 Testing LLM API integration...")
    
    # Test concept explanations
    test_concepts = ["React Hooks", "State Management", "Component Lifecycle"]
    topic = "comp-sci"
    prompt = "I want to learn React hooks and state management"
    
    try:
        explanations = await llm_service.generate_concept_explanations(test_concepts, topic, prompt)
        print(f"✅ Generated {len(explanations)} concept explanations:")
        for concept, explanation in explanations.items():
            print(f"   📚 {concept}: {explanation[:100]}...")
        
        # Test learning suggestions
        suggestions = await llm_service.generate_learning_suggestions(explanations, topic, prompt)
        print(f"\n✅ Generated {len(suggestions)} learning suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        return True
    except Exception as e:
        print(f"❌ LLM API test failed: {e}")
        return False

async def test_full_workflow():
    """Test the complete workflow"""
    print("\n🚀 Testing complete workflow...")
    
    topic = "swe"
    prompt = "I want to learn about microservices architecture"
    
    try:
        # Step 1: Get concepts from Perplexity
        print("Step 1: Getting key concepts...")
        concepts = await perplexity_service.get_key_concepts(topic, prompt)
        print(f"   Retrieved {len(concepts)} concepts")
        
        # Step 2: Generate explanations
        print("Step 2: Generating explanations...")
        explanations = await llm_service.generate_concept_explanations(concepts, topic, prompt)
        print(f"   Generated {len(explanations)} explanations")
        
        # Step 3: Generate suggestions
        print("Step 3: Generating learning suggestions...")
        suggestions = await llm_service.generate_learning_suggestions(explanations, topic, prompt)
        print(f"   Generated {len(suggestions)} suggestions")
        
        print("\n✅ Complete workflow test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Complete workflow test failed: {e}")
        return False

def check_api_keys():
    """Check if API keys are configured"""
    print("🔑 Checking API key configuration...")
    
    keys_status = {
        "PERPLEXITY_API_KEY": bool(os.getenv("PERPLEXITY_API_KEY")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY"))
    }
    
    for key, configured in keys_status.items():
        status = "✅" if configured else "❌"
        print(f"   {status} {key}: {'Configured' if configured else 'Not configured'}")
    
    return keys_status

async def main():
    """Run all tests"""
    print("🧪 Leo Learning Platform - API Integration Tests\n")
    
    # Check API keys
    keys_status = check_api_keys()
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    # Test Perplexity if key is available
    if keys_status["PERPLEXITY_API_KEY"]:
        if await test_perplexity_integration():
            tests_passed += 1
    else:
        print("⚠️  Skipping Perplexity test (no API key)")
    
    # Test LLM if any key is available
    if keys_status["OPENAI_API_KEY"] or keys_status["ANTHROPIC_API_KEY"]:
        if await test_llm_integration():
            tests_passed += 1
    else:
        print("⚠️  Skipping LLM test (no API keys)")
    
    # Test full workflow if both are available
    if keys_status["PERPLEXITY_API_KEY"] and (keys_status["OPENAI_API_KEY"] or keys_status["ANTHROPIC_API_KEY"]):
        if await test_full_workflow():
            tests_passed += 1
    else:
        print("⚠️  Skipping full workflow test (missing API keys)")
    
    # Summary
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Your API integrations are working correctly.")
    elif tests_passed > 0:
        print("⚠️  Some tests passed. Check the failed tests above.")
    else:
        print("❌ No tests passed. Please check your API key configuration.")
        print("\n💡 Setup instructions:")
        print("   1. Copy env_example.txt to .env")
        print("   2. Add your API keys to .env")
        print("   3. Run this test again")

if __name__ == "__main__":
    asyncio.run(main())
