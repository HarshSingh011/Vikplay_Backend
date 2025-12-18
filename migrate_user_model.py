"""
Migration script to add phone_number and full_name fields to existing users.
Run this script after updating the User model.

This is a one-time migration script.
"""
from sqlalchemy import text
from database import engine, SessionLocal
from auth.models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    db = SessionLocal()
    try:
        # For SQLite
        result = db.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result]
        return column_name in columns
    except Exception as e:
        logger.error(f"Error checking column: {e}")
        return False
    finally:
        db.close()


def add_column_if_not_exists(table_name: str, column_name: str, column_type: str):
    """Add a column to a table if it doesn't exist."""
    db = SessionLocal()
    try:
        if not check_column_exists(table_name, column_name):
            logger.info(f"Adding column {column_name} to {table_name}")
            db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
            db.commit()
            logger.info(f"Column {column_name} added successfully")
        else:
            logger.info(f"Column {column_name} already exists in {table_name}")
    except Exception as e:
        logger.error(f"Error adding column: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_user_model():
    """Add phone_number and full_name to users table."""
    logger.info("Starting user model migration...")
    
    # Add phone_number column
    add_column_if_not_exists(
        table_name="users",
        column_name="phone_number",
        column_type="VARCHAR(20)"
    )
    
    # Add full_name column
    add_column_if_not_exists(
        table_name="users",
        column_name="full_name",
        column_type="VARCHAR(100)"
    )
    
    logger.info("User model migration completed!")


def add_sample_phone_numbers():
    """
    Add sample phone numbers to existing users for testing.
    WARNING: This is for development/testing only!
    """
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.phone_number == None).all()
        
        if not users:
            logger.info("No users without phone numbers found")
            return
        
        logger.info(f"Found {len(users)} users without phone numbers")
        
        # Add sample phone numbers (for testing only)
        for idx, user in enumerate(users, start=1):
            sample_phone = f"+1234567{idx:04d}"  # Generate unique phone numbers
            user.phone_number = sample_phone
            
            if not user.full_name:
                user.full_name = user.username.title()
            
            logger.info(f"Updated user {user.username}: phone={sample_phone}, name={user.full_name}")
        
        db.commit()
        logger.info(f"Added phone numbers to {len(users)} users")
        
    except Exception as e:
        logger.error(f"Error adding sample phone numbers: {e}")
        db.rollback()
    finally:
        db.close()


def verify_migration():
    """Verify the migration was successful."""
    logger.info("Verifying migration...")
    
    db = SessionLocal()
    try:
        # Check if columns exist
        has_phone = check_column_exists("users", "phone_number")
        has_name = check_column_exists("users", "full_name")
        
        if has_phone and has_name:
            logger.info("✅ Migration verified: All columns exist")
            
            # Count users with phone numbers
            users_with_phone = db.query(User).filter(User.phone_number != None).count()
            total_users = db.query(User).count()
            
            logger.info(f"📊 Users with phone numbers: {users_with_phone}/{total_users}")
            
            return True
        else:
            logger.error("❌ Migration verification failed")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying migration: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("User Model Migration Script")
    print("=" * 60)
    print()
    
    # Step 1: Migrate schema
    migrate_user_model()
    
    # Step 2: Verify migration
    if verify_migration():
        print()
        print("Migration successful!")
        print()
        
        # Optional: Add sample data
        response = input("Do you want to add sample phone numbers to existing users? (y/n): ")
        if response.lower() == 'y':
            add_sample_phone_numbers()
            verify_migration()
        
        print()
        print("=" * 60)
        print("Migration completed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Verify users have phone numbers in the database")
        print("2. Update user registration to include phone_number field")
        print("3. Test the call feature with call_client.html")
    else:
        print()
        print("Migration failed. Please check the logs.")
