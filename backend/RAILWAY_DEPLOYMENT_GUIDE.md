# Railway Deployment Guide for Docs-Wiki Backend

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- GitHub account
- Railway account (free at [railway.app](https://railway.app))
- Your optimized backend code

### Step 1: Prepare Your Repository

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

2. **Verify these files are in your repository**:
   - `railway.json` ✅
   - `nixpacks.toml` ✅
   - `Procfile` ✅
   - `requirements.txt` ✅
   - `main.py` ✅

### Step 2: Deploy to Railway

1. **Go to [railway.app](https://railway.app)** and sign in
2. **Click "New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Choose your repository** (`docs-wiki`)
5. **Select the backend folder** as the root directory
6. **Click "Deploy"**

### Step 3: Configure Environment Variables

In your Railway project dashboard:

1. **Go to Variables tab**
2. **Add these environment variables**:

```bash
# API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here

# Backend Configuration
BACKEND_URL=https://your-app-name.railway.app
PYTHON_VERSION=3.11.0
WORKERS=2
WORKER_CONNECTIONS=1000

# Optional: Performance Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=INFO
```

### Step 4: Test Your Deployment

1. **Wait for deployment to complete** (2-3 minutes)
2. **Visit your app URL**: `https://your-app-name.railway.app`
3. **Test the health endpoint**: `https://your-app-name.railway.app/api/performance`
4. **Test the chat endpoint** with a simple request

## 🔧 Railway Configuration Files Explained

### railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/performance",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Key features**:
- Uses Nixpacks for automatic dependency detection
- Health check on `/api/performance` endpoint
- Auto-restart on failure
- Optimized for FastAPI

### nixpacks.toml
```toml
[phases.setup]
nixPkgs = ["python311", "nodejs", "chromium"]

[phases.install]
cmds = [
  "pip install --upgrade pip",
  "pip install -r requirements.txt",
  "playwright install --with-deps"
]

[phases.build]
cmds = [
  "echo 'Build completed'"
]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2"
```

**Key features**:
- Installs Python 3.11, Node.js, and Chromium
- Installs Playwright browsers for web scraping
- Uses 2 workers for better performance
- Optimized build process

### Procfile
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
```

**Key features**:
- Defines the web process
- Uses 2 workers for concurrent requests
- Binds to all interfaces (0.0.0.0)

## 📊 Performance Optimizations for Railway

### 1. Worker Configuration
Your backend is configured with 2 workers for better concurrency:
```python
# In Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
```

### 2. Health Check Optimization
Railway will monitor your app using the `/api/performance` endpoint:
```python
@app.get("/api/performance")
async def get_performance_stats():
    # Returns system stats, cache stats, and optimization status
    return {
        "status": "healthy",
        "optimizations": {
            "gzip_compression": "enabled",
            "response_caching": "enabled",
            "model_optimization": "enabled",
            "streaming_optimization": "enabled"
        }
    }
```

### 3. Memory Optimization
Railway provides 512MB RAM by default. Your optimizations help:
- **Response caching** reduces API calls
- **Gzip compression** reduces bandwidth
- **Smart model selection** uses optimal models
- **Streaming** provides better perceived performance

## 🚀 Advanced Railway Features

### 1. Custom Domains
1. **Go to Settings → Domains**
2. **Add your custom domain**
3. **Configure DNS** as instructed
4. **SSL is automatic**

### 2. Environment Management
- **Development**: Use Railway's preview deployments
- **Production**: Use main branch
- **Staging**: Use separate Railway project

### 3. Monitoring and Logs
- **Real-time logs** in Railway dashboard
- **Performance metrics** via `/api/performance`
- **Error tracking** with automatic restarts

### 4. Scaling
Railway automatically scales based on traffic:
- **CPU usage** monitoring
- **Memory usage** monitoring
- **Request queue** management

## 🔍 Troubleshooting

### Common Issues:

#### 1. **Build Failures**
```bash
# Check logs in Railway dashboard
# Common fixes:
- Update requirements.txt
- Check Python version compatibility
- Verify all dependencies are listed
```

#### 2. **Playwright Installation Issues**
```bash
# The nixpacks.toml handles this automatically
# If issues persist, check:
- Chromium installation in logs
- Playwright browser dependencies
```

#### 3. **Memory Issues**
```bash
# Optimize by:
- Reducing worker count to 1
- Enabling more aggressive caching
- Using smaller model responses
```

#### 4. **API Key Issues**
```bash
# Verify in Railway dashboard:
- All environment variables are set
- No typos in variable names
- Values don't have extra spaces
```

### Debug Commands:

#### Check App Status:
```bash
curl https://your-app-name.railway.app/api/performance
```

#### Test Chat Endpoint:
```bash
curl -X POST https://your-app-name.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "model": "openai/gpt-5"}'
```

## 📈 Expected Performance on Railway

### With Your Optimizations:
- **Average Response Time**: 2-5 seconds
- **Concurrent Users**: 50-100
- **Uptime**: 99.9%
- **Memory Usage**: 200-400MB
- **CPU Usage**: 20-40%

### Monitoring:
- **Health Check**: Every 30 seconds
- **Auto-restart**: On failure
- **Logs**: Real-time in dashboard
- **Metrics**: Available via API

## 💰 Railway Pricing

### Free Tier:
- **$5 credit** per month
- **512MB RAM**
- **1GB storage**
- **Custom domains**
- **Perfect for development/testing**

### Pro Plan ($5/month):
- **$5 credit** per month
- **1GB RAM**
- **10GB storage**
- **Priority support**
- **Perfect for production**

## 🎯 Next Steps After Deployment

1. **Test all endpoints** thoroughly
2. **Monitor performance** via `/api/performance`
3. **Set up custom domain** (optional)
4. **Configure monitoring alerts** (optional)
5. **Scale up** if needed

## 🚀 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables configured
- [ ] Deployment successful
- [ ] Health check passing
- [ ] Chat endpoint working
- [ ] Performance optimizations active
- [ ] Custom domain configured (optional)
- [ ] Monitoring set up (optional)

## 🆘 Support

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **GitHub Issues**: Create issue in your repository

Your optimized backend is now ready for Railway deployment! 🎉
