#!/usr/bin/env python3
"""
Script to run the Flask application with proper configuration
"""
import os
import sys
import subprocess

def run_app():
    """Run the Flask application with proper configuration"""
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['PUBLIC_APIS'] = '1'  # Allow public API access for testing
    
    # Check if app.py has duplicate route definitions
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Check for duplicate route definitions
    if content.count("@app.route('/enhanced/company_screening')") > 1:
        print("⚠️ Detected duplicate route definitions, fixing...")
        # Remove duplicate route definitions
        lines = content.split('\n')
        route_found = False
        fixed_lines = []
        skip_block = False
        
        for line in lines:
            if "@app.route('/enhanced/company_screening')" in line:
                if not route_found:
                    route_found = True
                    fixed_lines.append(line)
                else:
                    skip_block = True
                    continue
            elif skip_block:
                if line.strip() == '':
                    skip_block = False
                continue
            else:
                fixed_lines.append(line)
        
        # Write fixed content back to app.py
        with open('app.py', 'w') as f:
            f.write('\n'.join(fixed_lines))
        print("✅ Fixed duplicate route definitions")
    
    # Run the Flask application
    print("🚀 Starting Flask application...")
    subprocess.run(['flask', 'run', '--host=0.0.0.0'])

if __name__ == "__main__":
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found in current directory")
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    run_app()
