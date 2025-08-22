from fastapi import FastAPI, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
import asyncio
import uuid
import json
from typing import Dict, Any, List
from db import SessionLocal, RepoDoc, init_db
from vectorstore import add_to_vectorstore, add_to_vectorstore_async, query_vectorstore, query_vectorstore_async
from scraper import crawl_website
from llm import summarize_page, chat_with_context
from utils import chunk_lines
from schemas import ChatRequest, ChatResponse, IngestResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import settings


app = FastAPI()
init_db()

# Task tracking storage (in production, use Redis or database)
task_status: Dict[str, Dict[str, Any]] = {}

# WebSocket connection management
active_connections: List[WebSocket] = []

async def connect_websocket(websocket: WebSocket):
    """Add a new WebSocket connection"""
    await websocket.accept()
    active_connections.append(websocket)

def disconnect_websocket(websocket: WebSocket):
    """Remove a WebSocket connection"""
    if websocket in active_connections:
        active_connections.remove(websocket)

async def broadcast_task_update(task_id: str, update: Dict[str, Any]):
    """Broadcast task update to all connected WebSocket clients"""
    message = {
        "task_id": task_id,
        "timestamp": asyncio.get_event_loop().time(),
        **update
    }
    
    # Remove disconnected connections
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(message))
        except:
            disconnected.append(connection)
    
    # Clean up disconnected connections
    for connection in disconnected:
        disconnect_websocket(connection)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



# Enhanced background task in main.py
async def background_ingest_task_enhanced(task_id: str, url: str):
    """Enhanced background task with comprehensive logging and error handling"""
    start_time = time.time()
    logger.info(f"Starting ingestion task {task_id} for {url}")
    
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL: {url}")
        
        task_manager.update_task(task_id, 
            status="processing",
            progress=0,
            message="Starting crawl...",
            phase="crawling"
        )
        await broadcast_task_update(task_id, task_manager.tasks[task_id])
        
        # Crawl website with enhanced scraper
        logger.info(f"Task {task_id}: Starting website crawl")
        pages = await crawl_website_enhanced(url, max_pages=100)
        
        if not pages:
            raise ValueError("No pages were successfully crawled")
        
        logger.info(f"Task {task_id}: Crawled {len(pages)} pages")
        task_manager.update_task(task_id,
            progress=30,
            message=f"Crawled {len(pages)} pages, processing content...",
            phase="processing"
        )
        await broadcast_task_update(task_id, task_manager.tasks[task_id])
        
        # Process pages with batching
        docs = []
        summaries = []
        diagrams = []
        
        for i, page in enumerate(pages):
            try:
                chunks = chunk_lines(page["lines"], chunk_size=500)
                docs.append({
                    "url": page["url"], 
                    "chunks": chunks,
                    "metadata": page.get("metadata", {})
                })
                
                # Generate summaries
                page_text = "\n".join(page["lines"])
                if len(page_text.strip()) > 50:  # Only process substantial content
                    result = summarize_page(page_text)
                    summaries.append(result["summary"])
                    if result["diagram"]:
                        diagrams.append(result["diagram"])
                
                # Update progress
                progress = 30 + (i / len(pages)) * 40
                if i % 10 == 0:  # Update every 10 pages
                    task_manager.update_task(task_id,
                        progress=int(progress),
                        message=f"Processing page {i+1}/{len(pages)}..."
                    )
                    await broadcast_task_update(task_id, task_manager.tasks[task_id])
                    
            except Exception as e:
                logger.error(f"Task {task_id}: Error processing page {page['url']}: {e}")
                continue
        
        if not docs:
            raise ValueError("No documents were successfully processed")
        
        # Vector database insertion
        task_manager.update_task(task_id,
            progress=70,
            message="Adding to vector database...",
            phase="vectorization"
        )
        await broadcast_task_update(task_id, task_manager.tasks[task_id])
        
        logger.info(f"Task {task_id}: Adding {len(docs)} documents to vector store")
        await add_to_vectorstore_async(docs, batch_size=200)
        
        # Database storage
        task_manager.update_task(task_id,
            progress=90,
            message="Saving to database...",
            phase="database_save"
        )
        await broadcast_task_update(task_id, task_manager.tasks[task_id])
        
        db = SessionLocal()
        try:
            full_summary = "\n".join(summaries)
            full_diagram = "\n".join(diagrams)
            
            repo_doc = RepoDoc(
                url=url, 
                summary=full_summary, 
                diagram=full_diagram
            )
            db.add(repo_doc)
            db.commit()
            db.refresh(repo_doc)
            
            logger.info(f"Task {task_id}: Saved to database with ID {repo_doc.id}")
            
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
        
        # Task completed
        total_time = time.time() - start_time
        task_manager.update_task(task_id,
            status="completed",
            progress=100,
            message="Ingestion completed successfully",
            phase="completed",
            result={
                "id": repo_doc.id,
                "summary": full_summary,
                "diagram": full_diagram,
                "pages_processed": len(pages),
                "documents_created": len(docs),
                "processing_time": total_time
            }
        )
        await broadcast_task_update(task_id, task_manager.tasks[task_id])
        
        logger.info(f"Task {task_id}: Completed successfully in {total_time:.2f}s")
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Task {task_id}: Failed after {total_time:.2f}s: {str(e)}")
        
        task_manager.update_task(task_id,
            status="failed",
            message=f"Error: {str(e)}",
            phase="error",
            error_details=str(e),
            processing_time=total_time
        )
        await broadcast_task_update(task_id, task_manager.tasks[task_id])

origins = [
    "http://localhost",
    "http://localhost:3001",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.post("/ingest")
@limiter.limit("10/minute")
async def ingest_docs(background_tasks: BackgroundTasks, url: str=Query(..., description="Root docs page URL")):
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task status
    task_status[task_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Task queued for processing",
        "url": url,
        "created_at": asyncio.get_event_loop().time()
    }
    
    # Add background task
    background_tasks.add_task(background_ingest_task, task_id, url)
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Ingestion task started. Use /status/{task_id} to check progress."
    }

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a background ingestion task"""
    if task_id not in task_status:
        return {"error": "Task not found"}, 404
    
    return task_status[task_id]

@app.get("/tasks")
async def list_tasks():
    """List all tasks and their statuses"""
    return {"tasks": task_status}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    context_chunks = await query_vectorstore_async(request.question, top_k=5)
    context = "\n".join(context_chunks)
    answer = chat_with_context(request.question, context)
    return {"answer": answer, "context_used": context}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live task updates"""
    await connect_websocket(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Send current task statuses on connection
            if data == "get_tasks":
                await websocket.send_text(json.dumps({
                    "type": "task_list",
                    "tasks": task_status
                }))
    except WebSocketDisconnect:
        disconnect_websocket(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        disconnect_websocket(websocket)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check vector store
    try:
        await query_vectorstore_async("test", top_k=1)
        vector_status = "healthy"
    except Exception as e:
        vector_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" and vector_status == "healthy" else "unhealthy",
        "database": db_status,
        "vector_store": vector_status,
        "task_stats": task_manager.stats,
        "active_tasks": len([t for t in task_manager.tasks.values() if t["status"] == "processing"]),
        "timestamp": time.time()
    }