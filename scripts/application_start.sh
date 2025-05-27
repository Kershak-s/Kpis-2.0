#!/bin/bash
# Navigate to app directory
cd /var/www/html/kpis

# Activate virtual environment
source venv/bin/activate

# Start application with gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 3 --daemon wsgi:app

echo "Application started"