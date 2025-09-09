"""
Comprehensive Test Suite for Docs-Wiki Chat API
Tests performance, model providers, and tool calling functionality
"""

import asyncio
import json
import time
import statistics
import httpx
import pytest
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"  # Change to your deployed URL for production tests
API_ENDPOINT = f"{BASE_URL}/api/chat"

# Available models from the frontend
AVAILABLE_MODELS = [
    "x-ai/grok-code-fast-1",
    "openai/gpt-5",
    "anthropic/claude-sonnet-4",
    "qwen/qwen3-coder",
    "deepseek/deepseek-chat-v3.1",
    "google/gemini-2.5-pro",
]

# Test prompts for different scenarios
TEST_PROMPTS = {
    "simple": "Hello, how are you?",
    "code_generation": "Write a Python function to calculate fibonacci numbers",
    "math_problem": "Solve this equation: 2x + 5 = 13",
    "diagram_request": "Create a flowchart showing the software development lifecycle",
    "quiz_request": "Create a quiz about Python data types",
    "rag_query": "What information do you have about machine learning?",
    "web_search": "What are the latest developments in AI in 2024?",
    "complex_reasoning": "Explain how a neural network learns and provide a simple example",
}

@dataclass
class TestResult:
    model: str
    prompt_type: str
    response_time: float
    success: bool
    error_message: Optional[str] = None
    tool_calls: List[Dict] = None
    response_length: int = 0
    first_token_time: float = 0.0

class ChatAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/chat"
        self.results: List[TestResult] = []
        
    async def test_single_request(
        self, 
        model: str, 
        prompt: str, 
        prompt_type: str,
        use_rag: bool = False,
        use_web_search: bool = False,
        top_k: int = 4
    ) -> TestResult:
        """Test a single chat request and measure performance"""
        start_time = time.time()
        first_token_time = 0.0
        response_length = 0
        tool_calls = []
        success = False
        error_message = None
        
        try:
            payload = {
                "message": prompt,
                "model": model,
                "top_k": top_k,
                "use_rag": use_rag,
                "use_web_search": use_web_search
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    self.api_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status_code != 200:
                        error_message = f"HTTP {response.status_code}: {await response.aread()}"
                        return TestResult(
                            model=model,
                            prompt_type=prompt_type,
                            response_time=time.time() - start_time,
                            success=False,
                            error_message=error_message
                        )
                    
                    first_token_received = False
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk_data = json.loads(line)
                                
                                # Measure first token time
                                if not first_token_received and "content" in chunk_data:
                                    first_token_time = time.time() - start_time
                                    first_token_received = True
                                
                                # Track tool calls
                                if "tool_call" in chunk_data:
                                    tool_calls.append(chunk_data["tool_call"])
                                
                                # Track response length
                                if "content" in chunk_data:
                                    response_length += len(chunk_data["content"])
                                elif "answer_chunk" in chunk_data:
                                    response_length += len(chunk_data["answer_chunk"])
                                    
                            except json.JSONDecodeError:
                                continue
                    
                    success = True
                    
        except Exception as e:
            error_message = str(e)
            success = False
        
        total_time = time.time() - start_time
        
        result = TestResult(
            model=model,
            prompt_type=prompt_type,
            response_time=total_time,
            success=success,
            error_message=error_message,
            tool_calls=tool_calls,
            response_length=response_length,
            first_token_time=first_token_time
        )
        
        self.results.append(result)
        return result
    
    async def test_all_models_performance(self) -> Dict[str, Any]:
        """Test performance across all available models"""
        print("🚀 Starting performance tests across all models...")
        
        # Test each model with a simple prompt
        tasks = []
        for model in AVAILABLE_MODELS:
            task = self.test_single_request(
                model=model,
                prompt=TEST_PROMPTS["simple"],
                prompt_type="simple"
            )
            tasks.append(task)
        
        # Run all tests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = [r for r in results if isinstance(r, TestResult) and r.success]
        failed_results = [r for r in results if isinstance(r, TestResult) and not r.success]
        
        if successful_results:
            response_times = [r.response_time for r in successful_results]
            first_token_times = [r.first_token_time for r in successful_results if r.first_token_time > 0]
            
            performance_stats = {
                "total_models_tested": len(AVAILABLE_MODELS),
                "successful_requests": len(successful_results),
                "failed_requests": len(failed_results),
                "average_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "average_first_token_time": statistics.mean(first_token_times) if first_token_times else 0,
                "fastest_model": min(successful_results, key=lambda x: x.response_time).model,
                "slowest_model": max(successful_results, key=lambda x: x.response_time).model,
                "failed_models": [r.model for r in failed_results]
            }
        else:
            performance_stats = {
                "total_models_tested": len(AVAILABLE_MODELS),
                "successful_requests": 0,
                "failed_requests": len(failed_results),
                "error": "All requests failed"
            }
        
        return performance_stats
    
    async def test_tool_calling(self) -> Dict[str, Any]:
        """Test tool calling functionality across different models"""
        print("🔧 Testing tool calling functionality...")
        
        tool_tests = [
            ("code_generation", TEST_PROMPTS["code_generation"]),
            ("math_problem", TEST_PROMPTS["math_problem"]),
            ("diagram_request", TEST_PROMPTS["diagram_request"]),
            ("quiz_request", TEST_PROMPTS["quiz_request"]),
        ]
        
        tool_results = {}
        
        for prompt_type, prompt in tool_tests:
            print(f"  Testing {prompt_type}...")
            
            # Test with a few different models
            test_models = ["openai/gpt-5", "anthropic/claude-sonnet-4", "deepseek/deepseek-chat-v3.1", "google/gemini-2.5-pro"]
            
            for model in test_models:
                result = await self.test_single_request(
                    model=model,
                    prompt=prompt,
                    prompt_type=prompt_type
                )
                
                if result.success and result.tool_calls:
                    tool_name = prompt_type
                    if tool_name not in tool_results:
                        tool_results[tool_name] = {
                            "total_tests": 0,
                            "successful_tool_calls": 0,
                            "models_that_used_tools": [],
                            "average_response_time": 0,
                            "response_times": []
                        }
                    
                    tool_results[tool_name]["total_tests"] += 1
                    tool_results[tool_name]["successful_tool_calls"] += 1
                    tool_results[tool_name]["models_that_used_tools"].append(model)
                    tool_results[tool_name]["response_times"].append(result.response_time)
        
        # Calculate averages
        for tool_name in tool_results:
            if tool_results[tool_name]["response_times"]:
                tool_results[tool_name]["average_response_time"] = statistics.mean(
                    tool_results[tool_name]["response_times"]
                )
        
        return tool_results
    
    async def test_rag_functionality(self) -> Dict[str, Any]:
        """Test RAG (Retrieval Augmented Generation) functionality"""
        print("📚 Testing RAG functionality...")
        
        rag_tests = [
            ("rag_query", TEST_PROMPTS["rag_query"], True, False),
            ("web_search", TEST_PROMPTS["web_search"], False, True),
            ("complex_reasoning", TEST_PROMPTS["complex_reasoning"], False, False),
        ]
        
        rag_results = {}
        
        for test_name, prompt, use_rag, use_web_search in rag_tests:
            print(f"  Testing {test_name} (RAG: {use_rag}, Web: {use_web_search})...")
            
            result = await self.test_single_request(
                model="openai/gpt-5",  # Use a reliable model for RAG tests
                prompt=prompt,
                prompt_type=test_name,
                use_rag=use_rag,
                use_web_search=use_web_search
            )
            
            rag_results[test_name] = {
                "success": result.success,
                "response_time": result.response_time,
                "response_length": result.response_length,
                "tool_calls": len(result.tool_calls) if result.tool_calls else 0,
                "error": result.error_message
            }
        
        return rag_results
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        print("🧪 Starting comprehensive chat API tests...")
        print(f"Testing endpoint: {self.api_endpoint}")
        print(f"Available models: {', '.join(AVAILABLE_MODELS)}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test suites
        performance_results = await self.test_all_models_performance()
        tool_results = await self.test_tool_calling()
        rag_results = await self.test_rag_functionality()
        
        total_time = time.time() - start_time
        
        # Compile comprehensive results
        comprehensive_results = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "endpoint": self.api_endpoint,
                "total_test_duration": total_time,
                "models_tested": AVAILABLE_MODELS
            },
            "performance": performance_results,
            "tool_calling": tool_results,
            "rag_functionality": rag_results,
            "summary": {
                "total_tests_run": len(self.results),
                "successful_tests": len([r for r in self.results if r.success]),
                "failed_tests": len([r for r in self.results if not r.success]),
                "overall_success_rate": len([r for r in self.results if r.success]) / len(self.results) if self.results else 0
            }
        }
        
        return comprehensive_results
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        # Performance Summary
        perf = results["performance"]
        print(f"\n🚀 PERFORMANCE SUMMARY:")
        print(f"  Models tested: {perf.get('total_models_tested', 0)}")
        print(f"  Successful requests: {perf.get('successful_requests', 0)}")
        print(f"  Failed requests: {perf.get('failed_requests', 0)}")
        
        if perf.get('successful_requests', 0) > 0:
            print(f"  Average response time: {perf.get('average_response_time', 0):.2f}s")
            print(f"  Median response time: {perf.get('median_response_time', 0):.2f}s")
            print(f"  Fastest model: {perf.get('fastest_model', 'N/A')}")
            print(f"  Slowest model: {perf.get('slowest_model', 'N/A')}")
        
        # Tool Calling Summary
        print(f"\n🔧 TOOL CALLING SUMMARY:")
        for tool_name, tool_data in results["tool_calling"].items():
            success_rate = (tool_data["successful_tool_calls"] / tool_data["total_tests"]) * 100 if tool_data["total_tests"] > 0 else 0
            print(f"  {tool_name}: {tool_data['successful_tool_calls']}/{tool_data['total_tests']} ({success_rate:.1f}%)")
            if tool_data["models_that_used_tools"]:
                print(f"    Models using tools: {', '.join(tool_data['models_that_used_tools'])}")
        
        # RAG Summary
        print(f"\n📚 RAG FUNCTIONALITY SUMMARY:")
        for test_name, test_data in results["rag_functionality"].items():
            status = "✅" if test_data["success"] else "❌"
            print(f"  {test_name}: {status} ({test_data['response_time']:.2f}s)")
            if test_data["tool_calls"] > 0:
                print(f"    Tool calls made: {test_data['tool_calls']}")
        
        # Overall Summary
        summary = results["summary"]
        print(f"\n📈 OVERALL SUMMARY:")
        print(f"  Total tests: {summary['total_tests_run']}")
        print(f"  Success rate: {summary['overall_success_rate']:.1%}")
        print(f"  Test duration: {results['test_metadata']['total_test_duration']:.2f}s")

# Test runner functions
async def run_performance_tests():
    """Run performance tests only"""
    tester = ChatAPITester()
    results = await tester.test_all_models_performance()
    tester.print_results({"performance": results, "tool_calling": {}, "rag_functionality": {}})
    return results

async def run_tool_calling_tests():
    """Run tool calling tests only"""
    tester = ChatAPITester()
    results = await tester.test_tool_calling()
    print("\n🔧 Tool Calling Results:")
    for tool, data in results.items():
        print(f"  {tool}: {data['successful_tool_calls']}/{data['total_tests']} successful")
    return results

async def run_rag_tests():
    """Run RAG tests only"""
    tester = ChatAPITester()
    results = await tester.test_rag_functionality()
    print("\n📚 RAG Results:")
    for test, data in results.items():
        status = "✅" if data["success"] else "❌"
        print(f"  {test}: {status}")
    return results

async def run_all_tests():
    """Run all comprehensive tests"""
    tester = ChatAPITester()
    results = await tester.run_comprehensive_tests()
    tester.print_results(results)
    return results

# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "performance":
            asyncio.run(run_performance_tests())
        elif test_type == "tools":
            asyncio.run(run_tool_calling_tests())
        elif test_type == "rag":
            asyncio.run(run_rag_tests())
        elif test_type == "all":
            asyncio.run(run_all_tests())
        else:
            print("Usage: python test_suite1.py [performance|tools|rag|all]")
    else:
        print("Running all tests...")
        asyncio.run(run_all_tests())
