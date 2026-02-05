import random
import string
from datetime import datetime, timedelta
from threading import Lock


class OTPCache:
    """
    Simple in-memory OTP cache
    Thread-safe storage for OTP verification
    """
    
    def __init__(self):
        self._cache = {}  # {email: {otp, expires_at, registration_data}}
        self._lock = Lock()
    
    @staticmethod
    def generate_otp():
        """Generate 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def create_otp(self, email, registration_data=None, expiry_minutes=10):
        """
        Create and store OTP for email
        
        Returns:
            str: Generated OTP code
        """
        with self._lock:
            otp_code = self.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
            
            self._cache[email] = {
                'otp_code': otp_code,
                'expires_at': expires_at,
                'registration_data': registration_data,
                'created_at': datetime.utcnow()
            }
            
            return otp_code
    
    def verify_otp(self, email, otp_code):
        """
        Verify OTP for email
        
        Returns:
            tuple: (registration_data, error_message)
        """
        with self._lock:
            cached = self._cache.get(email)
            
            if not cached:
                return None, "Kode OTP tidak ditemukan. Silakan request OTP baru."
            
            # Check if expired
            if datetime.utcnow() > cached['expires_at']:
                del self._cache[email]  # Clean up expired
                return None, "Kode OTP sudah kadaluarsa. Silakan request OTP baru."
            
            # Check if OTP matches
            if cached['otp_code'] != otp_code:
                return None, "Kode OTP salah. Silakan coba lagi."
            
            # OTP valid - return registration data and delete from cache
            registration_data = cached['registration_data']
            del self._cache[email]
            
            return registration_data, None
    
    def has_otp(self, email):
        """Check if email has pending OTP"""
        with self._lock:
            cached = self._cache.get(email)
            if not cached:
                return False
            
            # Check if expired
            if datetime.utcnow() > cached['expires_at']:
                del self._cache[email]
                return False
            
            return True
    
    def get_registration_data(self, email):
        """Get registration data without verifying OTP"""
        with self._lock:
            cached = self._cache.get(email)
            if cached:
                return cached.get('registration_data')
            return None
    
    def cleanup_expired(self):
        """Remove expired OTPs from cache"""
        with self._lock:
            now = datetime.utcnow()
            expired_emails = [
                email for email, data in self._cache.items()
                if now > data['expires_at']
            ]
            for email in expired_emails:
                del self._cache[email]
    
    def delete_otp(self, email):
        """Delete OTP for email"""
        with self._lock:
            if email in self._cache:
                del self._cache[email]


# Global OTP cache instance
otp_cache = OTPCache()