from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration - supports both SQLite and PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    # If no DATABASE_URL provided, try individual settings for PostgreSQL
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "vikpay_db")
    
    # Default to SQLite if PostgreSQL credentials not provided
    if all([DB_USER != "postgres" or os.getenv("DB_PASSWORD"), DB_HOST, DB_PORT, DB_NAME]):
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        DATABASE_URL = "sqlite:///./vidplay.db"

print(f"Using database: {DATABASE_URL}")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()