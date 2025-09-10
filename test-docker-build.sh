#!/bin/bash

echo "🐳 Testing Docker Build Locally..."
echo

echo "📦 Building Docker image..."
docker build -t docs-wiki-backend .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "✅ Docker build successful!"
echo

echo "🚀 Testing Docker container..."
docker run -d -p 8000:8000 --name docs-wiki-test docs-wiki-backend

echo "⏳ Waiting for container to start..."
sleep 10

echo "🧪 Testing health endpoint..."
curl -f http://localhost:8000/api/performance

if [ $? -ne 0 ]; then
    echo "❌ Health check failed!"
    echo "📋 Container logs:"
    docker logs docs-wiki-test
    echo
    echo "🧹 Cleaning up..."
    docker stop docs-wiki-test
    docker rm docs-wiki-test
    exit 1
fi

echo "✅ Health check passed!"
echo

echo "🧪 Testing chat endpoint..."
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "model": "openai/gpt-5"}'

echo
echo "✅ Local testing completed successfully!"
echo
echo "🧹 Cleaning up..."
docker stop docs-wiki-test
docker rm docs-wiki-test

echo "🎉 Ready for Railway deployment!"
