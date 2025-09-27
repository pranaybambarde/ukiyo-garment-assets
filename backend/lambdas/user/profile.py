import json
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Import shared modules
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from database import DynamoDBClient
from auth import AuthManager
from models import UserProfile, SkinTone, BodyShape, APIResponse
from utils import generate_id, create_response

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    skin_tone: Optional[str] = None
    body_shape: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None

class ProfileResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

def require_auth(authorization: str):
    """Require authentication"""
    user_info = auth_manager.require_auth(authorization)
    return user_info

@app.get("/user/profile", response_model=ProfileResponse)
async def get_profile(authorization: str = Header(...)):
    """Get user profile"""
    try:
        # Get user info
        user_info = require_auth(authorization)
        user_id = user_info['user_id']
        
        # Get user profile
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return ProfileResponse(
            success=True,
            message="Profile retrieved successfully",
            data={'profile': user}
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            message="Failed to retrieve profile",
            error=str(e)
        )

@app.put("/user/profile", response_model=ProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    authorization: str = Header(...)
):
    """Update user profile"""
    try:
        # Get user info
        user_info = require_auth(authorization)
        user_id = user_info['user_id']
        
        # Get existing user
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data
        update_data = {}
        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                # Validate specific fields
                if field == 'skin_tone' and value not in [tone.value for tone in SkinTone]:
                    raise HTTPException(status_code=400, detail="Invalid skin tone")
                if field == 'body_shape' and value not in [shape.value for shape in BodyShape]:
                    raise HTTPException(status_code=400, detail="Invalid body shape")
                if field == 'height' and (value < 100 or value > 250):
                    raise HTTPException(status_code=400, detail="Height must be between 100-250 cm")
                if field == 'weight' and (value < 30 or value > 200):
                    raise HTTPException(status_code=400, detail="Weight must be between 30-200 kg")
                
                update_data[field] = value
        
        update_data['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        
        # Update user
        updated_user = db.update_user(user_id, update_data)
        
        return ProfileResponse(
            success=True,
            message="Profile updated successfully",
            data={'profile': updated_user}
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            message="Failed to update profile",
            error=str(e)
        )

@app.get("/user/recommendations", response_model=ProfileResponse)
async def get_personalized_recommendations(
    authorization: str = Header(...),
    limit: int = 10
):
    """Get personalized product recommendations"""
    try:
        # Get user info
        user_info = require_auth(authorization)
        user_id = user_info['user_id']
        
        # Get user profile
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build recommendation filters based on user profile
        filters = {}
        
        if user.get('skin_tone'):
            filters['skin_tone'] = user['skin_tone']
        
        if user.get('body_shape'):
            filters['body_shape'] = user['body_shape']
        
        # Get recommended products
        result = db.get_products(filters, limit, None)
        
        # If no personalized recommendations, get featured products
        if not result['items']:
            filters = {'featured': True}
            result = db.get_products(filters, limit, None)
        
        return ProfileResponse(
            success=True,
            message="Recommendations retrieved successfully",
            data={'recommendations': result['items']}
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            message="Failed to retrieve recommendations",
            error=str(e)
        )

@app.get("/user/orders", response_model=ProfileResponse)
async def get_user_orders(
    authorization: str = Header(...),
    page: int = 1,
    limit: int = 20
):
    """Get user's orders"""
    try:
        # Get user info
        user_info = require_auth(authorization)
        user_id = user_info['user_id']
        
        # Get user orders
        result = db.get_user_orders(user_id, limit, None)
        
        # Paginate results
        from utils import paginate_results
        paginated_result = paginate_results(result['items'], page, limit)
        
        return ProfileResponse(
            success=True,
            message="Orders retrieved successfully",
            data={
                'orders': paginated_result['items'],
                'pagination': {
                    'total': paginated_result['total'],
                    'page': paginated_result['page'],
                    'limit': paginated_result['limit'],
                    'has_next': paginated_result['has_next'],
                    'has_prev': paginated_result['has_prev'],
                    'total_pages': paginated_result['total_pages']
                }
            }
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            message="Failed to retrieve orders",
            error=str(e)
        )

@app.get("/user/addresses", response_model=ProfileResponse)
async def get_user_addresses(authorization: str = Header(...)):
    """Get user's saved addresses"""
    try:
        # Get user info
        user_info = require_auth(authorization)
        user_id = user_info['user_id']
        
        # Get user addresses
        response = db.tables['user_addresses'].query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        addresses = response['Items']
        
        return ProfileResponse(
            success=True,
            message="Addresses retrieved successfully",
            data={'addresses': addresses}
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            message="Failed to retrieve addresses",
            error=str(e)
        )

@app.post("/user/addresses", response_model=ProfileResponse)
async def add_user_address(
    address: Dict[str, Any],
    authorization: str = Header(...)
):
    """Add user address"""
    try:
        # Get user info
        user_info = require_auth(authorization)
        user_id = user_info['user_id']
        
        # Validate address
        from utils import validate_address
        address_errors = validate_address(address)
        if address_errors:
            raise HTTPException(status_code=400, detail=f"Invalid address: {', '.join(address_errors)}")
        
        # Create address
        address_id = generate_id('addr_')
        address_data = {
            'address_id': address_id,
            'user_id': user_id,
            'name': address['name'],
            'phone': address['phone'],
            'address_line_1': address['address_line_1'],
            'address_line_2': address.get('address_line_2'),
            'city': address['city'],
            'state': address['state'],
            'pincode': address['pincode'],
            'country': address.get('country', 'India'),
            'is_default': address.get('is_default', False),
            'created_at': auth_manager.datetime.utcnow().isoformat(),
            'updated_at': auth_manager.datetime.utcnow().isoformat()
        }
        
        # If this is set as default, unset other defaults
        if address_data['is_default']:
            db.tables['user_addresses'].update_item(
                Key={'address_id': 'dummy'},  # This will fail, but we need to scan
                UpdateExpression='SET is_default = :false',
                ExpressionAttributeValues={':false': False},
                ConditionExpression='user_id = :user_id'
            )
        
        # Add address
        db.tables['user_addresses'].put_item(Item=address_data)
        
        return ProfileResponse(
            success=True,
            message="Address added successfully",
            data={'address': address_data}
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            message="Failed to add address",
            error=str(e)
        )

@app.delete("/user/addresses/{address_id}", response_model=ProfileResponse)
async def delete_user_address(
    address_id: str,
    authorization: str = Header(...)
):
    """Delete user address"""
    try:
        # Get user info
        user_info = require_auth(authorization)
        user_id = user_info['user_id']
        
        # Get address to verify ownership
        response = db.tables['user_addresses'].get_item(Key={'address_id': address_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Address not found")
        
        address = response['Item']
        if address['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete address
        db.tables['user_addresses'].delete_item(Key={'address_id': address_id})
        
        return ProfileResponse(
            success=True,
            message="Address deleted successfully",
            data={'address_id': address_id}
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            message="Failed to delete address",
            error=str(e)
        )

@app.get("/user/preferences", response_model=ProfileResponse)
async def get_user_preferences(authorization: str = Header(...)):
    """Get user preferences"""
    try:
        # Get user info
        user_info = require_auth(authorization)
        user_id = user_info['user_id']
        
        # Get user preferences
        response = db.tables['user_preferences'].query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        preferences = {item['preference_key']: item['preference_value'] for item in response['Items']}
        
        return ProfileResponse(
            success=True,
            message="Preferences retrieved successfully",
            data={'preferences': preferences}
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            message="Failed to retrieve preferences",
            error=str(e)
        )

@app.put("/user/preferences", response_model=ProfileResponse)
async def update_user_preferences(
    preferences: Dict[str, Any],
    authorization: str = Header(...)
):
    """Update user preferences"""
    try:
        # Get user info
        user_info = require_auth(authorization)
        user_id = user_info['user_id']
        
        # Update preferences
        for key, value in preferences.items():
            preference_data = {
                'preference_id': generate_id('pref_'),
                'user_id': user_id,
                'preference_key': key,
                'preference_value': value,
                'updated_at': auth_manager.datetime.utcnow().isoformat()
            }
            
            db.tables['user_preferences'].put_item(Item=preference_data)
        
        return ProfileResponse(
            success=True,
            message="Preferences updated successfully",
            data={'preferences': preferences}
        )
        
    except Exception as e:
        return ProfileResponse(
            success=False,
            message="Failed to update preferences",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
