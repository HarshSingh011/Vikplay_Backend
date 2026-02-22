# Testing Your Deployed API

## 🚀 Your Production API
**Base URL**: https://vikplay-backend.onrender.com

## ✅ Quick Health Check

Open in browser:
```
https://vikplay-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "VikPay Backend",
  "version": "1.0.0"
}
```

## 📚 API Documentation

Interactive API docs (Swagger UI):
```
https://vikplay-backend.onrender.com/docs
```

Alternative API docs (ReDoc):
```
https://vikplay-backend.onrender.com/redoc
```

## 🧪 Test Endpoints

### 1. Test Registration Flow

**Step 1: Register a user**
```bash
curl -X POST "https://vikplay-backend.onrender.com/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser123",
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

**Step 2: Check logs for OTP**
- Go to Render Dashboard → Your Service → Logs
- Look for `📧 EMAIL (Development Mode)` with the 6-digit OTP code

**Step 3: Verify registration with OTP**
```bash
curl -X POST "https://vikplay-backend.onrender.com/auth/verify-registration" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp": "123456"
  }'
```

**Step 4: Login**
```bash
curl -X POST "https://vikplay-backend.onrender.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

Response will include:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { ... }
}
```

### 2. Test Protected Endpoints

Use the JWT token from login:
```bash
curl -X GET "https://vikplay-backend.onrender.com/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## 🎥 Test HTML Clients

Your HTML files are now configured to use production API:

### A. Broadcaster (JWT Auth)
1. Open `broadcaster_jwt.html` in your browser (locally)
2. Login with credentials
3. It will connect to: `https://vikplay-backend.onrender.com`

### B. Viewer (JWT Auth)
1. Open `viewer_jwt.html` in your browser
2. Login with credentials
3. Watch a stream from production backend

### C. WhatsApp Call Test
1. Open `whatsapp_call_test.html` in your browser
2. Paste JWT token
3. Test video calling features

## 🔄 Switch Between Local and Production

To test locally, change these lines in HTML files:

**For Local Development:**
```javascript
const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000';
```

**For Production:**
```javascript
const API_URL = 'https://vikplay-backend.onrender.com';
const WS_URL = 'wss://vikplay-backend.onrender.com';
```

## 🐛 Troubleshooting

### CORS Issues
If you see CORS errors in browser console:
- Check that your backend allows `*` origins (already configured)
- Ensure you're using HTTPS (not HTTP) for production URLs

### WebSocket Connection Failed
- Verify service is running (not sleeping)
- Check Render logs for errors
- Use `wss://` (secure WebSocket), not `ws://`

### First Request Slow
- Render free tier sleeps after 15 min inactivity
- First request wakes it up (30-60 seconds)
- Subsequent requests are fast

### 502/503 Errors
- Service is starting or crashed
- Check Render logs for errors
- Verify environment variables are set

## 📊 Monitor Your API

### Render Dashboard
- **Logs**: Real-time logs (web + celery)
- **Metrics**: CPU, memory, bandwidth
- **Events**: Deployment history

### Check Service Status
```bash
curl https://vikplay-backend.onrender.com/health
```

### Check Celery Worker
Look for in logs:
```
celery.worker INFO: Ready to process tasks
```

## 🎯 Next Steps

1. ✅ Test all endpoints via `/docs`
2. ✅ Test registration and login flow
3. ✅ Test HTML clients (broadcaster, viewer, calls)
4. ✅ Monitor logs for errors
5. 🔜 Set up custom domain (optional)
6. 🔜 Configure email provider for production (SendGrid, Mailgun)
7. 🔜 Add Cloudflare R2 for video storage
8. 🔜 Set up monitoring/alerts

## 🆘 Common Issues

**Email OTP not received in production**
- Development mode logs OTPs to console (check Render logs)
- For production, set up SMTP credentials (Gmail, SendGrid)

**Database connection errors**
- Verify `DATABASE_URL` is correct in Render environment
- Use Internal Database URL (not External)

**Redis connection errors**
- Check `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- App works without Redis (fallback mode)

**Service keeps restarting**
- Check startup logs for errors
- Verify all required env vars are set

---

## 🚀 Your API is LIVE!

Base URL: **https://vikplay-backend.onrender.com**

Docs: **https://vikplay-backend.onrender.com/docs**

Health: **https://vikplay-backend.onrender.com/health**

Happy testing! 🎉
