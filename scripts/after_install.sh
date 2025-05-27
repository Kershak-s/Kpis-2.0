#!/bin/bash
# Navigate to app directory
cd /var/www/html/kpis

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Set up database (if it doesn't exist)
if [ ! -f "users.db" ]; then
    echo "Setting up database"
    FLASK_APP=app.py flask shell -c "from app import db; db.create_all()"
fi

# Set proper permissions
chown -R www-data:www-data /var/www/html/kpis

# Set up Nginx configuration
cat > /etc/nginx/sites-available/kpis << 'EOL'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOL

# Enable site
ln -sf /etc/nginx/sites-available/kpis /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Reload Nginx
systemctl reload nginx