# Step-by-Step Guide: PostgreSQL on Render & Redis on Upstash

## Part 1: Create PostgreSQL Database on Render (Free)

### Step 1: Access Render Dashboard
1. Go to https://render.com
2. Sign in with your account (or sign up if new - use GitHub login for easy integration)
3. You'll land on the Render Dashboard

### Step 2: Create New PostgreSQL Database
1. Click the **"New +"** button in the top right corner
2. From the dropdown menu, select **"PostgreSQL"**
3. You'll see the "New PostgreSQL" setup page

### Step 3: Configure Database Settings
Fill in the following:

- **Name**: `vikpay-db` (or any name you prefer)
  - This is just a label for you to identify the database
  
- **Database**: `vikpay_db` (the actual database name)
  - Leave as default or customize
  
- **User**: Leave as auto-generated
  - Render will create a secure username automatically
  
- **Region**: Choose the region closest to you or your users
  - Options: `Oregon (US West)`, `Ohio (US East)`, `Frankfurt (EU)`, `Singapore (Southeast Asia)`
  - Pick the same region you'll use for your web service
  
- **PostgreSQL Version**: Leave default (latest stable version)
  
- **Plan**: Select **"Free"**
  - 90-day trial then $7/month
  - Free tier includes: 1GB storage, 97 connections, daily backups
  
4. Click **"Create Database"** button at the bottom

### Step 4: Wait for Provisioning
- Render will provision your database (takes 1-2 minutes)
- Status will change from "Creating" → "Available"
- Green checkmark means it's ready

### Step 5: Copy Connection Details
Once the database is **Available**:

1. Find the **"Connections"** section on the database page
2. You'll see several connection strings:
   - **Internal Database URL** (starts with `postgresql://`)
   - **External Database URL** (has `.oregon-postgres.render.com` or similar)
   - **PSQL Command**

3. **IMPORTANT**: Copy the **"Internal Database URL"**
   - Click the copy icon next to it
   - It looks like: `postgresql://vikpay_db_user:XXXXX@dpg-XXXXX/vikpay_db`
   - This is what you'll use for `DATABASE_URL` environment variable

4. Keep this tab open or save the URL somewhere safe

### Step 6: Note Other Details (Optional)
You can also find individual connection details if needed:
- **Host**: `dpg-xxxxx` (internal hostname)
- **Port**: `5432`
- **Database**: `vikpay_db`
- **Username**: `vikpay_db_user` (auto-generated)
- **Password**: (shown in the connection string)

---

## Part 2: Create Redis on Upstash (Free Forever)

### Step 1: Create Upstash Account
1. Go to https://console.upstash.com
2. Click **"Sign Up"** button
3. Sign up with:
   - GitHub (recommended - one click)
   - Or Google
   - Or Email
4. Verify your email if needed

### Step 2: Access Console
1. After login, you'll see the Upstash Console
2. Click on **"Redis"** in the left sidebar (if not already there)
3. You'll see your Redis databases list (empty at first)

### Step 3: Create New Redis Database
1. Click the green **"Create Database"** button
2. You'll see the "Create a new Database" form

### Step 4: Configure Redis Database
Fill in the following:

- **Name**: `vikpay-redis` (or any name you prefer)
  - Just a label for identification
  
- **Type**: Select **"Regional"**
  - This is the free tier option
  - Global costs money; Regional is free forever
  
- **Region**: Choose closest to your Render region
  - AWS US-EAST-1 (Virginia) → matches Render Ohio
  - AWS US-WEST-1 (N. California) → matches Render Oregon
  - EU-CENTRAL-1 (Frankfurt) → matches Render Frankfurt
  - AP-SOUTHEAST-1 (Singapore) → matches Render Singapore
  
- **TLS (SSL)**: Keep **enabled** (recommended)
  - Encrypts data in transit
  
- **Eviction**: Leave as default
  - `allkeys-lru` is fine for most uses

5. Click **"Create"** button at the bottom

### Step 5: Wait for Creation
- Takes 5-10 seconds
- You'll see your new database in the list
- Click on it to open the database details page

### Step 6: Copy Connection Details
On the database details page, you'll see:

#### Method 1: Copy Individual Details (Recommended)
1. Scroll to **"REST API"** or **"Details"** section
2. Find and copy these values:

   - **Endpoint**: `happy-goose-12345.upstash.io`
     - This is your `REDIS_HOST`
   
   - **Port**: `6379` or `6380`
     - If you see two ports, use `6379` (non-TLS) or `6380` (TLS)
     - This is your `REDIS_PORT`
   
   - **Password**: Click the eye icon to reveal, then copy
     - Long string like: `AXWxASnX...`
     - This is your `REDIS_PASSWORD`
   
   - **Database**: `0` (default)
     - This is your `REDIS_DB`

3. Save these values - you'll need them for Render environment variables

#### Method 2: Copy Full Redis URL (Alternative)
1. Find **"Redis URL"** or **"Connection String"**
2. It looks like: `redis://default:AXWxASnX...@happy-goose-12345.upstash.io:6379`
3. Parse it:
   - Host: `happy-goose-12345.upstash.io`
   - Port: `6379`
   - Password: `AXWxASnX...` (between `:` and `@`)

### Step 7: Test Connection (Optional)
1. On the database page, find **"CLI"** tab
2. Try commands like:
   ```
   PING
   ```
   Should return: `PONG`
3. This confirms your Redis is working

---

## Part 3: Summary - What You Need for Render

After completing both steps above, you should have:

### From Render PostgreSQL:
```
DATABASE_URL=postgresql://vikpay_db_user:XXX@dpg-XXX/vikpay_db
```

### From Upstash Redis:
```
REDIS_HOST=happy-goose-12345.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=AXWxASnXXXXXXXX
REDIS_DB=0
```

### Next Step:
Go to [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) Step 4 to create your Web Service and add these as environment variables.

---

## 💡 Pro Tips

### PostgreSQL on Render:
- **Use Internal URL** (not External) for better performance and security
- Free tier has 90-day trial, then $7/month
- Database auto-backs up daily
- You can connect with any PostgreSQL client (pgAdmin, DBeaver, psql)

### Redis on Upstash:
- **Free tier is forever** (10,000 commands/day)
- Upgrade to Pro if you need more (first million commands free, then pay-as-you-go)
- TLS encryption is recommended for production
- Upstash has a great web CLI for debugging

### Matching Regions:
For best performance, keep all services in the same region:
- **US East**: Render Ohio + Upstash us-east-1
- **US West**: Render Oregon + Upstash us-west-1
- **EU**: Render Frankfurt + Upstash eu-central-1
- **Asia**: Render Singapore + Upstash ap-southeast-1

---

## 🆘 Troubleshooting

### PostgreSQL Issues:
- **"Can't connect"**: Make sure you're using Internal URL, not External
- **"Too many connections"**: Free tier has 97 connection limit
- **"Database doesn't exist"**: Check database name in connection string

### Upstash Redis Issues:
- **"Connection timeout"**: Check if TLS is enabled; you may need port 6380
- **"Authentication failed"**: Double-check password (no extra spaces)
- **"Command limit exceeded"**: Upgrade to paid tier or optimize usage

### Still Stuck?
- **Render Support**: https://render.com/docs/databases
- **Upstash Docs**: https://docs.upstash.com/redis
- **My logs**: Check Render service logs for specific error messages

---

## ✅ Ready for Next Step

Once you have both:
1. ✅ PostgreSQL Internal URL copied
2. ✅ Redis connection details copied

Proceed to create your Web Service on Render and add these as environment variables!

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for the next steps.
