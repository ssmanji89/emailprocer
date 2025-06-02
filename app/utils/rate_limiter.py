import asyncio
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for controlling API request rates and preventing abuse."""
    
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds (default: 1 hour)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        
        # Track requests per client/operation
        self.request_history: Dict[str, deque] = defaultdict(deque)
        
        # Track blocked clients
        self.blocked_clients: Dict[str, float] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "unique_clients": 0
        }
    
    async def allow_request(self, client_id: str) -> bool:
        """
        Check if a request should be allowed for the given client.
        
        Args:
            client_id: Unique identifier for the client making the request
            
        Returns:
            True if request is allowed, False if rate limited
        """
        async with self._lock:
            current_time = time.time()
            self.stats["total_requests"] += 1
            
            # Check if client is currently blocked
            if client_id in self.blocked_clients:
                if current_time < self.blocked_clients[client_id]:
                    self.stats["blocked_requests"] += 1
                    logger.warning(f"Request blocked for client {client_id} - still in timeout")
                    return False
                else:
                    # Remove expired block
                    del self.blocked_clients[client_id]
            
            # Clean old requests outside time window
            self._cleanup_old_requests(client_id, current_time)
            
            # Check current request count
            request_count = len(self.request_history[client_id])
            
            if request_count >= self.max_requests:
                # Rate limit exceeded
                self._block_client(client_id, current_time)
                self.stats["blocked_requests"] += 1
                logger.warning(
                    f"Rate limit exceeded for client {client_id}: "
                    f"{request_count} requests in {self.time_window}s window"
                )
                return False
            
            # Allow request and record it
            self.request_history[client_id].append(current_time)
            self.stats["allowed_requests"] += 1
            
            # Update unique clients count
            if request_count == 0:  # First request from this client
                self.stats["unique_clients"] += 1
                
            logger.debug(f"Request allowed for client {client_id}: {request_count + 1}/{self.max_requests}")
            return True
    
    def _cleanup_old_requests(self, client_id: str, current_time: float) -> None:
        """Remove requests outside the current time window."""
        cutoff_time = current_time - self.time_window
        
        while (self.request_history[client_id] and 
               self.request_history[client_id][0] < cutoff_time):
            self.request_history[client_id].popleft()
    
    def _block_client(self, client_id: str, current_time: float) -> None:
        """Block a client for a specified duration."""
        # Block for the time window duration
        block_until = current_time + self.time_window
        self.blocked_clients[client_id] = block_until
        
        logger.info(f"Client {client_id} blocked until {datetime.fromtimestamp(block_until)}")
    
    async def get_client_status(self, client_id: str) -> Dict[str, Any]:
        """Get current status for a specific client."""
        async with self._lock:
            current_time = time.time()
            self._cleanup_old_requests(client_id, current_time)
            
            request_count = len(self.request_history[client_id])
            is_blocked = client_id in self.blocked_clients
            
            status = {
                "client_id": client_id,
                "current_requests": request_count,
                "max_requests": self.max_requests,
                "time_window_seconds": self.time_window,
                "requests_remaining": max(0, self.max_requests - request_count),
                "is_blocked": is_blocked,
                "reset_time": None
            }
            
            if is_blocked:
                reset_time = self.blocked_clients[client_id]
                status["reset_time"] = datetime.fromtimestamp(reset_time).isoformat()
                status["seconds_until_reset"] = max(0, int(reset_time - current_time))
            elif request_count > 0:
                # Calculate when the window resets (when oldest request expires)
                oldest_request = self.request_history[client_id][0]
                reset_time = oldest_request + self.time_window
                status["reset_time"] = datetime.fromtimestamp(reset_time).isoformat()
                status["seconds_until_reset"] = max(0, int(reset_time - current_time))
            
            return status
    
    async def reset_client(self, client_id: str) -> bool:
        """Reset rate limiting for a specific client (admin function)."""
        async with self._lock:
            try:
                # Remove from blocked clients
                if client_id in self.blocked_clients:
                    del self.blocked_clients[client_id]
                
                # Clear request history
                if client_id in self.request_history:
                    self.request_history[client_id].clear()
                
                logger.info(f"Rate limiting reset for client {client_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error resetting client {client_id}: {str(e)}")
                return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall rate limiting statistics."""
        async with self._lock:
            current_time = time.time()
            
            # Count currently active clients
            active_clients = 0
            for client_id in list(self.request_history.keys()):
                self._cleanup_old_requests(client_id, current_time)
                if len(self.request_history[client_id]) > 0:
                    active_clients += 1
            
            # Count blocked clients
            blocked_count = len([
                client_id for client_id, block_time in self.blocked_clients.items()
                if block_time > current_time
            ])
            
            return {
                **self.stats,
                "active_clients": active_clients,
                "blocked_clients": blocked_count,
                "max_requests_per_window": self.max_requests,
                "time_window_seconds": self.time_window,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup_expired_data(self) -> None:
        """Clean up expired request history and blocks."""
        async with self._lock:
            current_time = time.time()
            
            # Clean up expired blocks
            expired_blocks = [
                client_id for client_id, block_time in self.blocked_clients.items()
                if block_time <= current_time
            ]
            
            for client_id in expired_blocks:
                del self.blocked_clients[client_id]
                logger.debug(f"Removed expired block for client {client_id}")
            
            # Clean up empty request histories
            empty_clients = [
                client_id for client_id, requests in self.request_history.items()
                if len(requests) == 0
            ]
            
            for client_id in empty_clients:
                del self.request_history[client_id]
                logger.debug(f"Removed empty request history for client {client_id}")
            
            logger.debug(f"Cleanup completed: removed {len(expired_blocks)} expired blocks, "
                        f"{len(empty_clients)} empty histories")


class AdaptiveRateLimiter(RateLimiter):
    """Advanced rate limiter with adaptive limits based on system load."""
    
    def __init__(self, base_max_requests: int = 100, time_window: int = 3600):
        super().__init__(base_max_requests, time_window)
        self.base_max_requests = base_max_requests
        self.load_factor = 1.0  # Multiplier for rate limits based on system load
        
        # Load monitoring
        self.load_history = deque(maxlen=60)  # Last 60 measurements
        self.last_load_check = 0
        self.load_check_interval = 60  # Check load every 60 seconds
    
    async def allow_request(self, client_id: str) -> bool:
        """Allow request with adaptive rate limiting based on system load."""
        await self._update_system_load()
        
        # Adjust max requests based on current load
        self.max_requests = max(1, int(self.base_max_requests * self.load_factor))
        
        return await super().allow_request(client_id)
    
    async def _update_system_load(self) -> None:
        """Update system load factor for adaptive rate limiting."""
        current_time = time.time()
        
        if current_time - self.last_load_check < self.load_check_interval:
            return
        
        self.last_load_check = current_time
        
        try:
            # Simple load calculation based on active requests
            total_active_requests = sum(
                len(requests) for requests in self.request_history.values()
            )
            
            # Calculate load factor (lower when system is busy)
            if total_active_requests > self.base_max_requests * 2:
                self.load_factor = 0.5  # Reduce to 50% capacity
            elif total_active_requests > self.base_max_requests:
                self.load_factor = 0.75  # Reduce to 75% capacity
            else:
                self.load_factor = 1.0  # Normal capacity
            
            self.load_history.append({
                "timestamp": current_time,
                "load_factor": self.load_factor,
                "active_requests": total_active_requests
            })
            
            logger.debug(f"Updated load factor to {self.load_factor} "
                        f"(active requests: {total_active_requests})")
            
        except Exception as e:
            logger.error(f"Error updating system load: {str(e)}")
            self.load_factor = 1.0  # Fall back to normal capacity
    
    async def get_load_statistics(self) -> Dict[str, Any]:
        """Get load-related statistics."""
        stats = await self.get_statistics()
        
        stats.update({
            "current_load_factor": self.load_factor,
            "base_max_requests": self.base_max_requests,
            "adjusted_max_requests": self.max_requests,
            "load_history_size": len(self.load_history)
        })
        
        if self.load_history:
            recent_loads = [entry["load_factor"] for entry in self.load_history]
            stats.update({
                "average_load_factor": sum(recent_loads) / len(recent_loads),
                "min_load_factor": min(recent_loads),
                "max_load_factor": max(recent_loads)
            })
        
        return stats


# Global rate limiter instances
default_rate_limiter = RateLimiter(max_requests=100, time_window=3600)
adaptive_rate_limiter = AdaptiveRateLimiter(base_max_requests=100, time_window=3600) 