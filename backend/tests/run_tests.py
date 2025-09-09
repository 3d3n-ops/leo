#!/usr/bin/env python3
"""
Test runner script for the Docs-Wiki Chat API
Provides easy command-line interface for running different test suites
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Optional, List
import time

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from test_suite1 import ChatAPITester, run_all_tests, run_performance_tests, run_tool_calling_tests, run_rag_tests
from test_utilities import TestReporter, ModelComparator, TestConfig

class TestRunner:
    """Main test runner class"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.tester = ChatAPITester(base_url)
        self.results = {}
    
    async def run_test_suite(self, test_type: str, save_report: bool = True) -> dict:
        """Run a specific test suite"""
        print(f"🚀 Starting {test_type} tests...")
        print(f"Target URL: {self.base_url}")
        print("=" * 60)
        
        start_time = time.time()
        
        if test_type == "all":
            results = await self.tester.run_comprehensive_tests()
        elif test_type == "performance":
            results = await run_performance_tests()
        elif test_type == "tools":
            results = await run_tool_calling_tests()
        elif test_type == "rag":
            results = await run_rag_tests()
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        duration = time.time() - start_time
        print(f"\n⏱️  Test suite completed in {duration:.2f} seconds")
        
        if save_report:
            self.save_results(results, test_type)
        
        return results
    
    def save_results(self, results: dict, test_type: str):
        """Save test results to files"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        json_filename = f"test_results_{test_type}_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📄 JSON results saved to: {json_filename}")
        
        # Save HTML report
        html_report = TestReporter.generate_html_report(results)
        html_filename = f"test_report_{test_type}_{timestamp}.html"
        TestReporter.save_report_to_file(html_report, html_filename)
        print(f"📊 HTML report saved to: {html_filename}")
    
    def print_quick_summary(self, results: dict):
        """Print a quick summary of results"""
        print("\n" + "=" * 40)
        print("📋 QUICK SUMMARY")
        print("=" * 40)
        
        if "summary" in results:
            summary = results["summary"]
            print(f"Total Tests: {summary.get('total_tests_run', 0)}")
            print(f"Success Rate: {summary.get('overall_success_rate', 0):.1%}")
        
        if "performance" in results:
            perf = results["performance"]
            print(f"Average Response Time: {perf.get('average_response_time', 0):.2f}s")
            print(f"Fastest Model: {perf.get('fastest_model', 'N/A')}")
        
        if "tool_calling" in results:
            tool_count = len(results["tool_calling"])
            print(f"Tool Tests: {tool_count} different tools tested")
        
        if "rag_functionality" in results:
            rag_count = len(results["rag_functionality"])
            print(f"RAG Tests: {rag_count} different scenarios tested")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run tests for the Docs-Wiki Chat API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py all                    # Run all tests
  python run_tests.py performance            # Run performance tests only
  python run_tests.py tools                  # Run tool calling tests only
  python run_tests.py rag                    # Run RAG tests only
  python run_tests.py all --url https://api.example.com  # Test different URL
  python run_tests.py performance --no-save  # Run without saving reports
        """
    )
    
    parser.add_argument(
        "test_type",
        choices=["all", "performance", "tools", "rag"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API to test (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to files"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Show only quick summary (no detailed output)"
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner(args.url)
    
    # Run the tests
    try:
        results = asyncio.run(runner.run_test_suite(
            test_type=args.test_type,
            save_report=not args.no_save
        ))
        
        if args.quick:
            runner.print_quick_summary(results)
        else:
            # Print detailed results
            if hasattr(runner.tester, 'print_results'):
                runner.tester.print_results(results)
            else:
                print(json.dumps(results, indent=2, default=str))
        
        # Exit with appropriate code
        if "summary" in results:
            success_rate = results["summary"].get("overall_success_rate", 0)
            if success_rate >= 0.8:  # 80% success rate threshold
                print("\n✅ Tests completed successfully!")
                sys.exit(0)
            else:
                print(f"\n⚠️  Tests completed with {success_rate:.1%} success rate")
                sys.exit(1)
        else:
            print("\n❌ Tests failed to complete")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
