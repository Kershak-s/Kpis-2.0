#!/bin/bash
# Stop application if it's running
if pgrep -f "gunicorn wsgi:app"; then
    echo "Stopping existing application"
    pkill -f "gunicorn wsgi:app"
fi

# Clean up old deployment
if [ -d /var/www/html/kpis ]; then
    echo "Removing old deployment files"
    rm -rf /var/www/html/kpis
fi

# Install system dependencies
echo "Installing system dependencies"
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx