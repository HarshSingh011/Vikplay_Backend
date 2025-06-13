#!/usr/bin/env python3
"""
Create database tables for VidPlay application
"""
from database import engine, Base
import models.models as models

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
