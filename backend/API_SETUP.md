# API Integration Setup Guide

This guide explains how to set up the API integrations for the Leo Learning Platform.

## Required API Keys

### 1. Perplexity Sonar API
- **Purpose**: Research agent for getting key concepts related to learning topics
- **Get API Key**: https://www.perplexity.ai/settings/api
- **Model Used**: `sonar`
- **Rate Limits**: Check Perplexity documentation for current limits

### 2. OpenAI API
- **Purpose**: Generate concept explanations and learning suggestions
- **Get API Key**: https://platform.openai.com/api-keys
- **Model Used**: `gpt-3.5-turbo`
- **Rate Limits**: Varies by tier, check OpenAI documentation

### 3. Anthropic API (Optional)
- **Purpose**: Fallback LLM service if OpenAI is unavailable
- **Get API Key**: https://console.anthropic.com/
- **Model Used**: `claude-3-haiku-20240307`
- **Rate Limits**: Check Anthropic documentation

## Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration
1. Copy `env_example.txt` to `.env`:
   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` and add your API keys:
   ```env
   PERPLEXITY_API_KEY=your_actual_perplexity_key
   OPENAI_API_KEY=your_actual_openai_key
   ANTHROPIC_API_KEY=your_actual_anthropic_key
   ```

### 3. Test the Integration
Start the backend server:
```bash
python main.py
```

The system will automatically:
- Use Perplexity Sonar for research when API key is available
- Fall back to mock data if Perplexity API is unavailable
- Use OpenAI for LLM processing when API key is available
- Fall back to Anthropic if OpenAI is unavailable
- Use mock responses if no LLM APIs are available

## API Usage Flow

### 1. Research Phase (Perplexity Sonar)
```
User Input: Topic + Prompt
↓
Perplexity Sonar API Call
↓
Key Concepts (6-8 concepts)
```

### 2. Explanation Phase (OpenAI/Anthropic)
```
Key Concepts
↓
LLM API Call for each concept
↓
Concept Explanations
```

### 3. Suggestions Phase (OpenAI/Anthropic)
```
Concept Explanations + Topic + Prompt
↓
LLM API Call
↓
Personalized Learning Suggestions
```

## Error Handling

The system includes comprehensive error handling:

- **API Key Missing**: Falls back to mock data with warning logs
- **API Rate Limits**: Logs error and uses fallback
- **Network Errors**: Logs error and uses fallback
- **Invalid Responses**: Parses what it can, fills gaps with mock data

## Cost Considerations

### Perplexity Sonar
- Pay-per-request model
- Estimated cost: $0.01-0.05 per learning path generation

### OpenAI GPT-3.5-turbo
- Pay-per-token model
- Estimated cost: $0.01-0.03 per learning path generation

### Anthropic Claude Haiku
- Pay-per-token model (cheaper than GPT-3.5)
- Estimated cost: $0.005-0.015 per learning path generation

## Monitoring and Logging

All API calls are logged with:
- Request details
- Response status
- Error messages
- Fallback usage

Check logs for:
- API key validation
- Rate limit warnings
- Fallback usage patterns
- Cost optimization opportunities

## Troubleshooting

### Common Issues

1. **"API key not found" warnings**
   - Check `.env` file exists and has correct variable names
   - Ensure no extra spaces in API keys
   - Restart the server after adding keys

2. **Rate limit errors**
   - Check your API usage limits
   - Consider upgrading your API plan
   - Implement request queuing if needed

3. **Network timeouts**
   - Check internet connection
   - Verify API endpoints are accessible
   - Consider increasing timeout values

### Debug Mode
Set logging level to DEBUG for detailed API call information:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Notes

- Never commit `.env` files to version control
- Use environment variables in production
- Rotate API keys regularly
- Monitor API usage for unusual patterns
- Consider IP whitelisting for production APIs
