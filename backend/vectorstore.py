import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

load_dotenv()

# ----------------------
# Environment variables
# ----------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
INDEX_NAME = os.getenv("PINECONE_INDEX", "docs-wiki")  # Default name
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Handle missing OpenAI API key gracefully
if not OPENAI_API_KEY:
    print("⚠️  OPENAI_API_KEY not found, will use fallback embedding model")

# ----------------------
# Initialize Pinecone and OpenAI
# ----------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ----------------------
# Index management
# ----------------------
def delete_and_recreate_index():
    """Delete existing index and recreate with correct dimensions"""
    try:
        existing_indexes = pc.list_indexes().names()
        if INDEX_NAME in existing_indexes:
            print(f"🗑️  Deleting existing index: {INDEX_NAME}")
            pc.delete_index(INDEX_NAME)
            print(f"✅ Index '{INDEX_NAME}' deleted")
        
        print(f"Creating new Pinecone index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,  # all-MiniLM-L6-v2 dimensions
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print(f"✅ Index '{INDEX_NAME}' created successfully with 384 dimensions")
        return pc.Index(INDEX_NAME)
    except Exception as e:
        print(f"❌ Error recreating index: {e}")
        raise

def create_index_if_not_exists():
    """Create Pinecone index if it doesn't exist"""
    try:
        existing_indexes = pc.list_indexes().names()
        if INDEX_NAME not in existing_indexes:
            print(f"Creating new Pinecone index: {INDEX_NAME}")
            pc.create_index(
                name=INDEX_NAME,
                dimension=384,  # all-MiniLM-L6-v2 dimensions
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"✅ Index '{INDEX_NAME}' created successfully")
        else:
            print(f"✅ Index '{INDEX_NAME}' already exists")
        return pc.Index(INDEX_NAME)
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        raise

# Initialize index - recreate if dimension mismatch
try:
    index = create_index_if_not_exists()
    # Test with a dummy vector to check dimensions
    test_vector = [0.0] * 384
    index.query(vector=test_vector, top_k=1)
except Exception as e:
    if "dimension" in str(e).lower():
        print("🔧 Dimension mismatch detected, recreating index...")
        index = delete_and_recreate_index()
    else:
        raise

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Connection pooling
executor = ThreadPoolExecutor(max_workers=4)

# ----------------------
# Helper functions
# ----------------------
def embed_text(text: str) -> List[float]:
    return embed_model.encode(text).tolist()

async def embed_text_async(text: str) -> List[float]:
    """Async wrapper for embedding text"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, embed_text, text)

async def embed_batch_concurrent(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Embed multiple texts concurrently in batches"""
    embeddings = []
    
    # Process in batches to avoid overwhelming the model
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Create concurrent tasks for this batch
        tasks = [embed_text_async(text) for text in batch]
        batch_embeddings = await asyncio.gather(*tasks)
        embeddings.extend(batch_embeddings)
        
        print(f"✅ Embedded batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
    
    return embeddings

async def add_to_vectorstore_async(docs: List[Dict[str, Any]], batch_size: int = 200) -> None:
    """
    Optimized async batch upsert documents to Pinecone with concurrent embedding.
    """
    # Collect all chunks and their metadata
    all_chunks = []
    chunk_metadata = []
    
    for doc in docs:
        for i, chunk in enumerate(doc["chunks"]):
            all_chunks.append(chunk)
            chunk_metadata.append({
                "id": f"{doc['url']}_{i}",
                "url": doc["url"],
                "text": chunk
            })
    
    print(f"🔄 Processing {len(all_chunks)} chunks with concurrent embedding...")
    
    # Generate embeddings concurrently
    embeddings = await embed_batch_concurrent(all_chunks, batch_size=32)
    
    # Prepare vectors for Pinecone
    vectors = []
    for i, (embedding, metadata) in enumerate(zip(embeddings, chunk_metadata)):
        vectors.append({
            "id": metadata["id"],
            "values": embedding,
            "metadata": {"url": metadata["url"], "text": metadata["text"]}
        })
    
    # Upsert in larger batches
    print(f"🔄 Upserting {len(vectors)} vectors to Pinecone in batches of {batch_size}...")
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        print(f"✅ Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")

def add_to_vectorstore(docs: List[Dict[str, Any]], batch_size: int = 200) -> None:
    """
    Sync wrapper for backward compatibility
    """
    asyncio.run(add_to_vectorstore_async(docs, batch_size))

async def query_vectorstore_async(query_text: str, top_k: int = 5) -> List[str]:
    """Async query Pinecone with concurrent embedding"""
    query_vec = await embed_text_async(query_text)
    results = index.query(vector=query_vec, top_k=top_k, include_metadata=True)
    
    # Extract text content from the matches
    text_chunks = []
    for match in results['matches']:
        if 'metadata' in match and 'text' in match['metadata']:
            text_chunks.append(match['metadata']['text'])
        else:
            text_chunks.append(f"Content from: {match['id']}")
    
    return text_chunks

def query_vectorstore(query_text: str, top_k: int = 5) -> List[str]:
    """Sync wrapper for backward compatibility"""
    return asyncio.run(query_vectorstore_async(query_text, top_k))
