# Backend-VikPay Project Structure

## Core Application Files
- `main.py` - FastAPI application entry point and configuration
- `database.py` - Database connection and session management
- `requirements.txt` - Python dependencies
- `vidplay.db` - SQLite database file

## Authentication System 🔐
- `auth/` - Complete authentication module
  - `auth/models.py` - User and OTP database models
  - `auth/schemas.py` - Pydantic schemas for validation
  - `auth/routes.py` - Authentication API endpoints
  - `auth/utils.py` - Authentication utilities (JWT, password hashing, email, OTP)
  - `auth/API_DOCS.md` - Complete API documentation
  - `auth/__init__.py` - Module initialization

## Authentication APIs
1. **POST** `/auth/register` - Register new user with email/username/password
2. **POST** `/auth/verify-registration` - Verify registration OTP
3. **POST** `/auth/login` - Login with email/password (returns JWT token)
4. **POST** `/auth/forgot-password` - Send OTP for password reset
5. **POST** `/auth/verify-forgot-password-otp` - Verify password reset OTP
6. **POST** `/auth/reset-password` - Reset password with OTP verification
7. **GET** `/auth/me` - Get current user info (protected route)

## Models & Schemas
- `models/models.py` - SQLAlchemy database models (includes auth models)
- `models/streaming.py` - Streaming-specific models
- `schemas/schemas.py` - Pydantic schemas for API validation
- `schemas/streaming.py` - Streaming-specific schemas
- `schemas/__init__.py` - Schema imports

## API Routes
- `routes/webrtc.py` - WebRTC signaling and streaming endpoints
- `routes/streaming.py` - Live streaming functionality
- `routes/videos.py` - Video management endpoints
- `routes/__init__.py` - Route imports

## Utilities
- `utils/webrtc.py` - WebRTC connection management and signaling logic
- `utils/websocket.py` - WebSocket connection manager for real-time features

## Static Files
- `static/webrtc-test.html` - WebRTC testing interface
- `static/favicon.ico` - Website icon
- `static/videos/` - Video storage directory

## Configuration & Setup
- `r2_utils.py` - R2 cloud storage utilities
- `create_tables.py` - Database table creation script
- `create_categories.py` - Initial category data setup
- `cert.pem` & `key.pem` - SSL certificates
- `docker-compose.yml` - Docker configuration
- `.env` - Environment variables (create from `.env.example`)
- `.env.example` - Environment variables template
- `__init__.py` - Package initialization

## Testing
- `test_auth.py` - Authentication API test script

## Development Files
- `.vscode/` - VS Code configuration
- `.git/` - Git repository
- `.venv/` - Python virtual environment

## Security Features
- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure access tokens with expiration
- **Email Verification**: OTP-based email verification
- **Password Reset**: Secure OTP-based password reset
- **Input Validation**: Comprehensive validation with Pydantic
- **Rate Limiting**: Built-in protection against abuse

## Email Features
- **Registration Verification**: OTP sent to email upon registration
- **Password Reset**: OTP sent for secure password reset
- **HTML Email Templates**: Professional email formatting
- **SMTP Support**: Works with Gmail and other SMTP providers

## Getting Started with Authentication

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your email credentials
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Server**:
   ```bash
   python main.py
   ```

4. **Test APIs**:
   ```bash
   python test_auth.py
   ```

5. **View Documentation**:
   - Interactive docs: http://localhost:8000/docs
   - API docs: `auth/API_DOCS.md`

## Removed Files
The following backup and test files were removed to clean up the project:
- `routes/webrtc_backup.py`
- `routes/webrtc_corrupted.py`
- `routes/webrtc_fixed.py`
- `routes/webrtc_original.py`
- `routes/webrtc_simple.py`
- `utils/webrtc_backup.py`
- `utils/webrtc_original.py`
- `utils/webrtc_simple.py`
- `utils/webrtc_simplified.py`
- `.cph/` (competitive programming cache)
- `__pycache__/` directories (Python cache)
