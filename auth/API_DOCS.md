# VikPay Authentication API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication Endpoints

### 1. Register User
**POST** `/auth/register`

**Request Body:**
```json
{
    "username": "testuser",
    "email": "user@example.com",
    "password": "SecurePass123"
}
```

**Response:**
```json
{
    "message": "Registration successful! Please check your email for OTP verification.",
    "success": true
}
```

### 2. Verify Registration OTP
**POST** `/auth/verify-registration`

**Request Body:**
```json
{
    "email": "user@example.com",
    "otp": "123456"
}
```

**Response:**
```json
{
    "message": "Email verified successfully! You can now login.",
    "success": true
}
```

### 3. Login User
**POST** `/auth/login`

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "SecurePass123"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "user@example.com",
        "is_active": true,
        "is_verified": true,
        "created_at": "2025-06-19T10:30:00.000Z"
    }
}
```

### 4. Forgot Password (Send OTP)
**POST** `/auth/forgot-password`

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response:**
```json
{
    "message": "Password reset OTP sent to your email.",
    "success": true
}
```

### 5. Verify Forgot Password OTP
**POST** `/auth/verify-forgot-password-otp`

**Request Body:**
```json
{
    "email": "user@example.com",
    "otp": "654321"
}
```

**Response:**
```json
{
    "message": "OTP verified successfully! You can now reset your password.",
    "success": true
}
```

### 6. Reset Password
**POST** `/auth/reset-password`

**Request Body:**
```json
{
    "email": "user@example.com",
    "otp": "654321",
    "new_password": "NewSecurePass123",
    "confirm_password": "NewSecurePass123"
}
```

**Response:**
```json
{
    "message": "Password reset successfully! You can now login with your new password.",
    "success": true
}
```

### 7. Get Current User (Protected Route)
**GET** `/auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "id": 1,
    "username": "testuser",
    "email": "user@example.com",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-06-19T10:30:00.000Z"
}
```

## Error Responses

### Validation Error (422)
```json
{
    "detail": [
        {
            "loc": ["body", "password"],
            "msg": "Password must be at least 8 characters long",
            "type": "value_error"
        }
    ]
}
```

### Authentication Error (401)
```json
{
    "detail": "Invalid email or password"
}
```

### Bad Request (400)
```json
{
    "detail": "Email already registered"
}
```

### Not Found (404)
```json
{
    "detail": "No account found with this email address"
}
```

## Password Requirements
- At least 8 characters long
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## Username Requirements
- At least 3 characters long
- Maximum 50 characters
- Only alphanumeric characters allowed

## OTP Details
- 6-digit numeric code
- Expires in 10 minutes
- Single use only

## Testing with cURL

### Register User
```bash
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "user@example.com",
       "password": "SecurePass123"
     }'
```

### Login User
```bash
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "SecurePass123"
     }'
```

### Get Current User
```bash
curl -X GET "http://localhost:8000/auth/me" \
     -H "Authorization: Bearer <your_access_token>"
```
