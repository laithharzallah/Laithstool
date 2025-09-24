# Environment configuration helper for app.py
import os
from dotenv import load_dotenv
import logging

def configure_environment():
    """Configure environment variables and return config dict"""
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create configuration dictionary
    config = {
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'production'),
        'DEBUG': os.environ.get('FLASK_ENV') == 'development',
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'default-insecure-key'),
        'API_KEYS': {
            'DART': os.environ.get('DART_API_KEY'),
            'DILISENSE': os.environ.get('DILISENSE_API_KEY'),
            'GOOGLE': os.environ.get('GOOGLE_API_KEY'),
            'GOOGLE_CSE_ID': os.environ.get('GOOGLE_CSE_ID'),
            'OPENAI': os.environ.get('OPENAI_API_KEY')
        }
    }
    
    # Log configuration status
    if config['FLASK_ENV'] == 'development':
        logger.info("🌍 Development mode: using .env file")
    else:
        logger.info("🌍 Production mode: using system environment variables")
    
    # Check for critical environment variables
    missing_vars = []
    if not config['API_KEYS']['DART']:
        missing_vars.append('DART_API_KEY')
    if not config['API_KEYS']['DILISENSE']:
        missing_vars.append('DILISENSE_API_KEY')
    if not config['API_KEYS']['GOOGLE']:
        missing_vars.append('GOOGLE_API_KEY')
    if not config['API_KEYS']['GOOGLE_CSE_ID']:
        missing_vars.append('GOOGLE_CSE_ID')
    if not config['API_KEYS']['OPENAI']:
        missing_vars.append('OPENAI_API_KEY')
    
    if missing_vars:
        logger.warning(f"⚠️ WARNING: Missing critical environment variables: {', '.join(missing_vars)}")
        logger.info("📝 Set these in Render Environment Variables or .env file")
    
    # Check for insecure secret key
    if config['SECRET_KEY'] == 'default-insecure-key':
        logger.warning("⚠️ WARNING: Using default SECRET_KEY. Set SECRET_KEY in the environment for production.")
    
    return config

def initialize_services(app, config):
    """Initialize services with API keys"""
    # Initialize OpenAI client if key is available
    if config['API_KEYS']['OPENAI']:
        try:
            from openai import OpenAI
            app.openai_client = OpenAI(api_key=config['API_KEYS']['OPENAI'])
            app.logger.info("✅ OpenAI client initialized")
        except Exception as e:
            app.logger.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
    
    # Initialize Dilisense service if key is available
    if config['API_KEYS']['DILISENSE']:
        try:
            # Import and initialize Dilisense service
            from services.dilisense import DilisenseService
            app.dilisense_service = DilisenseService(config['API_KEYS']['DILISENSE'])
            app.logger.info("✅ Dilisense service initialized")
        except Exception as e:
            app.logger.error(f"❌ Failed to initialize Dilisense service: {str(e)}")
    else:
        app.logger.warning("⚠️ DILISENSE_API_KEY not found - company screening will not work")
        app.logger.info("📝 Add DILISENSE_API_KEY in Render → Environment")
    
    # Initialize DART service if key is available
    if config['API_KEYS']['DART']:
        try:
            # Import and initialize DART service
            from services.dart import DartService
            app.dart_service = DartService(config['API_KEYS']['DART'])
            app.logger.info("✅ DART service initialized")
        except Exception as e:
            app.logger.error(f"❌ Failed to initialize DART service: {str(e)}")
    
    # Initialize Google service if keys are available
    if config['API_KEYS']['GOOGLE'] and config['API_KEYS']['GOOGLE_CSE_ID']:
        try:
            # Import and initialize Google service
            from services.google import GoogleService
            app.google_service = GoogleService(
                config['API_KEYS']['GOOGLE'],
                config['API_KEYS']['GOOGLE_CSE_ID']
            )
            app.logger.info("✅ Google service initialized")
        except Exception as e:
            app.logger.error(f"❌ Failed to initialize Google service: {str(e)}")
    
    return app
