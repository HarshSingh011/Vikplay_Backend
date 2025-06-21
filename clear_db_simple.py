#!/usr/bin/env python3
"""
Clear all user data from the database - AUTO CONFIRM
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from auth.models import User, OTP

def clear_all_auth_data():
    """Clear all authentication-related data"""
    print("🗑️  Clearing all authentication data from database...")
    
    db = next(get_db())
    try:
        # Count existing records
        user_count = db.query(User).count()
        otp_count = db.query(OTP).count()
        
        print(f"Found {user_count} users, {otp_count} OTPs")
        
        # Delete all records
        deleted_users = db.query(User).delete()
        print(f"✅ Deleted {deleted_users} users")
        
        deleted_otps = db.query(OTP).delete()
        print(f"✅ Deleted {deleted_otps} OTPs")
        
        # Commit changes
        db.commit()
        print("✅ All authentication data cleared successfully!")
        
        # Verify deletion
        remaining_users = db.query(User).count()
        remaining_otps = db.query(OTP).count()
        
        print(f"✅ Verification: {remaining_users} users, {remaining_otps} OTPs remaining")
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_auth_data()
