import asyncio
import logging
import httpx
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

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
        logger.info(f"Starting crawl from: {start_url} with max_depth: {self.max_depth}, max_pages: {self.max_pages}")
        await self.urls_to_visit.put((start_url, 0))

        while not self.urls_to_visit.empty() and len(self.found_urls) < self.max_pages:
            current_url, depth = await self.urls_to_visit.get()

            if current_url in self.visited_urls:
                continue

            self.visited_urls.add(current_url)
            self.found_urls.append(current_url)
            logger.info(f"Crawling ({len(self.found_urls)}/{self.max_pages}) - Depth: {depth}, URL: {current_url}")

            html_content = await self._fetch_html(current_url)
            if html_content and depth < self.max_depth:
                links = self._extract_links(html_content, current_url)
                for link in links:
                    if link not in self.visited_urls:
                        await self.urls_to_visit.put((link, depth + 1))

        logger.info(f"Finished crawling. Found {len(self.found_urls)} unique URLs.")
        return self.found_urls