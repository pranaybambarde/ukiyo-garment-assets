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
from models import Order, OrderItem, ShippingAddress, OrderStatus, APIResponse
from utils import generate_id, create_response, calculate_order_summary, validate_address

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class CheckoutRequest(BaseModel):
    email: str
    shipping_address: ShippingAddress
    payment_method: str = "razorpay"  # Default payment method

class CheckoutResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

@app.post("/checkout/create-order", response_model=CheckoutResponse)
async def create_order(
    request: CheckoutRequest,
    authorization: Optional[str] = Header(None),
    session_id: Optional[str] = Header(None)
):
    """Create order from cart"""
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
        if not cart or not cart['items']:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Validate shipping address
        address_errors = validate_address(request.shipping_address.dict())
        if address_errors:
            raise HTTPException(status_code=400, detail=f"Invalid address: {', '.join(address_errors)}")
        
        # Validate email
        if not request.email or '@' not in request.email:
            raise HTTPException(status_code=400, detail="Valid email is required")
        
        # Prepare order items
        order_items = []
        for cart_item in cart['items']:
            # Get product details
            product = db.get_product(cart_item['product_id'])
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {cart_item['product_id']} not found")
            
            # Find variant
            variant = None
            for v in product['variants']:
                if v['variant_id'] == cart_item['variant_id']:
                    variant = v
                    break
            
            if not variant:
                raise HTTPException(status_code=404, detail=f"Product variant {cart_item['variant_id']} not found")
            
            # Check stock
            if variant['stock_quantity'] < cart_item['quantity']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for {product['name']} - {variant['color']} {variant['size']}"
                )
            
            # Create order item
            order_item = {
                'product_id': cart_item['product_id'],
                'variant_id': cart_item['variant_id'],
                'quantity': cart_item['quantity'],
                'price': variant['price'],
                'product_name': product['name'],
                'variant_details': f"{variant['color']} - {variant['size']}"
            }
            order_items.append(order_item)
        
        # Calculate order summary
        summary = calculate_order_summary(order_items)
        
        # Create order
        order_id = generate_id('order_')
        order_data = {
            'order_id': order_id,
            'user_id': user_id,
            'email': request.email,
            'items': order_items,
            'shipping_address': request.shipping_address.dict(),
            'subtotal': summary['subtotal'],
            'shipping_cost': summary['shipping'],
            'tax': summary['tax'],
            'total': summary['total'],
            'status': OrderStatus.PENDING.value,
            'created_at': auth_manager.datetime.utcnow().isoformat(),
            'updated_at': auth_manager.datetime.utcnow().isoformat()
        }
        
        order = db.create_order(order_data)
        
        # Clear cart
        cart['items'] = []
        cart['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        db.update_cart(cart['cart_id'], cart)
        
        # TODO: Initialize payment with Razorpay
        # For now, we'll return the order with payment details
        payment_data = {
            'order_id': order_id,
            'amount': int(summary['total'] * 100),  # Convert to paise
            'currency': 'INR',
            'payment_method': request.payment_method
        }
        
        return CheckoutResponse(
            success=True,
            message="Order created successfully",
            data={
                'order': order,
                'payment': payment_data
            }
        )
        
    except Exception as e:
        return CheckoutResponse(
            success=False,
            message="Failed to create order",
            error=str(e)
        )

@app.post("/checkout/confirm-payment", response_model=CheckoutResponse)
async def confirm_payment(
    order_id: str,
    payment_id: str,
    authorization: Optional[str] = Header(None)
):
    """Confirm payment and update order status"""
    try:
        # Get order
        order = db.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update order with payment details
        order['payment_id'] = payment_id
        order['status'] = OrderStatus.CONFIRMED.value
        order['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        
        # Update order in database
        db.tables['orders'].put_item(Item=order)
        
        # Update product stock
        for item in order['items']:
            product = db.get_product(item['product_id'])
            if product:
                for variant in product['variants']:
                    if variant['variant_id'] == item['variant_id']:
                        variant['stock_quantity'] -= item['quantity']
                        break
                
                # Update product
                db.update_product(item['product_id'], {'variants': product['variants']})
        
        # TODO: Send confirmation email
        # TODO: Generate tracking number
        # TODO: Notify inventory management
        
        return CheckoutResponse(
            success=True,
            message="Payment confirmed successfully",
            data={'order': order}
        )
        
    except Exception as e:
        return CheckoutResponse(
            success=False,
            message="Failed to confirm payment",
            error=str(e)
        )

@app.get("/orders/{order_id}", response_model=CheckoutResponse)
async def get_order(
    order_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get order details"""
    try:
        # Get order
        order = db.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if user has access to this order
        if authorization:
            user_info = auth_manager.extract_user_from_token(authorization)
            if order['user_id'] and order['user_id'] != user_info['user_id']:
                raise HTTPException(status_code=403, detail="Access denied")
        elif order['user_id']:
            # Order belongs to a user but no auth provided
            raise HTTPException(status_code=401, detail="Authentication required")
        
        return CheckoutResponse(
            success=True,
            message="Order retrieved successfully",
            data={'order': order}
        )
        
    except Exception as e:
        return CheckoutResponse(
            success=False,
            message="Failed to retrieve order",
            error=str(e)
        )

@app.get("/orders", response_model=CheckoutResponse)
async def get_user_orders(
    authorization: str = Header(...),
    page: int = 1,
    limit: int = 20
):
    """Get user's orders"""
    try:
        # Get user info
        user_info = auth_manager.extract_user_from_token(authorization)
        user_id = user_info['user_id']
        
        # Get user orders
        result = db.get_user_orders(user_id, limit, None)
        
        # Paginate results
        from utils import paginate_results
        paginated_result = paginate_results(result['items'], page, limit)
        
        return CheckoutResponse(
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
        return CheckoutResponse(
            success=False,
            message="Failed to retrieve orders",
            error=str(e)
        )

@app.post("/orders/{order_id}/cancel", response_model=CheckoutResponse)
async def cancel_order(
    order_id: str,
    authorization: str = Header(...)
):
    """Cancel order"""
    try:
        # Get user info
        user_info = auth_manager.extract_user_from_token(authorization)
        user_id = user_info['user_id']
        
        # Get order
        order = db.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if user owns this order
        if order['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if order can be cancelled
        if order['status'] not in [OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value]:
            raise HTTPException(status_code=400, detail="Order cannot be cancelled")
        
        # Update order status
        order['status'] = OrderStatus.CANCELLED.value
        order['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        
        # Update order in database
        db.tables['orders'].put_item(Item=order)
        
        # Restore product stock
        for item in order['items']:
            product = db.get_product(item['product_id'])
            if product:
                for variant in product['variants']:
                    if variant['variant_id'] == item['variant_id']:
                        variant['stock_quantity'] += item['quantity']
                        break
                
                # Update product
                db.update_product(item['product_id'], {'variants': product['variants']})
        
        # TODO: Process refund if payment was made
        # TODO: Send cancellation email
        
        return CheckoutResponse(
            success=True,
            message="Order cancelled successfully",
            data={'order': order}
        )
        
    except Exception as e:
        return CheckoutResponse(
            success=False,
            message="Failed to cancel order",
            error=str(e)
        )

@app.post("/orders/{order_id}/return", response_model=CheckoutResponse)
async def initiate_return(
    order_id: str,
    items: List[Dict[str, Any]],
    reason: str,
    authorization: str = Header(...)
):
    """Initiate return for order items"""
    try:
        # Get user info
        user_info = auth_manager.extract_user_from_token(authorization)
        user_id = user_info['user_id']
        
        # Get order
        order = db.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if user owns this order
        if order['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if order is eligible for return
        if order['status'] != OrderStatus.DELIVERED.value:
            raise HTTPException(status_code=400, detail="Order is not eligible for return")
        
        # Create return request
        return_id = generate_id('return_')
        return_data = {
            'return_id': return_id,
            'order_id': order_id,
            'user_id': user_id,
            'items': items,
            'reason': reason,
            'status': 'pending',
            'created_at': auth_manager.datetime.utcnow().isoformat(),
            'updated_at': auth_manager.datetime.utcnow().isoformat()
        }
        
        db.tables['returns'].put_item(Item=return_data)
        
        # TODO: Notify admin about return request
        # TODO: Send return confirmation email
        
        return CheckoutResponse(
            success=True,
            message="Return request submitted successfully",
            data={'return': return_data}
        )
        
    except Exception as e:
        return CheckoutResponse(
            success=False,
            message="Failed to initiate return",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
