# TPRM Tool

A professional Third-Party Risk Management (TPRM) tool with enhanced UI and JSON visualization.

## Features

- Company Screening with interactive visualization
- Individual Screening with structured data presentation
- DART Registry lookup with financial charts and corporate structure visualization
- Enhanced JSON data viewer for all results
- Secure API credential management

## Setup

1. Clone the repository
2. Create a `.env` file with your API credentials (see `.env.example`)
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python simple_run_enhanced.py`

## Deployment on Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use `gunicorn simple_run_enhanced:app` as the start command
4. Add your API keys as environment variables
5. Deploy!

## API Endpoints

- `/api/screen` - Company screening API
- `/api/screen_individual` - Individual screening API
- `/api/dart_lookup` - DART Registry lookup API

## Environment Variables

Required environment variables:
- `DART_API_KEY` - API key for DART Registry
- `GOOGLE_API_KEY` - Google API key for search
- `GOOGLE_CSE_ID` - Google Custom Search Engine ID
- `OPENAI_API_KEY` - OpenAI API key for data extraction

Optional:
- `SERPER_API_KEY` - Serper Google wrapper
- `NEWS_MAX_RESULTS` (default 20)
- `SCRAPE_TIMEOUT_MS` (default 20000)
- `CACHE_TTL_MIN` (default 1440)

## License

© 2025 TPRM Tool. All rights reserved.
