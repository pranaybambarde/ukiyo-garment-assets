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
from models import Wishlist, WishlistItem, APIResponse
from utils import generate_id, create_response

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class AddToWishlistRequest(BaseModel):
    product_id: str

class WishlistResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

@app.get("/wishlist", response_model=WishlistResponse)
async def get_wishlist(
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Get user's wishlist"""
    try:
        user_id = None
        if authorization:
            try:
                user_info = auth_manager.extract_user_from_token(authorization)
                user_id = user_info['user_id']
            except:
                pass  # Continue as guest
        
        # Get wishlist
        wishlist = db.get_wishlist(user_id=user_id, session_id=session_id)
        
        if not wishlist:
            return WishlistResponse(
                success=True,
                message="Wishlist is empty",
                data={'wishlist': {'items': []}}
            )
        
        # Get product details for each wishlist item
        items_with_products = []
        for item in wishlist['items']:
            product = db.get_product(item['product_id'])
            if product:
                items_with_products.append({
                    'item_id': item['item_id'],
                    'product_id': item['product_id'],
                    'added_at': item['added_at'],
                    'product': product
                })
        
        return WishlistResponse(
            success=True,
            message="Wishlist retrieved successfully",
            data={
                'wishlist': {
                    'wishlist_id': wishlist['wishlist_id'],
                    'items': items_with_products
                }
            }
        )
        
    except Exception as e:
        return WishlistResponse(
            success=False,
            message="Failed to retrieve wishlist",
            error=str(e)
        )

@app.post("/wishlist/add", response_model=WishlistResponse)
async def add_to_wishlist(
    request: AddToWishlistRequest,
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Add item to wishlist"""
    try:
        user_id = None
        if authorization:
            try:
                user_info = auth_manager.extract_user_from_token(authorization)
                user_id = user_info['user_id']
            except:
                pass  # Continue as guest
        
        # Check if product exists
        product = db.get_product(request.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get or create wishlist
        wishlist = db.get_wishlist(user_id=user_id, session_id=session_id)
        
        if not wishlist:
            # Create new wishlist
            wishlist_id = generate_id('wishlist_')
            wishlist_data = {
                'wishlist_id': wishlist_id,
                'user_id': user_id,
                'session_id': session_id,
                'items': [],
                'created_at': auth_manager.datetime.utcnow().isoformat(),
                'updated_at': auth_manager.datetime.utcnow().isoformat()
            }
            wishlist = db.create_wishlist(wishlist_data)
        
        # Check if item already exists in wishlist
        for item in wishlist['items']:
            if item['product_id'] == request.product_id:
                return WishlistResponse(
                    success=True,
                    message="Item already in wishlist",
                    data={'wishlist': wishlist}
                )
        
        # Add new item
        new_item = {
            'item_id': generate_id('item_'),
            'product_id': request.product_id,
            'added_at': auth_manager.datetime.utcnow().isoformat()
        }
        wishlist['items'].append(new_item)
        
        # Update wishlist
        wishlist['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_wishlist(wishlist['wishlist_id'], wishlist)
        
        return WishlistResponse(
            success=True,
            message="Item added to wishlist successfully",
            data={'wishlist': wishlist}
        )
        
    except Exception as e:
        return WishlistResponse(
            success=False,
            message="Failed to add item to wishlist",
            error=str(e)
        )

@app.delete("/wishlist/remove/{item_id}", response_model=WishlistResponse)
async def remove_wishlist_item(
    item_id: str,
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Remove item from wishlist"""
    try:
        user_id = None
        if authorization:
            try:
                user_info = auth_manager.extract_user_from_token(authorization)
                user_id = user_info['user_id']
            except:
                pass  # Continue as guest
        
        # Get wishlist
        wishlist = db.get_wishlist(user_id=user_id, session_id=session_id)
        if not wishlist:
            raise HTTPException(status_code=404, detail="Wishlist not found")
        
        # Remove item
        item_found = False
        for item in wishlist['items']:
            if item['item_id'] == item_id:
                wishlist['items'].remove(item)
                item_found = True
                break
        
        if not item_found:
            raise HTTPException(status_code=404, detail="Item not found in wishlist")
        
        # Update wishlist
        wishlist['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_wishlist(wishlist['wishlist_id'], wishlist)
        
        return WishlistResponse(
            success=True,
            message="Item removed from wishlist successfully",
            data={'wishlist': wishlist}
        )
        
    except Exception as e:
        return WishlistResponse(
            success=False,
            message="Failed to remove item from wishlist",
            error=str(e)
        )

@app.delete("/wishlist/clear", response_model=WishlistResponse)
async def clear_wishlist(
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Clear all items from wishlist"""
    try:
        user_id = None
        if authorization:
            try:
                user_info = auth_manager.extract_user_from_token(authorization)
                user_id = user_info['user_id']
            except:
                pass  # Continue as guest
        
        # Get wishlist
        wishlist = db.get_wishlist(user_id=user_id, session_id=session_id)
        if not wishlist:
            raise HTTPException(status_code=404, detail="Wishlist not found")
        
        # Clear items
        wishlist['items'] = []
        wishlist['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_wishlist(wishlist['wishlist_id'], wishlist)
        
        return WishlistResponse(
            success=True,
            message="Wishlist cleared successfully",
            data={'wishlist': wishlist}
        )
        
    except Exception as e:
        return WishlistResponse(
            success=False,
            message="Failed to clear wishlist",
            error=str(e)
        )

@app.post("/wishlist/add-all-to-cart", response_model=WishlistResponse)
async def add_all_to_cart(
    authorization: str = Header(...)
):
    """Add all wishlist items to cart"""
    try:
        # Get user info
        user_info = auth_manager.extract_user_from_token(authorization)
        user_id = user_info['user_id']
        
        # Get wishlist
        wishlist = db.get_wishlist(user_id=user_id)
        if not wishlist or not wishlist['items']:
            return WishlistResponse(
                success=True,
                message="Wishlist is empty",
                data={'wishlist': wishlist}
            )
        
        # Get user's cart
        cart = db.get_cart(user_id=user_id)
        if not cart:
            # Create new cart
            cart_id = generate_id('cart_')
            cart_data = {
                'cart_id': cart_id,
                'user_id': user_id,
                'items': [],
                'created_at': auth_manager.datetime.utcnow().isoformat(),
                'updated_at': auth_manager.datetime.utcnow().isoformat()
            }
            cart = db.create_cart(cart_data)
        
        # Add each wishlist item to cart
        added_items = []
        for wishlist_item in wishlist['items']:
            product = db.get_product(wishlist_item['product_id'])
            if product and product['variants']:
                # Add the first available variant
                variant = product['variants'][0]
                
                # Check if item already exists in cart
                existing_item = None
                for cart_item in cart['items']:
                    if (cart_item['product_id'] == wishlist_item['product_id'] and 
                        cart_item['variant_id'] == variant['variant_id']):
                        existing_item = cart_item
                        break
                
                if existing_item:
                    # Update quantity
                    existing_item['quantity'] += 1
                else:
                    # Add new item
                    new_cart_item = {
                        'item_id': generate_id('item_'),
                        'product_id': wishlist_item['product_id'],
                        'variant_id': variant['variant_id'],
                        'quantity': 1,
                        'added_at': auth_manager.datetime.utcnow().isoformat()
                    }
                    cart['items'].append(new_cart_item)
                
                added_items.append(wishlist_item['product_id'])
        
        # Update cart
        cart['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_cart(cart['cart_id'], cart)
        
        return WishlistResponse(
            success=True,
            message=f"Added {len(added_items)} items to cart",
            data={
                'wishlist': wishlist,
                'added_items': added_items
            }
        )
        
    except Exception as e:
        return WishlistResponse(
            success=False,
            message="Failed to add items to cart",
            error=str(e)
        )

@app.post("/wishlist/merge", response_model=WishlistResponse)
async def merge_wishlists(
    guest_session_id: str,
    authorization: str = Header(...)
):
    """Merge guest wishlist with user wishlist after login"""
    try:
        # Get user info
        user_info = auth_manager.extract_user_from_token(authorization)
        user_id = user_info['user_id']
        
        # Get both wishlists
        user_wishlist = db.get_wishlist(user_id=user_id)
        guest_wishlist = db.get_wishlist(session_id=guest_session_id)
        
        if not guest_wishlist:
            # No guest wishlist to merge
            return WishlistResponse(
                success=True,
                message="No guest wishlist to merge",
                data={'wishlist': user_wishlist}
            )
        
        if not user_wishlist:
            # No user wishlist, just transfer guest wishlist
            guest_wishlist['user_id'] = user_id
            guest_wishlist['session_id'] = None
            guest_wishlist['updated_at'] = auth_manager.datetime.utcnow().isoformat()
            db.update_wishlist(guest_wishlist['wishlist_id'], guest_wishlist)
            
            return WishlistResponse(
                success=True,
                message="Guest wishlist transferred to user account",
                data={'wishlist': guest_wishlist}
            )
        
        # Merge wishlists
        merged_items = user_wishlist['items'].copy()
        
        for guest_item in guest_wishlist['items']:
            # Check if item already exists in user wishlist
            existing_item = None
            for item in merged_items:
                if item['product_id'] == guest_item['product_id']:
                    existing_item = item
                    break
            
            if not existing_item:
                # Add new item
                merged_items.append(guest_item)
        
        # Update user wishlist
        user_wishlist['items'] = merged_items
        user_wishlist['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_wishlist(user_wishlist['wishlist_id'], user_wishlist)
        
        # Delete guest wishlist
        db.tables['wishlist'].delete_item(Key={'session_id': guest_session_id})
        
        return WishlistResponse(
            success=True,
            message="Wishlists merged successfully",
            data={'wishlist': user_wishlist}
        )
        
    except Exception as e:
        return WishlistResponse(
            success=False,
            message="Failed to merge wishlists",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
