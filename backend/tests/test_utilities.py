"""
Test utilities and helpers for the chat API test suite
"""

import asyncio
import json
import time
import statistics
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import httpx
from datetime import datetime

@dataclass
class PerformanceMetrics:
    """Data class for performance metrics"""
    response_time: float
    first_token_time: float
    response_length: int
    tokens_per_second: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class ToolCallMetrics:
    """Data class for tool calling metrics"""
    tool_name: str
    call_count: int
    success_rate: float
    average_response_time: float
    models_used: List[str]

class TestConfig:
    """Configuration class for tests"""
    
    # Default test configuration
    DEFAULT_TIMEOUT = 120.0
    DEFAULT_TOP_K = 4
    
    # Performance thresholds
    FAST_RESPONSE_THRESHOLD = 5.0  # seconds
    ACCEPTABLE_RESPONSE_THRESHOLD = 15.0  # seconds
    SLOW_RESPONSE_THRESHOLD = 30.0  # seconds
    
    # Tool calling thresholds
    MIN_TOOL_CALL_SUCCESS_RATE = 0.7  # 70%
    
    # RAG thresholds
    MIN_RAG_SUCCESS_RATE = 0.8  # 80%

class TestDataGenerator:
    """Generate test data for different scenarios"""
    
    @staticmethod
    def get_code_generation_prompts() -> List[str]:
        """Get prompts that should trigger code generation tool calls"""
        return [
            "Write a Python function to sort a list",
            "Create a JavaScript class for a bank account",
            "Generate a SQL query to find users with more than 100 orders",
            "Write a recursive function to calculate factorial",
            "Create a React component for a todo list",
        ]
    
    @staticmethod
    def get_math_prompts() -> List[str]:
        """Get prompts that should trigger math tool calls"""
        return [
            "Solve the equation: 3x + 7 = 22",
            "Calculate the derivative of x^2 + 3x + 1",
            "Find the area of a circle with radius 5",
            "Solve this quadratic equation: x^2 - 5x + 6 = 0",
            "Calculate the compound interest for $1000 at 5% for 3 years",
        ]
    
    @staticmethod
    def get_diagram_prompts() -> List[str]:
        """Get prompts that should trigger diagram tool calls"""
        return [
            "Create a flowchart for user authentication",
            "Draw a class diagram for a library management system",
            "Create a sequence diagram for online shopping",
            "Make a flowchart for sorting algorithms",
            "Draw a network topology diagram",
        ]
    
    @staticmethod
    def get_quiz_prompts() -> List[str]:
        """Get prompts that should trigger quiz tool calls"""
        return [
            "Create a quiz about Python data types",
            "Make a quiz about database normalization",
            "Generate a quiz about machine learning algorithms",
            "Create a quiz about web development",
            "Make a quiz about data structures",
        ]
    
    @staticmethod
    def get_rag_prompts() -> List[str]:
        """Get prompts that should trigger RAG functionality"""
        return [
            "What information do you have about machine learning?",
            "Summarize the uploaded documents",
            "Find information about Python programming",
            "What does the documentation say about APIs?",
            "Search for information about data structures",
        ]
    
    @staticmethod
    def get_web_search_prompts() -> List[str]:
        """Get prompts that should trigger web search"""
        return [
            "What are the latest developments in AI in 2024?",
            "Find current news about quantum computing",
            "What's the latest version of Python?",
            "Search for recent updates about React",
            "What are the current trends in machine learning?",
        ]

class PerformanceAnalyzer:
    """Analyze performance metrics and generate reports"""
    
    @staticmethod
    def analyze_response_times(results: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze response time metrics"""
        if not results:
            return {"error": "No results to analyze"}
        
        successful_results = [r for r in results if r.success]
        if not successful_results:
            return {"error": "No successful results to analyze"}
        
        response_times = [r.response_time for r in successful_results]
        first_token_times = [r.first_token_time for r in successful_results if r.first_token_time > 0]
        
        return {
            "count": len(successful_results),
            "average_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "std_deviation": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "average_first_token_time": statistics.mean(first_token_times) if first_token_times else 0,
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
            "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
        }
    
    @staticmethod
    def categorize_performance(response_time: float) -> str:
        """Categorize response time performance"""
        if response_time <= TestConfig.FAST_RESPONSE_THRESHOLD:
            return "fast"
        elif response_time <= TestConfig.ACCEPTABLE_RESPONSE_THRESHOLD:
            return "acceptable"
        elif response_time <= TestConfig.SLOW_RESPONSE_THRESHOLD:
            return "slow"
        else:
            return "very_slow"
    
    @staticmethod
    def generate_performance_report(results: List[PerformanceMetrics]) -> str:
        """Generate a human-readable performance report"""
        analysis = PerformanceAnalyzer.analyze_response_times(results)
        
        if "error" in analysis:
            return f"Performance Analysis Error: {analysis['error']}"
        
        report = f"""
Performance Analysis Report
==========================
Total Requests: {analysis['count']}
Average Response Time: {analysis['average_response_time']:.2f}s
Median Response Time: {analysis['median_response_time']:.2f}s
Min Response Time: {analysis['min_response_time']:.2f}s
Max Response Time: {analysis['max_response_time']:.2f}s
Standard Deviation: {analysis['std_deviation']:.2f}s
95th Percentile: {analysis['p95_response_time']:.2f}s
99th Percentile: {analysis['p99_response_time']:.2f}s
Average First Token Time: {analysis['average_first_token_time']:.2f}s
"""
        return report

class ToolCallAnalyzer:
    """Analyze tool calling metrics"""
    
    @staticmethod
    def analyze_tool_calls(tool_results: Dict[str, List[Dict]]) -> Dict[str, ToolCallMetrics]:
        """Analyze tool calling results"""
        metrics = {}
        
        for tool_name, calls in tool_results.items():
            if not calls:
                continue
            
            successful_calls = [call for call in calls if call.get("success", False)]
            models_used = list(set([call.get("model", "unknown") for call in calls]))
            
            metrics[tool_name] = ToolCallMetrics(
                tool_name=tool_name,
                call_count=len(calls),
                success_rate=len(successful_calls) / len(calls) if calls else 0,
                average_response_time=statistics.mean([call.get("response_time", 0) for call in calls]) if calls else 0,
                models_used=models_used
            )
        
        return metrics
    
    @staticmethod
    def generate_tool_report(metrics: Dict[str, ToolCallMetrics]) -> str:
        """Generate a tool calling report"""
        if not metrics:
            return "No tool calling data to analyze"
        
        report = "Tool Calling Analysis Report\n"
        report += "============================\n\n"
        
        for tool_name, metric in metrics.items():
            report += f"{tool_name.upper()}:\n"
            report += f"  Total Calls: {metric.call_count}\n"
            report += f"  Success Rate: {metric.success_rate:.1%}\n"
            report += f"  Average Response Time: {metric.average_response_time:.2f}s\n"
            report += f"  Models Used: {', '.join(metric.models_used)}\n"
            report += f"  Status: {'✅ PASS' if metric.success_rate >= TestConfig.MIN_TOOL_CALL_SUCCESS_RATE else '❌ FAIL'}\n\n"
        
        return report

class TestReporter:
    """Generate comprehensive test reports"""
    
    @staticmethod
    def generate_html_report(results: Dict[str, Any]) -> str:
        """Generate an HTML report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Chat API Test Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 3px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .warning {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Chat API Test Report</h1>
        <p>Generated: {timestamp}</p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <div class="metric">Total Tests: {results.get('summary', {}).get('total_tests_run', 0)}</div>
        <div class="metric">Success Rate: {results.get('summary', {}).get('overall_success_rate', 0):.1%}</div>
        <div class="metric">Duration: {results.get('test_metadata', {}).get('total_test_duration', 0):.2f}s</div>
    </div>
    
    <div class="section">
        <h2>Performance Metrics</h2>
        <div class="metric">Average Response Time: {results.get('performance', {}).get('average_response_time', 0):.2f}s</div>
        <div class="metric">Fastest Model: {results.get('performance', {}).get('fastest_model', 'N/A')}</div>
        <div class="metric">Slowest Model: {results.get('performance', {}).get('slowest_model', 'N/A')}</div>
    </div>
    
    <div class="section">
        <h2>Tool Calling Results</h2>
        <table>
            <tr><th>Tool</th><th>Success Rate</th><th>Status</th></tr>
"""
        
        for tool_name, tool_data in results.get('tool_calling', {}).items():
            success_rate = (tool_data.get('successful_tool_calls', 0) / tool_data.get('total_tests', 1)) * 100
            status = "✅ PASS" if success_rate >= TestConfig.MIN_TOOL_CALL_SUCCESS_RATE * 100 else "❌ FAIL"
            html += f"<tr><td>{tool_name}</td><td>{success_rate:.1f}%</td><td>{status}</td></tr>"
        
        html += """
        </table>
    </div>
    
    <div class="section">
        <h2>RAG Functionality</h2>
        <table>
            <tr><th>Test</th><th>Status</th><th>Response Time</th></tr>
"""
        
        for test_name, test_data in results.get('rag_functionality', {}).items():
            status = "✅ PASS" if test_data.get('success', False) else "❌ FAIL"
            html += f"<tr><td>{test_name}</td><td>{status}</td><td>{test_data.get('response_time', 0):.2f}s</td></tr>"
        
        html += """
        </table>
    </div>
</body>
</html>
"""
        return html
    
    @staticmethod
    def save_report_to_file(report: str, filename: str = None):
        """Save report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Report saved to: {filename}")

class AsyncTestRunner:
    """Async test runner with proper error handling"""
    
    @staticmethod
    async def run_with_retry(coro, max_retries: int = 3, delay: float = 1.0):
        """Run a coroutine with retry logic"""
        for attempt in range(max_retries):
            try:
                return await coro
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
    
    @staticmethod
    async def run_concurrent_tests(tasks: List, max_concurrent: int = 5):
        """Run tests concurrently with a limit"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])

class ModelComparator:
    """Compare different models across various metrics"""
    
    @staticmethod
    def compare_models(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare models across different metrics"""
        model_stats = {}
        
        for result in results:
            model = result.get('model', 'unknown')
            if model not in model_stats:
                model_stats[model] = {
                    'response_times': [],
                    'success_count': 0,
                    'total_count': 0,
                    'tool_calls': 0,
                    'error_count': 0
                }
            
            stats = model_stats[model]
            stats['total_count'] += 1
            
            if result.get('success', False):
                stats['success_count'] += 1
                stats['response_times'].append(result.get('response_time', 0))
                stats['tool_calls'] += len(result.get('tool_calls', []))
            else:
                stats['error_count'] += 1
        
        # Calculate averages and rankings
        comparison = {}
        for model, stats in model_stats.items():
            if stats['response_times']:
                avg_response_time = statistics.mean(stats['response_times'])
                success_rate = stats['success_count'] / stats['total_count']
                
                comparison[model] = {
                    'average_response_time': avg_response_time,
                    'success_rate': success_rate,
                    'total_requests': stats['total_count'],
                    'tool_calls_made': stats['tool_calls'],
                    'error_count': stats['error_count']
                }
        
        return comparison
    
    @staticmethod
    def rank_models(comparison: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """Rank models by performance"""
        # Sort by success rate first, then by response time
        ranked = sorted(
            comparison.items(),
            key=lambda x: (x[1]['success_rate'], -x[1]['average_response_time']),
            reverse=True
        )
        return ranked
