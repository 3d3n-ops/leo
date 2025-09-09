import logging
from typing import List
from bs4 import BeautifulSoup
import httpx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from cache_manager import DocumentCache

logger = logging.getLogger(__name__)

class DocumentParser:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        self.cache = {}

    async def _fetch_html(self, url: str) -> str | None:
        if url in self.cache:
            return self.cache[url]
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=10)
                response.raise_for_status() # Raise an exception for HTTP errors
                html_content = response.text
                self.cache[url] = html_content
                return html_content
        except httpx.RequestError as e:
            logger.error(f"HTTPX request failed for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching {url}: {e}")
            return None

    async def parse_and_chunk(self, urls: List[str]) -> List[Document]:
        if not urls:
            return []
        
        # Check cache first
        urls_tuple = tuple(urls)
        cached_documents = DocumentCache.get_parsed_documents(urls_tuple)
        if cached_documents:
            logger.info(f"Using cached parsed documents: {len(cached_documents)} chunks")
            return cached_documents
        
        logger.info(f"Starting parallel parsing of {len(urls)} URLs")
        
        # PARALLEL PROCESSING: Process multiple URLs concurrently
        max_concurrent_requests = 8  # Higher limit for parsing since it's mostly CPU-bound
        semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        async def process_url_with_semaphore(url):
            async with semaphore:
                return await self._parse_single_url(url)
        
        # Create tasks for all URLs
        tasks = [process_url_with_semaphore(url) for url in urls]
        
        # Process all URLs in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all chunks from successful results
        all_chunks = []
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_chunks.extend(result)
                logger.info(f"Successfully processed URL {i+1}/{len(urls)}: {len(result)} chunks")
            elif isinstance(result, Exception):
                logger.error(f"Failed to process URL {urls[i]}: {result}")
        
        logger.info(f"Parallel parsing completed. Total chunks created: {len(all_chunks)}")
        
        # Cache the results
        DocumentCache.set_parsed_documents(urls_tuple, all_chunks)
        
        return all_chunks
    
    async def _parse_single_url(self, url: str) -> List[Document]:
        """Parse and chunk a single URL"""
        logger.info(f"Parsing and chunking URL: {url}")
        try:
            html = await self._fetch_html(url)
            if not html:
                return []

            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()

            if not text.strip():
                logger.warning(f"No text content found on {url}")
                return []
            
            doc = Document(page_content=text, metadata={"source": url})
            chunks = self.text_splitter.split_documents([doc])
            logger.info(f"Created {len(chunks)} chunks for {url}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to parse and chunk {url}: {e}")
            return []