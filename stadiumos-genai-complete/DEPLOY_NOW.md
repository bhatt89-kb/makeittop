# 🚀 Deploy Your Website to the Internet - Quick Guide

## Option 1: Render.com (EASIEST - Recommended) ⭐

**Time:** 10 minutes  
**Cost:** FREE  
**Perfect for:** Competitions, demos, quick sharing

### Step 1: Push Code to GitHub

```bash
# Open PowerShell and navigate to your project
cd c:\Users\User\OneDrive\Desktop\project4\stadiumos-genai-complete\stadiumos-genai

# Initialize git (if not already done)
git init
git add .
git commit -m "Ready for deployment"
```

**Now go to GitHub:**
1. Visit https://github.com/new
2. Create a new repository named: `stadiumos-genai`
3. Don't initialize with README
4. Copy the repository URL

**Push your code:**
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/stadiumos-genai.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Render

1. **Sign up for Render:**
   - Go to: https://render.com/register
   - Sign up with GitHub (easiest option)

2. **Create New Blueprint:**
   - Click **"New +"** button (top right)
   - Select **"Blueprint"**
   - Click **"Connect Repository"**
   - Find and select your `stadiumos-genai` repository
   - Click **"Connect"**

3. **Render will automatically detect `render.yaml` and create:**
   - ✅ Redis cache
   - ✅ Backend API
   - ✅ Frontend website

4. **Set Your API Key:**
   - In the dashboard, click on **"stadiumos-backend"**
   - Go to **"Environment"** tab
   - Find `ANTHROPIC_API_KEY`
   - Click **"Edit"** and paste your API key
   - Click **"Save Changes"**

5. **Wait for Deployment (5-10 minutes):**
   - Watch the build logs
   - When you see "Live" status, you're done! 🎉

6. **Get Your URLs:**
   - Frontend: `https://stadiumos-frontend.onrender.com`
   - Backend API: `https://stadiumos-backend.onrender.com`
   - API Docs: `https://stadiumos-backend.onrender.com/docs`

### Step 3: Test Your Live Website

```bash
# Test the backend API
curl https://stadiumos-backend.onrender.com/api/v1/health

# Should return: {"status":"ok","genai_available":true}
```

Open in browser:
- Your website: `https://stadiumos-frontend.onrender.com`

**⚠️ Note:** Free tier services sleep after 15 minutes of inactivity. First request after sleep takes ~30 seconds to wake up.

---

## Option 2: Railway.app (FASTEST - 5 minutes) ⭐

**Time:** 5 minutes  
**Cost:** $5/month (includes everything)  
**Perfect for:** Quick launches, always-on hosting

### Step 1: Install Railway CLI

**Windows PowerShell:**
```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

### Step 2: Deploy

```bash
cd c:\Users\User\OneDrive\Desktop\project4\stadiumos-genai-complete\stadiumos-genai

# Login to Railway (opens browser)
railway login

# Create new project
railway init

# Add Redis
railway add

# Select: Redis

# Deploy everything
railway up

# Set environment variables
railway variables set ANTHROPIC_API_KEY=your-api-key-here
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false

# Generate public URL
railway domain
```

### Step 3: Access Your Website

Railway will show you the URL, something like:
`https://stadiumos-genai-production.up.railway.app`

**That's it! Your website is live!** 🚀

---

## Option 3: Vercel (Frontend Only - FREE & Fast) ⭐

If you only want to deploy the frontend quickly:

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Deploy Frontend

```bash
cd c:\Users\User\OneDrive\Desktop\project4\stadiumos-genai-complete\stadiumos-genai\frontend

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Y
# - Which scope? (select your account)
# - Link to existing project? N
# - What's your project's name? stadiumos-frontend
# - In which directory is your code located? ./
# - Want to override settings? N
```

**Your website will be live at:**
`https://stadiumos-frontend.vercel.app`

**Note:** For backend API, you'll still need to deploy it separately (use Render or Railway).

---

## 🎯 My Recommendation

**For your competition submission, I recommend:**

### Use Render (Option 1) because:
✅ Completely FREE  
✅ Automatic SSL certificate  
✅ Easy to set up  
✅ Provides both frontend and backend  
✅ Professional URL  
✅ No credit card required for free tier  
✅ Perfect for demos and judging  

**The render.yaml file is already created for you!**

---

## 📋 Quick Checklist

Before deploying, make sure you have:

- [ ] GitHub account (create at https://github.com/signup)
- [ ] Anthropic API key (get at https://console.anthropic.com/)
- [ ] Code pushed to GitHub repository
- [ ] Render.com account (sign up with GitHub)

---

## 🔧 Troubleshooting

### "git: command not found"
**Solution:** Install Git from https://git-scm.com/download/win

### "Permission denied (publickey)"
**Solution:** 
```bash
# Use HTTPS instead of SSH
git remote set-url origin https://github.com/YOUR_USERNAME/stadiumos-genai.git
```

### "Build failed on Render"
**Solution:** 
- Check build logs in Render dashboard
- Ensure all files are committed: `git status`
- Make sure Dockerfile is in `backend/` folder

### "Backend not connecting to Redis"
**Solution:**
- Render automatically connects services via environment variables
- Wait for Redis to be "Live" before backend starts
- Check environment variables in Render dashboard

---

## 🌐 After Deployment - Share Your Website

Once deployed, you can share:

1. **Frontend URL:** `https://stadiumos-frontend.onrender.com`
   - Main user interface
   - Share with judges/users

2. **API Documentation:** `https://stadiumos-backend.onrender.com/docs`
   - Interactive API explorer
   - Show technical capabilities

3. **Health Check:** `https://stadiumos-backend.onrender.com/api/v1/health`
   - Prove system is working

---

## 🎉 Next Steps After Going Live

1. **Test your live website** - Try all features
2. **Share with judges** - Send them the frontend URL
3. **Monitor performance** - Check Render dashboard
4. **Add custom domain** (optional) - Connect your own domain
5. **Scale if needed** - Upgrade to paid plan for better performance

---

## 💡 Quick Tips

- **Custom Domain:** In Render, go to Settings → Custom Domains
- **View Logs:** Click on service → Logs tab (real-time)
- **Restart Service:** Click service → Manual Deploy → Deploy latest commit
- **Environment Variables:** Service → Environment → Add/Edit variables

---

## 📞 Need Help?

If you encounter any issues:

1. Check Render build logs for errors
2. Verify all environment variables are set
3. Make sure your GitHub repository is public or connected
4. Test locally first with Docker to ensure it works

---

## 🚀 Ready to Deploy?

**Choose your method:**

### Quick & Free (Render):
```bash
1. Push to GitHub
2. Connect to Render
3. Wait 10 minutes
4. Done! ✅
```

### Fastest (Railway):
```bash
railway login
railway up
railway domain
Done! ✅
```

**Let's get your website online! 🌐**

Pick Option 1 (Render) and follow the steps above. I've already created the `render.yaml` configuration file for you, so Render will automatically set everything up!
