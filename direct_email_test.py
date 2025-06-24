import os
import smtplib
from email.mime.text import MIMEText

# Force set the correct credentials
os.environ['EMAIL_USERNAME'] = 'monof88703@gmail.com'
os.environ['EMAIL_PASSWORD'] = 'vaiwetargjfbzyqn'

def test_email():
    username = os.environ['EMAIL_USERNAME']
    password = os.environ['EMAIL_PASSWORD']
    
    print(f"Testing with username: {username}")
    print(f"Password length: {len(password)}")
    print(f"Password starts with: {password[:4]}")
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(username, password)
        
        # Send test email
        msg = MIMEText("Test email from VikPay")
        msg['Subject'] = 'Test Email'
        msg['From'] = username
        msg['To'] = 'nelinom601@boxmach.com'
        
        server.send_message(msg)
        server.quit()
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

if __name__ == "__main__":
    test_email()
