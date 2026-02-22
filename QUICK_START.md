# Quick Deployment Checklist

## ✅ What's Been Done
- [x] Dockerfile configured to use `PORT` environment variable
- [x] Supervisor setup to run both FastAPI web server and Celery worker in one container
- [x] Health check endpoint configured
- [x] Environment variable template created

## 📋 Your Todo List

### 1. Push to GitHub (5 minutes)
```bash
git add .
git commit -m "Configure for Render deployment"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git branch -M main
git push -u origin main
```

### 2. Create Render Account
- Go to https://render.com
- Sign up with GitHub (recommended)
- Free tier is sufficient

### 3. Create PostgreSQL Database (2 minutes)
- Render Dashboard → New → PostgreSQL
- Name: `vikpay-db`
- Region: Choose closest to you
- Plan: **Free**
- Copy **Internal Database URL**

### 4. Get Redis (Choose One)

**Option A: Upstash (Recommended - Free Forever)**
1. Go to https://upstash.com
2. Create account
3. Create Redis database (free)
4. Note: host, port, password

**Option B: Render Redis (May not be free)**
- Render Dashboard → New → Redis
- Plan: Free (if available)

### 5. Create Web Service (3 minutes)
- Render Dashboard → New → Web Service
- Connect your GitHub repo
- Settings:
  - Environment: **Docker**
  - Plan: **Free**
  - Build/Start Commands: Leave blank

### 6. Add Environment Variables (5 minutes)

**Copy these to Render → Environment:**

```bash
# Database (from step 3)
DATABASE_URL=<paste-internal-database-url>

# Redis (from step 4)
REDIS_HOST=<your-redis-host>
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<your-redis-password>

# Security (generate new)
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_urlsafe(48))">

# Email (use Gmail with app password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=<your-gmail-app-password>
FROM_EMAIL=your-email@gmail.com
SENDER_NAME=VikPay
```

### 7. Deploy & Verify (5 minutes)
- Click "Create Web Service"
- Wait for build (3-5 minutes)
- Check logs for success messages
- Visit: `https://your-service.onrender.com/health`
- Should see: `{"status": "healthy"}`

## 🎯 Total Time: ~20 minutes

## 📚 Full Guide
See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed instructions and troubleshooting.

## 🆘 Quick Troubleshooting

### Build Failed
- Check Dockerfile syntax
- View build logs in Render

### Service Won't Start  
- Check required env vars are set
- View logs for error messages
- Verify DATABASE_URL is **Internal** URL (not External)

### Celery Not Working
- Verify Redis credentials
- Check logs for connection errors
- Ensure REDIS_HOST, REDIS_PORT, REDIS_PASSWORD are correct

### Emails Not Sending
- For Gmail: use App Password (not regular password)
- Enable 2FA on Gmail first
- Generate App Password in Google Account Security settings

## 🚀 Next Steps After Deployment

1. Test API at `/docs`
2. Test registration flow
3. Configure custom domain (optional)
4. Set up CI/CD auto-deploy

## 💰 Free Tier Limits (Render)
- 750 hours/month (enough for 1 service 24/7)
- Sleeps after 15 min inactivity
- First request wakes it (30-60 sec delay)
- 100GB bandwidth/month

To keep it awake: Use a cron job to ping `/health` every 10 minutes.
