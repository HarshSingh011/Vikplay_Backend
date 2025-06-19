#!/usr/bin/env python3
"""
Test script for VikPay Authentication APIs
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_auth_apis():
    """Test all authentication APIs"""
    print("🧪 Testing VikPay Authentication APIs...")
    
    # Test data
    test_user = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "TestPass123"
    }
    
    print("\n1. Testing User Registration...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Registration successful")
        else:
            print("❌ Registration failed")
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
    
    print("\n2. Testing Login (should fail - email not verified)...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 401:
            print("✅ Login correctly failed (email not verified)")
        else:
            print("❌ Login test unexpected result")
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
    
    print("\n3. Testing Forgot Password...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/forgot-password",
            json={"email": test_user["email"]},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Forgot password request successful")
        else:
            print("❌ Forgot password request failed")
            
    except Exception as e:
        print(f"❌ Forgot password test failed: {e}")
    
    print("\n4. Testing Invalid OTP Verification...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/verify-registration",
            json={
                "email": test_user["email"],
                "otp": "000000"
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400:
            print("✅ Invalid OTP correctly rejected")
        else:
            print("❌ Invalid OTP test unexpected result")
            
    except Exception as e:
        print(f"❌ OTP verification test failed: {e}")
    
    print("\n5. Testing API Documentation Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API documentation accessible")
        else:
            print("❌ API documentation not accessible")
            
    except Exception as e:
        print(f"❌ Documentation test failed: {e}")

def test_server_health():
    """Test if server is running"""
    print("🏥 Testing server health...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Server response: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🚀 VikPay Authentication Test Suite")
    print("=" * 50)
    
    # Check server health first
    if test_server_health():
        test_auth_apis()
    else:
        print("❌ Cannot run tests - server not accessible")
        print("💡 Make sure to start the server with: python main.py")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("\n📚 For detailed API documentation, visit:")
    print("   http://localhost:8000/docs")
    print("   or check auth/API_DOCS.md")
