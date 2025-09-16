# Vercel Serverless Functions Deployment Guide

This guide will help you deploy your FastAPI backend to Vercel serverless functions.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install globally with `npm i -g vercel`
3. **Environment Variables**: Set up your API keys

## Project Structure

```
docs-wiki/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ingest.py          # /api/ingest endpoint
│   │   ├── chat.py            # /api/chat endpoint
│   │   ├── performance.py     # /api/performance endpoint
│   │   └── cache_clear.py     # /api/cache/clear endpoint
│   ├── requirements.txt
│   └── [other backend files...]
├── vercel.json
└── [other project files...]
```

## Environment Variables

Set these in your Vercel dashboard or via CLI:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
PERPLEXITY_API_KEY=your_perplexity_key
OPENROUTER_API_KEY=your_openrouter_key

# Pinecone (for vector storage)
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_pinecone_environment

# Optional
LEO_API_KEY=your_leo_key
```

## Deployment Steps

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy from Project Root
```bash
cd C:\Users\3d3n2\docs-wiki
vercel
```

### 4. Set Environment Variables
```bash
# Set each environment variable
vercel env add OPENAI_API_KEY
vercel env add ANTHROPIC_API_KEY
vercel env add PERPLEXITY_API_KEY
vercel env add OPENROUTER_API_KEY
vercel env add PINECONE_API_KEY
vercel env add PINECONE_ENVIRONMENT
```

### 5. Redeploy with Environment Variables
```bash
vercel --prod
```

## API Endpoints

After deployment, your API will be available at:
- `https://your-project.vercel.app/api/ingest` - Document ingestion
- `https://your-project.vercel.app/api/chat` - Chat functionality
- `https://your-project.vercel.app/api/performance` - Performance stats
- `https://your-project.vercel.app/api/cache/clear` - Cache management

## Configuration Details

### vercel.json
- **Builds**: Uses `@vercel/python` for Python functions
- **Routes**: Maps API endpoints to individual Python files
- **Functions**: Sets 30-second timeout for all functions
- **Environment**: Sets `PYTHONPATH` to include backend directory

### Function Structure
Each API endpoint is a separate Python file with:
- FastAPI app instance
- Individual route handlers
- Mangum adapter for AWS Lambda compatibility
- Proper error handling and logging

## Testing Your Deployment

### 1. Test Ingest Endpoint
```bash
curl -X POST "https://your-project.vercel.app/api/ingest" \
  -F "topic=Python Programming" \
  -F "prompt=Learn the basics of Python"
```

### 2. Test Chat Endpoint
```bash
curl -X POST "https://your-project.vercel.app/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "model": "google/gemma-2-9b-it",
    "use_rag": false,
    "use_web_search": false
  }'
```

### 3. Test Performance Endpoint
```bash
curl "https://your-project.vercel.app/api/performance"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are in `requirements.txt`
2. **Timeout Issues**: Check function timeout settings in `vercel.json`
3. **Environment Variables**: Verify all required env vars are set
4. **Cold Starts**: First request may be slow due to cold start

### Debugging

1. **Check Logs**: Use `vercel logs` to view function logs
2. **Local Testing**: Test locally with `vercel dev`
3. **Function Status**: Check function status in Vercel dashboard

### Performance Optimization

1. **Keep Functions Warm**: Use cron jobs to ping endpoints
2. **Optimize Dependencies**: Remove unused packages
3. **Use Caching**: Implement response caching where possible
4. **Monitor Usage**: Track function execution times and memory usage

## Cost Considerations

- **Free Tier**: 100GB-hours per month
- **Pro Tier**: $20/month for additional resources
- **Function Timeout**: 30 seconds max (can be increased with Pro)
- **Memory**: 1024MB default (can be increased with Pro)

## Next Steps

1. **Monitor Performance**: Use Vercel Analytics
2. **Set up Alerts**: Configure error notifications
3. **Optimize**: Monitor and optimize function performance
4. **Scale**: Upgrade to Pro plan if needed

## Support

- [Vercel Documentation](https://vercel.com/docs)
- [Python Runtime Documentation](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Mangum Documentation](https://mangum.io/)
