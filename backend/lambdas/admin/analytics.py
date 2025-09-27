import json
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

# Import shared modules
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from database import DynamoDBClient
from auth import AuthManager
from models import APIResponse
from utils import generate_id, create_response, create_analytics_record

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class AnalyticsResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

def require_admin(authorization: str):
    """Require admin authentication"""
    user_info = auth_manager.require_admin(authorization)
    return user_info

@app.get("/admin/analytics/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(
    authorization: str = Header(...),
    period: str = Query("7d", regex="^(1d|7d|30d|90d|1y)$")
):
    """Get dashboard analytics"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Calculate date range
        end_date = datetime.utcnow()
        if period == "1d":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        else:  # 1y
            start_date = end_date - timedelta(days=365)
        
        # Get orders for the period
        orders_response = db.tables['orders'].scan(
            FilterExpression='created_at BETWEEN :start_date AND :end_date',
            ExpressionAttributeValues={
                ':start_date': start_date.isoformat(),
                ':end_date': end_date.isoformat()
            }
        )
        
        orders = orders_response['Items']
        
        # Calculate metrics
        total_orders = len(orders)
        total_revenue = sum(float(order['total']) for order in orders)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Orders by status
        orders_by_status = {}
        for order in orders:
            status = order['status']
            orders_by_status[status] = orders_by_status.get(status, 0) + 1
        
        # Revenue by day
        revenue_by_day = {}
        for order in orders:
            date = order['created_at'][:10]  # YYYY-MM-DD
            revenue_by_day[date] = revenue_by_day.get(date, 0) + float(order['total'])
        
        # Get user registrations
        users_response = db.tables['users'].scan(
            FilterExpression='created_at BETWEEN :start_date AND :end_date',
            ExpressionAttributeValues={
                ':start_date': start_date.isoformat(),
                ':end_date': end_date.isoformat()
            }
        )
        
        new_users = len(users_response['Items'])
        
        # Get top products
        product_sales = {}
        for order in orders:
            for item in order['items']:
                product_id = item['product_id']
                quantity = item['quantity']
                product_sales[product_id] = product_sales.get(product_id, 0) + quantity
        
        # Sort products by sales
        top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Get product details for top products
        top_products_with_details = []
        for product_id, sales_count in top_products:
            product = db.get_product(product_id)
            if product:
                top_products_with_details.append({
                    'product_id': product_id,
                    'name': product['name'],
                    'sales_count': sales_count
                })
        
        analytics = {
            'period': period,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'overview': {
                'total_orders': total_orders,
                'total_revenue': round(total_revenue, 2),
                'average_order_value': round(average_order_value, 2),
                'new_users': new_users
            },
            'orders_by_status': orders_by_status,
            'revenue_by_day': revenue_by_day,
            'top_products': top_products_with_details
        }
        
        return AnalyticsResponse(
            success=True,
            message="Dashboard analytics retrieved successfully",
            data={'analytics': analytics}
        )
        
    except Exception as e:
        return AnalyticsResponse(
            success=False,
            message="Failed to retrieve dashboard analytics",
            error=str(e)
        )

@app.get("/admin/analytics/sales", response_model=AnalyticsResponse)
async def get_sales_analytics(
    authorization: str = Header(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("day", regex="^(day|week|month)$")
):
    """Get sales analytics"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Parse dates
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = datetime.utcnow()
        
        # Get orders for the period
        orders_response = db.tables['orders'].scan(
            FilterExpression='created_at BETWEEN :start_date AND :end_date',
            ExpressionAttributeValues={
                ':start_date': start_date.isoformat(),
                ':end_date': end_date.isoformat()
            }
        )
        
        orders = orders_response['Items']
        
        # Group orders by time period
        sales_by_period = {}
        for order in orders:
            order_date = datetime.fromisoformat(order['created_at'])
            
            if group_by == "day":
                period_key = order_date.strftime("%Y-%m-%d")
            elif group_by == "week":
                # Get week start (Monday)
                week_start = order_date - timedelta(days=order_date.weekday())
                period_key = week_start.strftime("%Y-%W")
            else:  # month
                period_key = order_date.strftime("%Y-%m")
            
            if period_key not in sales_by_period:
                sales_by_period[period_key] = {
                    'orders': 0,
                    'revenue': 0,
                    'items_sold': 0
                }
            
            sales_by_period[period_key]['orders'] += 1
            sales_by_period[period_key]['revenue'] += float(order['total'])
            
            # Count items sold
            for item in order['items']:
                sales_by_period[period_key]['items_sold'] += item['quantity']
        
        # Convert to list and sort by period
        sales_data = []
        for period, data in sorted(sales_by_period.items()):
            sales_data.append({
                'period': period,
                'orders': data['orders'],
                'revenue': round(data['revenue'], 2),
                'items_sold': data['items_sold'],
                'average_order_value': round(data['revenue'] / data['orders'], 2) if data['orders'] > 0 else 0
            })
        
        # Calculate totals
        total_orders = sum(data['orders'] for data in sales_by_period.values())
        total_revenue = sum(data['revenue'] for data in sales_by_period.values())
        total_items_sold = sum(data['items_sold'] for data in sales_by_period.values())
        
        analytics = {
            'group_by': group_by,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_orders': total_orders,
                'total_revenue': round(total_revenue, 2),
                'total_items_sold': total_items_sold,
                'average_order_value': round(total_revenue / total_orders, 2) if total_orders > 0 else 0
            },
            'sales_data': sales_data
        }
        
        return AnalyticsResponse(
            success=True,
            message="Sales analytics retrieved successfully",
            data={'analytics': analytics}
        )
        
    except Exception as e:
        return AnalyticsResponse(
            success=False,
            message="Failed to retrieve sales analytics",
            error=str(e)
        )

@app.get("/admin/analytics/products", response_model=AnalyticsResponse)
async def get_product_analytics(
    authorization: str = Header(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Get product analytics"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Parse dates
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = datetime.utcnow()
        
        # Get orders for the period
        orders_response = db.tables['orders'].scan(
            FilterExpression='created_at BETWEEN :start_date AND :end_date',
            ExpressionAttributeValues={
                ':start_date': start_date.isoformat(),
                ':end_date': end_date.isoformat()
            }
        )
        
        orders = orders_response['Items']
        
        # Calculate product metrics
        product_metrics = {}
        for order in orders:
            for item in order['items']:
                product_id = item['product_id']
                
                if product_id not in product_metrics:
                    product_metrics[product_id] = {
                        'product_id': product_id,
                        'orders': 0,
                        'quantity_sold': 0,
                        'revenue': 0,
                        'views': 0,  # This would come from analytics table
                        'add_to_cart': 0  # This would come from analytics table
                    }
                
                product_metrics[product_id]['orders'] += 1
                product_metrics[product_id]['quantity_sold'] += item['quantity']
                product_metrics[product_id]['revenue'] += item['price'] * item['quantity']
        
        # Get product details and calculate conversion rate
        product_analytics = []
        for product_id, metrics in product_metrics.items():
            product = db.get_product(product_id)
            if product:
                # Calculate conversion rate (simplified)
                conversion_rate = (metrics['orders'] / max(metrics['views'], 1)) * 100 if metrics['views'] > 0 else 0
                
                product_analytics.append({
                    'product_id': product_id,
                    'name': product['name'],
                    'category': product['category'],
                    'orders': metrics['orders'],
                    'quantity_sold': metrics['quantity_sold'],
                    'revenue': round(metrics['revenue'], 2),
                    'views': metrics['views'],
                    'add_to_cart': metrics['add_to_cart'],
                    'conversion_rate': round(conversion_rate, 2)
                })
        
        # Sort by revenue and limit
        product_analytics.sort(key=lambda x: x['revenue'], reverse=True)
        product_analytics = product_analytics[:limit]
        
        analytics = {
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'products': product_analytics
        }
        
        return AnalyticsResponse(
            success=True,
            message="Product analytics retrieved successfully",
            data={'analytics': analytics}
        )
        
    except Exception as e:
        return AnalyticsResponse(
            success=False,
            message="Failed to retrieve product analytics",
            error=str(e)
        )

@app.get("/admin/analytics/users", response_model=AnalyticsResponse)
async def get_user_analytics(
    authorization: str = Header(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get user analytics"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Parse dates
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            end_date = datetime.utcnow()
        
        # Get users for the period
        users_response = db.tables['users'].scan(
            FilterExpression='created_at BETWEEN :start_date AND :end_date',
            ExpressionAttributeValues={
                ':start_date': start_date.isoformat(),
                ':end_date': end_date.isoformat()
            }
        )
        
        users = users_response['Items']
        
        # Calculate user metrics
        total_users = len(users)
        active_users = len([u for u in users if u.get('is_active', True)])
        
        # Get user registrations by day
        registrations_by_day = {}
        for user in users:
            date = user['created_at'][:10]  # YYYY-MM-DD
            registrations_by_day[date] = registrations_by_day.get(date, 0) + 1
        
        # Get user registrations by auth provider
        auth_providers = {}
        for user in users:
            # Get auth records for user
            auth_response = db.tables['user_auth'].query(
                IndexName='user-id-index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user['user_id']}
            )
            
            for auth_record in auth_response['Items']:
                provider = auth_record['provider']
                auth_providers[provider] = auth_providers.get(provider, 0) + 1
        
        # Get user orders
        user_orders = {}
        for user in users:
            user_id = user['user_id']
            orders_response = db.tables['orders'].query(
                IndexName='user-id-index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            
            user_orders[user_id] = {
                'order_count': len(orders_response['Items']),
                'total_spent': sum(float(order['total']) for order in orders_response['Items'])
            }
        
        # Calculate customer segments
        customers_with_orders = len([u for u in user_orders.values() if u['order_count'] > 0])
        repeat_customers = len([u for u in user_orders.values() if u['order_count'] > 1])
        
        analytics = {
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'overview': {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'customers_with_orders': customers_with_orders,
                'repeat_customers': repeat_customers
            },
            'registrations_by_day': registrations_by_day,
            'auth_providers': auth_providers,
            'customer_segments': {
                'new_customers': customers_with_orders - repeat_customers,
                'repeat_customers': repeat_customers,
                'repeat_customer_rate': round((repeat_customers / max(customers_with_orders, 1)) * 100, 2)
            }
        }
        
        return AnalyticsResponse(
            success=True,
            message="User analytics retrieved successfully",
            data={'analytics': analytics}
        )
        
    except Exception as e:
        return AnalyticsResponse(
            success=False,
            message="Failed to retrieve user analytics",
            error=str(e)
        )

@app.post("/admin/analytics/track", response_model=AnalyticsResponse)
async def track_event(
    event_type: str,
    event_data: Dict[str, Any],
    authorization: str = Header(...)
):
    """Track analytics event"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Create analytics record
        analytics_record = create_analytics_record(event_type, 1, event_data)
        db.create_analytics_record(analytics_record)
        
        return AnalyticsResponse(
            success=True,
            message="Event tracked successfully",
            data={'event': analytics_record}
        )
        
    except Exception as e:
        return AnalyticsResponse(
            success=False,
            message="Failed to track event",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
