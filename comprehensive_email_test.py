#!/usr/bin/env python3
"""
Comprehensive Gmail SMTP Test
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gmail_step_by_step():
    print("🔍 GMAIL SMTP COMPREHENSIVE TEST")
    print("=" * 50)
    
    # Get credentials
    username = os.getenv("EMAIL_USERNAME", "")
    password = os.getenv("EMAIL_PASSWORD", "")
    
    print(f"📧 Username: {username}")
    print(f"🔑 Password: {'*' * len(password)} (length: {len(password)})")
    print(f"🔑 Password starts with: {password[:4]}...")
    print()
    
    if not username or not password:
        print("❌ Missing email credentials!")
        return False
    
    # Test 1: Basic connection
    print("🔌 Test 1: Connecting to Gmail SMTP...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        print("✅ Connected to smtp.gmail.com:587")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Test 2: STARTTLS
    print("\n🔒 Test 2: Starting TLS encryption...")
    try:
        server.starttls()
        print("✅ TLS encryption started")
    except Exception as e:
        print(f"❌ TLS failed: {e}")
        server.quit()
        return False
    
    # Test 3: Authentication
    print("\n🔐 Test 3: Authenticating with Gmail...")
    try:
        server.login(username, password)
        print("✅ Authentication successful!")
        
        # Test 4: Send test email
        print("\n📨 Test 4: Sending test email...")
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username  # Send to yourself
        msg['Subject'] = "VikPay Email Test - Success!"
        
        body = """
        🎉 SUCCESS! 
        
        Your Gmail SMTP configuration is working correctly.
        This test email was sent from your VikPay backend.
        
        ✅ Authentication: Working
        ✅ SMTP Connection: Working  
        ✅ Email Sending: Working
        
        You can now use the registration API with confidence!
        """
        
        msg.attach(MIMEText(body, 'plain'))
        text = msg.as_string()
        
        server.sendmail(username, username, text)
        print("✅ Test email sent successfully!")
        print(f"📬 Check your inbox: {username}")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Go to https://myaccount.google.com/security")
        print("2. Enable 2-Step Verification if not already enabled")
        print("3. Go to https://myaccount.google.com/apppasswords")
        print("4. Generate a NEW app password for 'Mail'")
        print("5. Copy the 16-character password WITHOUT spaces")
        print("6. Update your .env file with the new password")
        print("7. Restart your application")
        
        server.quit()
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        server.quit()
        return False

def check_account_security():
    print("\n🛡️  ACCOUNT SECURITY CHECK")
    print("=" * 50)
    print("Please verify these settings in your Google Account:")
    print("1. 2-Step Verification: https://myaccount.google.com/security")
    print("2. App Passwords: https://myaccount.google.com/apppasswords")
    print("3. Recent Security Activity: https://myaccount.google.com/notifications")
    print("\nIf app passwords are not available:")
    print("- Your account might not have 2FA enabled")
    print("- Your organization might have restrictions")
    print("- You might need to use OAuth2 instead")

if __name__ == "__main__":
    success = test_gmail_step_by_step()
    
    if not success:
        check_account_security()
        print("\n❌ Gmail SMTP test failed!")
        print("Please follow the troubleshooting steps above.")
    else:
        print("\n🎉 Gmail SMTP test passed!")
        print("Your email configuration is working correctly.")
