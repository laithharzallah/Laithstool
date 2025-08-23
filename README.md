# 🔍 Company Screener - AI-Powered Due Diligence Tool

An advanced company intelligence platform that combines real-time web search with GPT-4 analysis to provide comprehensive due diligence reports. The system automatically searches the internet, gathers company information from multiple sources, and delivers intelligent analysis.

## ✨ Features

### 🌐 Real-time Web Intelligence
- **Live Internet Search**: Automatically searches Google for company information
- **News Monitoring**: Real-time adverse media detection from global news sources
- **Website Discovery**: Finds and analyzes official company websites
- **Executive Identification**: Locates key leadership and executive information

### 🤖 AI-Powered Analysis
- **GPT-4 Integration**: Advanced natural language processing for data analysis
- **Risk Assessment**: Intelligent risk scoring based on gathered information
- **Contextual Insights**: Meaningful interpretation of raw data
- **Structured Reports**: Clean, professional reporting format

### 📊 Multi-Source Data Aggregation
- **Google Search API** via Serper
- **News API** for adverse media monitoring
- **Financial APIs** (Alpha Vantage, Finnhub) for company financials
- **Web Scraping** for additional data enrichment

### 🎨 Modern UI/UX
- **Responsive Design**: Works perfectly on desktop and mobile
- **Real-time Updates**: Live progress indicators during searches
- **Interactive Results**: Hover effects and smooth animations
- **Clean Interface**: Professional, modern design

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- API keys for external services (see Configuration section)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd company-screener
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Run the application**
```bash
python app.py
```

5. **Open your browser**
Navigate to `http://localhost:5000`

## ⚙️ Configuration

### Required API Keys

Create a `.env` file with the following configuration:

```env
# OpenAI API Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Web Search APIs (Required for full functionality)
SERPER_API_KEY=your_serper_api_key_here
NEWS_API_KEY=your_newsapi_key_here

# Financial Data APIs (Optional)
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here
FINNHUB_KEY=your_finnhub_key_here

# Server Configuration
HOST=0.0.0.0
PORT=5000
```

### API Key Setup

1. **OpenAI API**: Get your key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Serper API**: Register at [Serper.dev](https://serper.dev) for Google Search access
3. **News API**: Sign up at [NewsAPI.org](https://newsapi.org) for news monitoring
4. **Alpha Vantage**: Get free key at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
5. **Finnhub**: Register at [Finnhub.io](https://finnhub.io) for financial data

## 📱 Usage

### Basic Company Search
1. Enter company name (e.g., "Apple Inc.", "Tesla")
2. Optionally specify country for localized results
3. Choose screening level (Basic or Advanced)
4. Click "Start AI-Powered Web Search & Analysis"

### Screening Levels

- **Basic Screening**: Website, key executives, major issues
- **Advanced Screening**: Comprehensive analysis including:
  - Detailed risk assessment
  - Financial highlights
  - Adverse media analysis
  - Executive backgrounds
  - Market intelligence

### Report Sections

Each report includes:
- **Company Website**: Official site and status
- **Key Executives**: Leadership team and backgrounds
- **Adverse Media**: Recent negative news and risk factors
- **Financial Highlights**: Revenue, employees, market data
- **Risk Assessment**: Overall risk level and recommendations

## 🛠️ Technical Architecture

### Backend Components
- **Flask Application**: Main web server and API
- **Integration Layer**: Handles external API communications
- **Data Processing**: Combines and analyzes multiple data sources
- **AI Analysis**: GPT-4 powered intelligent interpretation

### Frontend Features
- **Modern CSS**: Gradient backgrounds, animations, hover effects
- **Responsive Design**: Mobile-first approach
- **Real-time Updates**: Progress indicators and status updates
- **Interactive Elements**: Smooth transitions and feedback

### Data Sources
- **Google Search** (via Serper API)
- **Global News** (via News API)
- **Financial Markets** (via Alpha Vantage, Finnhub)
- **Web Scraping** (BeautifulSoup, Selenium)
- **AI Analysis** (OpenAI GPT-4)

## 🔧 Development

### Project Structure
```
company-screener/
├── app.py                 # Main Flask application
├── integrations.py        # External API integrations
├── templates/
│   └── index.html        # Frontend interface
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration template
└── README.md             # Documentation
```

### Adding New Data Sources

1. **Create integration function** in `integrations.py`
2. **Update data processing** in `app.py`
3. **Modify frontend display** in `templates/index.html`
4. **Add configuration** to `.env.example`

### Customizing Analysis

The AI analysis prompts can be customized in `app.py`:
- Modify `create_enhanced_prompt()` function
- Adjust `SYSTEM_PROMPT` for different analysis styles
- Update response schemas in Pydantic models

## 🚦 API Endpoints

### POST /api/screen
Screen a company and return comprehensive analysis.

**Request Body:**
```json
{
  "company_name": "Apple Inc.",
  "country": "USA",
  "screening_level": "advanced"
}
```

**Response:**
```json
{
  "company_name": "Apple Inc.",
  "country": "USA",
  "screening_level": "advanced",
  "timestamp": "2024-01-15 14:30:25 UTC",
  "website_info": {...},
  "executives": [...],
  "adverse_media": [...],
  "financial_highlights": {...},
  "risk_assessment": {...},
  "data_sources": ["Real-time web search", "GPT Analysis", "Google Search", "News API"]
}
```

## 📊 Performance & Limitations

### Performance
- **Search Time**: 20-40 seconds for comprehensive analysis
- **Rate Limits**: Respects API rate limits with built-in delays
- **Caching**: Consider implementing caching for production use

### Limitations
- **API Dependencies**: Requires multiple external API keys
- **Rate Limits**: Subject to third-party API limitations
- **Data Accuracy**: Dependent on source data quality
- **Real-time Nature**: Information reflects current web availability

## 🔒 Security & Privacy

- **No Data Storage**: Company data is not permanently stored
- **API Key Security**: Environment variables for sensitive information
- **HTTPS Ready**: Configure SSL for production deployment
- **Input Validation**: Sanitized inputs and error handling

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
```bash
# Using Gunicorn
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 app:app

# Using Docker
docker build -t company-screener .
docker run -p 5000:5000 --env-file .env company-screener
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support, questions, or feature requests:
- Create an issue on GitHub
- Check the documentation
- Review API provider documentation for API-related issues

---

**Built with ❤️ using Flask, OpenAI GPT-4, and modern web technologies**