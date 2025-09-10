# Railway Deployment Troubleshooting Guide

## 🚨 Common Issues and Solutions

### Issue 1: "pip: command not found" Error

**Problem**: Railway can't find the pip command during build.

**Solution**: Use the updated configuration files:

1. **Updated nixpacks.toml** (uses `python3 -m pip`):
```toml
[phases.install]
cmds = [
  "python3 -m pip install --upgrade pip",
  "python3 -m pip install -r requirements.txt",
  "python3 -m playwright install --with-deps"
]
```

2. **Alternative: Use Dockerfile** (more reliable):
```dockerfile
FROM python:3.11-slim
# ... rest of Dockerfile
```

### Issue 2: Python Environment Not Found

**Problem**: Python executable not found.

**Solutions**:
1. **Add runtime.txt**:
```
python-3.11.0
```

2. **Use explicit python3 commands**:
```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Issue 3: Playwright Installation Fails

**Problem**: Playwright browsers not installing.

**Solution**: Use the Dockerfile approach:
```dockerfile
# Install system dependencies first
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright after system deps
RUN playwright install --with-deps
```

### Issue 4: Memory Issues

**Problem**: App runs out of memory.

**Solutions**:
1. **Reduce workers** in Procfile:
```
web: python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. **Enable more caching** in your app
3. **Upgrade Railway plan** if needed

## 🔧 Fixed Configuration Files

### 1. Updated railway.json (Docker approach)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python -m uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/performance",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2. Updated nixpacks.toml (Nixpacks approach)
```toml
[phases.setup]
nixPkgs = ["python311", "nodejs", "chromium"]

[phases.install]
cmds = [
  "python3 -m pip install --upgrade pip",
  "python3 -m pip install -r requirements.txt",
  "python3 -m playwright install --with-deps"
]

[start]
cmd = "python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT"
```

### 3. Updated Procfile
```
web: python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 4. Added runtime.txt
```
python-3.11.0
```

## 🚀 Deployment Steps (Fixed)

### Option 1: Docker Approach (Recommended)

1. **Use the Dockerfile** (already created)
2. **Update railway.json** to use Dockerfile
3. **Deploy to Railway**

### Option 2: Nixpacks Approach (Fixed)

1. **Use updated nixpacks.toml**
2. **Add runtime.txt**
3. **Update Procfile**
4. **Deploy to Railway**

## 🔍 Debug Commands

### Check Build Logs
1. Go to Railway dashboard
2. Click on your project
3. Go to "Deployments" tab
4. Click on the failed deployment
5. Check the build logs

### Test Locally
```bash
# Test with Docker
docker build -t docs-wiki-backend .
docker run -p 8000:8000 docs-wiki-backend

# Test with Python directly
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📋 Deployment Checklist

- [ ] **Dockerfile** exists and is correct
- [ ] **railway.json** uses DOCKERFILE builder
- [ ] **runtime.txt** specifies Python 3.11.0
- [ ] **requirements.txt** has all dependencies
- [ ] **Environment variables** are set in Railway
- [ ] **Code is pushed** to GitHub
- [ ] **Railway project** is linked to GitHub repo

## 🆘 Still Having Issues?

### 1. Check Railway Logs
- Go to Railway dashboard
- Click on your project
- Check the "Logs" tab for errors

### 2. Verify Environment Variables
- Go to Railway dashboard
- Click on your project
- Go to "Variables" tab
- Ensure all API keys are set

### 3. Test Health Endpoint
```bash
curl https://your-app.railway.app/api/performance
```

### 4. Contact Support
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Railway Docs: [docs.railway.app](https://docs.railway.app)

## 🎯 Quick Fix Summary

The main issue was that Railway couldn't find the `pip` command. The fixes:

1. **Use `python3 -m pip`** instead of `pip`
2. **Add runtime.txt** for Python version
3. **Use Dockerfile** for more reliable builds
4. **Update all configuration files** with explicit Python commands

Try deploying again with these fixes! 🚀
