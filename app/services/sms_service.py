"""
SMS Service for sending OTP and notifications
Enhanced with Twilio Verify Service for better reliability
Supports Twilio Verify, basic Twilio SMS, and Azure Communication Services
"""
import logging
from typing import Optional, Dict, Any
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException
from ..config import settings
from app.services.twilio_verify_service import (
    twilio_verify_service,
    send_otp_verification,
    verify_otp_code,
    is_verify_available
)

logger = logging.getLogger(__name__)


class SMSService:
    """Enhanced SMS service with Twilio Verify integration and multiple provider support"""
    
    def __init__(self):
        self.twilio_client = None
        self.provider = None
        self.verify_available = False
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize SMS provider based on available configuration"""
        # Check for Twilio Verify Service first (preferred)
        if is_verify_available():
            self.verify_available = True
            self.provider = "twilio_verify"
            logger.info("Twilio Verify Service initialized successfully (preferred)")
            return
        
        # Fallback to basic Twilio SMS
        if (settings.TWILIO_ACCOUNT_SID and 
            settings.TWILIO_AUTH_TOKEN and 
            settings.TWILIO_PHONE_NUMBER):
            try:
                self.twilio_client = TwilioClient(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                self.provider = "twilio"
                logger.info("Twilio SMS provider initialized successfully (fallback mode)")
                return
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
        
        # Could add Azure Communication Services here
        # if settings.AZURE_COMMUNICATION_CONNECTION_STRING:
        #     self.provider = "azure"
        
        logger.warning("No SMS provider configured. Using development mode.")
    
    async def send_otp(self, mobile_number: str, otp: str = None, template_type: str = "login") -> Dict[str, Any]:
        """
        Send OTP via SMS using best available method
        
        Args:
            mobile_number: Phone number in E.164 format (+1234567890)
            otp: 6-digit OTP code (used only for basic SMS, Verify generates its own)
            template_type: Type of OTP (login, signup, recovery)
            
        Returns:
            Dict with success status and details
        """
        # Development mode if no provider configured
        if not self.provider:
            dev_otp = "123456"  # Fixed development OTP
            logger.info(f"Development mode: OTP {dev_otp} for {mobile_number}")
            return {
                "success": True,
                "provider": "development",
                "mobile_number": mobile_number,
                "otp_code": dev_otp,
                "message": "Development mode - use OTP: 123456"
            }
        
        # Format mobile number to E.164 if needed
        formatted_number = self._format_mobile_number(mobile_number)
        if not formatted_number:
            return {
                "success": False,
                "error": "Invalid mobile number format",
                "provider": self.provider
            }
        
        # Use Twilio Verify Service if available (preferred)
        if self.provider == "twilio_verify":
            try:
                result = await send_otp_verification(formatted_number, "sms")
                if result["success"]:
                    return result
                else:
                    logger.warning(f"Twilio Verify failed: {result.get('error')}, falling back to basic SMS")
                    # Fall through to basic SMS fallback
            except Exception as e:
                logger.error(f"Twilio Verify error: {e}, falling back to basic SMS")
                # Fall through to basic SMS fallback
        
        # Fallback to basic Twilio SMS
        if self.provider in ["twilio_verify", "twilio"]:
            # Reinitialize basic Twilio client if needed
            if not self.twilio_client and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                try:
                    self.twilio_client = TwilioClient(
                        settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_AUTH_TOKEN
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize Twilio client for fallback: {e}")
                    return await self._development_fallback(formatted_number, otp)
            
            if self.twilio_client and settings.TWILIO_PHONE_NUMBER:
                return await self._send_via_twilio(formatted_number, otp or self._generate_otp(), template_type)
        
        # Final fallback to development mode
        return await self._development_fallback(formatted_number, otp)
    
    async def verify_otp(self, mobile_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Verify OTP code using appropriate method
        
        Args:
            mobile_number: Phone number to verify for
            otp_code: OTP code to verify
            
        Returns:
            Dict with verification status and details
        """
        # Format mobile number
        formatted_number = self._format_mobile_number(mobile_number)
        if not formatted_number:
            return {
                "success": False,
                "error": "Invalid mobile number format",
                "provider": self.provider
            }
        
        # If Twilio Verify is available, use it for verification
        if self.verify_available:
            try:
                result = await verify_otp_code(formatted_number, otp_code)
                return result
            except Exception as e:
                logger.error(f"Twilio Verify verification failed: {e}")
                # Fall through to development mode
        
        # Development mode verification
        if otp_code == "123456":
            logger.info(f"Development mode: OTP verified for {formatted_number}")
            return {
                "success": True,
                "valid": True,
                "provider": "development",
                "mobile_number": formatted_number,
                "message": "Development mode - OTP verified"
            }
        
        # Invalid OTP in development mode
        return {
            "success": True,
            "valid": False,
            "provider": "development",
            "mobile_number": formatted_number,
            "message": "Invalid OTP - use 123456 for development"
        }
    
    async def _development_fallback(self, mobile_number: str, otp: str = None) -> Dict[str, Any]:
        """Development mode fallback"""
        dev_otp = otp or "123456"
        logger.info(f"Development fallback: OTP {dev_otp} for {mobile_number}")
        return {
            "success": True,
            "provider": "development_fallback",
            "mobile_number": mobile_number,
            "otp_code": dev_otp,
            "message": f"Provider unavailable - use development OTP: {dev_otp}"
        }
    
    def _generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        import random
        return str(random.randint(100000, 999999))
    
    async def _send_via_twilio(self, mobile_number: str, otp: str, template_type: str) -> Dict[str, Any]:
        """Send SMS via basic Twilio (fallback method)"""
        try:
            message = self._create_message(otp, template_type)
            
            message_response = self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=mobile_number
            )
            
            logger.info(f"SMS sent successfully via Twilio: {message_response.sid}")
            
            return {
                "success": True,
                "provider": "twilio",
                "message_id": message_response.sid,
                "status": message_response.status,
                "to": mobile_number,
                "otp_code": otp  # Include for basic SMS
            }
            
        except TwilioException as e:
            logger.error(f"Twilio SMS failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "twilio",
                "to": mobile_number
            }
        except Exception as e:
            logger.error(f"Unexpected SMS error: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "provider": "twilio",
                "to": mobile_number
            }
    
    def _format_mobile_number(self, mobile_number: str) -> Optional[str]:
        """
        Format mobile number to E.164 format
        
        Args:
            mobile_number: Raw mobile number
            
        Returns:
            Formatted number or None if invalid
        """
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in mobile_number if c.isdigit() or c == '+')
        
        # If no country code, assume US (+1) for now
        # In production, you'd want to detect country or ask user
        if not cleaned.startswith('+'):
            if len(cleaned) == 10:  # US number without country code
                cleaned = f"+1{cleaned}"
            elif len(cleaned) == 11 and cleaned.startswith('1'):  # US number with 1
                cleaned = f"+{cleaned}"
            elif len(cleaned) >= 10:  # International without +
                cleaned = f"+{cleaned}"
        
        # Basic validation - should be 10-15 digits after country code
        if len(cleaned) < 8 or len(cleaned) > 16:
            logger.warning(f"Invalid mobile number length: {cleaned}")
            return None
        
        return cleaned
    
    def _create_message(self, otp: str, template_type: str) -> str:
        """Create SMS message based on template type"""
        templates = {
            "login": f"Your TINKO login code: {otp}. Valid for 5 minutes. Don't share this code with anyone.",
            "signup": f"Welcome to TINKO! Your verification code: {otp}. Valid for 5 minutes.",
            "recovery": f"TINKO account recovery code: {otp}. Valid for 5 minutes. If you didn't request this, please ignore.",
            "payment": f"Your TINKO payment verification code: {otp}. Valid for 5 minutes."
        }
        
        return templates.get(template_type, templates["login"])
    
    async def send_recovery_notification(
        self, 
        mobile_number: str, 
        recovery_link: str, 
        amount: str, 
        merchant: str
    ) -> Dict[str, Any]:
        """
        Send payment recovery notification
        
        Args:
            mobile_number: Customer's mobile number
            recovery_link: Recovery link URL
            amount: Payment amount
            merchant: Merchant name
            
        Returns:
            Send result
        """
        if not self.provider:
            return await self._development_fallback(mobile_number)
        
        formatted_number = self._format_mobile_number(mobile_number)
        if not formatted_number:
            return {
                "success": False,
                "error": "Invalid mobile number format",
                "provider": self.provider
            }
        
        message = (
            f"Payment Failed - TINKO Recovery\n"
            f"Merchant: {merchant}\n"
            f"Amount: {amount}\n"
            f"Complete payment: {recovery_link}\n"
            f"Link expires in 24 hours."
        )
        
        # Use basic Twilio for recovery notifications (not Verify)
        if self.twilio_client and settings.TWILIO_PHONE_NUMBER:
            try:
                message_response = self.twilio_client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=formatted_number
                )
                
                return {
                    "success": True,
                    "provider": "twilio",
                    "message_id": message_response.sid,
                    "status": message_response.status,
                    "to": formatted_number
                }
            except Exception as e:
                logger.error(f"Recovery SMS failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "provider": "twilio"
                }
        
        return {
            "success": False,
            "error": f"Unsupported provider: {self.provider}",
            "provider": self.provider
        }
    
    def is_available(self) -> bool:
        """Check if SMS service is available"""
        return self.provider is not None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about configured provider"""
        return {
            "provider": self.provider,
            "verify_available": self.verify_available,
            "available": self.is_available(),
            "phone_number": settings.TWILIO_PHONE_NUMBER if self.provider == "twilio" else None
        }


# Global SMS service instance
sms_service = SMSService()


# Convenience functions
async def send_otp_sms(mobile_number: str, otp: str = None, template_type: str = "login") -> Dict[str, Any]:
    """Send OTP SMS"""
    return await sms_service.send_otp(mobile_number, otp, template_type)


async def verify_otp_sms(mobile_number: str, otp_code: str) -> Dict[str, Any]:
    """Verify OTP code"""
    return await sms_service.verify_otp(mobile_number, otp_code)


async def send_recovery_sms(
    mobile_number: str, 
    recovery_link: str, 
    amount: str, 
    merchant: str
) -> Dict[str, Any]:
    """Send payment recovery SMS"""
    return await sms_service.send_recovery_notification(
        mobile_number, recovery_link, amount, merchant
    )


def is_sms_available() -> bool:
    """Check if SMS service is available"""
    return sms_service.is_available()