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

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    try:
        cache_manager.clear()
        return JSONResponse(content={"message": "Cache cleared successfully"})
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# Vercel serverless function handler
from mangum import Mangum

handler = Mangum(app)
