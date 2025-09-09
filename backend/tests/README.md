# Chat API Test Suite

Comprehensive test suite for the Docs-Wiki Chat API that tests performance, model providers, and tool calling functionality.

## Overview

This test suite provides:
- **Performance Testing**: Measure response times across all available models
- **Model Testing**: Test all 6 available model providers
- **Tool Calling Testing**: Verify tool calling functionality (code, math, diagrams, quizzes)
- **RAG Testing**: Test Retrieval Augmented Generation functionality
- **Web Search Testing**: Test web search capabilities

## Available Models

The test suite tests all models available in the frontend:
- `x-ai/grok-code-fast-1`
- `openai/gpt-5`
- `anthropic/claude-sonnet-4`
- `qwen/qwen3-coder`
- `deepseek/deepseek-chat-v3.1`
- `google/gemini-2.5-pro`

## Test Types

### 1. Performance Tests
- Tests all models with simple prompts
- Measures response times, first token times
- Identifies fastest and slowest models
- Provides statistical analysis

### 2. Tool Calling Tests
Tests the following tool calling capabilities:
- **Code Generation**: Python, JavaScript, SQL, etc.
- **Math Problems**: Equations, derivatives, calculations
- **Diagrams**: Flowcharts, class diagrams, sequence diagrams
- **Quizzes**: Multiple choice questions with explanations

### 3. RAG Tests
- Tests document retrieval and context usage
- Tests web search functionality
- Tests complex reasoning with context

## Quick Start

### Prerequisites
1. Make sure your backend is running on `http://localhost:8000`
2. Install required dependencies:
   ```bash
   pip install httpx asyncio
   ```

### Running Tests

#### Run All Tests
```bash
python run_tests.py all
```

#### Run Specific Test Types
```bash
# Performance tests only
python run_tests.py performance

# Tool calling tests only
python run_tests.py tools

# RAG tests only
python run_tests.py rag
```

#### Test Different API Endpoint
```bash
python run_tests.py all --url https://your-api.com
```

#### Run Without Saving Reports
```bash
python run_tests.py all --no-save
```

#### Quick Summary Only
```bash
python run_tests.py all --quick
```

### Direct Test Suite Usage

You can also run tests directly using the test suite:

```python
import asyncio
from test_suite1 import run_all_tests

# Run all tests
results = asyncio.run(run_all_tests())
```

## Test Configuration

### Performance Thresholds
- **Fast**: ≤ 5 seconds
- **Acceptable**: ≤ 15 seconds
- **Slow**: ≤ 30 seconds
- **Very Slow**: > 30 seconds

### Success Rates
- **Tool Calling**: ≥ 70% success rate
- **RAG Functionality**: ≥ 80% success rate
- **Overall**: ≥ 80% success rate

## Output and Reports

### Console Output
The test suite provides detailed console output including:
- Real-time test progress
- Performance metrics
- Success/failure rates
- Model comparisons

### Generated Files
- **JSON Results**: `test_results_{type}_{timestamp}.json`
- **HTML Report**: `test_report_{type}_{timestamp}.html`

### Sample Output
```
🚀 Starting performance tests across all models...
  Testing openai/gpt-5...
  Testing anthropic/claude-sonnet-4...
  ...

📊 COMPREHENSIVE TEST RESULTS
============================================================

🚀 PERFORMANCE SUMMARY:
  Models tested: 6
  Successful requests: 6
  Failed requests: 0
  Average response time: 3.45s
  Median response time: 3.12s
  Fastest model: openai/gpt-5
  Slowest model: google/gemini-2.5-pro

🔧 TOOL CALLING SUMMARY:
  code_generation: 3/3 (100.0%)
  math_problem: 3/3 (100.0%)
  diagram_request: 2/3 (66.7%)
  quiz_request: 3/3 (100.0%)

📚 RAG FUNCTIONALITY SUMMARY:
  rag_query: ✅ (2.34s)
  web_search: ✅ (4.56s)
  complex_reasoning: ✅ (3.21s)
```

## Test Data

The test suite includes various test prompts:

### Code Generation
- "Write a Python function to sort a list"
- "Create a JavaScript class for a bank account"
- "Generate a SQL query to find users with more than 100 orders"

### Math Problems
- "Solve the equation: 3x + 7 = 22"
- "Calculate the derivative of x^2 + 3x + 1"
- "Find the area of a circle with radius 5"

### Diagram Requests
- "Create a flowchart for user authentication"
- "Draw a class diagram for a library management system"
- "Create a sequence diagram for online shopping"

### Quiz Generation
- "Create a quiz about Python data types"
- "Make a quiz about database normalization"
- "Generate a quiz about machine learning algorithms"

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure your backend is running on the correct port
   - Check the URL in the test configuration

2. **Timeout Errors**
   - Some models may take longer to respond
   - Increase timeout in test configuration if needed

3. **API Key Issues**
   - Ensure all required API keys are configured
   - Check environment variables

4. **Tool Calling Failures**
   - Some models may not support all tool calling features
   - Check model compatibility

### Debug Mode

For detailed debugging, you can modify the test configuration:

```python
# In test_suite1.py
BASE_URL = "http://localhost:8000"  # Your API URL
DEFAULT_TIMEOUT = 120.0  # Increase if needed
```

## Contributing

To add new tests:

1. Add new test prompts to `TEST_PROMPTS` in `test_suite1.py`
2. Add new test scenarios to the appropriate test methods
3. Update the test data generators in `test_utilities.py`
4. Add new metrics to the performance analyzer

## File Structure

```
tests/
├── test_suite1.py      # Main test suite
├── test_utilities.py   # Test utilities and helpers
├── run_tests.py        # Test runner script
└── README.md          # This file
```

## Dependencies

- `httpx`: For async HTTP requests
- `asyncio`: For async test execution
- `statistics`: For performance analysis
- `json`: For data serialization
- `time`: For timing measurements
- `dataclasses`: For structured data
