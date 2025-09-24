"""
Configuration file to enable public API access for testing
"""

import os

# Set environment variable to allow public API access
os.environ['PUBLIC_APIS'] = '1'

print("✅ Public API access enabled for testing")
