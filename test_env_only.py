#!/usr/bin/env python3
"""
Force test with .env file values only
"""
import os
import smtplib
from dotenv import load_dotenv

# Clear any existing environment variables
if 'EMAIL_USERNAME' in os.environ:
    del os.environ['EMAIL_USERNAME']
if 'EMAIL_PASSWORD' in os.environ:
    del os.environ['EMAIL_PASSWORD']

# Load from .env file
load_dotenv(override=True)

def test_with_env_file():
    print("="*60)
    print("TESTING EMAIL WITH .ENV FILE VALUES ONLY")
    print("="*60)
    
    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    
    print(f"📧 EMAIL_USERNAME: {email_username}")
    print(f"🔑 EMAIL_PASSWORD: {'*' * len(email_password) if email_password else 'NOT SET'} (length: {len(email_password) if email_password else 0})")
    print(f"🖥️  SMTP_SERVER: {smtp_server}")
    print(f"🔌 SMTP_PORT: {smtp_port}")
    print()
    
    if not email_username or not email_password:
        print("❌ Email credentials are missing from .env file!")
        return False
    
    if email_username != "harsh2004416@gmail.com":
        print(f"⚠️  Warning: Expected harsh2004416@gmail.com, got {email_username}")
    
    # Test SMTP connection step by step
    try:
        print("🔌 Step 1: Connecting to Gmail SMTP...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        print("✅ Connected successfully")
        
        print("🔒 Step 2: Starting TLS encryption...")
        server.starttls()
        print("✅ TLS started successfully")
        
        print("🔐 Step 3: Authenticating...")
        server.login(email_username, email_password)
        print("✅ Authentication successful!")
        
        print("📧 Step 4: Testing email send...")
        from email.mime.text import MIMEText
        
        msg = MIMEText("Test email from VikPay backend - Authentication working!")
        msg['Subject'] = "VikPay Test - Success!"
        msg['From'] = email_username
        msg['To'] = email_username
        
        server.send_message(msg)
        print("✅ Test email sent successfully!")
        print(f"📬 Check your inbox: {email_username}")
        
        server.quit()
        print("\n🎉 ALL TESTS PASSED! Email configuration is working.")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n🔧 POSSIBLE ISSUES:")
        print("1. Wrong app password for harsh2004416@gmail.com")
        print("2. App password not generated for this specific email")
        print("3. 2-Factor Authentication not enabled")
        print("4. Account security restrictions")
        
        server.quit()
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_with_env_file()
    
    if not success:
        print("\n" + "="*60)
        print("🔧 TROUBLESHOOTING CHECKLIST:")
        print("="*60)
        print("1. ✓ Go to https://myaccount.google.com/security")
        print("2. ✓ Enable 2-Step Verification")
        print("3. ✓ Go to https://myaccount.google.com/apppasswords")
        print("4. ✓ Generate NEW app password for 'Mail'")
        print("5. ✓ Copy the 16-character password (no spaces)")
        print("6. ✓ Update EMAIL_PASSWORD in .env file")
        print("7. ✓ Make sure EMAIL_USERNAME = harsh2004416@gmail.com")
        print("8. ✓ Restart your application")
    else:
        print("\n🚀 Ready to test registration API!")
        print("Your email configuration is working perfectly.")
