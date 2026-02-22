# Render Deployment Guide (Free Tier)

## What Changed
✅ Your app now runs both **web server (FastAPI)** and **background worker (Celery)** in a single Docker container using `supervisord`. This keeps everything free on Render.

## Prerequisites
1. A GitHub account
2. A Render account (free tier works)
3. Your code pushed to GitHub

---

## Step 1: Push Code to GitHub

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Ready for Render deployment with supervisor"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git branch -M main
git push -u origin main
```

---

## Step 2: Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** → **PostgreSQL**
3. Settings:
   - **Name**: `vikpay-db` (or your choice)
   - **Database**: `vikpay_db`
   - **User**: auto-generated
   - **Region**: Choose closest to you
   - **Instance Type**: **Free**
4. Click **Create Database**
5. **Copy the Internal Database URL** from the database info page (looks like: `postgresql://user:pass@host/dbname`)

---

## Step 3: Create Redis Instance on Render

1. Click **New +** → **Redis**
2. Settings:
   - **Name**: `vikpay-redis`
   - **Region**: Same as your database
   - **Instance Type**: **Free** (if available) or use external free Redis like [Upstash](https://upstash.com/)
3. Click **Create Redis**
4. **Copy the Internal Redis URL** (looks like: `redis://red-xxxxx:6379`)

### Alternative: Use Upstash Redis (Free)
If Render Redis isn't free or available:
1. Go to [Upstash](https://upstash.com/) and create free account
2. Create new Redis database
3. Copy connection details:
   - `REDIS_HOST`: endpoint (e.g., `us1-xxx.upstash.io`)
   - `REDIS_PORT`: `6379` or `6380`
   - `REDIS_PASSWORD`: your password
   - `REDIS_DB`: `0`

---

## Step 4: Create Web Service on Render

1. Click **New +** → **Web Service**
2. **Connect your GitHub repository**
3. Configure:
   - **Name**: `vikpay-backend` (or your choice)
   - **Region**: Same as database/redis
   - **Branch**: `main`
   - **Root Directory**: leave blank
   - **Environment**: **Docker**
   - **Instance Type**: **Free**
   - **Build Command**: leave blank (Docker handles it)
   - **Start Command**: leave blank (Dockerfile handles it)

---

## Step 5: Add Environment Variables

In the web service settings, go to **Environment** tab and add these variables:

### Required - Database
```
DATABASE_URL = <paste Internal Database URL from Step 2>
```

### Required - Redis (if using Render Redis)
```
REDIS_HOST = <paste redis hostname from Internal Redis URL>
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = <paste password from Redis URL if any>
```

### Required - Redis (if using Upstash)
```
REDIS_HOST = <your-upstash-endpoint>
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = <your-upstash-password>
```

### Required - Security
```
SECRET_KEY = <generate with: python -c "import secrets; print(secrets.token_urlsafe(48))">
```

### Required - Email (for OTP/registration emails)
**Option A: Gmail with App Password**
```
SMTP_SERVER = smtp.gmail.com
SMTP_PORT = 587
EMAIL_USERNAME = your-email@gmail.com
EMAIL_PASSWORD = <your-gmail-app-password>
FROM_EMAIL = your-email@gmail.com
SENDER_NAME = VikPay
```

**How to get Gmail App Password:**
1. Enable 2FA on your Google account
2. Go to Google Account → Security → 2-Step Verification → App passwords
3. Generate new app password for "Mail"
4. Copy the 16-character password

**Option B: SendGrid (Recommended for production)**
```
SMTP_SERVER = smtp.sendgrid.net
SMTP_PORT = 587
EMAIL_USERNAME = apikey
EMAIL_PASSWORD = <your-sendgrid-api-key>
FROM_EMAIL = your-verified-sender@yourdomain.com
SENDER_NAME = VikPay
```

### Optional - Cloudflare R2 Storage (for video uploads)
```
R2_ACCOUNT_ID = <your-cloudflare-account-id>
R2_ACCESS_KEY_ID = <your-r2-access-key>
R2_SECRET_ACCESS_KEY = <your-r2-secret-key>
R2_BUCKET_NAME = <your-bucket-name>
```

---

## Step 6: Deploy

1. Click **Create Web Service**
2. Render will:
   - Clone your repo
   - Build the Docker image
   - Start the container with supervisor running both uvicorn and celery
3. Watch the **Logs** tab for:
   - ✅ "Successfully connected to R2 storage" or fallback warnings
   - ✅ "Redis connected successfully" or fallback warnings
   - ✅ Database connection and table creation
   - ✅ Celery worker starting
   - ✅ Uvicorn server starting on port

---

## Step 7: Verify Deployment

### Check Health Endpoint
Open your Render service URL + `/health`:
```
https://your-service.onrender.com/health
```
Should return:
```json
{
  "status": "healthy",
  "service": "VikPay Backend",
  "version": "1.0.0"
}
```

### Check API Docs
```
https://your-service.onrender.com/docs
```

### Test Registration Flow
1. Use `/docs` to test `/auth/register` endpoint
2. Check logs for OTP email (development mode logs to console)
3. Test `/auth/verify-registration` with OTP
4. Test `/auth/login`

---

## Monitoring

### View Logs
- Render Dashboard → Your Service → **Logs** tab
- You'll see both uvicorn (web) and celery (worker) logs mixed together

### Check Service Status
- Render Dashboard → Your Service → **Events** tab shows deployments and restarts

### Metrics
- Free tier includes basic metrics (CPU, memory, bandwidth)

---

## Common Issues

### Celery worker not starting
- Check `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` are set correctly
- View logs for connection errors

### Database connection failed
- Verify `DATABASE_URL` is correct (use **Internal** URL from Render, not External)
- Check database is in same region and running

### Emails not sending
- Development mode: emails are logged to console (check Logs tab)
- Production: verify SMTP credentials
- Gmail: use app password, not regular password

### Service keeps restarting
- Check logs for startup errors
- Verify all required env vars are set
- Ensure `PORT` is not manually set (Render provides it)

---

## Upgrading to Paid (Optional)

For better performance and reliability:
1. **Separate Background Worker**: Create dedicated Background Worker service
   - Start Command: `celery -A celery_config.celery_app worker --loglevel=info`
   - Remove celery from supervisord.conf
2. **Upgrade instance types**: More CPU/RAM
3. **Add custom domain**: Settings → Custom Domains

---

## Local Testing (Before Pushing)

### Test Docker build locally:
```bash
docker build -t vikpay:test .
```

### Run locally with env vars:
```bash
docker run --rm \
  -e DATABASE_URL="postgresql://user:pass@localhost:5432/vikpay_db" \
  -e REDIS_HOST="localhost" \
  -e REDIS_PORT="6379" \
  -e SECRET_KEY="test-secret-key" \
  -p 8000:8000 \
  vikpay:test
```

### Check both processes running:
```bash
docker exec -it <container-id> ps aux
# Should see both uvicorn and celery processes
```

---

## Next Steps After Deployment

1. ✅ Test all endpoints via `/docs`
2. ✅ Configure custom domain (if needed)
3. ✅ Set up monitoring/alerts
4. ✅ Add HTTPS (Render provides free SSL)
5. ✅ Set up CI/CD (auto-deploy on push to main)

---

## Support

- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Celery Docs**: https://docs.celeryq.dev/

Your backend is now running on Render's free tier with both web and worker processes! 🚀
