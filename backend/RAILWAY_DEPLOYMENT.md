# Railway Deployment Guide

This guide will help you deploy your FastAPI backend to Railway.

## Prerequisites

1. **GitHub Repository**: Your code should be pushed to a GitHub repository
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **API Keys**: Gather all required API keys (see Environment Variables section)

## Step-by-Step Deployment

### 1. Connect to Railway

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository (`docs-wiki`)
5. Select the `backend` folder as the root directory

### 2. Configure Environment Variables

In your Railway project dashboard, go to **Variables** tab and add:

#### Required API Keys
```bash
# Perplexity API (for research agent)
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# OpenAI API (for LLM processing)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API (backup LLM)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenRouter API (for Leo AI assistant)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Pinecone API (for vector storage)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
```

#### Optional Configuration
```bash
# Logging level (optional)
LOG_LEVEL=INFO

# CORS origins (optional - defaults are set in code)
CORS_ORIGINS=https://docs-wiki.vercel.app,http://localhost:3000
```

### 3. Deploy

1. Railway will automatically detect your Python application
2. It will install dependencies from `requirements.txt`
3. The deployment will start automatically
4. You'll get a URL like: `https://your-app-name.railway.app`

### 4. Verify Deployment

1. **Health Check**: Visit `https://your-app-name.railway.app/docs` to see the FastAPI docs
2. **API Test**: Test the endpoints:
   - `GET /docs` - API documentation
   - `POST /api/ingest` - Document ingestion
   - `POST /api/chat` - Chat functionality

## Configuration Files

### railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/docs",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Procfile
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Environment Variables Reference

| Variable | Required | Description | Where to Get |
|----------|----------|-------------|--------------|
| `PERPLEXITY_API_KEY` | Yes | Perplexity Sonar API for research | [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) |
| `OPENAI_API_KEY` | Yes | OpenAI API for LLM processing | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | No | Anthropic Claude API (backup) | [console.anthropic.com](https://console.anthropic.com/) |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API for Leo AI | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `PINECONE_API_KEY` | Yes | Pinecone vector database | [app.pinecone.io](https://app.pinecone.io) |
| `PINECONE_ENVIRONMENT` | Yes | Pinecone environment/region | [app.pinecone.io](https://app.pinecone.io) |

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check that all dependencies in `requirements.txt` are valid
   - Ensure Python version compatibility (Railway uses Python 3.11 by default)

2. **Runtime Errors**
   - Check Railway logs in the dashboard
   - Verify all environment variables are set correctly
   - Ensure API keys are valid and have proper permissions

3. **CORS Issues**
   - Update the `origins` list in `main.py` to include your frontend domain
   - Check that your frontend is making requests to the correct Railway URL

4. **Memory Issues**
   - Railway starter plan has 512MB RAM
   - For heavy operations, consider upgrading to a higher plan
   - Monitor memory usage in Railway dashboard

### Logs and Monitoring

- **View Logs**: Go to your Railway project → **Deployments** → Click on latest deployment → **View Logs**
- **Metrics**: Monitor CPU, memory, and network usage in the dashboard
- **Health Checks**: Railway automatically monitors your app health

## Updating Your Deployment

1. **Code Changes**: Push to your GitHub repository
2. **Automatic Deploy**: Railway will automatically redeploy
3. **Environment Variables**: Update in Railway dashboard → Variables
4. **Manual Deploy**: Use Railway CLI or dashboard to trigger manual deployments

## Railway CLI (Optional)

Install Railway CLI for advanced management:

```bash
npm install -g @railway/cli
railway login
railway link  # Link to your project
railway up    # Deploy manually
railway logs  # View logs
```

## Cost Information

- **Starter Plan**: $5/month (512MB RAM, 1GB storage)
- **Developer Plan**: $20/month (2GB RAM, 8GB storage)
- **Team Plan**: $99/month (8GB RAM, 32GB storage)

## Security Notes

- Never commit API keys to your repository
- Use Railway's environment variables for all secrets
- Regularly rotate your API keys
- Monitor usage and costs in Railway dashboard

## Next Steps

1. Deploy your backend to Railway
2. Update your frontend to use the Railway URL
3. Test all functionality end-to-end
4. Set up monitoring and alerts
5. Consider setting up a custom domain (optional)

## Support

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Railway Status**: [status.railway.app](https://status.railway.app)
