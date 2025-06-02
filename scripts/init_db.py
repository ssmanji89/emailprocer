#!/usr/bin/env python3
"""
Database initialization script for EmailBot.
This script creates the database schema and initial data.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import init_database, close_database, Base, engine
from app.config.settings import settings
from app.models.email_models import *  # Import Pydantic models
from app.models.database_models import *  # Import SQLAlchemy models
from app.models.security_models import *  # Import security models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_initial_data():
    """Create initial data for the database."""
    from app.config.database import get_async_session
    
    try:
        async with get_async_session() as session:
            # Check if we need to create initial data
            logger.info("Database initialization completed successfully")
            
            # Add any initial data here if needed
            # For example, default configuration entries, admin users, etc.
            
    except Exception as e:
        logger.error(f"Failed to create initial data: {str(e)}")
        raise


async def verify_database_schema():
    """Verify that all tables were created correctly."""
    from app.config.database import get_async_session
    
    try:
        async with get_async_session() as session:
            # Get list of tables
            result = await session.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Created tables: {', '.join(tables)}")
            
            # Verify expected tables exist
            expected_tables = [
                'emailmessages',
                'classificationresults', 
                'processingresults',
                'escalationteams',
                'emailpatterns'
            ]
            
            missing_tables = [table for table in expected_tables if table not in tables]
            if missing_tables:
                logger.warning(f"Missing expected tables: {', '.join(missing_tables)}")
            else:
                logger.info("All expected tables created successfully")
                
    except Exception as e:
        # For SQLite, use different query
        if "information_schema" in str(e):
            try:
                async with get_async_session() as session:
                    result = await session.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """)
                    tables = [row[0] for row in result.fetchall()]
                    logger.info(f"Created tables (SQLite): {', '.join(tables)}")
            except Exception as sqlite_e:
                logger.error(f"Failed to verify database schema: {str(sqlite_e)}")
        else:
            logger.error(f"Failed to verify database schema: {str(e)}")


async def main():
    """Main initialization function."""
    logger.info("Starting EmailBot database initialization...")
    
    try:
        # Initialize database connection and create tables
        logger.info("Initializing database connection...")
        await init_database()
        
        logger.info("Creating database schema...")
        # Tables are created in init_database()
        
        # Verify schema
        logger.info("Verifying database schema...")
        await verify_database_schema()
        
        # Create initial data
        logger.info("Creating initial data...")
        await create_initial_data()
        
        logger.info("✅ Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        sys.exit(1)
        
    finally:
        # Close database connections
        await close_database()


if __name__ == "__main__":
    # Check if environment is set up
    if not settings.database_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)
    
    # Run initialization
    asyncio.run(main()) 