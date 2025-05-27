#!/bin/bash
# Stop application
if pgrep -f "gunicorn wsgi:app"; then
    echo "Stopping application"
    pkill -f "gunicorn wsgi:app"
fi

echo "Application stopped"