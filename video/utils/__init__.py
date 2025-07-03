"""
Video Module Utilities
Shared utility functions for video routes
"""
from typing import Dict
from fastapi import Request

def extract_device_info(request: Request) -> Dict[str, str]:
    """
    Extract device information from request headers
    Used across multiple route modules for consistent device tracking
    """
    user_agent = request.headers.get("user-agent", "").lower()
    
    # Basic device detection
    device_type = "desktop"
    if "mobile" in user_agent or "android" in user_agent or "iphone" in user_agent:
        device_type = "mobile"
    elif "tablet" in user_agent or "ipad" in user_agent:
        device_type = "tablet"
    
    # Basic browser detection
    browser = "unknown"
    if "chrome" in user_agent:
        browser = "chrome"
    elif "firefox" in user_agent:
        browser = "firefox"
    elif "safari" in user_agent:
        browser = "safari"
    elif "edge" in user_agent:
        browser = "edge"
    
    # Basic OS detection
    os = "unknown"
    if "windows" in user_agent:
        os = "windows"
    elif "mac" in user_agent:
        os = "macos"
    elif "linux" in user_agent:
        os = "linux"
    elif "android" in user_agent:
        os = "android"
    elif "ios" in user_agent:
        os = "ios"
    
    return {
        "device_type": device_type,
        "browser": browser,
        "os": os,
        "ip_address": request.client.host if request.client else None,
        "user_agent": user_agent
    }

def calculate_time_pattern(hour: int) -> str:
    """
    Calculate time pattern from hour
    Used for behavioral analysis in session tracking
    """
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"
