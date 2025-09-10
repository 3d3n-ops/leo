#!/bin/bash

# Railway Deployment Script for Docs-Wiki Backend
# This script helps you deploy your optimized backend to Railway

echo "🚀 Railway Deployment Script for Docs-Wiki Backend"
echo "=================================================="

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run this from your project root."
    exit 1
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

echo "✅ Prerequisites check passed"

# Check if all required files exist
echo "🔍 Checking required files..."

required_files=("railway.json" "nixpacks.toml" "Procfile" "requirements.txt" "main.py")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All required files found"

# Check if environment variables are set
echo "🔍 Checking environment variables..."

required_vars=("OPENROUTER_API_KEY" "PERPLEXITY_API_KEY" "OPENAI_API_KEY" "PINECONE_API_KEY")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "⚠️  Environment variable $var is not set"
        echo "   Please set it in Railway dashboard after deployment"
    fi
done

# Commit and push changes
echo "📤 Committing and pushing changes..."

git add .
git commit -m "Add Railway deployment configuration" || echo "No changes to commit"
git push origin main

echo "✅ Code pushed to GitHub"

# Deploy to Railway
echo "🚀 Deploying to Railway..."

if railway login; then
    echo "✅ Logged in to Railway"
    
    if railway link; then
        echo "✅ Project linked to Railway"
        
        if railway up; then
            echo "✅ Deployment started!"
            echo ""
            echo "🎉 Your backend is being deployed to Railway!"
            echo ""
            echo "📋 Next steps:"
            echo "1. Go to https://railway.app/dashboard"
            echo "2. Find your project and click on it"
            echo "3. Go to Variables tab"
            echo "4. Add your API keys:"
            echo "   - OPENROUTER_API_KEY"
            echo "   - PERPLEXITY_API_KEY"
            echo "   - OPENAI_API_KEY"
            echo "   - ANTHROPIC_API_KEY"
            echo "   - PINECONE_API_KEY"
            echo "   - PINECONE_ENVIRONMENT"
            echo "5. Wait for deployment to complete"
            echo "6. Test your API at the provided URL"
            echo ""
            echo "🔗 Your app will be available at: https://your-app-name.railway.app"
            echo "🏥 Health check: https://your-app-name.railway.app/api/performance"
        else
            echo "❌ Deployment failed. Check Railway dashboard for details."
            exit 1
        fi
    else
        echo "❌ Failed to link project to Railway"
        exit 1
    fi
else
    echo "❌ Failed to login to Railway"
    echo "Please run 'railway login' manually and try again"
    exit 1
fi

echo ""
echo "🎉 Deployment script completed!"
echo "Check the Railway dashboard for deployment status and logs."
