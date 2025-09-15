# 🚀 Baseball Trade AI - Production Deployment Guide

## Quick Launch Summary

**Time to Deploy: 15-30 minutes** ⏱️

1. **Create GitHub Repository** (5 min)
2. **Deploy Backend to Railway** (10 min) 
3. **Deploy Frontend to Vercel** (10 min)
4. **Configure Environment Variables** (5 min)
5. **Test & Go Live!** 🎉

---

## 📋 Prerequisites

Before deploying, ensure you have:
- [x] GitHub account
- [x] Railway account (free tier available)
- [x] Vercel account (free tier available)
- [x] Supabase account (free tier available)
- [x] OpenAI API key

## 🏗️ Step 1: Create GitHub Repository

1. **Go to GitHub** and create a new repository:
   ```
   Repository name: MLB_trade_analyzer
   Description: Baseball Trade AI - Complete MLB front office simulation using CrewAI
   Visibility: Public (recommended for portfolio)
   ```

2. **Push your code**:
   ```bash
   cd "/Users/brycehenthorn/Desktop/github repos/MLB_trade_analyzer"
   git remote add origin https://github.com/bhenthorn2757/MLB_trade_analyzer.git
   git branch -M main
   git push -u origin main
   ```

## 🚂 Step 2: Deploy Backend to Railway

1. **Go to [Railway](https://railway.app)** and sign in
2. **Click "New Project"** → **"Deploy from GitHub repo"**
3. **Select your repository** → **Choose root directory**
4. **Configure deployment**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `/` (leave empty)

5. **Set Environment Variables** in Railway dashboard:
   ```bash
   OPENAI_API_KEY=your_openai_key_here
   SUPABASE_URL=your_supabase_url
   SUPABASE_SECRET_KEY=your_supabase_service_key
   SUPABASE_ANON_KEY=your_supabase_anon_key
   ENVIRONMENT=production
   API_HOST=0.0.0.0
   PORT=$PORT
   LOG_LEVEL=INFO
   ```

6. **Deploy** - Railway will automatically build and deploy your backend

## ⚡ Step 3: Deploy Frontend to Vercel

1. **Go to [Vercel](https://vercel.com)** and sign in
2. **Click "New Project"** → **Import from Git**
3. **Select your repository** → **Configure project**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

4. **Set Environment Variables** in Vercel dashboard:
   ```bash
   NEXT_PUBLIC_API_URL=https://your-railway-backend-url.railway.app
   REVALIDATION_SECRET=your-32-character-random-secret-here
   NODE_ENV=production
   ```

5. **Deploy** - Vercel will build and deploy your frontend

## 🔧 Step 4: Configure Production Settings

### Update CORS Settings
1. **Get your Vercel URL** (e.g., `https://your-app.vercel.app`)
2. **Update backend CORS** in Railway environment variables:
   ```bash
   ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com
   ```

### Generate Strong Secrets
```bash
# Generate a secure revalidation secret
openssl rand -hex 32
# Use this for REVALIDATION_SECRET in Vercel
```

### Set Up Custom Domain (Optional)
1. **In Vercel Dashboard**: Go to Project → Domains → Add Domain
2. **Configure DNS**: Point your domain to Vercel
3. **Update CORS**: Add your custom domain to ALLOWED_ORIGINS

## 🧪 Step 5: Test Your Deployment

### Backend Health Check
```bash
curl https://your-railway-backend.railway.app/api/health
# Should return: {"status": "healthy", "timestamp": "..."}
```

### Frontend Health Check
```bash
curl https://your-app.vercel.app/api/health
# Should return: {"service": "frontend", "status": "operational"}
```

### Test Trade Evaluation
```bash
curl -X POST https://your-railway-backend.railway.app/api/trades/quick-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "team": "yankees",
    "request": "I need a power bat with high OPS"
  }'
```

## 🔒 Security Checklist

Before going live, verify:
- [x] **CORS properly configured** (no wildcard origins)
- [x] **Environment variables set** in both platforms
- [x] **Strong secrets generated** (32+ characters)
- [x] **HTTPS enabled** (automatic on both platforms)
- [x] **API documentation disabled** in production
- [x] **Security headers active** (check with browser dev tools)

## 📊 Monitoring & Maintenance

### Set Up Monitoring
1. **Railway**: Monitor logs and performance in dashboard
2. **Vercel**: Use Analytics and Functions tabs
3. **Supabase**: Monitor database performance and usage

### Regular Maintenance
- **Weekly**: Check error logs and performance
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review API usage and costs

## 🚨 Troubleshooting

### Common Issues

**Backend won't start on Railway:**
```bash
# Check these in Railway logs:
1. Python version compatibility (uses Python 3.9+)
2. Requirements.txt dependencies
3. Environment variables are set
4. Port binding: Use $PORT, not hardcoded 8000
```

**Frontend build fails on Vercel:**
```bash
# Common fixes:
1. Set Node.js version to 18.x in Vercel
2. Check TypeScript errors in build logs
3. Verify all dependencies in package.json
4. Set correct root directory: frontend/
```

**CORS errors:**
```bash
# Update Railway environment:
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
# Redeploy backend after changing CORS settings
```

### Performance Optimization

**Backend (Railway):**
- Use Redis for caching (Railway Redis add-on)
- Monitor API response times
- Consider upgrading plan for higher traffic

**Frontend (Vercel):**
- Enable Vercel Analytics
- Use ISR for team and player data
- Optimize images and bundle size

## 💰 Cost Estimation

### Free Tier Limits
- **Railway**: 512MB RAM, $5 credit/month
- **Vercel**: 100GB bandwidth, unlimited requests
- **Supabase**: 500MB database, 2GB bandwidth
- **OpenAI**: Pay per token (~$0.001-0.03 per request)

### Scaling Costs
- **Railway Pro**: $20/month for 8GB RAM
- **Vercel Pro**: $20/month for team features
- **OpenAI**: Budget $50-200/month for moderate usage

## 🎉 You're Live!

Once deployed:
1. **Share your app**: `https://your-app.vercel.app`
2. **Monitor usage**: Check dashboards daily for first week
3. **Gather feedback**: Share with baseball fans and friends
4. **Iterate**: Use feedback to improve features

## 📞 Support

Need help? Check:
- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Project Issues**: https://github.com/bhenthorn2757/MLB_trade_analyzer/issues

---

**🚀 Congratulations! Your Baseball Trade AI is now live and ready to revolutionize how people think about baseball trades!** ⚾