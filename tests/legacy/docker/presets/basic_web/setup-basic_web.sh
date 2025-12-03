#!/bin/bash
# Setup script for basic_web preset

echo "Setting up basic_web preset..."

# Install web server and Python packages
apt-get update
apt-get install -y nginx apache2

# Install Python packages
pip install flask gunicorn

# Create example Flask application
mkdir -p /var/www/flask_app
cat > /var/www/flask_app/app.py << 'EOF'
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Flask!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

# Create systemd service
cat > /etc/systemd/system/flask_app.service << 'EOF'
[Unit]
Description=Flask Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/flask_app
Environment="PATH=/var/www/flask_app/venv/bin"
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
cat > /etc/nginx/sites-available/flask_app << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable Nginx configuration
ln -sf /etc/nginx/sites-available/flask_app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Start services
systemctl enable flask_app
systemctl start flask_app
systemctl restart nginx

echo "Basic web preset setup completed!" 