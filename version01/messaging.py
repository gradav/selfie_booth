#!/usr/bin/env python3
"""
Messaging services module for Selfie Booth application
Handles different messaging platforms (Twilio, Email, Local Storage)
Optimized for modular architecture and web hosting
"""

import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# Twilio imports with error handling
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TwilioClient = None
    TWILIO_AVAILABLE = False


class MessagingService:
    """Base class for messaging services"""
    def send_photo(self, recipient, photo_data, message):
        raise NotImplementedError


class TwilioService(MessagingService):
    """Twilio SMS/MMS messaging service with enhanced error handling"""
    
    def __init__(self, account_sid=None, auth_token=None, from_number=None):
        if not TWILIO_AVAILABLE:
            raise ImportError("Twilio library not available. Install with: pip install twilio")
        
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_FROM_NUMBER')
        
        # Validate required credentials
        if not all([self.account_sid, self.auth_token, self.from_number]):
            missing = []
            if not self.account_sid: missing.append('TWILIO_ACCOUNT_SID')
            if not self.auth_token: missing.append('TWILIO_AUTH_TOKEN')
            if not self.from_number: missing.append('TWILIO_FROM_NUMBER')
            raise ValueError(f"Missing Twilio credentials: {', '.join(missing)}")
        
        # Initialize client
        try:
            self.client = TwilioClient(self.account_sid, self.auth_token)
        except Exception as e:
            raise ValueError(f"Failed to initialize Twilio client: {str(e)}")
        
    def send_photo(self, phone, photo_data, message):
        """Send photo via Twilio MMS"""
        try:
            # Ensure phone number is properly formatted
            if not phone.startswith('+'):
                if phone.startswith('1') and len(phone) == 11:
                    phone = f'+{phone}'
                elif len(phone) == 10:
                    phone = f'+1{phone}'
                else:
                    return False, f"Invalid phone number format: {phone}"
            
            # Save photo temporarily for Twilio (they need a file path)
            temp_filename = f"temp_mms_{datetime.now().timestamp()}.jpg"
            temp_path = os.path.join(os.path.dirname(__file__), temp_filename)
            
            try:
                with open(temp_path, 'wb') as f:
                    f.write(photo_data)
                
                # Send MMS message
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
                    pass  # File cleanup failed, but message was sent
                    
        except Exception as e:
            return False, f"Twilio error: {str(e)}"


class EmailService(MessagingService):
    """Email messaging service with enhanced configuration"""
    
    def __init__(self, smtp_server=None, smtp_port=None, email=None, password=None):
        self.smtp_server = smtp_server or os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(smtp_port or os.getenv('EMAIL_SMTP_PORT', '587'))
        self.email = email or os.getenv('EMAIL_ADDRESS')
        self.password = password or os.getenv('EMAIL_PASSWORD')
        
        # Validate required credentials
        if not all([self.email, self.password]):
            missing = []
            if not self.email: missing.append('EMAIL_ADDRESS')
            if not self.password: missing.append('EMAIL_PASSWORD')
            raise ValueError(f"Missing email credentials: {', '.join(missing)}")
        
    def send_photo(self, recipient_email, photo_data, message):
        """Send photo via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient_email
            msg['Subject'] = "Your Selfie Booth Photo! 📸"
            
            # Add text body
            body = f"{message}\n\nEnjoy your photo!"
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
    """Local storage service for development/testing with enhanced features"""
    
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Create a log file for tracking sent photos
        self.log_file = os.path.join(upload_folder, 'photo_log.txt')
        
    def send_photo(self, identifier, photo_data, message):
        """Save photo locally with detailed logging"""
        try:
            timestamp = datetime.now()
            filename = f"photo_{identifier}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(self.upload_folder, filename)
            
            # Save photo
            with open(filepath, 'wb') as f:
                f.write(photo_data)
            
            # Log the action
            log_entry = f"{timestamp.isoformat()} | {identifier} | {filename} | {len(photo_data)} bytes | {message}\n"
            
            try:
                with open(self.log_file, 'a') as log_f:
                    log_f.write(log_entry)
            except OSError:
                pass  # Log write failed, but photo was saved
            
            file_size_mb = len(photo_data) / (1024 * 1024)
            return True, f"Photo saved locally: {filename} ({file_size_mb:.1f}MB)"
            
        except OSError as e:
            return False, f"File system error: {str(e)}"
        except Exception as e:
            return False, f"Local storage error: {str(e)}"


class MessagingServiceFactory:
    """Factory for creating messaging services with enhanced error handling"""
    
    @staticmethod
    def create_service(service_type=None, upload_folder='uploads'):
        """Create appropriate messaging service based on configuration"""
        if service_type is None:
            service_type = os.getenv('MESSAGING_SERVICE', 'local')
        
        try:
            if service_type.lower() == 'twilio':
                return TwilioService()
            elif service_type.lower() == 'email':
                return EmailService()
            else:
                return LocalStorageService(upload_folder)
                
        except (ImportError, ValueError) as e:
            print(f"⚠️ Failed to create {service_type} service: {e}")
            print(f"🔄 Falling back to local storage")
            return LocalStorageService(upload_folder)
    
    @staticmethod
    def get_recipient_for_service(service, phone, email, session_id):
        """Get appropriate recipient based on service type"""
        if isinstance(service, EmailService):
            return email if email else phone  # Fallback to phone if no email
        elif isinstance(service, TwilioService):
            return phone
        else:  # LocalStorageService
            return session_id
    
    @staticmethod
    def validate_service_config(service_type=None):
        """Validate configuration for a specific messaging service"""
        if service_type is None:
            service_type = os.getenv('MESSAGING_SERVICE', 'local')
        
        errors = []
        
        if service_type.lower() == 'twilio':
            if not TWILIO_AVAILABLE:
                errors.append("Twilio library not installed")
            
            required_vars = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_FROM_NUMBER']
            for var in required_vars:
                if not os.getenv(var):
                    errors.append(f"{var} environment variable not set")
        
        elif service_type.lower() == 'email':
            required_vars = ['EMAIL_ADDRESS', 'EMAIL_PASSWORD']
            for var in required_vars:
                if not os.getenv(var):
                    errors.append(f"{var} environment variable not set")
        
        # Local storage always works, no validation needed
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_service_status():
        """Get status of all available messaging services"""
        status = {}
        
        # Check Twilio
        twilio_valid, twilio_errors = MessagingServiceFactory.validate_service_config('twilio')
        status['twilio'] = {
            'available': TWILIO_AVAILABLE,
            'configured': twilio_valid,
            'errors': twilio_errors
        }
        
        # Check Email
        email_valid, email_errors = MessagingServiceFactory.validate_service_config('email')
        status['email'] = {
            'available': True,  # Email is always available (built-in)
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


# Convenience function for quick service creation
def get_messaging_service(service_type=None, upload_folder='uploads'):
    """Convenience function to get a messaging service instance"""
    factory = MessagingServiceFactory()
    return factory.create_service(service_type, upload_folder)