"""
Test configuration for the Chat API test suite
"""

# API Configuration
DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_API_ENDPOINT = f"{DEFAULT_BASE_URL}/api/chat"

# Test Configuration
DEFAULT_TIMEOUT = 120.0
DEFAULT_TOP_K = 4
MAX_CONCURRENT_TESTS = 5

# Performance Thresholds (in seconds)
FAST_RESPONSE_THRESHOLD = 5.0
ACCEPTABLE_RESPONSE_THRESHOLD = 15.0
SLOW_RESPONSE_THRESHOLD = 30.0

# Success Rate Thresholds
MIN_TOOL_CALL_SUCCESS_RATE = 0.7  # 70%
MIN_RAG_SUCCESS_RATE = 0.8  # 80%
MIN_OVERALL_SUCCESS_RATE = 0.8  # 80%

# Available Models (from frontend model-selector.tsx)
AVAILABLE_MODELS = [
    "x-ai/grok-code-fast-1",
    "openai/gpt-5",
    "anthropic/claude-sonnet-4",
    "qwen/qwen3-coder",
    "deepseek/deepseek-chat-v3.1",
    "google/gemini-2.5-pro",
]

# Test Prompts by Category
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

# Tool Call Test Prompts
TOOL_CALL_PROMPTS = {
    "write_code": [
        "Write a Python function to sort a list",
        "Create a JavaScript class for a bank account",
        "Generate a SQL query to find users with more than 100 orders",
        "Write a recursive function to calculate factorial",
        "Create a React component for a todo list",
    ],
    "write_math": [
        "Solve the equation: 3x + 7 = 22",
        "Calculate the derivative of x^2 + 3x + 1",
        "Find the area of a circle with radius 5",
        "Solve this quadratic equation: x^2 - 5x + 6 = 0",
        "Calculate the compound interest for $1000 at 5% for 3 years",
    ],
    "write_diagrams": [
        "Create a flowchart for user authentication",
        "Draw a class diagram for a library management system",
        "Create a sequence diagram for online shopping",
        "Make a flowchart for sorting algorithms",
        "Draw a network topology diagram",
    ],
    "write_quiz": [
        "Create a quiz about Python data types",
        "Make a quiz about database normalization",
        "Generate a quiz about machine learning algorithms",
        "Create a quiz about web development",
        "Make a quiz about data structures",
    ],
}

# RAG Test Scenarios
RAG_TEST_SCENARIOS = [
    {
        "name": "rag_query",
        "prompt": "What information do you have about machine learning?",
        "use_rag": True,
        "use_web_search": False,
    },
    {
        "name": "web_search",
        "prompt": "What are the latest developments in AI in 2024?",
        "use_rag": False,
        "use_web_search": True,
    },
    {
        "name": "complex_reasoning",
        "prompt": "Explain how a neural network learns and provide a simple example",
        "use_rag": False,
        "use_web_search": False,
    },
]

# Report Configuration
REPORT_FORMATS = ["json", "html", "txt"]
DEFAULT_REPORT_FORMAT = "html"

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0
RETRY_BACKOFF_MULTIPLIER = 2.0

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Output Configuration
SAVE_RESULTS = True
RESULTS_DIR = "test_results"
REPORTS_DIR = "test_reports"

# Model-specific configurations
MODEL_CONFIGS = {
    "openai/gpt-5": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 60.0,
    },
    "anthropic/claude-sonnet-4": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 60.0,
    },
    "deepseek/deepseek-chat-v3.1": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 60.0,
    },
    "google/gemini-2.5-pro": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 60.0,
    },
    "qwen/qwen3-coder": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 60.0,
    },
    "x-ai/grok-code-fast-1": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 60.0,
    },
}

# Test Categories
TEST_CATEGORIES = {
    "performance": {
        "description": "Test response times and performance across all models",
        "prompts": ["simple"],
        "models": AVAILABLE_MODELS,
    },
    "tool_calling": {
        "description": "Test tool calling functionality",
        "prompts": list(TOOL_CALL_PROMPTS.keys()),
        "models": ["openai/gpt-5", "anthropic/claude-sonnet-4", "deepseek/deepseek-chat-v3.1"],
    },
    "rag": {
        "description": "Test RAG and web search functionality",
        "scenarios": RAG_TEST_SCENARIOS,
        "models": ["openai/gpt-5"],
    },
}
