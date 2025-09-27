import json
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Import shared modules
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from database import DynamoDBClient
from auth import AuthManager
from models import ReturnRequest, ReturnStatus, APIResponse
from utils import generate_id, create_response

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class UpdateReturnRequest(BaseModel):
    status: str
    admin_notes: Optional[str] = None

class AdminResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

def require_admin(authorization: str):
    """Require admin authentication"""
    user_info = auth_manager.require_admin(authorization)
    return user_info

@app.get("/admin/returns", response_model=AdminResponse)
async def get_returns(
    authorization: str = Header(...),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get all return requests"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Build filter expression
        filter_expression = None
        expression_values = {}
        
        if status:
            filter_expression = '#status = :status'
            expression_values[':status'] = status
        
        # Get returns
        if filter_expression:
            response = db.tables['returns'].scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames={'#status': 'status'}
            )
        else:
            response = db.tables['returns'].scan()
        
        returns = response['Items']
        
        # Paginate results
        from utils import paginate_results
        paginated_result = paginate_results(returns, page, limit)
        
        # Get order details for each return
        returns_with_details = []
        for return_request in paginated_result['items']:
            order = db.get_order(return_request['order_id'])
            if order:
                return_request['order_details'] = order
            returns_with_details.append(return_request)
        
        return AdminResponse(
            success=True,
            message="Returns retrieved successfully",
            data={
                'returns': returns_with_details,
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
        return AdminResponse(
            success=False,
            message="Failed to retrieve returns",
            error=str(e)
        )

@app.get("/admin/returns/{return_id}", response_model=AdminResponse)
async def get_return_details(
    return_id: str,
    authorization: str = Header(...)
):
    """Get return request details"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get return request
        response = db.tables['returns'].get_item(Key={'return_id': return_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Return request not found")
        
        return_request = response['Item']
        
        # Get order details
        order = db.get_order(return_request['order_id'])
        if order:
            return_request['order_details'] = order
        
        # Get user details
        if return_request['user_id']:
            user = db.get_user(return_request['user_id'])
            if user:
                return_request['user_details'] = user
        
        return AdminResponse(
            success=True,
            message="Return details retrieved successfully",
            data={'return': return_request}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to retrieve return details",
            error=str(e)
        )

@app.put("/admin/returns/{return_id}", response_model=AdminResponse)
async def update_return(
    return_id: str,
    request: UpdateReturnRequest,
    authorization: str = Header(...)
):
    """Update return request status"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get existing return request
        response = db.tables['returns'].get_item(Key={'return_id': return_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Return request not found")
        
        return_request = response['Item']
        
        # Validate status
        valid_statuses = [status.value for status in ReturnStatus]
        if request.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # Update return request
        update_data = {
            'status': request.status,
            'updated_at': auth_manager.datetime.utcnow().isoformat()
        }
        
        if request.admin_notes:
            update_data['admin_notes'] = request.admin_notes
        
        # Build update expression
        update_expression = "SET "
        expression_values = {}
        expression_names = {}
        
        for key, value in update_data.items():
            update_expression += f"#{key} = :{key}, "
            expression_values[f":{key}"] = value
            expression_names[f"#{key}"] = key
        
        # Remove trailing comma
        update_expression = update_expression.rstrip(", ")
        
        # Update in database
        db.tables['returns'].update_item(
            Key={'return_id': return_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
            ReturnValues='ALL_NEW'
        )
        
        # If approved, process the return
        if request.status == ReturnStatus.APPROVED.value:
            await process_return(return_id, return_request)
        
        return AdminResponse(
            success=True,
            message="Return request updated successfully",
            data={'return_id': return_id, 'status': request.status}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to update return request",
            error=str(e)
        )

async def process_return(return_id: str, return_request: Dict[str, Any]):
    """Process approved return"""
    try:
        # Get order details
        order = db.get_order(return_request['order_id'])
        if not order:
            return
        
        # Restore product stock
        for item in return_request['items']:
            product = db.get_product(item['product_id'])
            if product:
                for variant in product['variants']:
                    if variant['variant_id'] == item['variant_id']:
                        variant['stock_quantity'] += item['quantity']
                        break
                
                # Update product
                db.update_product(item['product_id'], {'variants': product['variants']})
        
        # TODO: Process refund
        # TODO: Send return confirmation email
        # TODO: Generate return shipping label
        
        # Update return status to processed
        db.tables['returns'].update_item(
            Key={'return_id': return_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':status': ReturnStatus.PROCESSED.value,
                ':updated_at': auth_manager.datetime.utcnow().isoformat()
            },
            ExpressionAttributeNames={'#status': 'status'}
        )
        
    except Exception as e:
        print(f"Error processing return {return_id}: {e}")

@app.get("/admin/returns/analytics", response_model=AdminResponse)
async def get_returns_analytics(
    authorization: str = Header(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get returns analytics"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Parse dates
        from datetime import datetime, timedelta
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = datetime.utcnow()
        
        # Get returns for the period
        response = db.tables['returns'].scan(
            FilterExpression='created_at BETWEEN :start_date AND :end_date',
            ExpressionAttributeValues={
                ':start_date': start_date.isoformat(),
                ':end_date': end_date.isoformat()
            }
        )
        
        returns = response['Items']
        
        # Calculate analytics
        total_returns = len(returns)
        returns_by_status = {}
        returns_by_reason = {}
        
        for return_request in returns:
            # Count by status
            status = return_request['status']
            returns_by_status[status] = returns_by_status.get(status, 0) + 1
            
            # Count by reason
            reason = return_request['reason']
            returns_by_reason[reason] = returns_by_reason.get(reason, 0) + 1
        
        # Calculate return rate (simplified)
        # Get total orders for the period
        orders_response = db.tables['orders'].scan(
            FilterExpression='created_at BETWEEN :start_date AND :end_date',
            ExpressionAttributeValues={
                ':start_date': start_date.isoformat(),
                ':end_date': end_date.isoformat()
            }
        )
        
        total_orders = len(orders_response['Items'])
        return_rate = (total_returns / total_orders * 100) if total_orders > 0 else 0
        
        analytics = {
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'overview': {
                'total_returns': total_returns,
                'total_orders': total_orders,
                'return_rate': round(return_rate, 2)
            },
            'returns_by_status': returns_by_status,
            'returns_by_reason': returns_by_reason
        }
        
        return AdminResponse(
            success=True,
            message="Returns analytics retrieved successfully",
            data={'analytics': analytics}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to retrieve returns analytics",
            error=str(e)
        )

@app.post("/admin/returns/{return_id}/refund", response_model=AdminResponse)
async def process_refund(
    return_id: str,
    refund_amount: float,
    authorization: str = Header(...)
):
    """Process refund for return"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get return request
        response = db.tables['returns'].get_item(Key={'return_id': return_id})
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Return request not found")
        
        return_request = response['Item']
        
        # Check if return is approved
        if return_request['status'] != ReturnStatus.APPROVED.value:
            raise HTTPException(status_code=400, detail="Return must be approved before processing refund")
        
        # TODO: Process refund with payment gateway
        # For now, we'll just update the return status
        
        # Update return with refund details
        db.tables['returns'].update_item(
            Key={'return_id': return_id},
            UpdateExpression='SET refund_amount = :refund_amount, refund_processed_at = :refund_processed_at, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':refund_amount': refund_amount,
                ':refund_processed_at': auth_manager.datetime.utcnow().isoformat(),
                ':updated_at': auth_manager.datetime.utcnow().isoformat()
            }
        )
        
        return AdminResponse(
            success=True,
            message="Refund processed successfully",
            data={'return_id': return_id, 'refund_amount': refund_amount}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to process refund",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
