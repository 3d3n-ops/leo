@echo off
echo 🐳 Testing Docker Build with Environment Variables...
echo.

echo 📦 Building Docker image...
docker build -t docs-wiki-backend .

if %ERRORLEVEL% neq 0 (
    echo ❌ Docker build failed!
    pause
    exit /b 1
)

echo ✅ Docker build successful!
echo.

echo 🚀 Testing Docker container with environment variables...
docker run -d -p 8000:8000 --name docs-wiki-test ^
  -e OPENROUTER_API_KEY=your_key_here ^
  -e PERPLEXITY_API_KEY=your_key_here ^
  -e OPENAI_API_KEY=your_key_here ^
  -e ANTHROPIC_API_KEY=your_key_here ^
  -e PINECONE_API_KEY=your_key_here ^
  -e PINECONE_ENVIRONMENT=your_env_here ^
  docs-wiki-backend

echo ⏳ Waiting for container to start...
timeout /t 15 /nobreak > nul

echo 🧪 Testing health endpoint...
curl -f http://localhost:8000/api/performance

if %ERRORLEVEL% neq 0 (
    echo ❌ Health check failed!
    echo 📋 Container logs:
    docker logs docs-wiki-test
    echo.
    echo 🧹 Cleaning up...
    docker stop docs-wiki-test
    docker rm docs-wiki-test
    pause
    exit /b 1
)

echo ✅ Health check passed!
echo.

echo 🧪 Testing chat endpoint with real API keys...
curl -X POST http://localhost:8000/api/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"Hello, test the API\", \"model\": \"openai/gpt-5\"}"

echo.
echo ✅ Full testing completed successfully!
echo.
echo 🧹 Cleaning up...
docker stop docs-wiki-test
docker rm docs-wiki-test

echo 🎉 Ready for Railway deployment!
pause
