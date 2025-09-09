import asyncio
import logging
import httpx
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from cache_manager import DocumentCache

logger = logging.getLogger(__name__)

class SimpleCrawler:
    def __init__(self, max_depth: int = 2, max_pages: int = 50):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited_urls = set()
        self.urls_to_visit = asyncio.Queue()
        self.found_urls = []

    async def _fetch_html(self, url: str) -> str | None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=10)
                response.raise_for_status() # Raise an exception for HTTP errors
                return response.text
        except httpx.RequestError as e:
            logger.error(f"HTTPX request failed for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching {url}: {e}")
            return None

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a_tag in soup.find_all("a", href=True):
            link = a_tag["href"]
            abs_link = urljoin(base_url, link)
            if urlparse(abs_link).netloc == urlparse(base_url).netloc:
                links.append(abs_link)
        return list(set(links))

    async def crawl(self, start_url: str) -> list[str]:
        logger.info(f"Starting parallel crawl from: {start_url} with max_depth: {self.max_depth}, max_pages: {self.max_pages}")
        
        # Check cache first
        cached_urls = DocumentCache.get_crawled_urls(start_url, self.max_depth, self.max_pages)
        if cached_urls:
            logger.info(f"Using cached crawl results: {len(cached_urls)} URLs")
            return cached_urls
        
        await self.urls_to_visit.put((start_url, 0))

        # PARALLEL CRAWLING: Process multiple URLs concurrently
        max_concurrent_requests = 5  # Limit concurrent requests to avoid overwhelming servers
        semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        async def process_url_with_semaphore(url_data):
            async with semaphore:
                return await self._process_single_url(url_data)
        
        # Start initial processing
        processing_tasks = set()
        
        while not self.urls_to_visit.empty() and len(self.found_urls) < self.max_pages:
            # Start new tasks if we have capacity
            while (len(processing_tasks) < max_concurrent_requests and 
                   not self.urls_to_visit.empty() and 
                   len(self.found_urls) < self.max_pages):
                
                current_url, depth = await self.urls_to_visit.get()
                
                if current_url in self.visited_urls:
                    continue
                
                self.visited_urls.add(current_url)
                self.found_urls.append(current_url)
                
                # Create task for parallel processing
                task = asyncio.create_task(
                    process_url_with_semaphore((current_url, depth))
                )
                processing_tasks.add(task)
            
            # Wait for at least one task to complete
            if processing_tasks:
                done, pending = await asyncio.wait(
                    processing_tasks, 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task in done:
                    try:
                        new_links = await task
                        if new_links:
                            for link in new_links:
                                if link not in self.visited_urls:
                                    await self.urls_to_visit.put((link, depth + 1))
                    except Exception as e:
                        logger.error(f"Error processing URL task: {e}")
                    finally:
                        processing_tasks.remove(task)
        
        # Wait for remaining tasks to complete
        if processing_tasks:
            await asyncio.gather(*processing_tasks, return_exceptions=True)

        logger.info(f"Finished parallel crawling. Found {len(self.found_urls)} unique URLs.")
        
        # Cache the results
        DocumentCache.set_crawled_urls(start_url, self.max_depth, self.max_pages, self.found_urls)
        
        return self.found_urls
    
    async def _process_single_url(self, url_data) -> list[str]:
        """Process a single URL and return new links found"""
        current_url, depth = url_data
        
        logger.info(f"Crawling ({len(self.found_urls)}/{self.max_pages}) - Depth: {depth}, URL: {current_url}")
        
        html_content = await self._fetch_html(current_url)
        if html_content and depth < self.max_depth:
            links = self._extract_links(html_content, current_url)
            return links
        
        return []