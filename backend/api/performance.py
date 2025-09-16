import os
import sys
import asyncio
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache_manager import cache_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Set event loop policy for Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@app.get("/api/performance")
async def get_performance_stats():
    """Get performance and cache statistics"""
    try:
        cache_stats = cache_manager.stats()
        
        # Get additional performance metrics
        import psutil
        system_stats = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "active_connections": len(asyncio.all_tasks())
        }
        
        return JSONResponse(content={
            "cache_stats": cache_stats,
            "system_stats": system_stats,
            "status": "healthy",
            "optimizations": {
                "gzip_compression": "enabled",
                "response_caching": "enabled",
                "model_optimization": "enabled",
                "streaming_optimization": "enabled",
                "parallel_processing": "enabled",
                "concurrent_requests": "optimized"
            },
            "model_configs": {
                # Groq models (ultra-fast)
                "moonshotai/kimi-k2-0905": {"timeout": 8.0, "priority": "ultra_high"},
                "openai/gpt-oss-120b": {"timeout": 10.0, "priority": "high"},
                "meta-llama/llama-guard-4-12b": {"timeout": 6.0, "priority": "ultra_high"},
                "deepseek/deepseek-r1-distill-llama-70b": {"timeout": 8.0, "priority": "high"},
                "google/gemma-2-9b-it": {"timeout": 5.0, "priority": "ultra_high"},
                # Fallback models
                "deepseek/deepseek-chat-v3.1": {"timeout": 30.0, "priority": "medium"},
                "openai/gpt-5": {"timeout": 45.0, "priority": "medium"},
                "anthropic/claude-sonnet-4": {"timeout": 50.0, "priority": "low"},
                "google/gemini-2.5-pro": {"timeout": 60.0, "priority": "low"},
                "qwen/qwen3-coder": {"timeout": 40.0, "priority": "medium"},
                "x-ai/grok-code-fast-1": {"timeout": 35.0, "priority": "medium"}
            }
        })
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# Vercel serverless function handler
from mangum import Mangum

handler = Mangum(app)
