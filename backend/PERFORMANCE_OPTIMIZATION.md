# Performance Optimization Guide for Docs-Wiki Chat API

## Current Performance Analysis

Based on test results from 2025-09-09:
- **Average Response Time**: 13.76s (Target: <5s)
- **Fastest Model**: deepseek/deepseek-chat-v3.1
- **Slowest Model**: google/gemini-2.5-pro
- **RAG Query**: 26.24s (Very slow)
- **Web Search**: 30.78s (Very slow)
- **Complex Reasoning**: 42.09s (Extremely slow)

## 🚀 Code-Level Optimizations

### 1. Streaming Response Optimizations

#### Current Issues:
- Tool calls use non-streaming approach
- RAG and web search are blocking operations
- No response caching

#### Solutions:

```python
# In leo_service.py - Optimize tool call handling
async def _handle_tool_calls_streaming(self, message: Dict, use_rag: bool, use_web_search: bool, rag_documents: Optional[List[Dict]]) -> AsyncGenerator[str, None]:
    """Handle tool calls with streaming for better perceived performance"""
    if "tool_calls" not in message:
        return
    
    for tool_call in message["tool_calls"]:
        function_name = tool_call.get("function", {}).get("name")
        function_args = tool_call.get("function", {}).get("arguments", "{}")
        
        # Stream tool call start immediately
        yield json.dumps({
            "tool_call_start": {
                "name": function_name,
                "status": "processing"
            }
        })
        
        # Process tool call asynchronously
        if function_name == "use_rag_search" and use_rag and rag_documents:
            # Stream RAG results as they come
            async for chunk in self._stream_rag_search(function_args, rag_documents):
                yield chunk
        elif function_name == "use_web_search" and use_web_search:
            # Stream web search results
            async for chunk in self._stream_web_search(function_args):
                yield chunk
        else:
            # Handle other tool calls normally
            yield json.dumps({
                "tool_call": {
                    "name": function_name,
                    "arguments": function_args
                }
            })
```

### 2. Parallel Processing Optimizations

#### Current Issues:
- RAG and web search are sequential
- No concurrent tool execution
- Blocking LLM calls

#### Solutions:

```python
# In main.py - Enhanced parallel processing
async def chat_optimized(request: ChatRequest):
    """Optimized chat endpoint with better parallel processing"""
    
    # Start all operations in parallel
    parallel_tasks = []
    
    # 1. Leo decisions (fast, local)
    decision_task = asyncio.create_task(_get_leo_decisions(request.message, request.use_rag, request.use_web_search))
    parallel_tasks.append(("decisions", decision_task))
    
    # 2. RAG retrieval (if needed)
    if request.use_rag:
        rag_task = asyncio.create_task(_retrieve_rag_documents(request.message, request.top_k))
        parallel_tasks.append(("rag", rag_task))
    
    # 3. Web search (if needed) - start early
    if request.use_web_search:
        web_task = asyncio.create_task(_start_web_search(request.message))
        parallel_tasks.append(("web", web_task))
    
    # 4. Pre-warm model (if possible)
    model_warmup_task = asyncio.create_task(_warmup_model(request.model))
    parallel_tasks.append(("warmup", model_warmup_task))
    
    # Wait for critical tasks first
    critical_results = {}
    for task_name, task in parallel_tasks[:2]:  # decisions and rag
        try:
            critical_results[task_name] = await asyncio.wait_for(task, timeout=2.0)
        except asyncio.TimeoutError:
            critical_results[task_name] = None
    
    # Start streaming response immediately
    async def stream_generator():
        # Stream initial response
        yield json.dumps({"status": "processing", "message": "Analyzing your request..."})
        
        # Get remaining results as they complete
        for task_name, task in parallel_tasks[2:]:
            try:
                result = await asyncio.wait_for(task, timeout=10.0)
                critical_results[task_name] = result
            except asyncio.TimeoutError:
                critical_results[task_name] = None
        
        # Stream main response
        async for chunk in leo_service.chat_with_leo_optimized(
            message=request.message,
            model=request.model,
            rag_documents=critical_results.get("rag", []),
            use_rag=critical_results.get("decisions", {}).get("use_rag", False),
            use_web_search=critical_results.get("decisions", {}).get("use_web_search", False)
        ):
            yield chunk
    
    return StreamingResponse(stream_generator(), media_type="application/json")
```

### 3. Caching Optimizations

```python
# In cache_manager.py - Enhanced caching
class EnhancedCacheManager:
    def __init__(self):
        self.response_cache = {}  # Full response cache
        self.embedding_cache = {}  # Embedding cache
        self.model_cache = {}  # Model-specific cache
        self.ttl_cache = {}  # TTL tracking
    
    async def get_cached_response(self, key: str, ttl: int = 300) -> Optional[str]:
        """Get cached response with TTL"""
        if key in self.response_cache:
            if time.time() - self.ttl_cache.get(key, 0) < ttl:
                return self.response_cache[key]
            else:
                # Expired, remove
                del self.response_cache[key]
                del self.ttl_cache[key]
        return None
    
    async def cache_response(self, key: str, response: str, ttl: int = 300):
        """Cache response with TTL"""
        self.response_cache[key] = response
        self.ttl_cache[key] = time.time()
    
    async def get_cached_embeddings(self, text: str) -> Optional[List[float]]:
        """Get cached embeddings"""
        return self.embedding_cache.get(text)
    
    async def cache_embeddings(self, text: str, embeddings: List[float]):
        """Cache embeddings"""
        self.embedding_cache[text] = embeddings
```

### 4. Model-Specific Optimizations

```python
# In leo_service.py - Model-specific optimizations
MODEL_OPTIMIZATIONS = {
    "deepseek/deepseek-chat-v3.1": {
        "max_tokens": 1500,  # Reduce for faster response
        "temperature": 0.6,  # Lower for consistency
        "timeout": 30.0,     # Shorter timeout
        "stream_chunk_size": 50  # Smaller chunks for faster streaming
    },
    "openai/gpt-5": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 45.0,
        "stream_chunk_size": 100
    },
    "google/gemini-2.5-pro": {
        "max_tokens": 1500,  # Reduce for this slower model
        "temperature": 0.6,
        "timeout": 60.0,
        "stream_chunk_size": 75
    }
}

async def _optimized_stream_chat_response(self, messages: List[Dict], model: str) -> AsyncGenerator[str, None]:
    """Optimized streaming with model-specific settings"""
    optimizations = MODEL_OPTIMIZATIONS.get(model, {})
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": optimizations.get("temperature", 0.7),
        "max_tokens": optimizations.get("max_tokens", 2000)
    }
    
    # Use optimized timeout
    timeout = optimizations.get("timeout", 60.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        # ... streaming implementation with optimizations
```

## ☁️ Cloud Deployment Optimizations

### 1. Render-Specific Optimizations

#### render.yaml Updates:
```yaml
services:
  - type: web
    name: docs-wiki-backend
    env: python
    region: oregon
    plan: starter
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt
      playwright install --with-deps
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: WORKERS
        value: 2
      - key: WORKER_CONNECTIONS
        value: 1000
      - key: MAX_REQUESTS
        value: 1000
      - key: MAX_REQUESTS_JITTER
        value: 100
    healthCheckPath: /api/performance
    scaling:
      minInstances: 1
      maxInstances: 3
      targetCPUPercent: 70
```

### 2. Database and Vector Store Optimizations

```python
# In vector_store.py - Connection pooling
class OptimizedVectorStoreManager:
    def __init__(self, index_name: str = "docs-wiki-index"):
        self.index_name = index_name
        self.connection_pool = None
        self._initialize_connection_pool()
    
    def _initialize_connection_pool(self):
        """Initialize connection pool for better performance"""
        # Use connection pooling for Pinecone
        self.connection_pool = pinecone.Pinecone(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT"),
            pool_connections=10,  # Connection pool size
            pool_maxsize=20,     # Max connections
            max_retries=3,       # Retry failed requests
            timeout=30.0         # Connection timeout
        )
    
    async def optimized_search(self, query: str, top_k: int = 4, namespace: str = "default_docs"):
        """Optimized search with caching and connection pooling"""
        # Check cache first
        cache_key = f"search:{hash(query)}:{top_k}:{namespace}"
        cached_result = await cache_manager.get_cached_response(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        # Perform search with connection pool
        try:
            result = await self.connection_pool.query(
                vector=await self._get_query_embedding(query),
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
            
            # Cache result
            await cache_manager.cache_response(cache_key, json.dumps(result), ttl=300)
            return result
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
```

### 3. CDN and Caching Strategy

```python
# In main.py - Add caching headers
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cache import CacheMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CacheMiddleware,
    cache_control="public, max-age=300",  # 5 minutes
    vary_headers=["Accept-Encoding"]
)

@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add caching headers for static responses
    if request.url.path.startswith("/api/performance"):
        response.headers["Cache-Control"] = "public, max-age=60"
    elif request.url.path.startswith("/api/chat"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    return response
```

### 4. Load Balancing and Scaling

```yaml
# docker-compose.yml for local development
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - WORKERS=2
      - WORKER_CONNECTIONS=1000
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/performance"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📊 Performance Monitoring

### 1. Enhanced Performance Endpoint

```python
# In main.py - Enhanced performance monitoring
@app.get("/api/performance")
async def get_performance_stats():
    """Enhanced performance statistics"""
    try:
        cache_stats = cache_manager.stats()
        
        # Get system metrics
        import psutil
        system_stats = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "active_connections": len(asyncio.all_tasks())
        }
        
        # Get model performance stats
        model_stats = {}
        for model in AVAILABLE_MODELS:
            model_stats[model] = {
                "avg_response_time": await get_model_avg_response_time(model),
                "success_rate": await get_model_success_rate(model),
                "last_used": await get_model_last_used(model)
            }
        
        return {
            "cache_stats": cache_stats,
            "system_stats": system_stats,
            "model_stats": model_stats,
            "status": "healthy",
            "optimizations": {
                "parallel_processing": "enabled",
                "caching": "enabled",
                "connection_pooling": "enabled",
                "streaming": "optimized"
            }
        }
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return {"error": str(e)}
```

### 2. Real-time Performance Dashboard

```python
# In main.py - WebSocket for real-time monitoring
@app.websocket("/ws/performance")
async def websocket_performance(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        try:
            # Send performance metrics every 5 seconds
            stats = await get_performance_stats()
            await websocket.send_json(stats)
            await asyncio.sleep(5)
        except WebSocketDisconnect:
            break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            break
```

## 🎯 Expected Performance Improvements

### Target Metrics:
- **Average Response Time**: <5s (from 13.76s)
- **RAG Query**: <10s (from 26.24s)
- **Web Search**: <15s (from 30.78s)
- **Complex Reasoning**: <20s (from 42.09s)
- **First Token Time**: <2s

### Implementation Priority:
1. **High Priority**: Streaming optimizations, parallel processing
2. **Medium Priority**: Caching, connection pooling
3. **Low Priority**: CDN, advanced monitoring

### Monitoring:
- Set up alerts for response times >10s
- Monitor cache hit rates
- Track model performance trends
- Monitor error rates and retry patterns

## 🚀 Quick Wins (Immediate Implementation)

1. **Enable Gzip compression** (5-10% improvement)
2. **Add response caching** (20-30% improvement for repeated queries)
3. **Optimize model timeouts** (Prevent hanging requests)
4. **Implement connection pooling** (10-15% improvement)
5. **Add streaming optimizations** (Better perceived performance)

This optimization plan should significantly improve your API's performance both locally and in the cloud!
