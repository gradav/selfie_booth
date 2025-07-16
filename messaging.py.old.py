#!/usr/bin/env python3
"""
Messaging services module for Selfie Booth application
Handles different messaging platforms (Twilio, Email, Local Storage)
"""

import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage


class MessagingService:
    """Base class for messaging services"""
    def send_photo(self, recipient, photo_data, message):
        raise NotImplementedError


class TwilioService(MessagingService):
    """Twilio SMS/MMS messaging service"""
    
    def __init__(self, account_sid=None, auth_token=None, from_number=None):
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_FROM_NUMBER')
        
    def send_photo(self, phone, photo_data, message):
        """Send photo via Twilio MMS"""
        try:
            from twilio.rest import Client
            client = Client(self.account_sid, self.auth_token)
            
            # Save photo temporarily for Twilio
            temp_path = f"temp_{datetime.now().timestamp()}.jpg"
            with open(temp_path, 'wb') as f:
                f.write(photo_data)
            
            # Send MMS
            message_obj = client.messages.create(
                body=message,
                media_url=[f"file://{os.path.abspath(temp_path)}"],
                from_=self.from_number,
                to=phone
            )
            
            # Cleanup
            os.remove(temp_path)
            return True, f"Photo sent via Twilio: {message_obj.sid}"
        except Exception as e:
            return False, f"Twilio error: {str(e)}"


class EmailService(MessagingService):
    """Email messaging service"""
    
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587, email=None, password=None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email or os.getenv('EMAIL_ADDRESS')
        self.password = password or os.getenv('EMAIL_PASSWORD')
        
    def send_photo(self, recipient_email, photo_data, message):
        """Send photo via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient_email
            msg['Subject'] = "Your Selfie Booth Photo!"
            
            # Add text
            msg.attach(MIMEText(message, 'plain'))
            
            # Add photo
            img = MIMEImage(photo_data)
            img.add_header('Content-Disposition', 'attachment', filename='selfie.jpg')
            msg.attach(img)
            
            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True, "Photo sent via email"
        except Exception as e:
            return False, f"Email error: {str(e)}"


class LocalStorageService(MessagingService):
    """Local storage service for development/testing"""
    
    def __init__(self, upload_folder='photos'):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
        
    def send_photo(self, identifier, photo_data, message):
        """Save photo locally"""
        try:
            filename = f"photo_{identifier}_{datetime.now().timestamp()}.jpg"
            filepath = os.path.join(self.upload_folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(photo_data)
            
            return True, f"Photo saved locally: {filepath}"
        except Exception as e:
            return False, f"Local storage error: {str(e)}"


class MessagingServiceFactory:
    """Factory for creating messaging services"""
    
    @staticmethod
    def create_service(service_type=None, upload_folder='photos'):
        """Create appropriate messaging service based on configuration"""
        if service_type is None:
            service_type = os.getenv('MESSAGING_SERVICE', 'local')
        
        if service_type == 'twilio':
            return TwilioService()
        elif service_type == 'email':
            return EmailService()
        else:
            return LocalStorageService(upload_folder)
    
    @staticmethod
    def get_recipient_for_service(service, phone, email, session_id):
        """Get appropriate recipient based on service type"""
        if isinstance(service, EmailService) and email:
            return email
        elif isinstance(service, LocalStorageService):
            return session_id
        else:
            return phone