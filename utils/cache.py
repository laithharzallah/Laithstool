"""
Caching utilities for external API calls
"""
import os
import json
import time
import hashlib
from functools import wraps
from datetime import datetime, timedelta


class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self.cache = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _generate_key(self, *args, **kwargs):
        """Generate cache key from arguments"""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key):
        """Get value from cache"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if expiry > time.time():
                self.stats['hits'] += 1
                return value
            else:
                # Expired
                del self.cache[key]
                self.stats['evictions'] += 1
        
        self.stats['misses'] += 1
        return None
    
    def set(self, key, value, ttl_seconds=300):
        """Set value in cache with TTL"""
        expiry = time.time() + ttl_seconds
        self.cache[key] = (value, expiry)
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [k for k, (_, exp) in self.cache.items() if exp <= current_time]
        for key in expired_keys:
            del self.cache[key]
            self.stats['evictions'] += 1
    
    def get_stats(self):
        """Get cache statistics"""
        self.cleanup_expired()
        return {
            **self.stats,
            'size': len(self.cache),
            'hit_rate': self.stats['hits'] / max(self.stats['hits'] + self.stats['misses'], 1)
        }


# Global cache instance
_cache = SimpleCache()


def cached(ttl_seconds=300, cache_errors=False):
    """
    Decorator to cache function results
    
    Args:
        ttl_seconds: Time to live in seconds (default: 5 minutes)
        cache_errors: Whether to cache error results (default: False)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _cache._generate_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call the function
            try:
                result = func(*args, **kwargs)
                _cache.set(cache_key, result, ttl_seconds)
                return result
            except Exception as e:
                if cache_errors:
                    # Cache the error for a shorter time
                    _cache.set(cache_key, {'error': str(e)}, ttl_seconds // 10)
                raise
        
        return wrapper
    return decorator


def cached_async(ttl_seconds=300, cache_errors=False):
    """
    Decorator to cache async function results
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _cache._generate_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call the function
            try:
                result = await func(*args, **kwargs)
                _cache.set(cache_key, result, ttl_seconds)
                return result
            except Exception as e:
                if cache_errors:
                    # Cache the error for a shorter time
                    _cache.set(cache_key, {'error': str(e)}, ttl_seconds // 10)
                raise
        
        return wrapper
    return decorator


def get_cache_stats():
    """Get global cache statistics"""
    return _cache.get_stats()


def clear_cache():
    """Clear all cache entries"""
    _cache.clear()


# Cache TTL configurations
CACHE_TTL = {
    'company_screening': int(os.getenv('CACHE_TTL_COMPANY', '300')),  # 5 minutes
    'individual_screening': int(os.getenv('CACHE_TTL_INDIVIDUAL', '300')),  # 5 minutes
    'dart_lookup': int(os.getenv('CACHE_TTL_DART', '3600')),  # 1 hour
    'dart_search': int(os.getenv('CACHE_TTL_DART_SEARCH', '600')),  # 10 minutes
}