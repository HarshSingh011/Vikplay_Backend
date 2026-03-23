"""
Regex patterns and validation utilities for authentication
"""
import re

# Email regex pattern - RFC 5322 simplified
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Password regex pattern
# Must contain: uppercase, lowercase, digit, special character, and be at least 8 characters
# Special characters allowed: @$!%*?&
PASSWORD_REGEX = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

# Username regex pattern
# Allow letters, numbers, underscore, hyphen, dot (3-50 characters)
USERNAME_REGEX = r'^[a-zA-Z0-9_.-]{3,50}$'


def validate_email_regex(email: str) -> bool:
    """Validate email with regex"""
    return bool(re.match(EMAIL_REGEX, email))


def validate_password_regex(password: str) -> bool:
    """
    Validate password with regex.
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character: @$!%*?&
    """
    return bool(re.match(PASSWORD_REGEX, password))


def validate_username_regex(username: str) -> bool:
    """Validate username with regex"""
    return bool(re.match(USERNAME_REGEX, username))
