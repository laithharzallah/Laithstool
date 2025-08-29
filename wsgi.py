# Entry point for Gunicorn
print("🚀 Initializing Flask application...")

try:
    from app import app
    application = app
    print("✅ Flask app loaded successfully in wsgi.py")

except Exception as e:
    print(f"❌ Failed to load Flask app in wsgi.py: {e}")
    import traceback
    traceback.print_exc()
    raise

if __name__ == "__main__":
    print("🚀 Starting Flask app in development mode...")
    application.run()
