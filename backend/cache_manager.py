import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)

class CacheManager:
    """High-performance caching system for reducing API calls and processing time"""
    
    def __init__(self, default_ttl: int = 3600):  # 1 hour default TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean expired cache entries"""
        try:
            loop = asyncio.get_running_loop()
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_expired())
        except RuntimeError:
            # No event loop running, skip cleanup task for now
            # It will be started when the first async operation is called
            pass
    
    async def _cleanup_expired(self):
        """Remove expired cache entries"""
        while True:
            try:
                current_time = time.time()
                expired_keys = []
                
                for key, data in self.cache.items():
                    if current_time > data.get('expires_at', 0):
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.cache[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                # Run cleanup every 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        def serialize_arg(arg):
            """Convert argument to a serializable format"""
            if hasattr(arg, '__dict__'):
                # For objects with __dict__, use class name and relevant attributes
                if hasattr(arg, '__class__'):
                    return f"{arg.__class__.__name__}:{id(arg)}"
                else:
                    return str(type(arg))
            return arg
        
        # Serialize args, handling the first argument specially (usually 'self')
        serialized_args = []
        for i, arg in enumerate(args):
            if i == 0 and hasattr(arg, '__class__') and hasattr(arg, '__dict__'):
                # Skip 'self' parameter for class methods
                continue
            serialized_args.append(serialize_arg(arg))
        
        # Create a hash of the arguments for consistent key generation
        key_data = {
            'args': serialized_args,
            'kwargs': {k: serialize_arg(v) for k, v in kwargs.items()} if kwargs else {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            data = self.cache[key]
            if time.time() < data.get('expires_at', 0):
                logger.debug(f"Cache hit for key: {key}")
                return data['value']
            else:
                # Expired, remove it
                del self.cache[key]
                logger.debug(f"Cache expired for key: {key}")
        
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        
        # Start cleanup task if not already running
        self._start_cleanup_task()
        
        logger.debug(f"Cached value for key: {key} (TTL: {ttl}s)")
    
    async def get_or_set(self, key: str, async_func, ttl: Optional[int] = None, *args, **kwargs) -> Any:
        """Get from cache or compute and cache the result"""
        # Try to get from cache first
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Not in cache, compute the value
        logger.debug(f"Computing value for cache key: {key}")
        value = await async_func(*args, **kwargs)
        
        # Cache the result
        self.set(key, value, ttl)
        return value
    
    def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern"""
        keys_to_remove = [key for key in self.cache.keys() if pattern in key]
        for key in keys_to_remove:
            del self.cache[key]
        
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching pattern: {pattern}")
        return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cleared {count} cache entries")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = sum(1 for data in self.cache.values() if current_time < data.get('expires_at', 0))
        expired_entries = len(self.cache) - active_entries
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'memory_usage_mb': sum(len(str(data)) for data in self.cache.values()) / 1024 / 1024
        }


# Global cache instance
cache_manager = CacheManager()

def cached(prefix: str, ttl: int = 3600):
    """Decorator for caching async function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Not in cache, compute result
            logger.debug(f"Cache miss for {func.__name__}, computing...")
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache_manager.set(key, result, ttl)
            return result
        
        return wrapper
    return decorator


# Specific cache functions for common operations
class APICache:
    """Specialized caching for API responses"""
    
    @staticmethod
    async def get_key_concepts(topic: str, prompt: str) -> list:
        """Cached key concepts retrieval"""
        key = cache_manager._generate_key("key_concepts", topic, prompt)
        return await cache_manager.get_or_set(
            key, 
            lambda: None,  # Will be replaced by actual function
            ttl=1800  # 30 minutes
        )
    
    @staticmethod
    async def get_concept_explanations(concepts: list, topic: str, prompt: str) -> dict:
        """Cached concept explanations"""
        key = cache_manager._generate_key("concept_explanations", tuple(concepts), topic, prompt)
        return await cache_manager.get_or_set(
            key,
            lambda: None,  # Will be replaced by actual function
            ttl=3600  # 1 hour
        )
    
    @staticmethod
    async def get_learning_suggestions(explanations: dict, topic: str, prompt: str) -> list:
        """Cached learning suggestions"""
        key = cache_manager._generate_key("learning_suggestions", str(explanations), topic, prompt)
        return await cache_manager.get_or_set(
            key,
            lambda: None,  # Will be replaced by actual function
            ttl=3600  # 1 hour
        )


class DocumentCache:
    """Specialized caching for document processing"""
    
    @staticmethod
    def get_crawled_urls(url: str, max_depth: int, max_pages: int) -> Optional[list]:
        """Get cached crawled URLs"""
        key = cache_manager._generate_key("crawled_urls", url, max_depth, max_pages)
        return cache_manager.get(key)
    
    @staticmethod
    def set_crawled_urls(url: str, max_depth: int, max_pages: int, urls: list) -> None:
        """Cache crawled URLs"""
        key = cache_manager._generate_key("crawled_urls", url, max_depth, max_pages)
        cache_manager.set(key, urls, ttl=7200)  # 2 hours
    
    @staticmethod
    def get_parsed_documents(urls: tuple) -> Optional[list]:
        """Get cached parsed documents"""
        key = cache_manager._generate_key("parsed_docs", urls)
        return cache_manager.get(key)
    
    @staticmethod
    def set_parsed_documents(urls: tuple, documents: list) -> None:
        """Cache parsed documents"""
        key = cache_manager._generate_key("parsed_docs", urls)
        cache_manager.set(key, documents, ttl=3600)  # 1 hour


class VectorCache:
    """Specialized caching for vector operations"""
    
    @staticmethod
    def get_embeddings(texts: tuple) -> Optional[list]:
        """Get cached embeddings"""
        key = cache_manager._generate_key("embeddings", texts)
        return cache_manager.get(key)
    
    @staticmethod
    def set_embeddings(texts: tuple, embeddings: list) -> None:
        """Cache embeddings"""
        key = cache_manager._generate_key("embeddings", texts)
        cache_manager.set(key, embeddings, ttl=86400)  # 24 hours
    
    @staticmethod
    def get_similarity_search(query: str, namespace: str, top_k: int) -> Optional[list]:
        """Get cached similarity search results"""
        key = cache_manager._generate_key("similarity_search", query, namespace, top_k)
        return cache_manager.get(key)
    
    @staticmethod
    def set_similarity_search(query: str, namespace: str, top_k: int, results: list) -> None:
        """Cache similarity search results"""
        key = cache_manager._generate_key("similarity_search", query, namespace, top_k)
        cache_manager.set(key, results, ttl=1800)  # 30 minutes
