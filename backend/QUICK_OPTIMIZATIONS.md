# Quick Performance Optimizations - Implementation Guide

## 🚀 Immediate Impact Optimizations (5-15 minutes each)

### 1. Enable Gzip Compression (2 minutes)
Add to `main.py`:

```python
from fastapi.middleware.gzip import GZipMiddleware

# Add after app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Expected Impact**: 5-10% faster responses

### 2. Add Response Caching (5 minutes)
Add to `main.py`:

```python
from optimizations import fast_cache, cache_response

# Add caching to chat endpoint
@app.post("/api/chat")
@cache_response(ttl=300)  # Cache for 5 minutes
async def chat(request: ChatRequest):
    # ... existing code
```

**Expected Impact**: 20-30% faster for repeated queries

### 3. Optimize Model Timeouts (3 minutes)
Update `leo_service.py`:

```python
# Add at the top
from optimizations import MODEL_CONFIGS

# In _stream_chat_response method, replace timeout=60.0 with:
config = MODEL_CONFIGS.get(model, {})
timeout = config.get("timeout", 60.0)

# Use optimized timeout
async with httpx.AsyncClient(timeout=timeout) as client:
```

**Expected Impact**: Prevents hanging requests, 10-15% improvement

### 4. Add Connection Pooling (5 minutes)
Update `leo_service.py`:

```python
# Add at the top
from optimizations import http_client

# Replace httpx.AsyncClient() calls with:
# async with http_client.client as client:
```

**Expected Impact**: 10-15% faster API calls

### 5. Optimize Model Selection (3 minutes)
Add to `main.py`:

```python
from optimizations import select_optimal_model

# In chat endpoint, before calling leo_service:
optimal_model = select_optimal_model(request.message, [request.model])
# Use optimal_model instead of request.model
```

**Expected Impact**: 15-25% faster responses by using best model for task

## 🔧 Medium Impact Optimizations (15-30 minutes each)

### 6. Implement Parallel Processing (20 minutes)
Update `main.py` chat endpoint:

```python
from optimizations import execute_parallel_tasks

# Replace sequential processing with:
tasks = [
    ("decisions", _get_leo_decisions(request.message, request.use_rag, request.use_web_search)),
    ("rag", chat_service.retrieve_documents(query=request.message, top_k=request.top_k)) if request.use_rag else None,
    ("web", leo_service.web_search(request.message)) if request.use_web_search else None
]

# Filter out None tasks
tasks = [(name, task) for name, task in tasks if task is not None]

# Execute in parallel
results = await execute_parallel_tasks(tasks)
```

**Expected Impact**: 30-50% faster for complex requests

### 7. Add Performance Monitoring (15 minutes)
Add to `main.py`:

```python
from optimizations import perf_monitor

# In chat endpoint, add timing:
start_time = time.time()
# ... existing code ...
response_time = time.time() - start_time
perf_monitor.record_response_time(model, response_time)

# Update performance endpoint:
@app.get("/api/performance")
async def get_performance_stats():
    cache_stats = cache_manager.stats()
    perf_stats = perf_monitor.get_stats()
    
    return {
        "cache_stats": cache_stats,
        "performance_stats": perf_stats,
        "status": "healthy"
    }
```

**Expected Impact**: Better visibility into performance bottlenecks

## 📊 Expected Results After Quick Optimizations

### Before Optimizations:
- Average Response Time: 13.76s
- RAG Query: 26.24s
- Web Search: 30.78s
- Complex Reasoning: 42.09s

### After Quick Optimizations (1-7):
- Average Response Time: **6-8s** (40-50% improvement)
- RAG Query: **15-18s** (30-40% improvement)
- Web Search: **20-25s** (20-30% improvement)
- Complex Reasoning: **25-30s** (25-35% improvement)

## 🎯 Implementation Order (Recommended)

1. **Gzip Compression** (2 min) - Immediate 5-10% gain
2. **Model Timeouts** (3 min) - Prevents hanging requests
3. **Response Caching** (5 min) - 20-30% gain for repeated queries
4. **Connection Pooling** (5 min) - 10-15% gain
5. **Model Selection** (3 min) - 15-25% gain
6. **Performance Monitoring** (15 min) - Visibility
7. **Parallel Processing** (20 min) - 30-50% gain for complex requests

**Total Implementation Time**: ~1 hour
**Expected Overall Improvement**: 40-60% faster responses

## 🚀 Cloud Deployment Optimizations

### Render Configuration Updates
Update `render.yaml`:

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
      - key: WORKERS
        value: 2
      - key: WORKER_CONNECTIONS
        value: 1000
    healthCheckPath: /api/performance
```

### Environment Variables for Production
Add to your Render environment:
```
WORKERS=2
WORKER_CONNECTIONS=1000
CACHE_TTL=300
ENABLE_GZIP=true
ENABLE_CACHING=true
```

## 📈 Monitoring and Validation

### Test Performance After Each Optimization
```bash
# Run performance tests
python run_tests.py performance

# Check specific improvements
python run_tests.py all --quick
```

### Key Metrics to Watch
- Average response time < 8s
- First token time < 2s
- Cache hit rate > 30%
- Error rate < 5%

### Performance Alerts
Set up monitoring for:
- Response times > 15s
- Error rates > 10%
- Cache hit rates < 20%
- Memory usage > 80%

## 🔍 Troubleshooting

### If Optimizations Don't Work
1. Check logs for errors
2. Verify environment variables
3. Test individual optimizations
4. Monitor resource usage
5. Check API rate limits

### Common Issues
- **Caching not working**: Check TTL settings
- **Connection pooling errors**: Verify HTTP client setup
- **Model selection issues**: Check model availability
- **Performance monitoring errors**: Verify metrics collection

## 🎉 Next Steps After Quick Optimizations

1. **Advanced Caching**: Redis for distributed caching
2. **CDN Integration**: CloudFlare or AWS CloudFront
3. **Database Optimization**: Connection pooling, query optimization
4. **Load Balancing**: Multiple backend instances
5. **Advanced Monitoring**: APM tools like DataDog or New Relic

The quick optimizations should give you significant performance improvements with minimal effort!
