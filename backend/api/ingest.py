import os
import sys
import asyncio
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_services import perplexity_service, llm_service
from leo_service import leo_service
from vector_store import VectorStoreManager
from file_parser import FileParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Set event loop policy for Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Learning research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


# Vercel serverless function handler
from mangum import Mangum

handler = Mangum(app)
