@echo off
echo 🚀 Testing Backend Directly (Fastest Method)...
echo.

echo 📁 Changing to backend directory...
cd backend

echo 📦 Installing dependencies...
python -m pip install -r requirements.txt

if %ERRORLEVEL% neq 0 (
    echo ❌ Dependency installation failed!
    pause
    exit /b 1
)

echo ✅ Dependencies installed!
echo.

echo 🚀 Starting backend server...
echo ⏳ Server will start on http://localhost:8000
echo ⏳ Press Ctrl+C to stop the server
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
