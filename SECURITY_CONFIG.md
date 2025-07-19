# Selfie Booth Security Configuration

## CRITICAL: Environment Variables to Set

Before deploying the security fixes, set these environment variables on your server:

### Required Security Variables
```bash
# Strong secret key for Flask sessions (generate a new one!)
export FLASK_SECRET_KEY="your-very-long-random-secret-key-here-minimum-32-chars"

# Restrict CORS to your domain only
export ALLOWED_ORIGINS="https://lockhartlovesyou.com,https://www.lockhartlovesyou.com"

# Strong admin credentials
export ADMIN_PASSWORD="your-strong-admin-password-here"

# Strong kiosk credentials  
export KIOSK_USERNAME="your-kiosk-username"
export KIOSK_PASSWORD="your-strong-kiosk-password"
```

### How to Generate a Strong Secret Key
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Deployment Steps

1. **Set Environment Variables** (above)
2. **Replace .htaccess file**:
   ```bash
   cp .htaccess .htaccess.backup
   cp .htaccess.secure .htaccess
   ```
3. **Test Authentication**:
   - Try accessing `/selfie_booth/admin.html` directly (should redirect to login)
   - Try accessing `/selfie_booth/index.html` directly (should redirect to login)
4. **Verify HTTPS**: Ensure your site uses SSL/TLS

## Security Features Implemented

### ✅ Fixed - Static File Access Control
- All HTML files now served through Flask with authentication
- Direct file access blocked by .htaccess rules
- Server-side authentication cannot be bypassed

### ✅ Fixed - Session Security
- Secure cookie settings (HttpOnly, Secure, SameSite)
- Environment-based secret key
- Session timeout implemented

### ✅ Fixed - API Security
- CORS restricted to allowed origins
- Security headers added (XSS protection, clickjacking prevention)
- Rate limiting on sensitive endpoints

### ✅ Fixed - Authentication Improvements
- Cryptographically secure verification codes
- Strong password requirements in documentation
- Admin session timeout

## Remaining Security Recommendations

### 1. Network Security
- Enable HTTPS/SSL (required for secure cookies)
- Use a firewall to restrict access to admin interfaces
- Consider VPN access for admin functions

### 2. Monitoring
- Log authentication attempts
- Monitor for unusual session patterns
- Set up alerts for failed login attempts

### 3. Regular Maintenance
- Change default passwords immediately
- Regularly rotate the Flask secret key
- Keep Flask and dependencies updated
- Review access logs periodically

## Testing the Security Fixes

### Test Direct Access Prevention
1. Visit `https://yoursite.com/selfie_booth/admin.html` - should redirect to login
2. Visit `https://yoursite.com/selfie_booth/index.html` - should redirect to login
3. Verify assets still load: `https://yoursite.com/selfie_booth/assets/css/admin.css`

### Test Authentication Flow
1. Login as admin -> should access admin.html successfully
2. Login as kiosk -> should access index.html successfully
3. Logout -> should redirect back to login

### Test API Security
1. Try API calls without authentication -> should fail appropriately
2. Verify CORS headers are restricted to your domain
3. Check that security headers are present in responses

## Emergency Rollback

If issues occur, restore the original .htaccess:
```bash
cp .htaccess.backup .htaccess
```

And revert the Flask app changes by checking out the previous version of `api/app.py`.