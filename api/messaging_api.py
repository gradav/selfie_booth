#!/usr/bin/env python3
"""
Messaging services for Selfie Booth API
Handles Twilio, Email, and Local storage for photo delivery
"""

import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from config_api import APIConfig

# Twilio imports with fallback
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TwilioClient = None
    TWILIO_AVAILABLE = False


class MessagingService:
    """Base messaging service class"""
    def send_photo(self, recipient, photo_data, message):
        raise NotImplementedError


class TwilioMessagingService(MessagingService):
    """Twilio SMS/MMS service"""
    
    def __init__(self, account_sid=None, auth_token=None, from_number=None):
        if not TWILIO_AVAILABLE:
            raise ImportError("Twilio library not available - install with: pip install twilio")
        
        self.account_sid = account_sid or APIConfig.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or APIConfig.TWILIO_AUTH_TOKEN
        self.from_number = from_number or APIConfig.TWILIO_FROM_NUMBER
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            missing = []
            if not self.account_sid: missing.append('TWILIO_ACCOUNT_SID')
            if not self.auth_token: missing.append('TWILIO_AUTH_TOKEN')
            if not self.from_number: missing.append('TWILIO_FROM_NUMBER')
            raise ValueError(f"Missing Twilio credentials: {', '.join(missing)}")
        
        try:
            self.client = TwilioClient(self.account_sid, self.auth_token)
            print("✅ Twilio messaging service initialized")
        except Exception as e:
            raise ValueError(f"Failed to initialize Twilio client: {str(e)}")
    
    def send_photo(self, phone, photo_data, message):
        """Send photo via Twilio MMS"""
        try:
            # Format phone number
            if not phone.startswith('+'):
                if phone.startswith('1') and len(phone) == 11:
                    phone = f'+{phone}'
                elif len(phone) == 10:
                    phone = f'+1{phone}'
                else:
                    return False, f"Invalid phone number format: {phone}"
            
            # Save photo temporarily (Twilio needs file path)
            temp_filename = f"temp_mms_{datetime.now().timestamp()}.jpg"
            temp_path = os.path.join(APIConfig.UPLOAD_FOLDER, temp_filename)
            
            # Ensure upload directory exists
            os.makedirs(APIConfig.UPLOAD_FOLDER, exist_ok=True)
            
            try:
                with open(temp_path, 'wb') as f:
                    f.write(photo_data)
                
                # Send MMS
                message_obj = self.client.messages.create(
                    body=message,
                    media_url=[f"file://{os.path.abspath(temp_path)}"],
                    from_=self.from_number,
                    to=phone
                )
                
                return True, f"Photo sent via Twilio MMS: {message_obj.sid}"
                
            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except OSError:
                    pass
                    
        except Exception as e:
            return False, f"Twilio error: {str(e)}"


class EmailMessagingService(MessagingService):
    """Email messaging service"""
    
    def __init__(self, smtp_server=None, smtp_port=None, email=None, password=None):
        self.smtp_server = smtp_server or APIConfig.EMAIL_SMTP_SERVER
        self.smtp_port = int(smtp_port or APIConfig.EMAIL_SMTP_PORT)
        self.email = email or APIConfig.EMAIL_ADDRESS
        self.password = password or APIConfig.EMAIL_PASSWORD
        
        if not all([self.email, self.password]):
            missing = []
            if not self.email: missing.append('EMAIL_ADDRESS')
            if not self.password: missing.append('EMAIL_PASSWORD')
            raise ValueError(f"Missing email credentials: {', '.join(missing)}")
        
        print("✅ Email messaging service initialized")
    
    def send_photo(self, recipient_email, photo_data, message):
        """Send photo via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient_email
            msg['Subject'] = "Your Selfie Booth Photo! 📸"
            
            # Add text body
            body = f"{message}\n\nEnjoy your photo!\n\nThanks for using our Selfie Booth!"
            msg.attach(MIMEText(body, 'plain'))
            
            # Add photo attachment
            img = MIMEImage(photo_data)
            img.add_header('Content-Disposition', 'attachment', filename='selfie.jpg')
            msg.attach(img)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True, f"Photo sent via email to {recipient_email}"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Email authentication failed - check credentials"
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Email error: {str(e)}"


class LocalStorageService(MessagingService):
    """Local storage service for development/testing"""
    
    def __init__(self, upload_folder=None):
        self.upload_folder = upload_folder or APIConfig.UPLOAD_FOLDER
        
        # Ensure upload directory exists
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Create log file for tracking
        self.log_file = os.path.join(self.upload_folder, 'photo_delivery_log.txt')
        
        print(f"✅ Local storage service initialized: {self.upload_folder}")
    
    def send_photo(self, identifier, photo_data, message):
        """Save photo locally with detailed logging"""
        try:
            timestamp = datetime.now()
            filename = f"photo_{identifier}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(self.upload_folder, filename)
            
            # Save photo
            with open(filepath, 'wb') as f:
                f.write(photo_data)
            
            # Log the delivery
            log_entry = (f"{timestamp.isoformat()} | {identifier} | {filename} | "
                        f"{len(photo_data)} bytes | {message}\n")
            
            try:
                with open(self.log_file, 'a', encoding='utf-8') as log_f:
                    log_f.write(log_entry)
            except OSError:
                pass  # Log write failed but photo was saved
            
            file_size_mb = len(photo_data) / (1024 * 1024)
            return True, f"Photo saved locally: {filename} ({file_size_mb:.1f}MB)"
            
        except OSError as e:
            return False, f"File system error: {str(e)}"
        except Exception as e:
            return False, f"Local storage error: {str(e)}"


def get_messaging_service():
    """Factory function to get appropriate messaging service"""
    service_type = APIConfig.MESSAGING_SERVICE.lower()
    
    try:
        if service_type == 'twilio':
            if not TWILIO_AVAILABLE:
                print("⚠️ Twilio requested but not available, falling back to local storage")
                return LocalStorageService()
            return TwilioMessagingService()
            
        elif service_type == 'email':
            return EmailMessagingService()
            
        else:  # Default to local storage
            return LocalStorageService()
            
    except (ImportError, ValueError) as e:
        print(f"⚠️ Failed to create {service_type} service: {e}")
        print("🔄 Falling back to local storage")
        return LocalStorageService()


def validate_service_config(service_type=None):
    """Validate messaging service configuration"""
    if service_type is None:
        service_type = APIConfig.MESSAGING_SERVICE.lower()
    
    errors = []
    
    if service_type == 'twilio':
        if not TWILIO_AVAILABLE:
            errors.append("Twilio library not installed (pip install twilio)")
        
        if not APIConfig.TWILIO_ACCOUNT_SID:
            errors.append("TWILIO_ACCOUNT_SID environment variable not set")
        if not APIConfig.TWILIO_AUTH_TOKEN:
            errors.append("TWILIO_AUTH_TOKEN environment variable not set")
        if not APIConfig.TWILIO_FROM_NUMBER:
            errors.append("TWILIO_FROM_NUMBER environment variable not set")
    
    elif service_type == 'email':
        if not APIConfig.EMAIL_ADDRESS:
            errors.append("EMAIL_ADDRESS environment variable not set")
        if not APIConfig.EMAIL_PASSWORD:
            errors.append("EMAIL_PASSWORD environment variable not set")
    
    # Local storage always works
    
    return len(errors) == 0, errors


def get_service_status():
    """Get status of all available messaging services"""
    status = {}
    
    # Check Twilio
    twilio_valid, twilio_errors = validate_service_config('twilio')
    status['twilio'] = {
        'available': TWILIO_AVAILABLE,
        'configured': twilio_valid,
        'errors': twilio_errors
    }
    
    # Check Email
    email_valid, email_errors = validate_service_config('email')
    status['email'] = {
        'available': True,  # Email is always available
        'configured': email_valid,
        'errors': email_errors
    }
    
    # Local storage
    status['local'] = {
        'available': True,
        'configured': True,
        'errors': []
    }
    
    return status


# Helper functions for recipient determination
def get_recipient_for_service(service, phone, email, session_id):
    """Get appropriate recipient based on service type"""
    if isinstance(service, EmailMessagingService):
        return email if email else phone  # Fallback to phone if no email
    elif isinstance(service, TwilioMessagingService):
        return phone
    else:  # LocalStorageService
        return session_id or phone


# Test function for development
def test_messaging_service(service_type=None):
    """Test messaging service functionality"""
    service_type = service_type or APIConfig.MESSAGING_SERVICE
    
    print(f"🧪 Testing {service_type} messaging service...")
    
    try:
        service = get_messaging_service()
        
        # Create test photo data (1x1 pixel JPEG)
        test_photo = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x11, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0x02, 0x11, 0x01, 0x03, 0x11, 0x01,
            0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0xFF, 0xC4,
            0x00, 0x14, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xDA, 0x00, 0x0C,
            0x03, 0x01, 0x00, 0x02, 0x11, 0x03, 0x11, 0x00, 0x3F, 0x00, 0x80, 0xFF, 0xD9
        ])
        
        test_message = "Test message from Selfie Booth API"
        
        if isinstance(service, LocalStorageService):
            success, result = service.send_photo("test_session", test_photo, test_message)
        else:
            # For real services, use test recipient
            test_recipient = "test@example.com" if isinstance(service, EmailMessagingService) else "+15551234567"
            success, result = service.send_photo(test_recipient, test_photo, test_message)
        
        if success:
            print(f"✅ Test successful: {result}")
            return True
        else:
            print(f"❌ Test failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


if __name__ == '__main__':
    # Run tests when executed directly
    print("🧪 Running messaging service tests...")
    
    status = get_service_status()
    for service_name, service_status in status.items():
        print(f"\n{service_name.upper()} Service:")
        print(f"  Available: {service_status['available']}")
        print(f"  Configured: {service_status['configured']}")
        if service_status['errors']:
            print(f"  Errors: {', '.join(service_status['errors'])}")
    
    print(f"\nTesting current service ({APIConfig.MESSAGING_SERVICE})...")
    test_messaging_service()