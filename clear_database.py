#!/usr/bin/env python3
"""
Clear all user data from the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from auth.models import User, OTP, PendingRegistration

def clear_all_auth_data():
    """Clear all authentication-related data"""
    print("🗑️  Clearing all authentication data from database...")
    
    db = next(get_db())
    try:
        # Count existing records
        user_count = db.query(User).count()
        otp_count = db.query(OTP).count()
        
        try:
            pending_count = db.query(PendingRegistration).count()
        except:
            pending_count = 0  # Table might not exist yet
        
        print(f"Found {user_count} users, {otp_count} OTPs, {pending_count} pending registrations")
        
        # Delete all records
        db.query(User).delete()
        print("✅ Deleted all users")
        
        db.query(OTP).delete()
        print("✅ Deleted all OTPs")
        
        try:
            db.query(PendingRegistration).delete()
            print("✅ Deleted all pending registrations")
        except:
            print("ℹ️  No pending registrations table found (will be created later)")
        
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
    print("⚠️  WARNING: This will delete ALL user data!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        clear_all_auth_data()
    else:
        print("❌ Operation cancelled")
