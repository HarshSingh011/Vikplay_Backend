"""
Gmail App Password Troubleshooting Guide
========================================

The error "Username and Password not accepted" with Gmail usually means one of these issues:

1. INCORRECT APP PASSWORD
   - The app password might be wrong, expired, or typo
   - Solution: Generate a NEW app password

2. 2-FACTOR AUTHENTICATION NOT ENABLED
   - App passwords only work when 2FA is enabled
   - Solution: Enable 2FA first, then generate app password

3. LESS SECURE APP ACCESS
   - Google might have disabled less secure app access
   - Solution: Use App Passwords (more secure method)

4. ACCOUNT SECURITY RESTRICTIONS
   - Google might have security restrictions on your account
   - Solution: Check Google Account security settings

STEPS TO FIX:
=============

Step 1: Verify 2-Factor Authentication
- Go to: https://myaccount.google.com/security
- Make sure "2-Step Verification" is ON

Step 2: Generate NEW App Password
- Go to: https://myaccount.google.com/apppasswords
- Select "Mail" as the app
- Generate a new 16-character password
- COPY THE PASSWORD EXACTLY (no spaces)

Step 3: Update .env file
- Replace EMAIL_PASSWORD with the new password
- NO SPACES in the password

Step 4: Alternative - Use OAuth2 (if app passwords don't work)
- Some Google accounts have app passwords disabled
- Would need to implement OAuth2 flow

CURRENT DIAGNOSIS:
==================
- Username: monof88703@gmail.com ✓
- Password format: 16 characters ✓  
- SMTP settings: Correct ✓
- Issue: Gmail rejecting the app password ❌

IMMEDIATE ACTION NEEDED:
- Generate a FRESH app password from Google
- Double-check 2FA is enabled
- Update the .env file with the new password
"""
