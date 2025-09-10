# 🧪 Local Testing Guide for Railway Deployment

Test your Docker build and deployment locally before pushing to Railway!

## 🚀 **Quick Start - Choose Your Method**

### **Method 1: Docker Build Test (Recommended)**
```bash
# Windows
test-docker-build.bat

# Linux/Mac
chmod +x test-docker-build.sh
./test-docker-build.sh
```

### **Method 2: Backend Direct Test (Fastest)**
```bash
# Windows
test-backend-direct.bat

# Linux/Mac
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **Method 3: Comprehensive Test Suite**
```bash
# Install requests if needed
pip install requests

# Run comprehensive tests
python test-comprehensive.py
```

## 📋 **What Each Test Does**

### **Docker Build Test**
- ✅ Builds Docker image locally
- ✅ Starts container on port 8000
- ✅ Tests health endpoint (`/api/performance`)
- ✅ Tests chat endpoint (`/api/chat`)
- ✅ Cleans up container

### **Backend Direct Test**
- ✅ Installs dependencies
- ✅ Starts server with hot reload
- ✅ Tests endpoints manually
- ⚡ **Fastest method** for development

### **Comprehensive Test Suite**
- ✅ Full Docker build and container test
- ✅ Automated health checks
- ✅ API endpoint validation
- ✅ Container log analysis
- ✅ Automatic cleanup

## 🔧 **Prerequisites**

### **For Docker Tests:**
- Docker Desktop installed
- Docker daemon running

### **For Backend Direct Test:**
- Python 3.11+ installed
- Backend dependencies available

### **For Comprehensive Tests:**
- Docker Desktop
- Python 3.11+
- `requests` library: `pip install requests`

## 🧪 **Testing Scenarios**

### **1. Basic Functionality Test**
```bash
# Test if the app starts and responds
test-docker-build.bat
```

### **2. Development Test**
```bash
# Test with hot reload for development
test-backend-direct.bat
```

### **3. Production Simulation Test**
```bash
# Test with environment variables
test-with-env.bat
```

### **4. Full Validation Test**
```bash
# Comprehensive automated testing
python test-comprehensive.py
```

## 🐛 **Troubleshooting**

### **Docker Build Fails**
```bash
# Check Docker is running
docker --version

# Check Dockerfile syntax
docker build -t test-image . --no-cache

# Check container logs
docker logs docs-wiki-test
```

### **Backend Direct Test Fails**
```bash
# Check Python version
python --version

# Install dependencies
cd backend
pip install -r requirements.txt

# Check for missing modules
python -c "import main"
```

### **API Endpoints Not Responding**
```bash
# Check if server is running
curl http://localhost:8000/api/performance

# Check server logs
# Look for error messages in terminal
```

## 🎯 **Expected Results**

### **Successful Test Output:**
```
🐳 Testing Docker Build Locally...
📦 Building Docker image...
✅ Docker build successful!
🚀 Testing Docker container...
✅ Container started!
⏳ Waiting for container to start...
🧪 Testing health endpoint...
✅ Health check passed!
🧪 Testing chat endpoint...
✅ Local testing completed successfully!
🧹 Cleaning up...
🎉 Ready for Railway deployment!
```

### **Health Check Response:**
```json
{
  "cache_stats": {...},
  "system_stats": {...},
  "status": "healthy",
  "optimizations": {...}
}
```

## 🚀 **After Successful Testing**

1. **Commit your changes:**
```bash
git add .
git commit -m "Test locally - ready for Railway deployment"
git push origin main
```

2. **Deploy to Railway:**
   - Go to [railway.app](https://railway.app)
   - Create new project
   - Deploy from GitHub
   - Select your repository
   - Deploy!

3. **Verify deployment:**
```bash
# Test your live Railway app
curl https://your-app.railway.app/api/performance
```

## 💡 **Pro Tips**

### **For Development:**
- Use `test-backend-direct.bat` for quick iteration
- Use `--reload` flag for automatic restarts
- Test with real API keys using `test-with-env.bat`

### **For Production:**
- Always run `test-comprehensive.py` before deploying
- Test with the same environment variables as Railway
- Check container logs for any issues

### **For Debugging:**
- Use `docker logs docs-wiki-test` to see container logs
- Check `test-comprehensive.py` output for detailed error info
- Test individual components separately

## 🎉 **Success Checklist**

Before deploying to Railway, ensure:
- [ ] Docker build succeeds locally
- [ ] Container starts without errors
- [ ] Health endpoint returns 200 OK
- [ ] Chat endpoint responds (even with 500 due to missing API keys)
- [ ] No critical errors in container logs
- [ ] All dependencies are properly installed
- [ ] Environment variables are configured

**You're ready for Railway deployment!** 🚀
