# workers.py
import asyncio
from scraper import crawl_website
from utils import chunk_lines
from vectorstore import add_to_vectorstore

async def ingest_website(url: str):
    pages = await crawl_website(url, max_pages=200)
    docs = []
    for page in pages:
        chunks = chunk_lines(page["lines"], chunk_size=500)
        docs.append({"url": page["url"], "chunks": chunks})
    add_to_vectorstore(docs)
    print(f"✅ Ingested {len(docs)} pages")
