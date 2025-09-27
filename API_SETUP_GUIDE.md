# TPRM Tool - API Setup Guide

## Overview
The TPRM Tool works with both **demo data** (for testing) and **real APIs** (for production use). The application automatically detects available API keys and switches between modes.

## Current Status
- ✅ **Demo Mode Active** - All features work with realistic sample data
- ⚠️ **Real APIs** - Configure API keys below to access live data

## Required API Keys

### 1. OpenAI API Key (Required for AI Analysis)
```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```
- **Purpose**: AI-powered data extraction and analysis
- **Get it**: https://platform.openai.com/api-keys
- **Cost**: Pay-per-use, typically $0.01-0.03 per screening
- **Required for**: Company analysis, adverse media detection, executive identification

### 2. DART API Key (Required for Korean Companies)
```bash
DART_API_KEY=your-dart-api-key-here
```
- **Purpose**: Official Korean Financial Supervisory Service company registry
- **Get it**: https://opendart.fss.or.kr/
- **Cost**: Free with registration
- **Required for**: Korean company financial data, corporate structure, regulatory filings

### 3. Google Custom Search API (Required for Web Search)
```bash
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_CSE_ID=your-custom-search-engine-id-here
```
- **Purpose**: Real-time web search for company information
- **Get it**: https://developers.google.com/custom-search/v1/introduction
- **Cost**: Free tier: 100 searches/day, Paid: $5 per 1000 queries
- **Required for**: Real-time company information, executive data, adverse media

### 4. Dilisense API Key (Required for Sanctions/PEP Screening)
```bash
DILISENSE_API_KEY=your-dilisense-api-key-here
```
- **Purpose**: Professional sanctions, PEP, and adverse media screening
- **Get it**: Contact Dilisense for enterprise access
- **Cost**: Enterprise pricing
- **Required for**: Individual PEP screening, sanctions checking, compliance data

### 5. Serper API Key (Optional - Alternative to Google CSE)
```bash
SERPER_API_KEY=your-serper-api-key-here
```
- **Purpose**: Alternative Google search API with better rate limits
- **Get it**: https://serper.dev/
- **Cost**: $5 per 1000 searches
- **Required for**: Enhanced search capabilities (optional)

## Configuration Methods

### Method 1: Environment Variables (Recommended for Production)
Set these in your hosting platform (Render, Heroku, etc.):
```bash
OPENAI_API_KEY=sk-your-key...
DART_API_KEY=your-key...
GOOGLE_API_KEY=your-key...
GOOGLE_CSE_ID=your-id...
DILISENSE_API_KEY=your-key...
```

### Method 2: .env File (Development)
Create a `.env` file in the project root:
```bash
# Copy .env.example to .env and fill in your keys
cp .env.example .env
# Edit .env with your actual API keys
```

### Method 3: Toggle Demo Mode
To force demo mode even with API keys configured:
```bash
USE_DEMO_DATA=1
```

## API Key Verification

The application provides real-time API key status:

1. **Dashboard**: Shows API configuration status
2. **Debug Endpoint**: Visit `/debug/providers` for detailed status
3. **Banner**: Yellow banner appears when in demo mode

## Data Quality Comparison

| Feature | Demo Mode | Real APIs |
|---------|-----------|-----------|
| Company Info | ✅ Realistic samples | ✅ Live web data |
| Executive Data | ✅ Sample executives | ✅ Real leadership info |
| Adverse Media | ✅ Sample incidents | ✅ Real-time news scan |
| DART Registry | ✅ Korean company samples | ✅ Official FSS data |
| PEP Screening | ✅ Sample PEP data | ✅ Live sanctions/PEP lists |
| Response Time | ⚡ Instant | 🕐 2-5 seconds |
| Data Freshness | 📅 Static samples | 🔄 Real-time updates |

## Troubleshooting

### Common Issues

1. **"No data" error**
   - Check if API keys are correctly set
   - Verify `.env` file exists and is readable
   - Check application logs for specific errors

2. **DART search returns empty**
   - DART only contains Korean companies
   - Try searching for "Samsung", "LG", "SK Hynix"
   - Check DART API key configuration

3. **Individual screening shows "Low" for everyone**
   - Dilisense API key may be missing
   - Try known PEP names in demo mode
   - Check API rate limits

### Enable Debug Logging
```bash
FLASK_ENV=development
```

### Test API Keys
Use the `/debug/providers` endpoint to verify which APIs are configured.

## Production Deployment

### Render.com
1. Connect your GitHub repository
2. Add environment variables in Render dashboard
3. Use start command: `gunicorn app:app`

### Other Platforms
1. Set all required environment variables
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python app.py` or `gunicorn app:app`

## Cost Estimation (Monthly)

For **100 screenings/month**:
- OpenAI API: ~$3-10
- Google CSE: ~$5-15  
- DART API: Free
- Dilisense: Enterprise pricing
- **Total**: ~$8-25/month + Dilisense

## Support

- 📧 For API issues: Check individual provider documentation
- 🐛 For application bugs: Check application logs
- 💡 For feature requests: The application is fully customizable

---

**Ready to go live?** Configure your API keys and the application will automatically switch to real data mode!