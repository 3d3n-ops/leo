
import logging
import json
import time
import sys
import asyncio
import os
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from crawler import SimpleCrawler
from parser import DocumentParser
from file_parser import FileParser
from vector_store import VectorStoreManager
from rag_service import ChatService # Import ChatService
from api_services import perplexity_service, llm_service
from leo_service import leo_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    "http://localhost:3000",
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
    logger.info(f"Received learning path request - Topic: {topic}, Prompt: {prompt}")
    
    try:
        # 1. Research Agent Integration (Perplexity Sonar)
        logger.info("Sending request to research agent...")
        key_concepts = await perplexity_service.get_key_concepts(topic, prompt)
        logger.info(f"Retrieved {len(key_concepts)} key concepts from research agent")
        
        # 2. LLM Processing for concept explanation
        logger.info("Generating concept explanations...")
        concept_explanations = await llm_service.generate_concept_explanations(key_concepts, topic, prompt)
        
        # 3. Indexing Logic
        pages_crawled = 0
        chunks_indexed = 0
        
        if url:
            logger.info(f"Processing URL: {url}")
            # Run existing website indexing pipeline
            crawler = SimpleCrawler(max_depth=2, max_pages=50)
            crawled_urls = await crawler.crawl(url)
            pages_crawled = len(crawled_urls)
            
            if crawled_urls:
                parser = DocumentParser()
                document_chunks = await parser.parse_and_chunk(crawled_urls)
                
                if document_chunks:
                    vector_store = VectorStoreManager(index_name="docs-wiki-index")
                    chunks_indexed = await vector_store.upsert_documents(document_chunks, "default_docs")
        
        if file:
            logger.info(f"Processing uploaded file: {file.filename}")
            # Add new file indexing pipeline
            file_chunks = await process_uploaded_file(file)
            if file_chunks:
                vector_store = VectorStoreManager(index_name="docs-wiki-index")
                file_chunks_indexed = await vector_store.upsert_documents(file_chunks, "default_docs")
                chunks_indexed += file_chunks_indexed
        
        # 4. Generate learning suggestions
        learning_suggestions = await llm_service.generate_learning_suggestions(concept_explanations, topic, prompt)
        
        response_data = {
            "topic": topic,
            "prompt": prompt,
            "key_concepts": key_concepts,
            "concept_explanations": concept_explanations,
            "learning_suggestions": learning_suggestions,
            "pages_crawled": pages_crawled,
            "chunks_indexed": chunks_indexed,
            "namespace": "default_docs",
        }
        
        logger.info("Learning path generation completed successfully")
        return response_data
        
    except Exception as e:
        logger.error(f"Learning path generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    start_time = time.time()
    logger.info(f"Received chat request: {request.message} with model: {request.model}")

    try:
        # Determine if we should use RAG or web search based on Leo's intelligence
        should_use_rag = leo_service.should_use_rag(request.message, request.use_rag)
        should_use_web_search = leo_service.should_use_web_search(request.message) or request.use_web_search
        
        logger.info(f"Leo decision - Use RAG: {should_use_rag}, Use Web Search: {should_use_web_search}")

        # Retrieve relevant documents if RAG is needed
        retrieved_documents = []
        if should_use_rag:
            try:
                chat_service = ChatService(index_name="docs-wiki-index", namespace="default_docs")
                retrieved_documents = await chat_service.retrieve_documents(
                    query=request.message,
                    top_k=request.top_k
                )
                retrieval_time = time.time() - start_time
                logger.info(f"Retrieved {len(retrieved_documents)} documents in {retrieval_time:.2f} seconds.")
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without RAG: {e}")
                retrieved_documents = []

        # Use Leo service for dynamic AI responses (non-streaming for now)
        response_content = ""
        async for chunk_data in leo_service.chat_with_leo(
            message=request.message,
            model=request.model,
            rag_documents=retrieved_documents,
            use_rag=should_use_rag,
            use_web_search=should_use_web_search
        ):
            try:
                import json
                data = json.loads(chunk_data)
                if "content" in data:
                    response_content += data["content"]
                elif "error" in data:
                    raise Exception(data["error"])
            except json.JSONDecodeError:
                # If it's not JSON, treat as plain text
                response_content += chunk_data

        return {"response": response_content, "sources": []}

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
