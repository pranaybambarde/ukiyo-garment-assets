import jwt
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import requests
from jose import JWTError, jwt as jose_jwt

class AuthManager:
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key')
        self.jwt_algorithm = 'HS256'
        self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.apple_client_id = os.getenv('APPLE_CLIENT_ID')
        self.otp_expiry_minutes = 10

    def generate_jwt_token(self, user_id: str, role: str = 'customer', expires_in_minutes: int = 10080) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except JWTError:
            return None

    def generate_otp(self, length: int = 6) -> str:
        """Generate OTP for phone verification"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))

    def hash_otp(self, otp: str) -> str:
        """Hash OTP for storage"""
        return hashlib.sha256(otp.encode()).hexdigest()

    def verify_otp(self, provided_otp: str, stored_hash: str) -> bool:
        """Verify OTP against stored hash"""
        return self.hash_otp(provided_otp) == stored_hash

    def generate_session_id(self) -> str:
        """Generate session ID for guest users"""
        return secrets.token_urlsafe(32)

    async def verify_google_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Google OAuth token"""
        try:
            # Verify token with Google
            response = requests.get(
                f'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}'
            )
            
            if response.status_code == 200:
                user_info = response.json()
                if user_info.get('audience') == self.google_client_id:
                    return {
                        'provider_id': user_info['user_id'],
                        'email': user_info['email'],
                        'name': user_info.get('name', ''),
                        'provider': 'google'
                    }
        except Exception as e:
            print(f"Google token verification error: {e}")
        
        return None

    async def verify_apple_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Apple Sign-In token"""
        try:
            # For Apple Sign-In, we would typically verify the JWT token
            # This is a simplified version - in production, you'd verify the signature
            # and decode the token properly
            response = requests.get(
                f'https://appleid.apple.com/auth/verify',
                params={'id_token': token}
            )
            
            if response.status_code == 200:
                # In a real implementation, you'd decode the JWT and verify signature
                # For now, we'll return a placeholder
                return {
                    'provider_id': 'apple_user_id',  # Extract from JWT
                    'email': 'user@example.com',     # Extract from JWT
                    'name': 'Apple User',            # Extract from JWT
                    'provider': 'apple'
                }
        except Exception as e:
            print(f"Apple token verification error: {e}")
        
        return None

    def create_otp_session(self, phone: str, otp: str) -> Dict[str, Any]:
        """Create OTP session for verification"""
        otp_hash = self.hash_otp(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
        
        return {
            'phone': phone,
            'otp_hash': otp_hash,
            'expires_at': expires_at.isoformat(),
            'attempts': 0
        }

    def verify_otp_session(self, session_data: Dict[str, Any], provided_otp: str) -> bool:
        """Verify OTP session"""
        # Check if session is expired
        expires_at = datetime.fromisoformat(session_data['expires_at'])
        if datetime.utcnow() > expires_at:
            return False
        
        # Check attempt limit
        if session_data.get('attempts', 0) >= 3:
            return False
        
        # Verify OTP
        return self.verify_otp(provided_otp, session_data['otp_hash'])

    def extract_user_from_token(self, auth_header: str) -> Optional[Dict[str, Any]]:
        """Extract user info from Authorization header"""
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        return self.verify_jwt_token(token)

    def require_auth(self, auth_header: str) -> Optional[Dict[str, Any]]:
        """Require authentication and return user info"""
        user_info = self.extract_user_from_token(auth_header)
        if not user_info:
            raise Exception("Authentication required")
        return user_info

    def require_admin(self, auth_header: str) -> Optional[Dict[str, Any]]:
        """Require admin authentication"""
        user_info = self.require_auth(auth_header)
        if user_info.get('role') != 'admin':
            raise Exception("Admin access required")
        return user_info
