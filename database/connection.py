"""Database connection management."""

from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from core.logger import get_logger
from core.config import Config
from core.exceptions import DatabaseError

logger = get_logger(__name__)

# SQLAlchemy base class for ORM models
Base = declarative_base()


class DatabaseConnection:
    """Database connection and session management."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            database_url: Database connection URL. Uses config if not provided.
        """
        try:
            if database_url is None:
                config = Config()
                database_url = config.database_url
            
            self.database_url = database_url
            logger.info(f"Initializing database: {database_url}")
            
            # Create engine with connection pooling
            self.engine = create_engine(
                database_url,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600,  # Recycle connections after 1 hour
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            )
            
            logger.info("Database connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    def get_session(self) -> Session:
        """Get a new database session.
        
        Returns:
            SQLAlchemy Session instance
        """
        return self.SessionLocal()
    
    def init_db(self):
        """Initialize database tables."""
        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise DatabaseError(f"Table creation failed: {e}")
    
    def drop_db(self):
        """Drop all database tables."""
        try:
            logger.warning("Dropping all database tables...")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise DatabaseError(f"Table drop failed: {e}")
    
    def close(self):
        """Close database connection."""
        try:
            self.engine.dispose()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
