# 🌐 Deploy StadiumOS GenAI to the Internet

This guide covers multiple options to deploy your application to the internet, from free hosting to production-grade cloud platforms.

---

## 🚀 Quick Comparison

| Platform | Cost | Difficulty | Best For | Deployment Time |
|----------|------|------------|----------|-----------------|
| **Render** | Free/$7/mo | ⭐ Easy | Quick demos, prototypes | 10 min |
| **Railway** | Free/$5/mo | ⭐ Easy | Hobby projects | 10 min |
| **Heroku** | $7-13/mo | ⭐⭐ Easy | Small apps | 15 min |
| **DigitalOcean** | $12/mo | ⭐⭐⭐ Medium | Production apps | 30 min |
| **AWS (ECS)** | $20+/mo | ⭐⭐⭐⭐ Hard | Enterprise | 1 hour |
| **Google Cloud Run** | Pay-per-use | ⭐⭐ Medium | Scalable apps | 20 min |

---

## Option 1: Render (Recommended for Beginners) ⭐

**Cost:** Free tier available, $7/month for production  
**Time:** 10 minutes  
**Perfect for:** Quick demos, competition submissions

### Step-by-Step Guide

#### 1. Sign Up for Render
Visit: https://render.com/register

#### 2. Connect GitHub Repository

```bash
# First, push your code to GitHub
cd c:\Users\User\OneDrive\Desktop\project4\stadiumos-genai-complete\stadiumos-genai
git init
git add .
git commit -m "Initial commit"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/stadiumos-genai.git
git push -u origin main
```

#### 3. Create `render.yaml` in Your Project Root

```yaml
# render.yaml
services:
  # Redis Cache
  - type: redis
    name: stadiumos-redis
    plan: free
    maxmemoryPolicy: allkeys-lru
    ipAllowList: []

  # Backend API
  - type: web
    name: stadiumos-backend
    runtime: docker
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    plan: free  # or 'starter' for $7/mo
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false  # Set manually in dashboard
      - key: ANTHROPIC_MODEL
        value: claude-sonnet-4-6
      - key: REDIS_HOST
        fromService:
          type: redis
          name: stadiumos-redis
          property: host
      - key: REDIS_PORT
        fromService:
          type: redis
          name: stadiumos-redis
          property: port
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
      - key: ADMIN_API_KEY
        generateValue: true
      - key: ALLOWED_ORIGINS
        value: '["https://stadiumos-frontend.onrender.com"]'
    healthCheckPath: /api/v1/health

  # Frontend
  - type: web
    name: stadiumos-frontend
    runtime: static
    buildCommand: echo "No build needed"
    staticPublishPath: ./frontend
    routes:
      - type: rewrite
        source: /api/*
        destination: https://stadiumos-backend.onrender.com/api/*
    headers:
      - path: /*
        name: Cache-Control
        value: public, max-age=3600
```

#### 4. Deploy to Render

1. Go to: https://dashboard.render.com/
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will detect `render.yaml` and create all services
5. Set `ANTHROPIC_API_KEY` in the dashboard:
   - Go to Backend service → Environment
   - Add your API key

#### 5. Access Your Live Application

Your app will be available at:
- **Frontend:** `https://stadiumos-frontend.onrender.com`
- **Backend API:** `https://stadiumos-backend.onrender.com`
- **Docs:** `https://stadiumos-backend.onrender.com/docs`

**Note:** Free tier services sleep after 15 minutes of inactivity and take ~30 seconds to wake up.

---

## Option 2: Railway.app (Fastest Deployment) ⭐

**Cost:** $5/month for 5GB RAM  
**Time:** 5 minutes  
**Perfect for:** Quick launches, hobby projects

### Deployment Steps

#### 1. Sign Up
Visit: https://railway.app/

#### 2. Install Railway CLI

```bash
# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# Verify installation
railway --version
```

#### 3. Deploy with One Command

```bash
cd c:\Users\User\OneDrive\Desktop\project4\stadiumos-genai-complete\stadiumos-genai

# Login
railway login

# Initialize project
railway init

# Add Redis
railway add --redis

# Deploy
railway up

# Set environment variables
railway variables set ANTHROPIC_API_KEY=sk-ant-your-key-here
railway variables set ENVIRONMENT=production

# Generate domain
railway domain
```

#### 4. Access Your Application

Railway will provide a public URL like:
`https://your-app.up.railway.app`

---

## Option 3: DigitalOcean App Platform (Production Ready) ⭐⭐⭐

**Cost:** $12/month (Basic plan)  
**Time:** 30 minutes  
**Perfect for:** Production deployments, competition finals

### Step-by-Step Guide

#### 1. Create DigitalOcean Account
Visit: https://www.digitalocean.com/  
**Get $200 free credit for 60 days with student/startup pack**

#### 2. Create `.do/app.yaml`

```yaml
# .do/app.yaml
name: stadiumos-genai
region: nyc

databases:
  - name: redis
    engine: REDIS
    production: true
    plan: basic

services:
  # Backend API
  - name: backend
    source:
      repo: YOUR_GITHUB_USERNAME/stadiumos-genai
      branch: main
      path: /backend
    dockerfile_path: backend/Dockerfile
    instance_size_slug: basic-xxs
    instance_count: 1
    http_port: 8000
    routes:
      - path: /api
      - path: /admin
      - path: /docs
      - path: /openapi.json
    health_check:
      http_path: /api/v1/health
    envs:
      - key: ANTHROPIC_API_KEY
        scope: RUN_TIME
        type: SECRET
      - key: ANTHROPIC_MODEL
        value: claude-sonnet-4-6
      - key: REDIS_HOST
        value: ${redis.HOSTNAME}
      - key: REDIS_PORT
        value: ${redis.PORT}
      - key: REDIS_PASSWORD
        value: ${redis.PASSWORD}
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false

  # Frontend
  - name: frontend
    source:
      repo: YOUR_GITHUB_USERNAME/stadiumos-genai
      branch: main
      path: /frontend
    static_sites:
      - name: frontend
        source_dir: /
        routes:
          - path: /
```

#### 3. Deploy via Dashboard

1. Go to: https://cloud.digitalocean.com/apps
2. Click **"Create App"**
3. Connect GitHub repository
4. DigitalOcean will detect `app.yaml`
5. Review and deploy

#### 4. Configure Custom Domain (Optional)

1. In App settings → Domains
2. Add your domain (e.g., `stadiumos.com`)
3. Update DNS records as instructed
4. SSL certificate is automatically provisioned

**Your app will be at:** `https://your-app.ondigitalocean.app`

---

## Option 4: Google Cloud Run (Auto-scaling) ⭐⭐

**Cost:** Pay per use (~$5-20/month)  
**Time:** 20 minutes  
**Perfect for:** Variable traffic, FIFA event spikes

### Deployment Guide

#### 1. Install Google Cloud SDK

Download from: https://cloud.google.com/sdk/docs/install

```bash
# Verify installation
gcloud --version

# Login
gcloud auth login

# Create project
gcloud projects create stadiumos-genai --name="StadiumOS GenAI"
gcloud config set project stadiumos-genai

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

#### 2. Deploy Backend to Cloud Run

```bash
cd c:\Users\User\OneDrive\Desktop\project4\stadiumos-genai-complete\stadiumos-genai\backend

# Build and push container
gcloud builds submit --tag gcr.io/stadiumos-genai/backend

# Deploy to Cloud Run
gcloud run deploy backend \
  --image gcr.io/stadiumos-genai/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars ANTHROPIC_API_KEY=your-key-here \
  --set-env-vars REDIS_HOST=your-redis-host \
  --max-instances 10 \
  --memory 1Gi \
  --cpu 1
```

#### 3. Set Up Redis (Cloud Memorystore)

```bash
# Create Redis instance
gcloud redis instances create stadiumos-redis \
  --size=1 \
  --region=us-central1 \
  --tier=basic

# Get connection info
gcloud redis instances describe stadiumos-redis --region=us-central1
```

#### 4. Deploy Frontend (Cloud Storage + CDN)

```bash
cd ../frontend

# Create bucket
gsutil mb gs://stadiumos-frontend

# Upload files
gsutil -m cp -r * gs://stadiumos-frontend

# Make public
gsutil iam ch allUsers:objectViewer gs://stadiumos-frontend

# Enable website hosting
gsutil web set -m index.html gs://stadiumos-frontend
```

**Your app will be at:** `https://backend-xxxxx-uc.a.run.app`

---

## Option 5: AWS (Production Enterprise) ⭐⭐⭐⭐

**Cost:** $20-50/month  
**Time:** 1 hour  
**Perfect for:** Large-scale production deployments

### Quick AWS Deployment

#### 1. Install AWS CLI

```bash
# Download from: https://aws.amazon.com/cli/

# Configure
aws configure
# Enter: Access Key ID, Secret Key, Region (us-east-1), Format (json)
```

#### 2. Deploy with AWS Copilot

```bash
# Install AWS Copilot
# Windows: https://github.com/aws/copilot-cli/releases

cd c:\Users\User\OneDrive\Desktop\project4\stadiumos-genai-complete\stadiumos-genai

# Initialize app
copilot app init stadiumos-genai

# Create environment
copilot env init --name production --profile default

# Deploy backend
copilot svc init --name backend \
  --svc-type "Load Balanced Web Service" \
  --dockerfile ./backend/Dockerfile

copilot svc deploy --name backend --env production

# Create Redis
copilot storage init --name cache \
  --storage-type Redis \
  --engine-version 7.0

# Deploy frontend to S3 + CloudFront
aws s3 mb s3://stadiumos-frontend
aws s3 sync frontend/ s3://stadiumos-frontend --acl public-read
```

---

## Option 6: Vercel (Frontend) + Render (Backend) 🔥

**Fastest for Demo:** Split deployment for optimal performance

### Deploy Frontend to Vercel (Free)

```bash
# Install Vercel CLI
npm install -g vercel

cd frontend
vercel

# Follow prompts:
# Set up and deploy? Yes
# Which scope? Your account
# Link to existing project? No
# What's your project name? stadiumos-frontend
# In which directory is your code? ./
# Override settings? No
```

**Frontend will be at:** `https://stadiumos-frontend.vercel.app`

### Deploy Backend to Render
Follow Option 1 (Render) above for backend only.

### Update CORS Settings
In `backend/.env`:
```env
ALLOWED_ORIGINS=["https://stadiumos-frontend.vercel.app"]
```

---

## 🔐 Security Checklist for Live Deployment

Before going live, ensure:

- [ ] Strong `ADMIN_API_KEY` set (32+ characters random)
- [ ] `DEBUG=false` and `ENVIRONMENT=production`
- [ ] `ALLOWED_ORIGINS` set to your actual domain
- [ ] SSL/TLS enabled (automatic on most platforms)
- [ ] Anthropic API key stored as secret (not in git)
- [ ] Rate limiting enabled (already configured)
- [ ] Database backups enabled (Redis)
- [ ] Monitoring and alerts configured

---

## 🎯 My Recommendation for Competition

### For Quick Demo (Next 30 minutes):
**Use Render (Option 1)**
- Free tier available
- 10-minute setup
- Automatic SSL
- Easy to share URL with judges

### For Final Competition Submission:
**Use DigitalOcean (Option 3)**
- Professional appearance
- Custom domain support
- Better performance than free tiers
- $200 free credit available

### Command to Deploy to Render Right Now:

```bash
# 1. Create render.yaml (I'll create it for you)
# 2. Push to GitHub
cd c:\Users\User\OneDrive\Desktop\project4\stadiumos-genai-complete\stadiumos-genai
git init
git add .
git commit -m "Deploy to Render"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/stadiumos-genai.git
git push -u origin main

# 3. Go to https://dashboard.render.com/
# 4. Click "New +" → "Blueprint"
# 5. Connect repo → Render deploys automatically!
```

---

## 📊 Cost Comparison (Monthly)

| Platform | Free Tier | Paid Plan | Best For |
|----------|-----------|-----------|----------|
| Render | ✅ Yes (sleeps) | $7 | Demos |
| Railway | ✅ 500 hours | $5 | Hobby |
| Heroku | ❌ No | $13 | Simple apps |
| DigitalOcean | ❌ No | $12 | Production |
| Google Cloud | ✅ Credits | ~$10 | Auto-scale |
| AWS | ✅ 12 months | $20+ | Enterprise |
| Vercel (Frontend) | ✅ Yes | Free | Frontend |

---

## 🚀 Quick Start - Get Online in 10 Minutes

I'll create the necessary files for you. Choose your platform:

**Option A - Render (Recommended):**
1. I'll create `render.yaml`
2. You push to GitHub
3. Connect to Render
4. Done!

**Option B - Railway:**
1. Install Railway CLI
2. Run `railway up`
3. Done!

Which option would you like me to help you with? I can create the configuration files and guide you through the deployment process step by step.

---

## 🆘 Need Help?

Let me know which platform you want to use, and I'll:
1. Create all necessary configuration files
2. Walk you through each step
3. Help troubleshoot any issues
4. Verify your deployment is working

**Ready to deploy? Just tell me:**
- "Deploy to Render" (easiest)
- "Deploy to Railway" (fastest)
- "Deploy to DigitalOcean" (production-ready)

Let's get your application online! 🌐🚀
