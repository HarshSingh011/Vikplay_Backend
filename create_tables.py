#!/usr/bin/env python3
"""
Create database tables for VidPlay application
"""
from database import engine, Base
import models.models as models
import auth.models as auth_models

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    # This will create all tables including auth tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print("Tables created:")
    for table in Base.metadata.tables:
        print(f"  - {table}")

if __name__ == "__main__":
    create_tables()
