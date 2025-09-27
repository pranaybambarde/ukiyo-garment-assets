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
from models import Cart, CartItem, APIResponse
from utils import generate_id, create_response, calculate_order_summary

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class AddToCartRequest(BaseModel):
    product_id: str
    variant_id: str
    quantity: int = 1

class UpdateCartItemRequest(BaseModel):
    item_id: str
    quantity: int

class CartResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

@app.get("/cart", response_model=CartResponse)
async def get_cart(
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Get user's cart"""
    try:
        user_id = None
        if authorization:
            try:
                user_info = auth_manager.extract_user_from_token(authorization)
                user_id = user_info['user_id']
            except:
                pass  # Continue as guest
        
        # Get cart
        cart = db.get_cart(user_id=user_id, session_id=session_id)
        
        if not cart:
            return CartResponse(
                success=True,
                message="Cart is empty",
                data={'cart': {'items': [], 'summary': {'subtotal': 0, 'tax': 0, 'shipping': 0, 'total': 0}}}
            )
        
        # Calculate summary
        summary = calculate_order_summary(cart['items'])
        
        return CartResponse(
            success=True,
            message="Cart retrieved successfully",
            data={
                'cart': {
                    'cart_id': cart['cart_id'],
                    'items': cart['items'],
                    'summary': summary
                }
            }
        )
        
    except Exception as e:
        return CartResponse(
            success=False,
            message="Failed to retrieve cart",
            error=str(e)
        )

@app.post("/cart/add", response_model=CartResponse)
async def add_to_cart(
    request: AddToCartRequest,
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Add item to cart"""
    try:
        user_id = None
        if authorization:
            try:
                user_info = auth_manager.extract_user_from_token(authorization)
                user_id = user_info['user_id']
            except:
                pass  # Continue as guest
        
        # Get product details
        product = db.get_product(request.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Find variant
        variant = None
        for v in product['variants']:
            if v['variant_id'] == request.variant_id:
                variant = v
                break
        
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        
        if variant['stock_quantity'] < request.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        # Get or create cart
        cart = db.get_cart(user_id=user_id, session_id=session_id)
        
        if not cart:
            # Create new cart
            cart_id = generate_id('cart_')
            cart_data = {
                'cart_id': cart_id,
                'user_id': user_id,
                'session_id': session_id,
                'items': [],
                'created_at': auth_manager.datetime.utcnow().isoformat(),
                'updated_at': auth_manager.datetime.utcnow().isoformat()
            }
            cart = db.create_cart(cart_data)
        
        # Check if item already exists in cart
        existing_item = None
        for item in cart['items']:
            if item['product_id'] == request.product_id and item['variant_id'] == request.variant_id:
                existing_item = item
                break
        
        if existing_item:
            # Update quantity
            existing_item['quantity'] += request.quantity
        else:
            # Add new item
            new_item = {
                'item_id': generate_id('item_'),
                'product_id': request.product_id,
                'variant_id': request.variant_id,
                'quantity': request.quantity,
                'added_at': auth_manager.datetime.utcnow().isoformat()
            }
            cart['items'].append(new_item)
        
        # Update cart
        cart['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_cart(cart['cart_id'], cart)
        
        # Calculate summary
        summary = calculate_order_summary(cart['items'])
        
        return CartResponse(
            success=True,
            message="Item added to cart successfully",
            data={
                'cart': {
                    'cart_id': cart['cart_id'],
                    'items': cart['items'],
                    'summary': summary
                }
            }
        )
        
    except Exception as e:
        return CartResponse(
            success=False,
            message="Failed to add item to cart",
            error=str(e)
        )

@app.put("/cart/update", response_model=CartResponse)
async def update_cart_item(
    request: UpdateCartItemRequest,
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Update cart item quantity"""
    try:
        user_id = None
        if authorization:
            try:
                user_info = auth_manager.extract_user_from_token(authorization)
                user_id = user_info['user_id']
            except:
                pass  # Continue as guest
        
        # Get cart
        cart = db.get_cart(user_id=user_id, session_id=session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        # Find and update item
        item_found = False
        for item in cart['items']:
            if item['item_id'] == request.item_id:
                if request.quantity <= 0:
                    # Remove item
                    cart['items'].remove(item)
                else:
                    # Update quantity
                    item['quantity'] = request.quantity
                item_found = True
                break
        
        if not item_found:
            raise HTTPException(status_code=404, detail="Item not found in cart")
        
        # Update cart
        cart['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_cart(cart['cart_id'], cart)
        
        # Calculate summary
        summary = calculate_order_summary(cart['items'])
        
        return CartResponse(
            success=True,
            message="Cart updated successfully",
            data={
                'cart': {
                    'cart_id': cart['cart_id'],
                    'items': cart['items'],
                    'summary': summary
                }
            }
        )
        
    except Exception as e:
        return CartResponse(
            success=False,
            message="Failed to update cart",
            error=str(e)
        )

@app.delete("/cart/remove/{item_id}", response_model=CartResponse)
async def remove_cart_item(
    item_id: str,
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Remove item from cart"""
    try:
        user_id = None
        if authorization:
            try:
                user_info = auth_manager.extract_user_from_token(authorization)
                user_id = user_info['user_id']
            except:
                pass  # Continue as guest
        
        # Get cart
        cart = db.get_cart(user_id=user_id, session_id=session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        # Remove item
        item_found = False
        for item in cart['items']:
            if item['item_id'] == item_id:
                cart['items'].remove(item)
                item_found = True
                break
        
        if not item_found:
            raise HTTPException(status_code=404, detail="Item not found in cart")
        
        # Update cart
        cart['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_cart(cart['cart_id'], cart)
        
        # Calculate summary
        summary = calculate_order_summary(cart['items'])
        
        return CartResponse(
            success=True,
            message="Item removed from cart successfully",
            data={
                'cart': {
                    'cart_id': cart['cart_id'],
                    'items': cart['items'],
                    'summary': summary
                }
            }
        )
        
    except Exception as e:
        return CartResponse(
            success=False,
            message="Failed to remove item from cart",
            error=str(e)
        )

@app.delete("/cart/clear", response_model=CartResponse)
async def clear_cart(
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Clear all items from cart"""
    try:
        user_id = None
        if authorization:
            try:
                user_info = auth_manager.extract_user_from_token(authorization)
                user_id = user_info['user_id']
            except:
                pass  # Continue as guest
        
        # Get cart
        cart = db.get_cart(user_id=user_id, session_id=session_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        # Clear items
        cart['items'] = []
        cart['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_cart(cart['cart_id'], cart)
        
        return CartResponse(
            success=True,
            message="Cart cleared successfully",
            data={
                'cart': {
                    'cart_id': cart['cart_id'],
                    'items': [],
                    'summary': {'subtotal': 0, 'tax': 0, 'shipping': 0, 'total': 0}
                }
            }
        )
        
    except Exception as e:
        return CartResponse(
            success=False,
            message="Failed to clear cart",
            error=str(e)
        )

@app.post("/cart/merge", response_model=CartResponse)
async def merge_carts(
    guest_session_id: str,
    authorization: str = Header(...)
):
    """Merge guest cart with user cart after login"""
    try:
        # Get user info
        user_info = auth_manager.extract_user_from_token(authorization)
        user_id = user_info['user_id']
        
        # Get both carts
        user_cart = db.get_cart(user_id=user_id)
        guest_cart = db.get_cart(session_id=guest_session_id)
        
        if not guest_cart:
            # No guest cart to merge
            return CartResponse(
                success=True,
                message="No guest cart to merge",
                data={'cart': user_cart}
            )
        
        if not user_cart:
            # No user cart, just transfer guest cart
            guest_cart['user_id'] = user_id
            guest_cart['session_id'] = None
            guest_cart['updated_at'] = auth_manager.datetime.utcnow().isoformat()
            db.update_cart(guest_cart['cart_id'], guest_cart)
            
            return CartResponse(
                success=True,
                message="Guest cart transferred to user account",
                data={'cart': guest_cart}
            )
        
        # Merge carts
        merged_items = user_cart['items'].copy()
        
        for guest_item in guest_cart['items']:
            # Check if item already exists in user cart
            existing_item = None
            for item in merged_items:
                if (item['product_id'] == guest_item['product_id'] and 
                    item['variant_id'] == guest_item['variant_id']):
                    existing_item = item
                    break
            
            if existing_item:
                # Update quantity
                existing_item['quantity'] += guest_item['quantity']
            else:
                # Add new item
                merged_items.append(guest_item)
        
        # Update user cart
        user_cart['items'] = merged_items
        user_cart['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_cart(user_cart['cart_id'], user_cart)
        
        # Delete guest cart
        db.tables['cart'].delete_item(Key={'session_id': guest_session_id})
        
        # Calculate summary
        summary = calculate_order_summary(user_cart['items'])
        
        return CartResponse(
            success=True,
            message="Carts merged successfully",
            data={
                'cart': {
                    'cart_id': user_cart['cart_id'],
                    'items': user_cart['items'],
                    'summary': summary
                }
            }
        )
        
    except Exception as e:
        return CartResponse(
            success=False,
            message="Failed to merge carts",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
