"""
Redis configuration utilities for Geriatric Administration System.
"""

import os
import logging
import redis
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_redis_info():
    """Get Redis connection information."""
    cache_settings = settings.CACHES['default']
    return {
        'backend': cache_settings['BACKEND'],
        'location': cache_settings['LOCATION'],
        'options': cache_settings.get('OPTIONS', {}),
    }


def test_redis_connection():
    """Test Redis connection and return status."""
    try:
        # Test Django cache
        cache.set('test_key', 'test_value', 30)
        result = cache.get('test_key')
        cache.delete('test_key')
        
        if result == 'test_value':
            logger.info("Redis connection successful")
            return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False
    return False


def get_redis_client():
    """Get direct Redis client for advanced operations."""
    try:
        redis_url = settings.CACHES['default']['LOCATION']
        client = redis.Redis.from_url(redis_url)
        return client
    except Exception as e:
        logger.error(f"Failed to create Redis client: {e}")
        return None


def get_redis_info_detailed():
    """Get detailed Redis server information."""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        info = client.info()
        return {
            'version': info.get('redis_version'),
            'mode': info.get('redis_mode'),
            'used_memory': info.get('used_memory_human'),
            'connected_clients': info.get('connected_clients'),
            'total_commands_processed': info.get('total_commands_processed'),
            'keyspace_hits': info.get('keyspace_hits'),
            'keyspace_misses': info.get('keyspace_misses'),
            'uptime_in_seconds': info.get('uptime_in_seconds'),
        }
    except Exception as e:
        logger.error(f"Failed to get Redis info: {e}")
        return None


def clear_redis_cache():
    """Clear all Redis cache data."""
    try:
        cache.clear()
        logger.info("Redis cache cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to clear Redis cache: {e}")
        return False


def get_cache_stats():
    """Get cache hit/miss statistics."""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        info = client.info()
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        stats = {
            'hits': hits,
            'misses': misses,
            'total_requests': total,
            'hit_rate_percentage': round(hit_rate, 2),
        }
        
        logger.info(f"Cache stats - Hit rate: {hit_rate:.2f}%, Hits: {hits}, Misses: {misses}")
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return None


def monitor_redis_memory():
    """Monitor Redis memory usage."""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        info = client.info('memory')
        memory_info = {
            'used_memory': info.get('used_memory'),
            'used_memory_human': info.get('used_memory_human'),
            'used_memory_peak': info.get('used_memory_peak'),
            'used_memory_peak_human': info.get('used_memory_peak_human'),
            'total_system_memory': info.get('total_system_memory'),
            'total_system_memory_human': info.get('total_system_memory_human'),
            'maxmemory': info.get('maxmemory'),
            'maxmemory_human': info.get('maxmemory_human'),
        }
        
        logger.info(f"Redis memory usage: {memory_info['used_memory_human']}")
        return memory_info
    except Exception as e:
        logger.error(f"Failed to get Redis memory info: {e}")
        return None


def cleanup_expired_keys():
    """Clean up expired keys from Redis."""
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        # Get info before cleanup
        info_before = client.info()
        keys_before = info_before.get('db1', {}).get('keys', 0) if 'db1' in info_before else 0
        
        # Force expire cleanup
        client.execute_command('MEMORY', 'PURGE')
        
        # Get info after cleanup
        info_after = client.info()
        keys_after = info_after.get('db1', {}).get('keys', 0) if 'db1' in info_after else 0
        
        cleaned_keys = keys_before - keys_after
        logger.info(f"Cleaned up {cleaned_keys} expired keys from Redis")
        
        return cleaned_keys
    except Exception as e:
        logger.error(f"Failed to cleanup expired keys: {e}")
        return 0


def set_cache_with_tags(key, value, timeout=300, tags=None):
    """Set cache value with tags for easier management."""
    try:
        cache.set(key, value, timeout)
        
        if tags:
            for tag in tags:
                tag_key = f"tag:{tag}"
                tagged_keys = cache.get(tag_key, set())
                tagged_keys.add(key)
                cache.set(tag_key, tagged_keys, timeout * 2)  # Tags live longer
        
        return True
    except Exception as e:
        logger.error(f"Failed to set cache with tags: {e}")
        return False


def invalidate_cache_by_tag(tag):
    """Invalidate all cache keys associated with a tag."""
    try:
        tag_key = f"tag:{tag}"
        tagged_keys = cache.get(tag_key, set())
        
        if tagged_keys:
            cache.delete_many(list(tagged_keys))
            cache.delete(tag_key)
            logger.info(f"Invalidated {len(tagged_keys)} cache keys for tag: {tag}")
            return len(tagged_keys)
        
        return 0
    except Exception as e:
        logger.error(f"Failed to invalidate cache by tag: {e}")
        return 0