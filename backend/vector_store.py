import logging
import os
from typing import List
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeApiException
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
from cache_manager import VectorCache

logger = logging.getLogger(__name__)

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not PINECONE_API_KEY or not OPENAI_API_KEY:
    logger.warning("PINECONE_API_KEY and OPENAI_API_KEY must be set in environment variables")
    # Don't raise error during import - let the application handle it gracefully

class VectorStoreManager:
    def __init__(self, index_name: str):
        if not PINECONE_API_KEY or not OPENAI_API_KEY:
            raise ValueError("PINECONE_API_KEY and OPENAI_API_KEY must be set in environment variables")
        
        self.index_name = index_name
        self.pinecone = Pinecone(api_key=PINECONE_API_KEY)
        self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        self._initialize_index()

    def _initialize_index(self):
        if self.index_name not in self.pinecone.list_indexes():
            logger.info(f"Creating Pinecone index: {self.index_name}")
            try:
                self.pinecone.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embeddings dimension
                    metric='cosine',
                    spec=ServerlessSpec(cloud='aws', region='us-east-1')
                )
            except PineconeApiException as e:
                if e.status == 409 and "ALREADY_EXISTS" in str(e.body):
                    logger.warning(f"Pinecone index {self.index_name} already exists. Proceeding with existing index.")
                else:
                    logger.error(f"Failed to create Pinecone index {self.index_name}: {e.body.decode()}")
                    raise
        self.index = self.pinecone.Index(self.index_name)
        logger.info(f"Pinecone index {self.index_name} initialized.")

    async def upsert_documents(self, documents: List[Document], namespace: str) -> int:
        logger.info(f"Upserting {len(documents)} documents into Pinecone namespace: {namespace}")
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        # Check cache for embeddings first
        texts_tuple = tuple(texts)
        cached_embeddings = VectorCache.get_embeddings(texts_tuple)
        
        if cached_embeddings:
            logger.info(f"Using cached embeddings for {len(texts)} texts")
            embeds = cached_embeddings
        else:
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeds = await self.embeddings.aembed_documents(texts)
            # Cache the embeddings
            VectorCache.set_embeddings(texts_tuple, embeds)

        # Prepare vectors for upsert
        vectors = []
        for i, (text, embed, metadata) in enumerate(zip(texts, embeds, metadatas)):
            vectors.append({
                "id": f"{namespace}-{i}", # Unique ID for each vector
                "values": embed,
                "metadata": {"text": text, **metadata}
            })

        # Upsert in batches
        upserted_count = 0
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch, namespace=namespace)
                upserted_count += len(batch)
                logger.debug(f"Upserted batch of {len(batch)} vectors to namespace {namespace}")
            except Exception as e:
                logger.error(f"Failed to upsert batch to Pinecone: {e}")

        logger.info(f"Successfully upserted {upserted_count} vectors to Pinecone namespace: {namespace}")
        return upserted_count

    async def amax_marginal_relevance_search(self, query: str, namespace: str, top_k: int = 4) -> List[Document]:
        logger.info(f"Performing similarity search for query: '{query}' in namespace: {namespace} (top_k={top_k})")
        
        # Check cache for search results first
        cached_results = VectorCache.get_similarity_search(query, namespace, top_k)
        if cached_results:
            logger.info(f"Using cached search results for query: '{query}'")
            return cached_results
        
        # Embed the query
        query_embed = await self.embeddings.aembed_query(query)

        # Perform similarity search
        response = self.index.query(
            vector=query_embed,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True
        )

        retrieved_documents = []
        for match in response.matches:
            if match.metadata and "text" in match.metadata:
                retrieved_documents.append(
                    Document(
                        page_content=match.metadata["text"],
                        metadata={k: v for k, v in match.metadata.items() if k != "text"}
                    )
                )
        
        # Cache the results
        VectorCache.set_similarity_search(query, namespace, top_k, retrieved_documents)
        
        logger.info(f"Retrieved {len(retrieved_documents)} documents for query: '{query}'")
        return retrieved_documents
