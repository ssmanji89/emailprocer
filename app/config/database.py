import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from contextlib import asynccontextmanager

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Database metadata and base
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Global database engine and session maker
engine: Optional[Any] = None
async_session_maker: Optional[sessionmaker] = None


def get_engine_config() -> Dict[str, Any]:
    """Get database engine configuration."""
    db_config = settings.get_database_config()
    
    # Determine if we're using SQLite or PostgreSQL
    is_sqlite = db_config["url"].startswith("sqlite")
    
    if is_sqlite:
        # SQLite configuration
        engine_config = {
            "url": db_config["url"],
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 20
            },
            "echo": settings.debug,
        }
    else:
        # PostgreSQL configuration
        engine_config = {
            "url": db_config["url"],
            "poolclass": QueuePool,
            "pool_size": db_config["pool_size"],
            "max_overflow": db_config["max_overflow"],
            "pool_timeout": db_config["pool_timeout"],
            "pool_recycle": db_config["pool_recycle"],
            "pool_pre_ping": True,
            "echo": settings.debug,
        }
    
    return engine_config


async def init_database() -> None:
    """Initialize database connection and create tables."""
    global engine, async_session_maker
    
    try:
        engine_config = get_engine_config()
        
        # Create async engine
        engine = create_async_engine(**engine_config)
        
        # Create session maker
        async_session_maker = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
        
        # Test connection
        await test_database_connection()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def test_database_connection() -> Dict[str, Any]:
    """Test database connection and return status."""
    try:
        async with get_async_session() as session:
            # Simple query to test connection
            result = await session.execute("SELECT 1 as test")
            test_value = result.scalar()
            
            if test_value == 1:
                return {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "engine_info": {
                        "url": str(engine.url).replace(engine.url.password or "", "***"),
                        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else None,
                        "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else None,
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Database test query failed"
                }
                
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with automatic cleanup."""
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


async def get_session() -> AsyncSession:
    """Get async database session (for dependency injection)."""
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return async_session_maker()


async def close_database() -> None:
    """Close database connections."""
    global engine, async_session_maker
    
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")
    
    engine = None
    async_session_maker = None


# Database session dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with get_async_session() as session:
        yield session


# Database health check
async def health_check() -> Dict[str, Any]:
    """Comprehensive database health check."""
    try:
        # Test basic connection
        connection_test = await test_database_connection()
        
        if connection_test["status"] != "healthy":
            return connection_test
        
        # Test transaction capability
        async with get_async_session() as session:
            await session.execute("BEGIN")
            await session.execute("ROLLBACK")
        
        # Get pool statistics
        pool_stats = {}
        if engine and hasattr(engine.pool, 'size'):
            pool_stats = {
                "pool_size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "invalid": engine.pool.invalid()
            }
        
        return {
            "status": "healthy",
            "message": "Database is fully operational",
            "pool_stats": pool_stats,
            "engine_info": connection_test.get("engine_info", {})
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database health check failed: {str(e)}"
        }


# Event listeners for connection management
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance and reliability."""
    if "sqlite" in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Set WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Set synchronous mode for better performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Set cache size
        cursor.execute("PRAGMA cache_size=10000")
        # Set temp store in memory
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


# Connection retry decorator
def with_db_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator for database operations with retry logic."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        logger.error(f"Database operation failed after {max_retries} attempts: {str(e)}")
            
            raise last_exception
        return wrapper
    return decorator 