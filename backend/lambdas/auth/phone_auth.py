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
from utils import generate_id, validate_phone, format_phone, create_response

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class SendOTPRequest(BaseModel):
    phone: str

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str

class PhoneAuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

@app.post("/auth/phone/send-otp", response_model=PhoneAuthResponse)
async def send_otp(request: SendOTPRequest):
    """Send OTP to phone number"""
    try:
        # Validate phone number
        if not validate_phone(request.phone):
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        
        formatted_phone = format_phone(request.phone)
        
        # Generate OTP
        otp = auth_manager.generate_otp()
        
        # Create OTP session
        otp_session = auth_manager.create_otp_session(formatted_phone, otp)
        
        # Store OTP session in DynamoDB (with TTL)
        session_data = {
            'session_id': generate_id('otp_'),
            'phone': formatted_phone,
            'otp_hash': otp_session['otp_hash'],
            'expires_at': otp_session['expires_at'],
            'attempts': 0,
            'ttl': int((auth_manager.datetime.utcnow() + auth_manager.timedelta(minutes=10)).timestamp())
        }
        
        db.tables['otp_sessions'].put_item(Item=session_data)
        
        # TODO: Send OTP via SMS service (Twilio, AWS SNS, etc.)
        # For now, we'll return the OTP in development
        if os.getenv('ENVIRONMENT') == 'development':
            print(f"OTP for {formatted_phone}: {otp}")
        
        return PhoneAuthResponse(
            success=True,
            message="OTP sent successfully",
            data={'phone': formatted_phone}
        )
        
    except Exception as e:
        return PhoneAuthResponse(
            success=False,
            message="Failed to send OTP",
            error=str(e)
        )

@app.post("/auth/phone/verify-otp", response_model=PhoneAuthResponse)
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and authenticate user"""
    try:
        # Validate phone number
        if not validate_phone(request.phone):
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        
        formatted_phone = format_phone(request.phone)
        
        # Get OTP session
        response = db.tables['otp_sessions'].query(
            IndexName='phone-index',
            KeyConditionExpression='phone = :phone',
            ExpressionAttributeValues={':phone': formatted_phone}
        )
        
        if not response['Items']:
            raise HTTPException(status_code=400, detail="OTP session not found or expired")
        
        session_data = response['Items'][0]
        
        # Verify OTP
        if not auth_manager.verify_otp_session(session_data, request.otp):
            # Increment attempts
            db.tables['otp_sessions'].update_item(
                Key={'session_id': session_data['session_id']},
                UpdateExpression='SET attempts = attempts + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # Check if user exists
        user = db.get_user_by_phone(formatted_phone)
        
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
                'phone': formatted_phone,
                'name': f"User {formatted_phone[-4:]}",  # Default name
                'role': 'customer',
                'created_at': auth_manager.datetime.utcnow().isoformat(),
                'updated_at': auth_manager.datetime.utcnow().isoformat(),
                'is_active': True
            }
            user = db.create_user(user_data)
            
            # Create auth record
            auth_data = {
                'user_id': user_id,
                'provider': 'phone',
                'provider_id': formatted_phone,
                'created_at': auth_manager.datetime.utcnow().isoformat()
            }
            db.tables['user_auth'].put_item(Item=auth_data)
        
        # Generate JWT token
        token = auth_manager.generate_jwt_token(user['user_id'], user['role'])
        
        # Delete OTP session
        db.tables['otp_sessions'].delete_item(
            Key={'session_id': session_data['session_id']}
        )
        
        return PhoneAuthResponse(
            success=True,
            message="Authentication successful",
            data={
                'token': token,
                'user': {
                    'user_id': user['user_id'],
                    'phone': user['phone'],
                    'name': user['name'],
                    'role': user['role']
                }
            }
        )
        
    except Exception as e:
        return PhoneAuthResponse(
            success=False,
            message="OTP verification failed",
            error=str(e)
        )

@app.post("/auth/phone/resend-otp", response_model=PhoneAuthResponse)
async def resend_otp(request: SendOTPRequest):
    """Resend OTP to phone number"""
    try:
        # Validate phone number
        if not validate_phone(request.phone):
            raise HTTPException(status_code=400, detail="Invalid phone number format")
        
        formatted_phone = format_phone(request.phone)
        
        # Check if there's an existing session
        response = db.tables['otp_sessions'].query(
            IndexName='phone-index',
            KeyConditionExpression='phone = :phone',
            ExpressionAttributeValues={':phone': formatted_phone}
        )
        
        if response['Items']:
            # Delete existing session
            db.tables['otp_sessions'].delete_item(
                Key={'session_id': response['Items'][0]['session_id']}
            )
        
        # Send new OTP
        return await send_otp(request)
        
    except Exception as e:
        return PhoneAuthResponse(
            success=False,
            message="Failed to resend OTP",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
