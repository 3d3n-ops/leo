
import logging
import json
import time
import sys
import asyncio
import os
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional

from crawler import SimpleCrawler
from parser import DocumentParser
from file_parser import FileParser
from vector_store import VectorStoreManager
from rag_service import ChatService # Import ChatService
from api_services import perplexity_service, llm_service
from leo_service import leo_service
from cache_manager import cache_manager
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Add Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

origins = [
    "http://localhost:3000",
    "https://docs-wiki.vercel.app",  # Your frontend domain
    "https://*.vercel.app",  # Vercel preview deployments
    "https://docs-wiki-frontend.onrender.com",  # Render frontend domain
    "https://*.onrender.com",  # Render preview deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class IngestRequest(BaseModel):
    topic: str
    prompt: str
    url: Optional[str] = None
    max_depth: int = 2
    max_pages: int = 50
    namespace: str = "default_docs"
    index_name: str = "docs-wiki-index"


class ChatRequest(BaseModel):
    message: str
    model: str
    top_k: int = 4 # Default to 4 relevant chunks
    use_rag: bool = False
    use_web_search: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.post("/api/ingest")
async def ingest_docs(
    topic: str = Form(...),
    prompt: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    logger.info(f"Received learning request - Topic: {topic}, Prompt: {prompt}")
    
    try:
        # PARALLEL EXECUTION: Research + Optional file processing
        logger.info("Starting parallel processing...")
        
        # Create tasks for parallel execution
        tasks = []
        
        # 1. Research Agent Integration (Perplexity Sonar) - Always run
        research_task = asyncio.create_task(
            perplexity_service.get_key_concepts(topic, prompt)
        )
        tasks.append(("research", research_task))
        
        # 2. File Processing (if provided) - Optional
        file_task = None
        if file:
            logger.info(f"Starting parallel file processing: {file.filename}")
            file_task = asyncio.create_task(process_uploaded_file(file))
            tasks.append(("file", file_task))
        
        # Wait for parallel tasks to complete
        logger.info("Waiting for parallel tasks to complete...")
        results = {}
        for task_name, task in tasks:
            try:
                results[task_name] = await task
                logger.info(f"Completed {task_name} task")
            except Exception as e:
                logger.error(f"Task {task_name} failed: {e}")
                results[task_name] = None
        
        # Extract results
        key_concepts = results.get("research", [])
        file_chunks = results.get("file", [])
        
        logger.info(f"Parallel processing completed - Concepts: {len(key_concepts)}, File chunks: {len(file_chunks)}")
        
        # PARALLEL LLM PROCESSING
        # Create parallel tasks for concept processing
        llm_tasks = []
        
        # Generate concept summary for Leo
        summary_task = asyncio.create_task(
            llm_service.generate_concept_summary(key_concepts, topic, prompt)
        )
        llm_tasks.append(("summary", summary_task))
        
        # Wait for summary to complete first
        llm_results = {}
        for task_name, task in llm_tasks:
            try:
                llm_results[task_name] = await task
            except Exception as e:
                logger.error(f"LLM task {task_name} failed: {e}")
                llm_results[task_name] = ""
        
        # Generate Leo's first message with the summary
        concept_summary = llm_results.get("summary", "")
        leo_first_message = await leo_service.generate_first_message(concept_summary, key_concepts, topic)
        
        # Optional: Store file chunks in vector store if provided
        chunks_indexed = 0
        if file_chunks:
            try:
                vector_store = VectorStoreManager(index_name="docs-wiki-index")
                chunks_indexed = await vector_store.upsert_documents(file_chunks, "default_docs")
                logger.info(f"Indexed {chunks_indexed} file chunks")
            except Exception as e:
                logger.error(f"Error indexing file chunks: {e}")
        
        response_data = {
            "topic": topic,
            "prompt": prompt,
            "key_concepts": key_concepts,
            "concept_summary": concept_summary,
            "leo_first_message": leo_first_message,
            "chunks_indexed": chunks_indexed,
            "namespace": "default_docs",
        }
        
        logger.info("Learning research completed successfully")
        return response_data
        
    except Exception as e:
        logger.error(f"Learning research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        return {
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
        }
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return {"error": str(e)}


@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    try:
        cache_manager.clear()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {"error": str(e)}


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


# Helper functions for file processing


async def process_uploaded_file(file: UploadFile) -> list[dict]:
    """
    Process uploaded file and convert to document chunks for indexing using LangChain
    """
    logger.info(f"Processing uploaded file: {file.filename}")
    
    try:
        # Use the new FileParser with LangChain document loaders
        file_parser = FileParser(chunk_size=1000, chunk_overlap=200)
        document_chunks = await file_parser.parse_uploaded_file(file)
        
        # Convert LangChain Documents to the expected format
        chunks = []
        for i, doc in enumerate(document_chunks):
            chunks.append({
                "text": doc.page_content,
                "metadata": {
                    **doc.metadata,
                    "chunk_index": i
                }
            })
        
        logger.info(f"Processed {len(chunks)} chunks from uploaded file using LangChain")
        return chunks
        
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        return []
