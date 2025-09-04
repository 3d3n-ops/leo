#!/usr/bin/env python3
"""
Test script for Leo AI Assistant integration
"""

import asyncio
import json
import os
from dotenv import load_dotenv
from leo_service import leo_service

# Load environment variables
load_dotenv()

async def test_leo_basic_chat():
    """Test basic Leo chat functionality"""
    print("🤖 Testing Leo AI Assistant...")
    
    # Test message
    test_message = "Hello Leo! Can you help me understand what a for loop is in Python?"
    
    print(f"📝 Test message: {test_message}")
    print("🔄 Streaming response:")
    print("-" * 50)
    
    try:
        response_chunks = []
        async for chunk in leo_service.chat_with_leo(
            message=test_message,
            model="openai/gpt-4o-mini",
            use_rag=False,
            use_web_search=False
        ):
            try:
                chunk_data = json.loads(chunk)
                if "content" in chunk_data:
                    print(chunk_data["content"], end="", flush=True)
                    response_chunks.append(chunk_data["content"])
                elif "tool_call" in chunk_data:
                    print(f"\n🔧 Tool call: {chunk_data['tool_call']['name']}")
                elif "error" in chunk_data:
                    print(f"\n❌ Error: {chunk_data['error']}")
            except json.JSONDecodeError:
                continue
        
        print("\n" + "-" * 50)
        print("✅ Basic chat test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

async def test_leo_tool_calls():
    """Test Leo's tool calling capabilities"""
    print("\n🔧 Testing Leo's tool calling capabilities...")
    
    test_messages = [
        "Write a Python function to calculate the factorial of a number",
        "Explain the quadratic formula with LaTeX formatting",
        "Create a flowchart showing the software development lifecycle",
        "Create a quiz about Python data types"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}: {message}")
        print("🔄 Response:")
        print("-" * 30)
        
        try:
            async for chunk in leo_service.chat_with_leo(
                message=message,
                model="openai/gpt-4o-mini",
                use_rag=False,
                use_web_search=False
            ):
                try:
                    chunk_data = json.loads(chunk)
                    if "content" in chunk_data:
                        print(chunk_data["content"], end="", flush=True)
                    elif "tool_call" in chunk_data:
                        tool_name = chunk_data["tool_call"]["name"]
                        print(f"\n🔧 Tool: {tool_name}")
                        if "arguments" in chunk_data["tool_call"]:
                            args = chunk_data["tool_call"]["arguments"]
                            if tool_name == "write_code":
                                print(f"   Language: {args.get('language', 'N/A')}")
                                print(f"   Code: {args.get('code', 'N/A')[:100]}...")
                            elif tool_name == "write_math":
                                print(f"   Formula: {args.get('formula', 'N/A')}")
                            elif tool_name == "write_diagrams":
                                print(f"   Diagram Type: {args.get('diagram_type', 'N/A')}")
                            elif tool_name == "write_quiz":
                                print(f"   Question: {args.get('question', 'N/A')[:50]}...")
                except json.JSONDecodeError:
                    continue
            
            print("\n" + "-" * 30)
            
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")

async def test_decision_logic():
    """Test Leo's decision logic for RAG and web search"""
    print("\n🧠 Testing Leo's decision logic...")
    
    test_cases = [
        ("What's the latest news about AI?", False, True),  # Should trigger web search
        ("What does the uploaded document say about Python?", True, False),  # Should trigger RAG
        ("Explain how to use a for loop", False, False),  # Should not trigger either
        ("What's the current version of React in 2024?", False, True),  # Should trigger web search
    ]
    
    for message, expected_rag, expected_web in test_cases:
        actual_rag = leo_service.should_use_rag(message, True)  # Assume files uploaded
        actual_web = leo_service.should_use_web_search(message)
        
        rag_status = "✅" if actual_rag == expected_rag else "❌"
        web_status = "✅" if actual_web == expected_web else "❌"
        
        print(f"📝 Message: {message}")
        print(f"   RAG: {rag_status} (expected: {expected_rag}, got: {actual_rag})")
        print(f"   Web: {web_status} (expected: {expected_web}, got: {actual_web})")
        print()

async def main():
    """Run all tests"""
    print("🚀 Starting Leo AI Assistant Integration Tests")
    print("=" * 60)
    
    # Check if OpenRouter API key is available
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  Warning: OPENROUTER_API_KEY not found in environment variables")
        print("   Some tests may fail. Please set up your .env file.")
        print()
    
    # Run tests
    await test_leo_basic_chat()
    await test_leo_tool_calls()
    await test_decision_logic()
    
    print("\n🎉 All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
