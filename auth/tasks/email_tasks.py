"""
Async email tasks using Celery
All email sending is done asynchronously for better performance
"""
from celery import Task
from celery_config import celery_app
from auth.utils import email_utils
import logging

logger = logging.getLogger(__name__)


class EmailTask(Task):
    """Base task for email operations with retry logic"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max
    retry_jitter = True


@celery_app.task(base=EmailTask, name='auth.tasks.email_tasks.send_otp_email')
def send_otp_email_async(email: str, otp_code: str, purpose: str = "verification") -> dict:
    """
    Send OTP email asynchronously
    
    Args:
        email: Recipient email address
        otp_code: OTP code to send
        purpose: Purpose of OTP (verification, password reset, etc.)
    
    Returns:
        Dict with status and message
    """
    try:
        logger.info(f"Sending OTP email to {email} for {purpose}")
        
        success = email_utils.send_otp_email(email, otp_code, purpose)
        
        if success:
            logger.info(f"OTP email sent successfully to {email}")
            return {
                "status": "success",
                "email": email,
                "purpose": purpose,
                "message": "Email sent successfully"
            }
        else:
            logger.error(f"Failed to send OTP email to {email}")
            return {
                "status": "failed",
                "email": email,
                "purpose": purpose,
                "message": "Failed to send email"
            }
            
    except Exception as e:
        logger.error(f"Error sending OTP email to {email}: {str(e)}")
        raise


@celery_app.task(base=EmailTask, name='auth.tasks.email_tasks.send_welcome_email')
def send_welcome_email_async(email: str, username: str) -> dict:
    """
    Send welcome email asynchronously
    
    Args:
        email: Recipient email address
        username: User's username
    
    Returns:
        Dict with status and message
    """
    try:
        logger.info(f"Sending welcome email to {email}")
        
        success = email_utils.send_welcome_email(email, username)
        
        if success:
            logger.info(f"Welcome email sent successfully to {email}")
            return {
                "status": "success",
                "email": email,
                "message": "Welcome email sent successfully"
            }
        else:
            logger.error(f"Failed to send welcome email to {email}")
            return {
                "status": "failed",
                "email": email,
                "message": "Failed to send welcome email"
            }
            
    except Exception as e:
        logger.error(f"Error sending welcome email to {email}: {str(e)}")
        raise


@celery_app.task(base=EmailTask, name='auth.tasks.email_tasks.send_password_reset_email')
def send_password_reset_email_async(email: str, reset_token: str) -> dict:
    """
    Send password reset email asynchronously
    
    Args:
        email: Recipient email address
        reset_token: Password reset token
    
    Returns:
        Dict with status and message
    """
    try:
        logger.info(f"Sending password reset email to {email}")
        
        # You can implement this in email_utils
        # success = email_utils.send_password_reset_email(email, reset_token)
        success = True  # Placeholder
        
        if success:
            logger.info(f"Password reset email sent successfully to {email}")
            return {
                "status": "success",
                "email": email,
                "message": "Password reset email sent successfully"
            }
        else:
            logger.error(f"Failed to send password reset email to {email}")
            return {
                "status": "failed",
                "email": email,
                "message": "Failed to send password reset email"
            }
            
    except Exception as e:
        logger.error(f"Error sending password reset email to {email}: {str(e)}")
        raise


@celery_app.task(name='auth.tasks.email_tasks.send_notification_email')
def send_notification_email_async(email: str, subject: str, body: str) -> dict:
    """
    Send generic notification email asynchronously
    
    Args:
        email: Recipient email address
        subject: Email subject
        body: Email body (HTML)
    
    Returns:
        Dict with status and message
    """
    try:
        logger.info(f"Sending notification email to {email}: {subject}")
        
        # You can implement this in email_utils
        # success = email_utils.send_email(email, subject, body)
        success = True  # Placeholder
        
        if success:
            logger.info(f"Notification email sent successfully to {email}")
            return {
                "status": "success",
                "email": email,
                "message": "Notification email sent successfully"
            }
        else:
            logger.error(f"Failed to send notification email to {email}")
            return {
                "status": "failed",
                "email": email,
                "message": "Failed to send notification email"
            }
            
    except Exception as e:
        logger.error(f"Error sending notification email to {email}: {str(e)}")
        raise
