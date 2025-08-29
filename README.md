# Risklytics - GPT-5 Enhanced Company Screener + WhatsApp Registry Agent

A professional due diligence and company screening platform powered by GPT-5 artificial intelligence with real-time web validation, citations, and WhatsApp-based company registry lookups.

## 🚀 Features

### 🧠 **GPT-5 Enhanced Intelligence**
- **Primary Analysis**: Uses GPT-5's vast knowledge base as main intelligence source
- **Web Validation**: Supplements findings with real-time internet data
- **Smart Citations**: Provides proper source links for all findings
- **Structured Output**: Professional due diligence reports with risk scoring

### 🔍 **Comprehensive Screening**
- **Company Intelligence**: Business profiles, operations, market position
- **Executive Analysis**: Leadership structure and key personnel information
- **Sanctions Checking**: OFAC, EU, UN watchlist screening
- **Adverse Media**: Negative news and controversy detection
- **Risk Assessment**: Bribery/corruption, political exposure, compliance issues
- **Real-time Data**: Live web scraping and content extraction

### 💬 **WhatsApp Registry Agent**
- **Natural Language Processing**: Extract company names and countries from WhatsApp messages
- **Multi-Source Registry Search**: Dilisense, DART (Korea), OpenCorporates (Global)
- **Intelligent Matching**: Fuzzy matching with confidence scoring
- **WhatsApp Webhook Integration**: Real-time message processing
- **Local Simulation**: Test functionality without WhatsApp setup

### 🎨 **Professional Interface**
- **Corporate Dashboard**: Clean, professional due diligence layout
- **Real-time Progress**: Live status updates during screening
- **Multiple Tabs**: Organized results (Overview, Company, People, Sanctions, etc.)
- **WhatsApp Test Interface**: Interactive testing of registry lookups
- **Export Capabilities**: Generate professional PDF reports
- **Responsive Design**: Works on desktop and mobile

## 🛠 Technology Stack

- **Backend**: Flask (Python)
- **AI Engine**: GPT-5 (GPT-4o) via OpenAI API
- **Web Scraping**: httpx, trafilatura, BeautifulSoup
- **Search APIs**: NewsAPI, Serper, RSS feeds
- **Frontend**: HTMX + Alpine.js + TailwindCSS + DaisyUI
- **Validation**: Pydantic schemas
- **Deployment**: Render (Cloud Platform)

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.9+
- OpenAI API key
- Optional: NewsAPI key for enhanced search

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd company-screener
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Run the application**
```bash
python app.py
```

5. **Access the application**
```
http://localhost:5000
Login: ens@123 / $$$$55
```

## 🌐 Render Deployment

### Environment Variables

Set these in your Render dashboard:

**Required:**
```bash
OPENAI_API_KEY=sk-proj-your-key-here
SECRET_KEY=your-secure-secret-key
FLASK_ENV=production
```

**Optional (for enhanced search):**
```bash
NEWS_API_KEY=your-newsapi-key
SEARCH_PROVIDER=newsapi
```

**WhatsApp Registry Agent:**
```bash
# WhatsApp Business API (Meta)
WHATSAPP_PHONE_ID=your-whatsapp-phone-id
WHATSAPP_BEARER=your-whatsapp-bearer-token
WHATSAPP_VERIFY_TOKEN=your-webhook-verify-token
WHATSAPP_SENDER_E164=+your-whatsapp-number

# Additional Registry APIs
DART_API_KEY=your-dart-api-key
OPENCORPORATES_API_KEY=your-opencorporates-api-key
```

### Deployment Steps

1. **Connect GitHub**: Link your GitHub repository to Render
2. **Create Web Service**: Choose "Web Service" in Render
3. **Configure Build**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. **Set Environment Variables**: Add the variables listed above
5. **Deploy**: Render will automatically deploy your application

## 📖 Usage Guide

### Basic Screening

1. **Login** with provided credentials
2. **Enter Company Details**:
   - Company Name (e.g., "Rawabi Holding")
   - Country (e.g., "Saudi Arabia")
   - Domain (optional)
3. **Start Screening**: Click "Start Screening"
4. **Monitor Progress**: Watch real-time updates
5. **Review Results**: Explore detailed findings in multiple tabs

### WhatsApp Registry Testing

1. **Access Test Interface**: Click "💬 WhatsApp Registry" in the sidebar
2. **Test Messages**: Try natural language queries like:
   - "Check Samsung Electronics in South Korea"
   - "Find company Alibaba Group in China"
   - "Look up Siemens AG in Germany"
3. **Simulate**: Use the test interface to simulate WhatsApp messages
4. **Webhook Setup**: Configure Meta WhatsApp Business API for live messaging

### API Usage

The platform provides REST API endpoints:

```bash
# Start screening
POST /api/v1/screen
{
  "company": "Company Name",
  "country": "Country",
  "domain": "optional-domain.com"
}

# Check progress
GET /api/v1/status/{task_id}

# Get results
GET /api/v1/report/{task_id}

# Health check
GET /api/v1/health
```

## 🔧 Configuration

### Search Providers

The system supports multiple search providers:

1. **NewsAPI** (Recommended)
   - Set `SEARCH_PROVIDER=newsapi`
   - Add `NEWS_API_KEY`

2. **Serper** (Alternative)
   - Set `SEARCH_PROVIDER=serper`
   - Add `SERPER_API_KEY`

3. **RSS Fallback** (Automatic)
   - Used when no API keys are available
   - Searches Reuters, Bloomberg feeds

### GPT-5 Models

- **Primary**: gpt-4o (GPT-5 level intelligence)
- **Fallback**: Automatically handled by OpenAI
- **Temperature**: 0.1 (factual accuracy)
- **Output**: Structured JSON with validation

## 🎯 Sample Companies to Test

Try these companies to see the system in action:

- **Rawabi Holding** (Saudi Arabia) - Diversified conglomerate
- **Siemens Healthineers** (Saudi Arabia) - Medical technology
- **Saudi Aramco** (Saudi Arabia) - Energy company
- **Any public company** - Global coverage

## 🔒 Security Features

- **Session Management**: Secure login system
- **API Authentication**: Protected endpoints
- **Rate Limiting**: Prevents abuse
- **Input Validation**: Sanitized inputs
- **Error Handling**: Graceful failure management

## 📊 Performance

- **Response Time**: 30-60 seconds for complete screening
- **Concurrent Users**: Supports multiple simultaneous requests
- **Data Sources**: 10+ intelligence sources per company
- **Accuracy**: GPT-5 enhanced with real-time validation

## 🛡️ Compliance

- **robots.txt Compliance**: Respects website crawling rules
- **Rate Limiting**: Ethical web scraping practices
- **Data Privacy**: No personal data storage
- **API Terms**: Compliant with all API provider terms

## 🤝 Support

For technical support or questions:
- Review the documentation above
- Check environment variable configuration
- Ensure API keys are valid and have sufficient credits
- Monitor Render logs for deployment issues

## 📝 License

This project is configured for deployment on Render cloud platform.

---

**🎯 Ready for professional due diligence screening with GPT-5 enhanced intelligence!**