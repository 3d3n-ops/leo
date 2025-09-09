"""
Immediate performance optimizations for the chat API
These can be implemented right away for significant performance gains
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, AsyncGenerator
from functools import lru_cache
import httpx

# 1. Enhanced Caching with TTL
class FastCache:
    def __init__(self):
        self.cache = {}
        self.ttl = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str, ttl: int = 300) -> Optional[any]:
        """Get cached value with TTL"""
        if key in self.cache:
            if time.time() - self.ttl.get(key, 0) < ttl:
                self.hits += 1
                return self.cache[key]
            else:
                # Expired, remove
                del self.cache[key]
                del self.ttl[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value: any, ttl: int = 300):
        """Set cached value with TTL"""
        self.cache[key] = value
        self.ttl[key] = time.time()
    
    def stats(self) -> Dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self.cache)
        }

# Global fast cache instance
fast_cache = FastCache()

# 2. Optimized HTTP Client with Connection Pooling
class OptimizedHTTPClient:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize HTTP client with optimizations"""
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
        
        timeout = httpx.Timeout(
            connect=10.0,
            read=60.0,
            write=10.0,
            pool=5.0
        )
        
        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            http2=True,  # Enable HTTP/2 for better performance
            follow_redirects=True
        )
    
    async def close(self):
        """Close the client"""
        if self.client:
            await self.client.aclose()

# Global HTTP client
http_client = OptimizedHTTPClient()

# 3. Model-Specific Optimizations
MODEL_CONFIGS = {
    "deepseek/deepseek-chat-v3.1": {
        "max_tokens": 1500,
        "temperature": 0.6,
        "timeout": 30.0,
        "priority": "high"  # Fastest model
    },
    "openai/gpt-5": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 45.0,
        "priority": "high"
    },
    "anthropic/claude-sonnet-4": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 50.0,
        "priority": "medium"
    },
    "google/gemini-2.5-pro": {
        "max_tokens": 1500,  # Reduced for this slower model
        "temperature": 0.6,
        "timeout": 60.0,
        "priority": "low"
    },
    "qwen/qwen3-coder": {
        "max_tokens": 1800,
        "temperature": 0.6,
        "timeout": 40.0,
        "priority": "medium"
    },
    "x-ai/grok-code-fast-1": {
        "max_tokens": 1500,
        "temperature": 0.6,
        "timeout": 35.0,
        "priority": "high"
    }
}

# 4. Optimized Streaming Response
async def optimized_stream_response(
    messages: List[Dict],
    model: str,
    base_url: str = "https://openrouter.ai/api/v1/chat/completions",
    api_key: str = None
) -> AsyncGenerator[str, None]:
    """Optimized streaming response with model-specific settings"""
    
    config = MODEL_CONFIGS.get(model, MODEL_CONFIGS["openai/gpt-5"])
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"]
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://docs-wiki.vercel.app",
        "X-Title": "Docs Wiki - Leo AI Assistant"
    }
    
    try:
        async with http_client.client.stream(
            "POST",
            base_url,
            headers=headers,
            json=payload
        ) as response:
            
            if response.status_code != 200:
                error_text = await response.aread()
                yield json.dumps({"error": f"API error: {response.status_code} - {error_text.decode()}"})
                return
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    
                    if data.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            choice = chunk["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                                if content:
                                    yield json.dumps({"content": content})
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        yield json.dumps({"error": str(e)})

# 5. Parallel Task Execution
async def execute_parallel_tasks(tasks: List[tuple], max_concurrent: int = 5) -> Dict[str, any]:
    """Execute tasks in parallel with concurrency limit"""
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}
    
    async def run_with_semaphore(task_name: str, task_coro):
        async with semaphore:
            try:
                result = await asyncio.wait_for(task_coro, timeout=30.0)
                return task_name, result
            except asyncio.TimeoutError:
                return task_name, None
            except Exception as e:
                return task_name, {"error": str(e)}
    
    # Execute all tasks
    task_coroutines = [run_with_semaphore(name, coro) for name, coro in tasks]
    task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
    
    # Process results
    for result in task_results:
        if isinstance(result, tuple) and len(result) == 2:
            task_name, task_result = result
            results[task_name] = task_result
        else:
            # Handle exceptions
            results[f"error_{len(results)}"] = str(result)
    
    return results

# 6. Response Caching Decorator
def cache_response(ttl: int = 300):
    """Decorator to cache function responses"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check cache first
            cached_result = fast_cache.get(cache_key, ttl)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            fast_cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

# 7. Optimized Model Selection
def select_optimal_model(prompt: str, available_models: List[str]) -> str:
    """Select the optimal model based on prompt characteristics"""
    
    # Simple heuristics for model selection
    prompt_lower = prompt.lower()
    
    # Code-related prompts - use coding-optimized models
    if any(keyword in prompt_lower for keyword in ["code", "function", "program", "script", "algorithm"]):
        if "deepseek/deepseek-chat-v3.1" in available_models:
            return "deepseek/deepseek-chat-v3.1"
        elif "qwen/qwen3-coder" in available_models:
            return "qwen/qwen3-coder"
    
    # Math-related prompts - use reasoning models
    if any(keyword in prompt_lower for keyword in ["solve", "calculate", "equation", "math", "derivative"]):
        if "openai/gpt-5" in available_models:
            return "openai/gpt-5"
        elif "anthropic/claude-sonnet-4" in available_models:
            return "anthropic/claude-sonnet-4"
    
    # General prompts - use fastest available model
    priority_order = [
        "deepseek/deepseek-chat-v3.1",
        "openai/gpt-5", 
        "x-ai/grok-code-fast-1",
        "anthropic/claude-sonnet-4",
        "qwen/qwen3-coder",
        "google/gemini-2.5-pro"
    ]
    
    for model in priority_order:
        if model in available_models:
            return model
    
    # Fallback to first available
    return available_models[0] if available_models else "openai/gpt-5"

# 8. Performance Monitoring
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "response_times": [],
            "model_performance": {},
            "error_counts": {},
            "cache_stats": {"hits": 0, "misses": 0}
        }
    
    def record_response_time(self, model: str, response_time: float):
        """Record response time for a model"""
        self.metrics["response_times"].append(response_time)
        
        if model not in self.metrics["model_performance"]:
            self.metrics["model_performance"][model] = []
        
        self.metrics["model_performance"][model].append(response_time)
        
        # Keep only last 100 measurements per model
        if len(self.metrics["model_performance"][model]) > 100:
            self.metrics["model_performance"][model] = self.metrics["model_performance"][model][-100:]
    
    def record_error(self, model: str, error: str):
        """Record error for a model"""
        if model not in self.metrics["error_counts"]:
            self.metrics["error_counts"][model] = {}
        
        if error not in self.metrics["error_counts"][model]:
            self.metrics["error_counts"][model][error] = 0
        
        self.metrics["error_counts"][model][error] += 1
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.metrics["response_times"]:
            return {"error": "No data available"}
        
        import statistics
        
        all_times = self.metrics["response_times"]
        model_stats = {}
        
        for model, times in self.metrics["model_performance"].items():
            if times:
                model_stats[model] = {
                    "avg_response_time": statistics.mean(times),
                    "median_response_time": statistics.median(times),
                    "min_response_time": min(times),
                    "max_response_time": max(times),
                    "request_count": len(times)
                }
        
        return {
            "overall": {
                "avg_response_time": statistics.mean(all_times),
                "median_response_time": statistics.median(all_times),
                "total_requests": len(all_times)
            },
            "by_model": model_stats,
            "error_counts": self.metrics["error_counts"],
            "cache_stats": fast_cache.stats()
        }

# Global performance monitor
perf_monitor = PerformanceMonitor()

# 9. Cleanup function
async def cleanup():
    """Cleanup resources"""
    await http_client.close()

# 10. Usage example
async def example_optimized_chat():
    """Example of how to use the optimizations"""
    
    # Select optimal model
    models = ["openai/gpt-5", "deepseek/deepseek-chat-v3.1", "anthropic/claude-sonnet-4"]
    optimal_model = select_optimal_model("Write a Python function", models)
    
    # Use caching
    @cache_response(ttl=300)
    async def get_cached_response(prompt: str, model: str):
        messages = [{"role": "user", "content": prompt}]
        return await optimized_stream_response(messages, model)
    
    # Execute with monitoring
    start_time = time.time()
    try:
        response = await get_cached_response("Hello, how are you?", optimal_model)
        response_time = time.time() - start_time
        perf_monitor.record_response_time(optimal_model, response_time)
        
        # Process streaming response
        async for chunk in response:
            print(chunk)
            
    except Exception as e:
        perf_monitor.record_error(optimal_model, str(e))
        print(f"Error: {e}")
    
    # Get performance stats
    stats = perf_monitor.get_stats()
    print(f"Performance stats: {stats}")

if __name__ == "__main__":
    asyncio.run(example_optimized_chat())
