#!/usr/bin/env python3
"""
Test email functionality
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email_config():
    """Test email configuration"""
    print("="*50)
    print("TESTING EMAIL CONFIGURATION")
    print("="*50)
    
    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    
    print(f"EMAIL_USERNAME: {email_username}")
    print(f"EMAIL_PASSWORD: {'*' * len(email_password) if email_password else 'NOT SET'}")
    print(f"SMTP_SERVER: {smtp_server}")
    print(f"SMTP_PORT: {smtp_port}")
    
    if not email_username or not email_password:
        print("❌ Email credentials are missing!")
        return False
    
    # Test SMTP connection
    import smtplib
    try:
        print("\n🔄 Testing SMTP connection...")
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(email_username, email_password)
        server.quit()
        print("✅ SMTP connection successful!")
        return True
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

if __name__ == "__main__":
    test_email_config()
