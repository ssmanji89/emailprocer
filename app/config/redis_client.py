import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
redis_client: Optional[Redis] = None
connection_pool: Optional[ConnectionPool] = None


class RedisClient:
    """Async Redis client with enhanced functionality."""
    
    def __init__(self, redis_instance: Redis):
        self.redis = redis_instance
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from Redis with JSON deserialization."""
        try:
            value = await self.redis.get(key)
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except Exception as e:
            logger.error(f"Redis GET operation failed for key '{key}': {str(e)}")
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set value in Redis with JSON serialization."""
        try:
            # Serialize value to JSON if it's not a string
            if isinstance(value, (dict, list, bool, int, float)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Set with options
            result = await self.redis.set(
                key, 
                serialized_value, 
                ex=ttl,
                nx=nx,
                xx=xx
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis SET operation failed for key '{key}': {str(e)}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from Redis."""
        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE operation failed for keys {keys}: {str(e)}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS operation failed for key '{key}': {str(e)}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        try:
            return bool(await self.redis.expire(key, ttl))
        except Exception as e:
            logger.error(f"Redis EXPIRE operation failed for key '{key}': {str(e)}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for key."""
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL operation failed for key '{key}': {str(e)}")
            return -1
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment key value."""
        try:
            return await self.redis.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR operation failed for key '{key}': {str(e)}")
            return None
    
    async def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement key value."""
        try:
            return await self.redis.decr(key, amount)
        except Exception as e:
            logger.error(f"Redis DECR operation failed for key '{key}': {str(e)}")
            return None
    
    async def hget(self, hash_key: str, field: str, default: Any = None) -> Any:
        """Get field from hash."""
        try:
            value = await self.redis.hget(hash_key, field)
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except Exception as e:
            logger.error(f"Redis HGET operation failed for '{hash_key}.{field}': {str(e)}")
            return default
    
    async def hset(self, hash_key: str, field: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set field in hash."""
        try:
            # Serialize value
            if isinstance(value, (dict, list, bool, int, float)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            result = await self.redis.hset(hash_key, field, serialized_value)
            
            # Set TTL if specified
            if ttl and result:
                await self.redis.expire(hash_key, ttl)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis HSET operation failed for '{hash_key}.{field}': {str(e)}")
            return False
    
    async def hgetall(self, hash_key: str) -> Dict[str, Any]:
        """Get all fields from hash."""
        try:
            result = await self.redis.hgetall(hash_key)
            
            # Convert and deserialize
            parsed_result = {}
            for field, value in result.items():
                field_str = field.decode('utf-8') if isinstance(field, bytes) else field
                
                try:
                    parsed_result[field_str] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_result[field_str] = value.decode('utf-8') if isinstance(value, bytes) else value
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Redis HGETALL operation failed for '{hash_key}': {str(e)}")
            return {}
    
    async def hdel(self, hash_key: str, *fields: str) -> int:
        """Delete fields from hash."""
        try:
            return await self.redis.hdel(hash_key, *fields)
        except Exception as e:
            logger.error(f"Redis HDEL operation failed for '{hash_key}': {str(e)}")
            return 0
    
    async def lpush(self, list_key: str, *values: Any) -> Optional[int]:
        """Push values to left of list."""
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list, bool, int, float)):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(str(value))
            
            return await self.redis.lpush(list_key, *serialized_values)
            
        except Exception as e:
            logger.error(f"Redis LPUSH operation failed for '{list_key}': {str(e)}")
            return None
    
    async def rpop(self, list_key: str, count: int = 1) -> Optional[Union[Any, List[Any]]]:
        """Pop values from right of list."""
        try:
            if count == 1:
                value = await self.redis.rpop(list_key)
                if value is None:
                    return None
                
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value.decode('utf-8') if isinstance(value, bytes) else value
            else:
                values = await self.redis.rpop(list_key, count)
                if not values:
                    return []
                
                result = []
                for value in values:
                    try:
                        result.append(json.loads(value))
                    except (json.JSONDecodeError, TypeError):
                        result.append(value.decode('utf-8') if isinstance(value, bytes) else value)
                
                return result
                
        except Exception as e:
            logger.error(f"Redis RPOP operation failed for '{list_key}': {str(e)}")
            return None
    
    async def llen(self, list_key: str) -> int:
        """Get list length."""
        try:
            return await self.redis.llen(list_key)
        except Exception as e:
            logger.error(f"Redis LLEN operation failed for '{list_key}': {str(e)}")
            return 0
    
    async def ping(self) -> bool:
        """Test Redis connection."""
        try:
            response = await self.redis.ping()
            return response is True
        except Exception as e:
            logger.error(f"Redis PING failed: {str(e)}")
            return False


async def init_redis() -> None:
    """Initialize Redis connection."""
    global redis_client, connection_pool
    
    try:
        redis_config = settings.get_redis_config()
        
        # Create connection pool
        connection_pool = ConnectionPool.from_url(
            redis_config["url"],
            password=redis_config["password"],
            max_connections=redis_config["max_connections"],
            socket_timeout=redis_config["socket_timeout"],
            socket_connect_timeout=redis_config["socket_connect_timeout"],
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Create Redis client
        redis_instance = Redis(connection_pool=connection_pool)
        redis_client = RedisClient(redis_instance)
        
        # Test connection
        if await redis_client.ping():
            logger.info("Redis connection initialized successfully")
        else:
            raise ConnectionError("Redis ping test failed")
            
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {str(e)}")
        raise


async def get_redis() -> RedisClient:
    """Get Redis client instance."""
    if redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


async def close_redis() -> None:
    """Close Redis connections."""
    global redis_client, connection_pool
    
    if redis_client:
        await redis_client.redis.close()
        logger.info("Redis connections closed")
    
    if connection_pool:
        await connection_pool.disconnect()
    
    redis_client = None
    connection_pool = None


async def health_check() -> Dict[str, Any]:
    """Redis health check."""
    try:
        if redis_client is None:
            return {
                "status": "unhealthy",
                "message": "Redis client not initialized"
            }
        
        # Test ping
        ping_success = await redis_client.ping()
        if not ping_success:
            return {
                "status": "unhealthy",
                "message": "Redis ping failed"
            }
        
        # Test basic operations
        test_key = "emailbot:health_check"
        test_value = {"timestamp": datetime.utcnow().isoformat(), "test": True}
        
        # Set and get test
        set_success = await redis_client.set(test_key, test_value, ttl=10)
        if not set_success:
            return {
                "status": "unhealthy",
                "message": "Redis SET operation failed"
            }
        
        get_result = await redis_client.get(test_key)
        if get_result != test_value:
            return {
                "status": "unhealthy",
                "message": "Redis GET operation failed"
            }
        
        # Clean up
        await redis_client.delete(test_key)
        
        # Get connection info
        info = await redis_client.redis.info()
        
        return {
            "status": "healthy",
            "message": "Redis is fully operational",
            "info": {
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "redis_version": info.get("redis_version"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
        }
        
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Redis health check failed: {str(e)}"
        }


# Cache decorator
def cache_result(key_template: str, ttl: int = 3600):
    """Decorator to cache function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = key_template.format(*args, **kwargs)
            
            try:
                # Try to get from cache
                cached_result = await redis_client.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await redis_client.set(cache_key, result, ttl=ttl)
                logger.debug(f"Cached result for key: {cache_key}")
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache operation failed for key '{cache_key}': {str(e)}")
                # Fall back to executing function without cache
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator 