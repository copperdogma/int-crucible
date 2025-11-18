"""
Unit tests for cache system.

Tests all cache types (Memory, Disk, Hybrid, Redis) and cache manager.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from kosmos.core.cache import (
    MemoryCache,
    DiskCache,
    HybridCache,
    CacheManager,
    CacheStats,
    CacheEntry
)


class TestMemoryCache:
    """Test MemoryCache implementation."""

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = MemoryCache(max_size=100)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent(self):
        """Test getting nonexistent key returns None."""
        cache = MemoryCache(max_size=100)
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = MemoryCache(max_size=100)

        # Set with 0 second TTL (should expire immediately)
        cache.set("key1", "value1", ttl=0)
        assert cache.get("key1") is None

    def test_delete(self):
        """Test deletion."""
        cache = MemoryCache(max_size=100)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        """Test clearing all entries."""
        cache = MemoryCache(max_size=100)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_exists(self):
        """Test exists check."""
        cache = MemoryCache(max_size=100)

        cache.set("key1", "value1")
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False

    def test_size_tracking(self):
        """Test size tracking."""
        cache = MemoryCache(max_size=1000)

        cache.set("key1", "a" * 100)
        stats = cache.stats()

        assert stats.entries == 1
        assert stats.size_bytes > 0

    def test_lru_eviction(self):
        """Test LRU eviction when max size exceeded."""
        cache = MemoryCache(max_size=100)  # Small size to trigger eviction

        # Fill cache beyond capacity
        for i in range(20):
            cache.set(f"key{i}", "x" * 10)

        stats = cache.stats()
        # Should have evicted old entries
        assert stats.entries < 20

    def test_stats(self):
        """Test statistics collection."""
        cache = MemoryCache(max_size=1000)

        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss

        stats = cache.stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.entries == 1


class TestDiskCache:
    """Test DiskCache implementation."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_set_and_get(self, temp_cache_dir):
        """Test basic set and get operations."""
        cache = DiskCache(cache_dir=temp_cache_dir, max_size=1024*1024)

        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")

        assert result["data"] == "value1"

    def test_persistence(self, temp_cache_dir):
        """Test data persists across cache instances."""
        cache1 = DiskCache(cache_dir=temp_cache_dir, max_size=1024*1024)
        cache1.set("key1", "value1")

        # Create new cache instance with same directory
        cache2 = DiskCache(cache_dir=temp_cache_dir, max_size=1024*1024)
        assert cache2.get("key1") == "value1"

    def test_ttl_expiration(self, temp_cache_dir):
        """Test TTL expiration on disk."""
        cache = DiskCache(cache_dir=temp_cache_dir, max_size=1024*1024)

        cache.set("key1", "value1", ttl=0)
        assert cache.get("key1") is None

    def test_file_creation(self, temp_cache_dir):
        """Test cache files are created."""
        cache = DiskCache(cache_dir=temp_cache_dir, max_size=1024*1024)

        cache.set("test_key", "test_value")

        # Check file exists
        cache_files = list(temp_cache_dir.glob("*.cache"))
        assert len(cache_files) > 0

    def test_cleanup_expired(self, temp_cache_dir):
        """Test cleanup of expired entries."""
        cache = DiskCache(cache_dir=temp_cache_dir, max_size=1024*1024)

        # Set with immediate expiration
        cache.set("expired", "value", ttl=0)
        cache.set("valid", "value", ttl=3600)

        # Cleanup should remove expired
        cache._cleanup()

        assert cache.get("expired") is None
        assert cache.get("valid") == "value"


class TestHybridCache:
    """Test HybridCache implementation."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_memory_then_disk(self, temp_cache_dir):
        """Test hybrid cache checks memory first, then disk."""
        cache = HybridCache(
            memory_max_size=100,
            disk_cache_dir=temp_cache_dir,
            disk_max_size=1024*1024
        )

        # Set in cache (should go to memory)
        cache.set("key1", "value1")

        # Should retrieve from memory (fast)
        assert cache.get("key1") == "value1"

        # Clear memory to force disk retrieval
        cache.memory_cache.clear()

        # Should still get value from disk
        assert cache.get("key1") == "value1"

    def test_stats_aggregation(self, temp_cache_dir):
        """Test stats aggregate from both caches."""
        cache = HybridCache(
            memory_max_size=100,
            disk_cache_dir=temp_cache_dir,
            disk_max_size=1024*1024
        )

        cache.set("key1", "value1")
        cache.get("key1")

        stats = cache.stats()
        assert stats.hits > 0


class TestCacheManager:
    """Test CacheManager orchestration."""

    def test_cache_selection(self):
        """Test cache selection by type."""
        manager = CacheManager()

        memory_cache = manager.get_cache("memory")
        assert isinstance(memory_cache, MemoryCache)

    def test_default_cache(self):
        """Test getting default cache."""
        manager = CacheManager()

        default_cache = manager.get_cache()
        assert default_cache is not None

    def test_set_get_through_manager(self):
        """Test set/get through manager."""
        manager = CacheManager()

        manager.set("test_key", "test_value", cache_type="memory")
        result = manager.get("test_key", cache_type="memory")

        assert result == "test_value"

    def test_clear_all_caches(self):
        """Test clearing all caches."""
        manager = CacheManager()

        manager.set("key1", "value1", cache_type="memory")
        manager.clear_all()

        assert manager.get("key1", cache_type="memory") is None

    def test_global_stats(self):
        """Test getting stats from all caches."""
        manager = CacheManager()

        manager.set("key1", "value1", cache_type="memory")
        manager.get("key1", cache_type="memory")

        stats = manager.get_stats()
        assert "memory" in stats


class TestCacheStats:
    """Test CacheStats data class."""

    def test_hit_ratio_calculation(self):
        """Test hit ratio calculation."""
        stats = CacheStats(hits=7, misses=3, entries=10, size_bytes=1000)

        assert stats.hit_ratio == 0.7

    def test_hit_ratio_zero_requests(self):
        """Test hit ratio when no requests."""
        stats = CacheStats(hits=0, misses=0, entries=0, size_bytes=0)

        assert stats.hit_ratio == 0.0


class TestCacheEntry:
    """Test CacheEntry data class."""

    def test_is_expired(self):
        """Test expiration checking."""
        # Entry with past expiry
        past = datetime.utcnow() - timedelta(seconds=10)
        expired_entry = CacheEntry(key="test", value="test", expires_at=past)

        assert expired_entry.is_expired() is True

        # Entry with future expiry
        future = datetime.utcnow() + timedelta(seconds=10)
        valid_entry = CacheEntry(key="test", value="test", expires_at=future)

        assert valid_entry.is_expired() is False

    def test_no_expiry(self):
        """Test entries without expiry never expire."""
        entry = CacheEntry(key="test", value="test", expires_at=None)

        assert entry.is_expired() is False


class TestRedisCache:
    """Test RedisCache implementation (requires Redis running)."""

    @pytest.fixture
    def redis_available(self):
        """Check if Redis is available for testing."""
        try:
            import redis
            client = redis.from_url("redis://localhost:6379/15", socket_timeout=1)
            client.ping()
            client.flushdb()  # Clean test database
            return True
        except:
            pytest.skip("Redis not available for testing")

    def test_redis_set_get(self, redis_available):
        """Test Redis cache set/get."""
        from kosmos.core.cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/15")

        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        cache.client.flushdb()

    def test_redis_ttl(self, redis_available):
        """Test Redis TTL expiration."""
        from kosmos.core.cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/15")

        cache.set("test_key", "test_value", ttl=1)

        import time
        time.sleep(2)

        assert cache.get("test_key") is None

        cache.client.flushdb()

    def test_redis_stats(self, redis_available):
        """Test Redis stats collection."""
        from kosmos.core.cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/15")

        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss

        stats = cache.stats()
        assert stats.hits == 1
        assert stats.misses == 1

        cache.client.flushdb()
