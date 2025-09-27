import json
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Import shared modules
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from database import DynamoDBClient
from auth import AuthManager
from models import UserProfile, UserAuth, APIResponse
from utils import generate_id, validate_email, create_response

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class EmailAuthRequest(BaseModel):
    email: str
    password: Optional[str] = None

class EmailMagicLinkRequest(BaseModel):
    email: str

class EmailAuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

@app.post("/auth/email/register", response_model=EmailAuthResponse)
async def register_with_email(request: EmailAuthRequest):
    """Register user with email and password"""
    try:
        # Validate email
        if not validate_email(request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Check if user already exists
        existing_user = db.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists with this email")
        
        # Create new user
        user_id = generate_id('user_')
        user_data = {
            'user_id': user_id,
            'email': request.email,
            'name': request.email.split('@')[0],  # Default name from email
            'role': 'customer',
            'created_at': auth_manager.datetime.utcnow().isoformat(),
            'updated_at': auth_manager.datetime.utcnow().isoformat(),
            'is_active': True
        }
        user = db.create_user(user_data)
        
        # Create auth record
        auth_data = {
            'user_id': user_id,
            'provider': 'email',
            'provider_id': request.email,
            'created_at': auth_manager.datetime.utcnow().isoformat()
        }
        db.tables['user_auth'].put_item(Item=auth_data)
        
        # Generate JWT token
        token = auth_manager.generate_jwt_token(user['user_id'], user['role'])
        
        return EmailAuthResponse(
            success=True,
            message="Registration successful",
            data={
                'token': token,
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            }
        )
        
    except Exception as e:
        return EmailAuthResponse(
            success=False,
            message="Registration failed",
            error=str(e)
        )

@app.post("/auth/email/login", response_model=EmailAuthResponse)
async def login_with_email(request: EmailAuthRequest):
    """Login with email and password"""
    try:
        # Validate email
        if not validate_email(request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Get user
        user = db.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # TODO: Implement password verification
        # For now, we'll just check if user exists
        if not user['is_active']:
            raise HTTPException(status_code=401, detail="Account is deactivated")
        
        # Generate JWT token
        token = auth_manager.generate_jwt_token(user['user_id'], user['role'])
        
        return EmailAuthResponse(
            success=True,
            message="Login successful",
            data={
                'token': token,
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            }
        )
        
    except Exception as e:
        return EmailAuthResponse(
            success=False,
            message="Login failed",
            error=str(e)
        )

@app.post("/auth/email/send-magic-link", response_model=EmailAuthResponse)
async def send_magic_link(request: EmailMagicLinkRequest):
    """Send magic link to email for passwordless login"""
    try:
        # Validate email
        if not validate_email(request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Generate magic link token
        magic_token = auth_manager.generate_jwt_token(
            request.email, 
            'magic_link',
            expires_in_minutes=15
        )
        
        # Store magic link session
        session_data = {
            'session_id': generate_id('magic_'),
            'email': request.email,
            'magic_token': magic_token,
            'expires_at': (auth_manager.datetime.utcnow() + auth_manager.timedelta(minutes=15)).isoformat(),
            'used': False,
            'ttl': int((auth_manager.datetime.utcnow() + auth_manager.timedelta(minutes=15)).timestamp())
        }
        
        db.tables['magic_link_sessions'].put_item(Item=session_data)
        
        # TODO: Send magic link via email service (SES, SendGrid, etc.)
        magic_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/auth/magic-link?token={magic_token}"
        
        if os.getenv('ENVIRONMENT') == 'development':
            print(f"Magic link for {request.email}: {magic_link}")
        
        return EmailAuthResponse(
            success=True,
            message="Magic link sent successfully",
            data={'email': request.email}
        )
        
    except Exception as e:
        return EmailAuthResponse(
            success=False,
            message="Failed to send magic link",
            error=str(e)
        )

@app.post("/auth/email/verify-magic-link", response_model=EmailAuthResponse)
async def verify_magic_link(request: EmailMagicLinkRequest):
    """Verify magic link and authenticate user"""
    try:
        # Extract token from request (assuming it's in the email field for simplicity)
        magic_token = request.email
        
        # Verify magic token
        payload = auth_manager.verify_jwt_token(magic_token)
        if not payload or payload.get('role') != 'magic_link':
            raise HTTPException(status_code=401, detail="Invalid magic link")
        
        email = payload['user_id']  # In magic link, user_id contains the email
        
        # Get magic link session
        response = db.tables['magic_link_sessions'].query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        
        if not response['Items']:
            raise HTTPException(status_code=400, detail="Magic link session not found or expired")
        
        session_data = response['Items'][0]
        
        if session_data['used']:
            raise HTTPException(status_code=400, detail="Magic link already used")
        
        # Check if user exists
        user = db.get_user_by_email(email)
        
        if user:
            # User exists, update last login
            db.update_user(user['user_id'], {
                'updated_at': auth_manager.datetime.utcnow().isoformat()
            })
        else:
            # Create new user
            user_id = generate_id('user_')
            user_data = {
                'user_id': user_id,
                'email': email,
                'name': email.split('@')[0],  # Default name from email
                'role': 'customer',
                'created_at': auth_manager.datetime.utcnow().isoformat(),
                'updated_at': auth_manager.datetime.utcnow().isoformat(),
                'is_active': True
            }
            user = db.create_user(user_data)
            
            # Create auth record
            auth_data = {
                'user_id': user_id,
                'provider': 'email',
                'provider_id': email,
                'created_at': auth_manager.datetime.utcnow().isoformat()
            }
            db.tables['user_auth'].put_item(Item=auth_data)
        
        # Mark magic link as used
        db.tables['magic_link_sessions'].update_item(
            Key={'session_id': session_data['session_id']},
            UpdateExpression='SET used = :used',
            ExpressionAttributeValues={':used': True}
        )
        
        # Generate JWT token
        token = auth_manager.generate_jwt_token(user['user_id'], user['role'])
        
        return EmailAuthResponse(
            success=True,
            message="Authentication successful",
            data={
                'token': token,
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            }
        )
        
    except Exception as e:
        return EmailAuthResponse(
            success=False,
            message="Magic link verification failed",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
