# Railway Deployment - Fixed Configuration

## 🚨 Issue Fixed: Dockerfile Not Found

The problem was that Railway was looking for the Dockerfile in the repository root, but it was in the `backend/` folder.

## ✅ Solution: Two Deployment Options

### Option 1: Docker Deployment (Recommended)

**Files created in repository root:**
- `Dockerfile` - Copies backend files and runs the app
- `.dockerignore` - Excludes frontend and unnecessary files
- `railway.json` - Uses Dockerfile builder

**How it works:**
1. Railway finds `Dockerfile` in root
2. Dockerfile copies `backend/` files to container
3. Installs dependencies and runs the app

### Option 2: Nixpacks Deployment (Alternative)

**Files created in repository root:**
- `nixpacks.toml` - Changes to backend directory
- `Procfile` - Runs from backend directory
- `railway.json` - Uses Nixpacks builder

## 🚀 Deploy Now

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Fix Railway deployment - add root level config files"
git push origin main
```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Create new project
3. Deploy from GitHub repo
4. Select `docs-wiki` repository
5. **Don't select a subfolder** - use root directory
6. Deploy!

### Step 3: Add Environment Variables
In Railway dashboard → Variables:
```
OPENROUTER_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
PINECONE_API_KEY=your_key
PINECONE_ENVIRONMENT=your_env
```

## 🔧 Configuration Files Explained

### Dockerfile (Root Level)
```dockerfile
# Copies backend/requirements.txt
COPY backend/requirements.txt .

# Installs dependencies
RUN pip install -r requirements.txt

# Copies all backend files
COPY backend/ .

# Runs the app
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### nixpacks.toml (Root Level)
```toml
[phases.install]
cmds = [
  "cd backend",  # Change to backend directory
  "python3 -m pip install --upgrade pip",
  "python3 -m pip install -r requirements.txt",
  "python3 -m playwright install --with-deps"
]

[start]
cmd = "cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT"
```

## 🎯 Why This Works

1. **Railway looks in repository root** for configuration files
2. **Dockerfile approach**: Copies backend files into container
3. **Nixpacks approach**: Changes to backend directory before running
4. **Both approaches** work with your existing backend code

## 🧪 Test Your Deployment

```bash
# Test health check
curl https://your-app.railway.app/api/performance

# Test chat endpoint
curl -X POST https://your-app.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "model": "openai/gpt-5"}'
```

## 🎉 Expected Results

- ✅ **Dockerfile found** in repository root
- ✅ **Backend code copied** to container
- ✅ **Dependencies installed** correctly
- ✅ **Playwright browsers** installed
- ✅ **App runs** on port 8000
- ✅ **Health check** works at `/api/performance`

Your deployment should work perfectly now! 🚀
