# db.py improvements
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool
import os
import dotenv

# Construct the absolute path to the .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("SUPABASE_URL")

# Enhanced engine with connection pooling and logging
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL logging
)

# Add connection event logging
@event.listens_for(engine, "connect")
def log_connection(dbapi_connection, connection_record):
    logger.info("New database connection established")

@event.listens_for(engine, "checkout")
def log_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("Connection checked out from pool")