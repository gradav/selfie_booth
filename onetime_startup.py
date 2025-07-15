#!/bin/bash
# quick_deploy.sh - Get production-ready in minutes

echo "🚀 Setting up Selfie Booth for production..."

# 1. Create production environment file
cat > .env.production << EOF
# Production Configuration
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Database (use absolute path for production)
DATABASE_PATH=/app/data/selfie_booth.db

# Messaging Service (choose one)
MESSAGING_SERVICE=local
# MESSAGING_SERVICE=twilio
# MESSAGING_SERVICE=email

# Twilio (if using)
# TWILIO_ACCOUNT_SID=your_account_sid_here
# TWILIO_AUTH_TOKEN=your_auth_token_here  
# TWILIO_FROM_NUMBER=+1234567890

# Email (if using)
# EMAIL_ADDRESS=your-email@gmail.com
# EMAIL_PASSWORD=your-app-password
# EMAIL_SMTP_SERVER=smtp.gmail.com
# EMAIL_SMTP_PORT=587
EOF

# 2. Install production dependencies
echo "📦 Installing production dependencies..."
cat > requirements.txt << EOF
Flask==3.0.0
Werkzeug==3.0.1
python-dotenv==1.0.0
gunicorn==21.2.0
twilio==8.9.1
Pillow==10.1.0
python-magic==0.4.27
EOF

pip3 install -r requirements.txt

# 3. Create production directories
mkdir -p data photos logs backups

# 4. Create production startup script
cat > start_production.sh << EOF
#!/bin/bash
export \$(cat .env.production | xargs)
mkdir -p data photos logs

echo "🗄️ Initializing database..."
python3 -c "
from database import SessionManager
sm = SessionManager('\$DATABASE_PATH')
print('Database initialized successfully')
"

echo "🚀 Starting Selfie Booth..."
echo "📱 Kiosk URL: http://\${HOST}:\${PORT}/"
echo "📱 Mobile URL: http://\${HOST}:\${PORT}/mobile"
echo "⚙️ Admin URL: http://\${HOST}:\${PORT}/admin/config"

gunicorn --bind \${HOST}:\${PORT} --workers 2 --timeout 30 --access-logfile logs/access.log --error-logfile logs/error.log selfie_booth_new:app
EOF

chmod +x start_production.sh

# 5. Create backup script
cat > backup.sh << EOF
#!/bin/bash
BACKUP_DIR="backups/\$(date +%Y%m%d_%H%M%S)"
mkdir -p "\$BACKUP_DIR"

# Backup database
cp data/selfie_booth.db "\$BACKUP_DIR/" 2>/dev/null || echo "No database to backup"

# Backup photos  
cp -r photos "\$BACKUP_DIR/" 2>/dev/null || echo "No photos to backup"

echo "✅ Backup created: \$BACKUP_DIR"
EOF

chmod +x backup.sh

echo "✅ Production setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit .env.production with your messaging service credentials"
echo "2. Run: ./start_production.sh"
echo "3. Test at http://localhost:8000"
echo ""
echo "📋 Optional improvements:"
echo "- Set up reverse proxy (nginx)"
echo "- Configure SSL/TLS certificate"  
echo "- Set up monitoring"