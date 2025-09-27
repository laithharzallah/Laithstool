# TPRM Tool - Professional Risk Management Platform

A comprehensive Third-Party Risk Management (TPRM) platform with AI-powered screening, real-time data integration, and professional analytics dashboard.

## 🚀 Features

### Core Screening Capabilities
- **Company Screening** - Comprehensive risk assessment with real-time web data
- **Individual Screening** - PEP, sanctions, and adverse media screening  
- **DART Registry** - Official Korean Financial Supervisory Service integration
- **Real-time Analytics** - Interactive dashboards and reporting

### Professional UI/UX
- **Modern Design** - Professional dark theme with responsive layout
- **Interactive Charts** - Financial trends, risk distribution, activity monitoring
- **Advanced JSON Viewer** - Collapsible, searchable data visualization
- **Export Capabilities** - JSON, CSV, and report generation
- **Mobile Optimized** - Full responsive design for all devices

### Intelligent Data Integration
- **Dual Mode Operation** - Demo data for testing, real APIs for production
- **Auto-Fallback** - Graceful degradation when APIs are unavailable
- **Real-time Status** - Live API health monitoring and configuration status
- **Smart Caching** - Optimized performance with intelligent data caching

## 🏃‍♂️ Quick Start

### Option 1: Demo Mode (Instant Setup)
```bash
# Clone and run immediately with demo data
git clone <repository>
cd tprm-tool
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Visit `http://localhost:5000` - **All features work immediately with realistic demo data!**

### Option 2: Production Mode (Real APIs)
1. Get API keys (see [API Setup Guide](API_SETUP_GUIDE.md))
2. Configure environment variables
3. Run the application

## 🔧 API Configuration

The application supports both **demo mode** (realistic sample data) and **real API mode** (live data).

### Demo Mode (Default)
- ✅ **Instant setup** - No API keys required
- ✅ **Realistic data** - Professional sample companies and individuals
- ✅ **Full functionality** - All features work immediately
- ✅ **Perfect for testing** - Demonstrate capabilities without external dependencies

### Real API Mode
Configure these environment variables for live data:

```bash
# Core APIs (Required for real data)
OPENAI_API_KEY=sk-your-openai-key-here
DART_API_KEY=your-dart-key-here  
GOOGLE_API_KEY=your-google-key-here
GOOGLE_CSE_ID=your-cse-id-here

# Optional APIs (Enhanced features)
DILISENSE_API_KEY=your-dilisense-key-here
SERPER_API_KEY=your-serper-key-here

# Control flags
USE_DEMO_DATA=0  # Set to 1 to force demo mode
ENHANCED_SCREENING=1
```

## 🌐 API Endpoints

### Company Screening
```bash
POST /api/screen
{
  "company": "Samsung Electronics",
  "country": "South Korea",
  "domain": "samsung.com",
  "level": "enhanced"
}
```

### Individual Screening  
```bash
POST /api/screen_individual
{
  "name": "John Smith",
  "country": "United Kingdom", 
  "date_of_birth": "1975-03-15"
}
```

### DART Registry Search
```bash
POST /api/dart/search
{
  "company": "Samsung"
}
```

### DART Registry Lookup
```bash
POST /api/dart_lookup
{
  "company": "Samsung Electronics",
  "registry_id": "00126380"
}
```

### System Status
```bash
GET /debug/providers
```

## 🎯 Application Pages

1. **Dashboard** (`/`) - Overview with KPIs, recent activity, and quick actions
2. **Company Screening** (`/enhanced/company_screening`) - Full company risk assessment
3. **Individual Screening** (`/enhanced/individual_screening`) - PEP and sanctions screening
4. **DART Registry** (`/enhanced/dart_registry`) - Korean company registry with financials
5. **Reports & Analytics** (`/reports`) - Historical data and trend analysis
6. **API Configuration** (`/api-config`) - Setup guide and testing tools

## 🚀 Deployment

### Render.com (Recommended)
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use start command: `gunicorn app:app`
4. Add environment variables in Render dashboard
5. Deploy!

### Other Platforms
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn (production)
gunicorn app:app --bind 0.0.0.0:$PORT

# Run with Flask (development)
python app.py
```

## 💡 Key Benefits

### For Developers
- **Zero Setup Time** - Works immediately with demo data
- **Professional UI** - Enterprise-grade interface out of the box
- **Real API Integration** - Production-ready with proper error handling
- **Comprehensive Documentation** - Clear setup guides and API documentation

### For Business Users
- **Immediate Value** - Test all features without any configuration
- **Professional Results** - High-quality risk assessments and reports
- **Scalable Solution** - Grows from demo to enterprise usage
- **Compliance Ready** - Proper audit trails and data export

## 📊 Data Sources

### Real Mode APIs
- **OpenAI GPT-4** - AI-powered data extraction and analysis
- **DART Registry** - Official Korean Financial Supervisory Service
- **Google Custom Search** - Real-time web intelligence
- **Dilisense** - Professional sanctions and PEP databases
- **Serper** - Enhanced Google search capabilities

### Demo Mode Data
- **Realistic Companies** - Samsung, SK Hynix, Acme Corp, Global Trade Inc
- **Sample Individuals** - Various PEP statuses and risk levels
- **Korean Registry** - Realistic DART-style data for Korean companies
- **Financial Data** - Multi-year financial trends and corporate structure

## 🔒 Security & Compliance

- **API Key Security** - Never logged or exposed in responses
- **Data Privacy** - No persistent storage of screening results
- **Audit Trails** - Complete request/response logging
- **Error Handling** - Graceful degradation and user feedback

## 📈 Performance

- **Response Times** - 2-5 seconds for real APIs, instant for demo data
- **Concurrent Requests** - Supports multiple simultaneous screenings
- **Smart Caching** - Optimized API usage and cost management
- **Rate Limiting** - Built-in protection against API limits

## 🆘 Support

- **Setup Issues**: See [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md)
- **API Problems**: Check `/debug/providers` for status
- **Demo vs Real**: Use `/api-config` page for testing
- **Error Logs**: Check application console output

---

**🎉 Ready to use!** The application works immediately with demo data. Configure API keys when ready for production use.
