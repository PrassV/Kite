#!/usr/bin/env python3
"""
Trading Analysis Platform - Production Startup Script
"""

import os
import sys
from app.main import app

if __name__ == '__main__':
    # Set environment for production
    if len(sys.argv) > 1 and sys.argv[1] == 'prod':
        os.environ['FLASK_ENV'] = 'production'
        print("🚀 Starting Trading Platform in PRODUCTION mode...")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        os.environ['FLASK_ENV'] = 'development'
        print("🔧 Starting Trading Platform in DEVELOPMENT mode...")
        app.run(host='127.0.0.1', port=5003, debug=True)