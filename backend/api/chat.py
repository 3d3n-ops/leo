import os
import sys
import asyncio
import logging
import time
import hashlib
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from leo_service import leo_service
from rag_service import ChatService
from cache_manager import cache_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Set event loop policy for Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Simple response caching
def get_cache_key(message: str, model: str, use_rag: bool, use_web_search: bool) -> str:
    """Generate cache key for chat requests"""
    cache_string = f"{message}:{model}:{use_rag}:{use_web_search}"
    return hashlib.md5(cache_string.encode()).hexdigest()

def should_cache_response(message: str) -> bool:
    """Determine if response should be cached based on message content"""
    # Don't cache very short messages or personal queries
    if len(message) < 10:
        return False
    
    # Don't cache time-sensitive queries
    time_sensitive_keywords = ["current", "latest", "now", "today", "recent", "2024", "2025"]
    if any(keyword in message.lower() for keyword in time_sensitive_keywords):
        return False
    
    return True

def select_optimal_model(message: str, requested_model: str) -> str:
    """Select the optimal model based on message characteristics"""
    # If user specifically requested a model, respect that choice
    if requested_model:
        return requested_model
    
    message_lower = message.lower()
    
    # Code-related prompts - use ultra-fast coding models
    if any(keyword in message_lower for keyword in ["code", "function", "program", "script", "algorithm", "debug", "error"]):
        return "google/gemma-2-9b-it"  # Ultra-fast for code
    
    # Math-related prompts - use reasoning models
    if any(keyword in message_lower for keyword in ["solve", "calculate", "equation", "math", "derivative", "integral", "algebra"]):
        return "deepseek/deepseek-r1-distill-llama-70b"  # Fast reasoning model
    
    # Creative prompts - use creative models
    if any(keyword in message_lower for keyword in ["write", "create", "story", "poem", "creative", "imagine"]):
        return "moonshotai/kimi-k2-0905"  # Fast creative model
    
    # Security/safety prompts - use specialized model
    if any(keyword in message_lower for keyword in ["security", "safety", "guard", "filter", "moderate"]):
        return "meta-llama/llama-guard-4-12b"  # Specialized safety model
    
    # General prompts - use fastest available model
    return "google/gemma-2-9b-it"  # Ultra-fast general model

class ChatRequest(BaseModel):
    message: str
    model: str
    top_k: int = 4  # Default to 4 relevant chunks
    use_rag: bool = False
    use_web_search: bool = False

@app.post("/api/chat")
async def chat(request: ChatRequest):
    start_time = time.time()
    logger.info(f"Received chat request: {request.message} with model: {request.model}")

    try:
        # Select optimal model based on message content
        optimal_model = select_optimal_model(request.message, request.model)
        if optimal_model != request.model:
            logger.info(f"Selected optimal model: {optimal_model} (requested: {request.model})")
        
        # Check cache first
        cache_key = get_cache_key(request.message, optimal_model, request.use_rag, request.use_web_search)
        cached_response = None
        
        if should_cache_response(request.message):
            cached_response = cache_manager.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for request: {cache_key[:8]}...")
                return StreamingResponse(
                    iter([cached_response.encode("utf-8")]), 
                    media_type="application/json"
                )
        
        # PARALLEL DECISION MAKING + RAG RETRIEVAL
        logger.info("Starting parallel chat processing...")

        # Create parallel tasks for independent operations
        parallel_tasks = []

        # 1. Leo intelligence decisions (fast, local computation)
        decision_task = asyncio.create_task(
            _get_leo_decisions(request.message, request.use_rag, request.use_web_search)
        )
        parallel_tasks.append(("decisions", decision_task))

        # 2. RAG retrieval (if potentially needed)
        rag_task = None
        if request.use_rag or leo_service.should_use_rag(request.message, request.use_rag):
            chat_service = ChatService(index_name="docs-wiki-index", namespace="default_docs")
            rag_task = asyncio.create_task(
                chat_service.retrieve_documents(query=request.message, top_k=request.top_k)
            )
            parallel_tasks.append(("rag", rag_task))

        # Wait for parallel tasks to complete
        parallel_results = {}
        for task_name, task in parallel_tasks:
            try:
                parallel_results[task_name] = await task
            except Exception as e:
                logger.warning(f"Parallel task {task_name} failed: {e}")
                parallel_results[task_name] = [] if task_name == "rag" else {"use_rag": False, "use_web_search": False}

        # Extract results
        decisions = parallel_results.get("decisions", {"use_rag": False, "use_web_search": False})
        retrieved_documents = parallel_results.get("rag", [])

        should_use_rag = decisions["use_rag"] and len(retrieved_documents) > 0
        should_use_web_search = decisions["use_web_search"]

        logger.info(f"Parallel processing completed - Use RAG: {should_use_rag}, Use Web Search: {should_use_web_search}, Documents: {len(retrieved_documents)}")

        # Collect response for caching
        response_chunks = []
        
        async def stream_generator():
            try:
                # Use Leo service with optimized Groq models through OpenRouter
                async for chunk_data in leo_service.chat_with_leo(
                    message=request.message,
                    model=optimal_model,
                    rag_documents=retrieved_documents,
                    use_rag=should_use_rag,
                    use_web_search=should_use_web_search
                ):
                    # Collect for caching
                    response_chunks.append(chunk_data)
                    # Pass through chunks immediately
                    yield (chunk_data + "\n").encode("utf-8")
            finally:
                total_time = time.time() - start_time
                logger.info(f"Chat completed in {total_time:.2f} seconds")
                
                # Cache the response if appropriate
                if should_cache_response(request.message) and response_chunks:
                    full_response = "\n".join(response_chunks)
                    cache_manager.set(cache_key, full_response, ttl=300)  # Cache for 5 minutes
                    logger.info(f"Cached response for key: {cache_key[:8]}...")

        return StreamingResponse(stream_generator(), media_type="application/json")

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_leo_decisions(message: str, use_rag: bool, use_web_search: bool) -> dict:
    """Get Leo's decisions about RAG and web search usage in parallel"""
    try:
        should_use_rag = leo_service.should_use_rag(message, use_rag)
        should_use_web_search = leo_service.should_use_web_search(message) or use_web_search
        
        return {
            "use_rag": should_use_rag,
            "use_web_search": should_use_web_search
        }
    except Exception as e:
        logger.error(f"Error getting Leo decisions: {e}")
        return {"use_rag": False, "use_web_search": False}


# Vercel serverless function handler
from mangum import Mangum

handler = Mangum(app)
