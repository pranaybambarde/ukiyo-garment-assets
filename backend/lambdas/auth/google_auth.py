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

class GoogleAuthRequest(BaseModel):
    token: str

class GoogleAuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

@app.post("/auth/google", response_model=GoogleAuthResponse)
async def google_auth(request: GoogleAuthRequest):
    """Authenticate user with Google OAuth token"""
    try:
        # Verify Google token
        google_user = await auth_manager.verify_google_token(request.token)
        if not google_user:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        
        # Check if user exists
        user = db.get_user_by_email(google_user['email'])
        
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
                'email': google_user['email'],
                'name': google_user['name'],
                'role': 'customer',
                'created_at': auth_manager.datetime.utcnow().isoformat(),
                'updated_at': auth_manager.datetime.utcnow().isoformat(),
                'is_active': True
            }
            user = db.create_user(user_data)
            
            # Create auth record
            auth_data = {
                'user_id': user_id,
                'provider': 'google',
                'provider_id': google_user['provider_id'],
                'created_at': auth_manager.datetime.utcnow().isoformat()
            }
            db.tables['user_auth'].put_item(Item=auth_data)
        
        # Generate JWT token
        token = auth_manager.generate_jwt_token(user['user_id'], user['role'])
        
        return GoogleAuthResponse(
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
        return GoogleAuthResponse(
            success=False,
            message="Authentication failed",
            error=str(e)
        )

@app.post("/auth/google/verify")
async def verify_google_token(request: GoogleAuthRequest):
    """Verify Google token without creating session"""
    try:
        google_user = await auth_manager.verify_google_token(request.token)
        if not google_user:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        
        return create_response(
            success=True,
            message="Token verified successfully",
            data={'email': google_user['email'], 'name': google_user['name']}
        )
        
    except Exception as e:
        return create_response(
            success=False,
            message="Token verification failed",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
