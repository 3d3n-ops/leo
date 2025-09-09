# Render Deployment Guide for Docs-Wiki Backend

This guide will help you deploy the Docs-Wiki backend to Render.

## Prerequisites

1. A Render account (sign up at https://render.com)
2. Your backend code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. All required API keys ready

## Required Environment Variables

Before deploying, make sure you have the following API keys:

- `PERPLEXITY_API_KEY` - Get from https://www.perplexity.ai/settings/api
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/ (optional)
- `OPENROUTER_API_KEY` - Get from https://openrouter.ai/keys
- `PINECONE_API_KEY` - Get from https://app.pinecone.io/
- `PINECONE_ENVIRONMENT` - Your Pinecone environment (e.g., "us-east-1-aws")

## Deployment Steps

### Method 1: Using render.yaml (Recommended)

1. **Push your code to Git repository**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Connect to Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your Git repository
   - Select your repository and branch

3. **Configure the service**
   - **Name**: `docs-wiki-backend`
   - **Environment**: `Python 3`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Build Command**: Leave empty (render.yaml will handle this)
   - **Start Command**: Leave empty (render.yaml will handle this)

4. **Add Environment Variables**
   - Go to the "Environment" tab
   - Add all the required environment variables listed above
   - Set `BACKEND_URL` to your Render service URL (will be provided after deployment)

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Method 2: Manual Configuration

If you prefer not to use render.yaml:

1. **Connect to Render** (same as above)

2. **Configure the service manually**:
   - **Name**: `docs-wiki-backend`
   - **Environment**: `Python 3`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Build Command**:
     ```bash
     pip install --upgrade pip
     pip install -r requirements.txt
     playwright install --with-deps
     ```
   - **Start Command**:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

3. **Add Environment Variables** (same as above)

4. **Deploy** (same as above)

## Post-Deployment Configuration

1. **Update Frontend CORS Settings**
   - Once deployed, update your frontend to use the new backend URL
   - The backend URL will be: `https://docs-wiki-backend.onrender.com`

2. **Test the Deployment**
   - Visit `https://docs-wiki-backend.onrender.com/api/performance`
   - This should return performance statistics if everything is working

3. **Update Environment Variables**
   - Update `BACKEND_URL` in your environment variables to the actual deployed URL

## Troubleshooting

### Common Issues

1. **Playwright Installation Fails**
   - The build command includes `playwright install --with-deps`
   - If it fails, try adding `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` as an environment variable

2. **Memory Issues**
   - Render's free tier has limited memory
   - Consider upgrading to a paid plan if you experience memory issues

3. **Build Timeout**
   - Playwright installation can take time
   - If build times out, try the manual configuration method

4. **CORS Issues**
   - Make sure your frontend domain is added to the CORS origins in `main.py`

### Logs and Debugging

- Check the "Logs" tab in your Render dashboard for detailed error messages
- The application logs will show any startup or runtime errors

## Performance Optimization

1. **Caching**: The application includes cache management for better performance
2. **Parallel Processing**: Multiple operations run in parallel for faster response times
3. **Health Check**: The `/api/performance` endpoint provides health monitoring

## Scaling

- Start with the free tier for testing
- Upgrade to a paid plan for production use
- Consider using Render's auto-scaling features for high traffic

## Security Notes

- Never commit API keys to your repository
- Use Render's environment variables for all sensitive data
- Regularly rotate your API keys
- Monitor your usage and costs

## Support

- Render Documentation: https://render.com/docs
- Render Support: https://render.com/support
- Check the logs in your Render dashboard for specific error messages
