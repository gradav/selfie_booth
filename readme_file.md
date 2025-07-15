# Selfie Booth Application

A web-based selfie booth system with separate kiosk and mobile interfaces. Users register on their mobile devices, verify with a code displayed on the kiosk, then have their photo taken and sent to their phone.

## 🎯 Features

- **Kiosk Display**: Large, attractive interface with QR code and camera
- **Mobile Registration**: Users scan QR code and enter details on their phone
- **Verification System**: 6-digit codes displayed on kiosk screen
- **Photo Capture**: Browser-based camera interface with countdown
- **Multi-Platform Delivery**: Send photos via SMS (Twilio), email, or local storage
- **Security**: Rate limiting, input validation, and file security
- **Responsive Design**: Works on tablets, phones, and kiosk displays

## 🔄 User Workflow

1. **Initial State**: Kiosk displays QR code and instructions
2. **Mobile Registration**: User scans QR code, fills form on phone
3. **Verification**: Kiosk shows 6-digit code, user enters on phone
4. **Photo Session**: Kiosk switches to camera, takes photo automatically
5. **Photo Delivery**: Photo sent to user via configured messaging service

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Basic Setup
```bash
# Run with default settings (local storage)
python selfie_booth_new.py
```

### 3. Access the Application
- **Kiosk Display**: http://localhost:5001/ (connect to monitor/TV)
- **Mobile Registration**: http://localhost:5001/mobile (for QR codes)
- **Admin Panel**: http://localhost:5001/admin/config

## ⚙️ Configuration

### Environment Variables

Set these in your environment or create a `.env` file:

```bash
# Application Settings
DEBUG=False
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your-secret-key-here

# Messaging Service (choose one)
MESSAGING_SERVICE=local  # local, twilio, email

# Twilio (for SMS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Email (for email delivery)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
```

### Production Deployment

```bash
# Create production environment
./onetime_startup.py

# Start production server
./start_production.sh
```

## 📱 Messaging Services

### Local Storage (Default)
Photos saved to `photos/` directory. Perfect for testing.

### Twilio SMS/MMS
Send photos directly to users' phones via text message.
- Requires Twilio account and phone number
- Set `MESSAGING_SERVICE=twilio`

### Email
Send photos via email attachment.
- Works with Gmail (requires app password)
- Set `MESSAGING_SERVICE=email`

## 🔧 Project Structure

```
selfie_booth/
├── selfie_booth_new.py    # Main application entry point
├── config.py              # Configuration and Flask app setup
├── routes.py              # All HTTP routes and handlers
├── database.py            # SQLite database operations
├── messaging.py           # Messaging service implementations
├── templates.py           # HTML templates for all pages
├── security_enhancements.py  # Security features
├── requirements.txt       # Python dependencies
├── onetime_startup.py     # Production setup script
└── photos/               # Photo storage directory
```

## 🛡️ Security Features

- **Rate Limiting**: Prevents spam and abuse
- **Input Validation**: Sanitizes all user inputs
- **File Validation**: Checks uploaded image files
- **Security Headers**: XSS protection, frame denial, etc.
- **Session Management**: Secure session handling
- **Phone Number Validation**: US format validation

## 🎨 Customization

### Styling
All CSS is inline in `templates.py`. Modify the `<style>` sections to customize appearance.

### Messaging
Add new messaging services by extending the `MessagingService` class in `messaging.py`.

### Camera Settings
Modify camera resolution and quality in the JavaScript sections of the templates.

## 🐛 Troubleshooting

### Common Issues

1. **Camera not working**: Ensure HTTPS or localhost for camera access
2. **Photos not sending**: Check messaging service credentials
3. **Database errors**: Ensure write permissions in project directory
4. **Rate limiting**: Wait a minute if you see "Rate limit exceeded"

### Debug Tools

- **Admin Panel**: `/admin/config` - View sessions and statistics
- **Console Logs**: Watch terminal for detailed debug information
- **Session Reset**: Use reset button in admin panel if stuck

## 📋 Requirements

- Python 3.7+
- Modern web browser with camera support
- Network access for messaging services (optional)

## 📄 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

Check the admin panel at `/admin/config` for debugging information and session status.