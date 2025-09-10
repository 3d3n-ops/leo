@echo off
REM Railway Deployment Script for Docs-Wiki Backend (Windows)
REM This script helps you deploy your optimized backend to Railway

echo 🚀 Railway Deployment Script for Docs-Wiki Backend
echo ==================================================

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed. Please install Git first.
    pause
    exit /b 1
)

REM Check if we're in a git repository
if not exist ".git" (
    echo ❌ Not in a git repository. Please run this from your project root.
    pause
    exit /b 1
)

REM Check if Railway CLI is installed
railway --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing Railway CLI...
    npm install -g @railway/cli
)

echo ✅ Prerequisites check passed

REM Check if all required files exist
echo 🔍 Checking required files...

if not exist "railway.json" (
    echo ❌ Missing required file: railway.json
    pause
    exit /b 1
)
if not exist "nixpacks.toml" (
    echo ❌ Missing required file: nixpacks.toml
    pause
    exit /b 1
)
if not exist "Procfile" (
    echo ❌ Missing required file: Procfile
    pause
    exit /b 1
)
if not exist "requirements.txt" (
    echo ❌ Missing required file: requirements.txt
    pause
    exit /b 1
)
if not exist "main.py" (
    echo ❌ Missing required file: main.py
    pause
    exit /b 1
)

echo ✅ All required files found

REM Commit and push changes
echo 📤 Committing and pushing changes...

git add .
git commit -m "Add Railway deployment configuration" 2>nul || echo No changes to commit
git push origin main

echo ✅ Code pushed to GitHub

REM Deploy to Railway
echo 🚀 Deploying to Railway...

railway login
if %errorlevel% neq 0 (
    echo ❌ Failed to login to Railway
    echo Please run 'railway login' manually and try again
    pause
    exit /b 1
)

echo ✅ Logged in to Railway

railway link
if %errorlevel% neq 0 (
    echo ❌ Failed to link project to Railway
    pause
    exit /b 1
)

echo ✅ Project linked to Railway

railway up
if %errorlevel% neq 0 (
    echo ❌ Deployment failed. Check Railway dashboard for details.
    pause
    exit /b 1
)

echo ✅ Deployment started!
echo.
echo 🎉 Your backend is being deployed to Railway!
echo.
echo 📋 Next steps:
echo 1. Go to https://railway.app/dashboard
echo 2. Find your project and click on it
echo 3. Go to Variables tab
echo 4. Add your API keys:
echo    - OPENROUTER_API_KEY
echo    - PERPLEXITY_API_KEY
echo    - OPENAI_API_KEY
echo    - ANTHROPIC_API_KEY
echo    - PINECONE_API_KEY
echo    - PINECONE_ENVIRONMENT
echo 5. Wait for deployment to complete
echo 6. Test your API at the provided URL
echo.
echo 🔗 Your app will be available at: https://your-app-name.railway.app
echo 🏥 Health check: https://your-app-name.railway.app/api/performance

echo.
echo 🎉 Deployment script completed!
echo Check the Railway dashboard for deployment status and logs.
pause
