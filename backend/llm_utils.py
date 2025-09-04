import os
import httpx
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY must be set in the .env file")

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

async def stream_openrouter_completion(
    model: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 1000,
):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000", # Replace with your app's actual URL
        "X-Title": "Docs Wiki Bot", # Replace with your app's actual name
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", f"{OPENROUTER_API_BASE}/chat/completions", headers=headers, json=payload, timeout=None) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk
