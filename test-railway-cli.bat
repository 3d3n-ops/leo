@echo off
echo 🚀 Testing with Railway CLI (Advanced)...
echo.

echo 📦 Installing Railway CLI...
npm install -g @railway/cli

if %ERRORLEVEL% neq 0 (
    echo ❌ Railway CLI installation failed!
    echo Please install Node.js and npm first
    pause
    exit /b 1
)

echo ✅ Railway CLI installed!
echo.

echo 🔐 Logging into Railway...
railway login

if %ERRORLEVEL% neq 0 (
    echo ❌ Railway login failed!
    pause
    exit /b 1
)

echo ✅ Logged into Railway!
echo.

echo 🧪 Testing local build with Railway...
railway up --detach

if %ERRORLEVEL% neq 0 (
    echo ❌ Railway local test failed!
    pause
    exit /b 1
)

echo ✅ Railway local test successful!
echo.

echo 🧹 Stopping local Railway instance...
railway down

echo 🎉 Ready for production deployment!
pause
