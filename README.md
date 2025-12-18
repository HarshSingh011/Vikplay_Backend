# VikPay Backend - Kubernetes Native

A cloud-native FastAPI backend with WebRTC support, designed for Kubernetes deployment with automatic dependency management.

## ☸️ Kubernetes-Native Deployment (Recommended)

### One-Command Deploy

```bash
# Clone repository
git clone <your-repo-url>
cd Backend-VikPay-

# Deploy with Kubernetes (automatic dependency management)
./quickstart.sh

# Or using make
make deploy
```

### Manual Kubernetes Deployment

```bash
# 1. Generate Kubernetes manifests
python3 setup.py

# 2. Deploy to cluster
./k8s-deploy.sh

# 3. Access application
kubectl port-forward service/vikpay-backend-service 8000:80 -n vikpay
```

## 🔧 What Happens During Kubernetes Deployment

The Kubernetes-native approach automatically:

- ✅ **Creates init containers** that install all Python dependencies
- ✅ **Manages ConfigMaps** for application configuration
- ✅ **Handles Secrets** for sensitive data
- ✅ **Sets up health probes** for application monitoring
- ✅ **Configures services** for network access
- ✅ **Enables auto-scaling** and self-healing

## 📦 Dependencies Automatically Managed

All dependencies from `requirements.txt` are installed automatically in Kubernetes:

| Category | Packages |
|----------|----------|
| **Web Framework** | FastAPI, Uvicorn, Starlette |
| **Database** | SQLAlchemy, psycopg2-binary |
| **Authentication** | bcrypt, PyJWT, email-validator |
| **Cloud Storage** | boto3 (AWS S3/R2 compatible) |
| **WebRTC** | aiortc |
| **Data Validation** | Pydantic |
| **Environment** | python-dotenv |

## 🚀 Available Commands

```bash
# Kubernetes Management
make setup      # Generate K8s manifests
make deploy     # Deploy to cluster
make status     # Check deployment status
make logs       # View application logs
make scale REPLICAS=3  # Scale deployment
make clean      # Delete from cluster

# Development
make local      # Local development (fallback)
make k8s-check  # Check K8s tools availability
```

## 🌐 Accessing Your Application

After deployment:

```bash
# Set up port forwarding
kubectl port-forward service/vikpay-backend-service 8000:80 -n vikpay

# Access API documentation
open http://localhost:8000/docs    # Swagger UI
open http://localhost:8000/redoc   # ReDoc
```

## 📊 Monitoring & Management

```bash
# Check pod status
kubectl get pods -n vikpay -w

# View logs
kubectl logs -l app=vikpay-backend -n vikpay -f

# Scale application
kubectl scale deployment vikpay-backend --replicas=3 -n vikpay

# Get service info
kubectl get svc vikpay-backend-service -n vikpay
```

## ⚙️ Configuration

The Kubernetes deployment uses:

- **ConfigMap**: Non-sensitive configuration
- **Secret**: Sensitive data (base64 encoded)
- **PersistentVolume**: Database storage
- **Service**: Network access
- **Deployment**: Application management

## 🔧 Local Development Fallback

If Kubernetes tools aren't available:

```bash
# Automatic fallback to local development
python3 setup.py

# Start local server
./local-dev.sh
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                       │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌─────────────────────────────────────┐ │
│  │ Init Container│  │        Main Application             │ │
│  │               │  │                                     │ │
│  │ • Install deps│  │ • VikPay Backend                    │ │
│  │ • Setup env   │  │ • FastAPI + WebRTC                  │ │
│  │ • Copy packages│  │ • Auto-scaling                      │ │
│  └───────────────┘  └─────────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  Storage & Config                       │ │
│  │  • ConfigMap (app config)                               │ │
│  │  • Secret (credentials)                                 │ │
│  │  • PersistentVolume (database)                          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Production Features

- **Auto-scaling**: Horizontal Pod Autoscaler ready
- **Health checks**: Liveness and readiness probes
- **Zero-downtime**: Rolling updates
- **Service discovery**: Kubernetes-native networking
- **Secret management**: Encrypted at rest
- **Resource limits**: CPU and memory constraints
- **Monitoring**: Ready for Prometheus/Grafana

## 🔒 Security

- Secrets stored in Kubernetes Secret objects
- Non-root container execution
- Resource limits enforced
- Network policies ready
- RBAC compatible

## 🚀 Getting Started

1. **Prerequisites**: `kubectl` and `docker` installed
2. **Deploy**: Run `./quickstart.sh` or `make deploy`
3. **Access**: `kubectl port-forward service/vikpay-backend-service 8000:80 -n vikpay`
4. **Develop**: Open http://localhost:8000/docs

## 🧪 Testing the Complete Registration Flow

### Quick Start: Automated Test Script

We've included a comprehensive test script that covers all scenarios:

```bash
# Run the interactive test suite
python test_registration_flow.py
```

**Available Tests:**
1. ✅ Complete Registration Flow (Step-by-step with OTP)
2. ✅ Rate Limiting Test (30s cooldown, attempt limits)
3. ✅ Duplicate Registration Test
4. ✅ Run All Tests

### Prerequisites
```bash
# 1. Start Redis (optional - system has fallback)
docker run -d --name vikpay-redis -p 6379:6379 redis:7-alpine

# 2. Start Celery (for async emails)
start_celery.bat  # Windows
# or
celery -A celery_config worker --beat --loglevel=info --pool=solo  # Linux/Mac

# 3. Start FastAPI server
uvicorn main:app --reload
```

### Test Flow: Complete User Registration

#### Step 1: Register New User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "status": "pending",
    "email": "test@example.com",
    "username": "testuser",
    "message": "Registration initiated. Please verify OTP sent to your email."
  },
  "message": "Registration initiated successfully. Check your email for OTP."
}
```

#### Step 2: Send OTP Verification Email
```bash
curl -X POST http://localhost:8000/auth/send-verification-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "email": "test@example.com",
    "expires_in_minutes": 15
  },
  "message": "OTP sent successfully"
}
```

**Check your email for the 6-digit OTP code!**

#### Step 3: Verify OTP (Completes Registration)
```bash
curl -X POST http://localhost:8000/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp_code": "123456"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "email": "test@example.com",
    "user_id": 1,
    "username": "testuser",
    "user_created": true,
    "user_activated": true
  },
  "message": "Registration completed successfully! Your account is now active."
}
```

#### Step 4: Login with New Account
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "test@example.com",
      "username": "testuser",
      "is_active": true
    }
  },
  "message": "Login successful"
}
```

### Test Scenarios: Rate Limiting

#### Test 1: Resend OTP Too Quickly (30s cooldown)
```bash
# Send OTP
curl -X POST http://localhost:8000/auth/send-verification-otp \
  -d '{"email":"test@example.com"}' -H "Content-Type: application/json"

# Immediately try to resend (should be blocked)
curl -X POST http://localhost:8000/auth/send-verification-otp \
  -d '{"email":"test@example.com"}' -H "Content-Type: application/json"
```

**Expected Error:**
```json
{
  "success": false,
  "message": "Please wait 28 seconds before requesting another OTP"
}
```

#### Test 2: Too Many OTP Requests (5 in 15 minutes)
```bash
# Send 6 OTPs quickly (wait 31s between each to bypass cooldown)
for i in {1..6}; do
  curl -X POST http://localhost:8000/auth/send-verification-otp \
    -d '{"email":"spam@test.com"}' -H "Content-Type: application/json"
  sleep 31
done
```

**Expected Error (on 6th request):**
```json
{
  "success": false,
  "message": "Too many OTP requests. Please try again in 12 minutes"
}
```

#### Test 3: Brute Force OTP Verification
```bash
# Try wrong OTPs multiple times
for i in {1..11}; do
  curl -X POST http://localhost:8000/auth/verify-email \
    -d '{"email":"test@example.com","otp_code":"999999"}' \
    -H "Content-Type: application/json"
done
```

**Expected Error (after 10 attempts):**
```json
{
  "success": false,
  "message": "Too many verification attempts. Please wait 300 seconds"
}
```

### Test Scenarios: Edge Cases

#### Test 4: Register with Same Email Again
```bash
# First registration
curl -X POST http://localhost:8000/auth/register \
  -d '{"email":"test@example.com","username":"test1","password":"Pass123!"}' \
  -H "Content-Type: application/json"

# Try again immediately
curl -X POST http://localhost:8000/auth/register \
  -d '{"email":"test@example.com","username":"test2","password":"Pass123!"}' \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "status": "pending",
    "message": "Registration already in progress. Please verify your email.",
    "resend_count": 1,
    "can_resend": true
  }
}
```

#### Test 5: Expired OTP (Wait 16 minutes)
```bash
# Send OTP
curl -X POST http://localhost:8000/auth/send-verification-otp \
  -d '{"email":"test@example.com"}' -H "Content-Type: application/json"

# Wait 16 minutes (OTP expires after 15 minutes)
sleep 960

# Try to verify expired OTP
curl -X POST http://localhost:8000/auth/verify-email \
  -d '{"email":"test@example.com","otp_code":"old_code"}' \
  -H "Content-Type: application/json"
```

**Expected Error:**
```json
{
  "success": false,
  "message": "Invalid or expired OTP"
}
```

### Interactive Testing with Swagger UI

Visit **http://localhost:8000/docs** for interactive API testing with:
- 📝 Auto-generated API documentation
- ▶️ Try it out feature
- 🔐 Authentication testing
- 📊 Schema validation

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Register
response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "python@test.com",
    "username": "pythonuser",
    "password": "PyTest123!"
})
print("Register:", response.json())

# 2. Send OTP
response = requests.post(f"{BASE_URL}/auth/send-verification-otp", json={
    "email": "python@test.com"
})
print("OTP Sent:", response.json())

# 3. Verify OTP (replace with actual OTP from email)
otp_code = input("Enter OTP from email: ")
response = requests.post(f"{BASE_URL}/auth/verify-email", json={
    "email": "python@test.com",
    "otp_code": otp_code
})
print("Verified:", response.json())

# 4. Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "python@test.com",
    "password": "PyTest123!"
})
print("Login:", response.json())
token = response.json()['data']['access_token']

# 5. Use authenticated endpoint
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print("User Info:", response.json())
```

### Monitoring & Debugging

#### Check Celery Tasks
```bash
# List active tasks
celery -A celery_config inspect active

# Check task stats
celery -A celery_config inspect stats

# Monitor in real-time with Flower
pip install flower
celery -A celery_config flower --port=5555
# Visit http://localhost:5555
```

#### Check Redis Status
```bash
# Connect to Redis CLI
redis-cli

# Check pending registrations
KEYS pending_reg:*

# Check rate limits
KEYS ratelimit:*

# Get specific data
GET pending_reg:test@example.com

# Monitor real-time
MONITOR
```

#### View Logs
```bash
# FastAPI logs (console)
# Check terminal where uvicorn is running

# Celery logs
# Check terminal where Celery worker is running

# Or redirect to file
celery -A celery_config worker --loglevel=info > celery.log 2>&1 &
tail -f celery.log
```

### Troubleshooting

**Problem:** "Failed to send OTP email"
```bash
# Check email credentials in .env
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password  # Not your regular password!

# Test email connection
python -c "from auth.utils.email_utils import send_otp_email; print(send_otp_email('test@test.com', '123456', 'test'))"
```

**Problem:** "Redis connection failed"
```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# Start Redis if not running
docker start vikpay-redis
# or
redis-server

# System works without Redis (fallback mode)
```

**Problem:** "Celery not processing tasks"
```bash
# Check if Celery worker is running
celery -A celery_config inspect active

# Restart worker
# Ctrl+C to stop, then:
celery -A celery_config worker --beat --loglevel=info --pool=solo
```

---

## 📚 Additional Documentation

- **[REDIS_SETUP.md](REDIS_SETUP.md)** - Redis installation and configuration
- **[CELERY_SETUP.md](CELERY_SETUP.md)** - Celery setup and monitoring
- **[PENDING_REGISTRATION_FLOW.md](PENDING_REGISTRATION_FLOW.md)** - Complete registration flow details
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Feature implementation overview
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick command reference

---

**VikPay Backend** - Cloud-native, Kubernetes-ready, production-grade! ☸️
