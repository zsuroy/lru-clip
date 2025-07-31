"""
Database configuration and session management for CLIP.LRU
"""
from sqlalchemy import create_engine, orm
from sqlalchemy.orm import sessionmaker
from app.config import settings


def check_database_dependencies(database_url: str):
    """Check if required database dependencies are installed"""
    if database_url.startswith("mysql"):
        try:
            import MySQLdb  # mysqlclient
        except ImportError:
            try:
                import pymysql  # alternative MySQL driver
            except ImportError:
                raise ImportError(
                    "MySQL database driver not found. Please install mysqlclient or pymysql:\n"
                    "  pip install -r requirements-mysql.txt\n"
                    "  or\n"
                    "  pip install mysqlclient\n"
                    "  or\n"
                    "  pip install pymysql"
                )
    elif database_url.startswith("postgresql"):
        try:
            import psycopg2  # PostgreSQL driver
        except ImportError:
            raise ImportError(
                "PostgreSQL database driver not found. Please install psycopg2:\n"
                "  pip install psycopg2-binary"
            )
    # SQLite is built into Python, no additional dependencies needed


def get_engine_config(database_url: str) -> dict:
    """Get database engine configuration based on database type"""
    if database_url.startswith("sqlite"):
        # SQLite specific configuration
        return {
            "connect_args": {
                "check_same_thread": False,  # Allow multiple threads
                "timeout": 20,  # Connection timeout
            },
            "pool_pre_ping": True,
            "echo": settings.debug,
            # SQLite doesn't support connection pooling in the traditional sense
            "poolclass": None,
        }
    else:
        # MySQL/PostgreSQL configuration
        return {
            "pool_pre_ping": True,
            "pool_recycle": settings.db_pool_recycle,
            "echo": settings.debug,
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
        }


# Check database dependencies before creating engine
check_database_dependencies(settings.database_url)

# Create database engine with optimized configuration
engine_config = get_engine_config(settings.database_url)
engine = create_engine(settings.database_url, **engine_config)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = orm.declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables (for testing)"""
    Base.metadata.drop_all(bind=engine)
