# Enhanced scraper.py
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Optional
import time
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, rate: float = 1.0):
        self.rate = rate
        self.last_called = 0.0
    
    async def acquire(self):
        now = time.time()
        time_since_last = now - self.last_called
        if time_since_last < self.rate:
            await asyncio.sleep(self.rate - time_since_last)
        self.last_called = time.time()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def fetch_page_with_retry(
    client: httpx.AsyncClient, 
    url: str, 
    sem: asyncio.Semaphore,
    rate_limiter: RateLimiter
) -> Dict[str, any]:
    async with sem:
        await rate_limiter.acquire()
        start_time = time.time()
        
        try:
            logger.debug(f"Fetching: {url}")
            resp = await client.get(url, timeout=30.0)
            resp.raise_for_status()
            
            fetch_time = time.time() - start_time
            logger.info(f"Successfully fetched {url} in {fetch_time:.2f}s")
            
            return {
                "url": url,
                "html": resp.text,
                "status_code": resp.status_code,
                "fetch_time": fetch_time,
                "size": len(resp.text)
            }
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} for {url}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            raise

async def crawl_website_enhanced(
    start_url: str, 
    max_pages: int = 100,
    max_concurrency: int = 10,
    rate_limit: float = 0.5
) -> List[Dict]:
    visited = set()
    to_visit = set([start_url])
    pages = []
    failed_urls = set()
    stats = {
        "pages_crawled": 0,
        "pages_failed": 0,
        "total_size": 0,
        "start_time": time.time()
    }
    
    sem = asyncio.Semaphore(max_concurrency)
    rate_limiter = RateLimiter(rate_limit)
    
    logger.info(f"Starting crawl of {start_url} (max_pages={max_pages})")
    
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    ) as client:
        while to_visit and len(visited) < max_pages:
            current_batch = list(to_visit)[:min(max_concurrency, len(to_visit))]
            to_visit -= set(current_batch)
            
            tasks = [
                fetch_page_with_retry(client, url, sem, rate_limiter) 
                for url in current_batch
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for url, result in zip(current_batch, results):
                visited.add(url)
                
                if isinstance(result, Exception):
                    failed_urls.add(url)
                    stats["pages_failed"] += 1
                    logger.error(f"Failed to crawl {url}: {result}")
                    continue
                
                try:
                    lines = clean_html(result["html"])
                    pages.append({
                        "url": url,
                        "lines": lines,
                        "metadata": {
                            "status_code": result["status_code"],
                            "fetch_time": result["fetch_time"],
                            "size": result["size"]
                        }
                    })
                    
                    stats["pages_crawled"] += 1
                    stats["total_size"] += result["size"]
                    
                    # Extract new links
                    links = extract_links(url, result["html"])
                    new_links = links - visited - failed_urls
                    to_visit.update(new_links)
                    
                    logger.info(f"Crawled {url} - Found {len(new_links)} new links")
                    
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    stats["pages_failed"] += 1
    
    total_time = time.time() - stats["start_time"]
    logger.info(f"Crawl completed: {stats['pages_crawled']} pages, "
               f"{stats['pages_failed']} failures, "
               f"{stats['total_size']/1024/1024:.2f}MB, "
               f"{total_time:.2f}s")
    
    return pages