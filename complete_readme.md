# 📸 Selfie Booth Application

A complete kiosk-style photo booth system with separate mobile and kiosk interfaces, built with Python Flask backend and static HTML/JavaScript frontend.

## 🎯 Overview

Users scan a QR code on their mobile device to register, verify with a code displayed on the kiosk, take their photo at the kiosk, and receive it on their mobile device for sharing.

## 🔄 Complete User Workflow

1. **Kiosk Display** - Shows QR code and instructions
2. **Mobile Registration** - User scans QR code, fills form on phone
3. **Verification** - Kiosk displays 6-digit code, user enters on phone
4. **Photo Session** - Automatic camera countdown and photo capture on kiosk
5. **Photo Review** - User reviews photo on mobile device
6. **Photo Sharing** - Keep/discard options and social media sharing

## 🏗️ Architecture

### **Backend (Python Flask)**
- **`api/app.py`** - Main Flask application with security system
- **`api/config_api.py`** - Configuration management
- **`api/database_api.py`** - Database abstraction (SQLite/MySQL)
- **`api/messaging_api.py`** - Photo delivery services (Twilio/Email/Local)
- **`api/passenger_wsgi.py`** - InMotion hosting WSGI entry point

### **Frontend (Static HTML/JS)**
- **`index.html`** - Kiosk display interface
- **`mobile.html`** - Mobile registration form
- **`verify-new.html`** - Mobile verification page
- **`photo-review.html`** - Mobile photo review interface
- **`admin.html`** - Admin dashboard

### **Styling**
- **`assets/css/kiosk.css`** - Kiosk interface styles
- **`assets/css/admin.css`** - Admin dashboard styles
- **`assets/js/admin.js`** - Admin dashboard functionality

## 🔐 Security System (IMPLEMENTED)

### **Authentication Levels**
- **Admin Login** (`/admin/login`) - Full dashboard access, 2-hour sessions
- **Kiosk Login** (`/kiosk/login`) - Persistent kiosk access until logout
- **API Protection** - Endpoints require appropriate authentication

### **Environment Variables Required**
```bash
ADMIN_PASSWORD=your_strong_admin_password
KIOSK_USERNAME=kiosk_username
KIOSK_PASSWORD=your_strong_kiosk_password
SECRET_KEY=your_random_64_character_secret_key
```

### **Protected Routes**
- `/admin` - Admin dashboard (requires admin auth)
- `/kiosk/display` - Kiosk interface (requires kiosk auth)
- `/api/admin/*` - Admin endpoints (admin only)
- `/api/register` - Registration (kiosk or admin auth)

## 📱 Mobile Experience Improvements (IMPLEMENTED)

### **Enhanced Registration Flow**
- **Kiosk status validation** - Verifies kiosk is active before registration
- **Better error messages** - Specific feedback for different error types
- **Input validation** - Phone number format checking, required field validation
- **Visual status feedback** - Color-coded status messages

### **Improved Verification**
- **Real-time countdown timer** - Shows exact time remaining (2:00 → 1:59...)
- **Auto-submit** - Automatically submits when 6 digits entered
- **Attempt limiting** - Redirects after 5 failed attempts
- **Paste support** - Handles pasted verification codes
- **Visual feedback** - Input field styling changes on errors

### **Enhanced Photo Review**
- **Robust photo detection** - localStorage first, API fallback
- **Debug information** - Troubleshooting panel (localhost only)
- **Better error handling** - Specific timeout and connection error messages
- **Status updates** - Progress indicators during photo waiting

## ⚡ Performance Optimizations (PLANNED)

### **High Priority**
- **Polling backoff** - Exponential backoff for session monitoring (reduce server load 30%)
- **Client-side caching** - Cache QR codes, session data, API responses
- **Batch operations** - Queue file operations, batch write every 5 seconds
- **Response compression** - Automatic gzip compression

### **Medium Priority**
- **Database optimization** - Connection pooling, query optimization
- **Static file optimization** - Minify CSS/JS, compress images
- **Rate limiting** - Simple IP-based request limiting

## 🚀 Future Features (ROADMAP)

### **Photo Compression (EASY - 1-2 hours)**
```javascript
// Reduce photo file sizes for mobile delivery
canvas.toBlob((blob) => {
    // Process blob
}, 'image/jpeg', 0.7); // 70% quality
```

### **Social Media Sharing (EASY - 3-4 hours)**
```javascript
// Universal sharing with Web Share API + fallbacks
if (navigator.share) {
    navigator.share({
        title: 'My Selfie Booth Photo',
        files: [photoBlob]
    });
} else {
    // Fallback share URLs for Facebook, Twitter, etc.
}
```

### **Event Overlays/Frames (EASY - 4-5 hours)**
- Custom event branding and sponsor logos
- Frames with event information
- Admin interface for overlay management
- Perfect for weddings, corporate events, conferences

### **Background Replacement (MEDIUM-HARD - 15-20 hours)**
- AI-powered background removal and replacement
- Multiple venue-specific background options
- Green screen alternative for easier implementation
- Mobile interface for background selection

**Event Marketing Value:**
- Wedding venues: "Get photos with your dream background!"
- Corporate events: "Brand every photo with your logo!"
- Conferences: "Take home a photo with [landmark]!"

## 🏛️ InMotion Shared Hosting Compatibility

### **Well-Suited Architecture**
- **Lightweight Flask app** - Minimal server resources
- **File-based sessions** - No complex database operations
- **Static file serving** - Most content is HTML/CSS/JS
- **Automatic cleanup** - Prevents resource buildup

### **Hosting Optimization**
- **Passenger WSGI** - Optimized for InMotion's Python hosting
- **Resource monitoring** - Built-in health checks and stats
- **Efficient polling** - Smart session monitoring to reduce CPU usage

## 🗃️ Database Support

### **SQLite (Development)**
- File-based database for development and small deployments
- Automatic initialization and session management
- Built-in cleanup and timeout handling

### **MySQL (Production)**
- Full MySQL support for production hosting
- Connection pooling and optimization
- Automatic fallback to SQLite if MySQL unavailable

## 📞 Messaging Services

### **Local Storage (Default)**
- File-based photo storage for development
- Detailed logging and tracking
- No external dependencies

### **Twilio SMS/MMS (Future)**
- Send photos via text message
- Configurable with environment variables
- Automatic fallback to local storage

### **Email Delivery (Future)**
- Send photos via email attachment
- SMTP configuration support
- HTML email templates

## 🎨 Kiosk Management

### **Dynamic Assignment**
- Automatic kiosk checkout system
- Status tracking (available/in_use/maintenance)
- Session timeout and cleanup
- Admin dashboard for kiosk monitoring

### **Multi-Kiosk Support**
- Up to 50 kiosks supported
- Individual kiosk status tracking
- Location-based configuration
- URL routing: `yoursite.com/1`, `yoursite.com/2`, etc.

## 📊 Admin Dashboard

### **Real-Time Statistics**
- Total sessions created/verified
- Photos taken count
- Current active sessions
- System health monitoring

### **Session Management**
- View recent sessions
- Session state monitoring
- Bulk session reset
- Export capabilities (planned)

### **Configuration**
- Messaging service selection
- Session timeout settings
- Kiosk management interface
- System status overview

## 🔧 Development Setup

### **Requirements**
```bash
pip install flask flask-cors
# Optional: pip install twilio mysql-connector-python
```

### **Environment Variables**
```bash
ADMIN_PASSWORD=your_admin_password
KIOSK_USERNAME=kiosk
KIOSK_PASSWORD=your_kiosk_password
```

### **Local Development**
```bash
cd api
python app.py
# Visit: http://localhost:5000/kiosk/login
```

## 📁 File Structure
```
selfie_booth/
├── api/
│   ├── app.py                 # Main Flask application (UPDATED with security)
│   ├── config_api.py          # Configuration management
│   ├── database_api.py        # Database abstraction
│   ├── messaging_api.py       # Photo delivery services
│   ├── passenger_wsgi.py      # InMotion WSGI entry point
│   └── .htaccess              # Apache configuration
├── assets/
│   ├── css/
│   │   ├── kiosk.css          # Kiosk interface styles
│   │   └── admin.css          # Admin dashboard styles
│   └── js/
│       └── admin.js           # Admin functionality
├── index.html                 # Kiosk display (protected route)
├── mobile.html                # Mobile registration (UPDATED)
├── verify-new.html            # Mobile verification (UPDATED)
├── photo-review.html          # Mobile photo review
├── admin.html                 # Admin dashboard (protected route)
├── .htaccess                  # URL routing
└── README.md                  # This file
```

## 🚨 Critical Implementation Notes

### **Security System Status: ✅ IMPLEMENTED**
- Complete authentication system built
- Admin and kiosk login protection
- API endpoint security
- Session management with timeouts
- Ready for production deployment

### **Mobile UX Improvements Status: ✅ IMPLEMENTED**
- Fixed localStorage variable conflicts
- Enhanced error handling and validation
- Real-time countdown timers
- Better user feedback and status messages

### **Performance Optimizations Status: 📋 PLANNED**
- Polling backoff strategy designed
- Caching mechanisms identified
- File operation batching planned
- Expected 50% performance improvement

### **Future Features Status: 📋 ROADMAP**
- Photo compression: Easy implementation ready
- Social sharing: Web Share API approach planned
- Event overlays: Admin interface designed
- Background replacement: AI approach researched

## 🎯 Next Implementation Priority

1. **✅ DONE: Security System** - Critical for production (2-3 hours)
2. **📋 NEXT: Photo Compression** - Easy win for user experience (1-2 hours)
3. **📋 FUTURE: Social Sharing** - High-value user feature (3-4 hours)
4. **📋 FUTURE: Event Features** - Revenue-generating capabilities (20+ hours)

## 💡 Business Value

### **Current State**
- Fully functional selfie booth system
- Secure for public deployment
- Professional admin interface
- Cross-device communication working
- InMotion hosting optimized

### **Revenue Potential**
- **Basic booth rental**: $200-500/event
- **Custom overlays/branding**: +$200/event
- **Background replacement**: +$300/event
- **Social media integration**: High user engagement

### **Scalability**
- Multi-kiosk support built-in
- Cloud hosting ready
- Enterprise security implemented
- Performance optimization roadmap

This project is **production-ready** with a clear roadmap for advanced features that significantly increase business value.