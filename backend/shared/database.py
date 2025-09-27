import boto3
import json
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
import os

class DynamoDBClient:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.tables = {
            'users': self.dynamodb.Table(os.getenv('USERS_TABLE', 'ukiyo-users')),
            'user_auth': self.dynamodb.Table(os.getenv('USER_AUTH_TABLE', 'ukiyo-user-auth')),
            'products': self.dynamodb.Table(os.getenv('PRODUCTS_TABLE', 'ukiyo-products')),
            'cart': self.dynamodb.Table(os.getenv('CART_TABLE', 'ukiyo-cart')),
            'wishlist': self.dynamodb.Table(os.getenv('WISHLIST_TABLE', 'ukiyo-wishlist')),
            'orders': self.dynamodb.Table(os.getenv('ORDERS_TABLE', 'ukiyo-orders')),
            'returns': self.dynamodb.Table(os.getenv('RETURNS_TABLE', 'ukiyo-returns')),
            'analytics': self.dynamodb.Table(os.getenv('ANALYTICS_TABLE', 'ukiyo-analytics'))
        }

    def decimal_serializer(self, obj):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def serialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DynamoDB item to JSON-serializable format"""
        return json.loads(json.dumps(item, default=self.decimal_serializer))

    def deserialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON item to DynamoDB format (handle Decimal conversion)"""
        return json.loads(json.dumps(item, default=self.decimal_serializer))

    # User operations
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        table = self.tables['users']
        response = table.put_item(Item=user_data)
        return self.serialize_item(user_data)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        table = self.tables['users']
        response = table.get_item(Key={'user_id': user_id})
        return self.serialize_item(response['Item']) if 'Item' in response else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email using GSI"""
        table = self.tables['users']
        response = table.query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        return self.serialize_item(response['Items'][0]) if response['Items'] else None

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data"""
        table = self.tables['users']
        
        # Build update expression
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for key, value in update_data.items():
            if key != 'user_id':  # Don't update the key
                update_expression += f"#{key} = :{key}, "
                expression_attribute_values[f":{key}"] = value
                expression_attribute_names[f"#{key}"] = key
        
        # Remove trailing comma
        update_expression = update_expression.rstrip(", ")
        
        response = table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues='ALL_NEW'
        )
        return self.serialize_item(response['Attributes'])

    # Product operations
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product"""
        table = self.tables['products']
        response = table.put_item(Item=product_data)
        return self.serialize_item(product_data)

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        table = self.tables['products']
        response = table.get_item(Key={'product_id': product_id})
        return self.serialize_item(response['Item']) if 'Item' in response else None

    def get_products(self, filters: Optional[Dict[str, Any]] = None, limit: int = 20, last_key: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get products with optional filtering"""
        table = self.tables['products']
        
        # Build query parameters
        query_params = {
            'Limit': limit,
            'FilterExpression': 'is_active = :active',
            'ExpressionAttributeValues': {':active': True}
        }
        
        if last_key:
            query_params['ExclusiveStartKey'] = last_key
        
        # Add filters
        if filters:
            filter_expressions = ['is_active = :active']
            expression_values = {':active': True}
            
            if filters.get('category'):
                filter_expressions.append('category = :category')
                expression_values[':category'] = filters['category']
            
            if filters.get('min_price'):
                filter_expressions.append('base_price >= :min_price')
                expression_values[':min_price'] = Decimal(str(filters['min_price']))
            
            if filters.get('max_price'):
                filter_expressions.append('base_price <= :max_price')
                expression_values[':max_price'] = Decimal(str(filters['max_price']))
            
            if filters.get('featured') is not None:
                filter_expressions.append('featured = :featured')
                expression_values[':featured'] = filters['featured']
            
            if filters.get('search_query'):
                filter_expressions.append('contains(searchable_text, :search_query)')
                expression_values[':search_query'] = filters['search_query'].lower()
            
            query_params['FilterExpression'] = ' AND '.join(filter_expressions)
            query_params['ExpressionAttributeValues'] = expression_values
        
        response = table.scan(**query_params)
        
        return {
            'items': [self.serialize_item(item) for item in response['Items']],
            'last_evaluated_key': response.get('LastEvaluatedKey'),
            'count': response['Count']
        }

    def update_product(self, product_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update product data"""
        table = self.tables['products']
        
        # Build update expression
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for key, value in update_data.items():
            if key != 'product_id':  # Don't update the key
                update_expression += f"#{key} = :{key}, "
                expression_attribute_values[f":{key}"] = value
                expression_attribute_names[f"#{key}"] = key
        
        # Remove trailing comma
        update_expression = update_expression.rstrip(", ")
        
        response = table.update_item(
            Key={'product_id': product_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues='ALL_NEW'
        )
        return self.serialize_item(response['Attributes'])

    # Cart operations
    def get_cart(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get cart for user or session"""
        table = self.tables['cart']
        
        if user_id:
            response = table.get_item(Key={'user_id': user_id})
        elif session_id:
            response = table.get_item(Key={'session_id': session_id})
        else:
            return None
        
        return self.serialize_item(response['Item']) if 'Item' in response else None

    def create_cart(self, cart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new cart"""
        table = self.tables['cart']
        response = table.put_item(Item=cart_data)
        return self.serialize_item(cart_data)

    def update_cart(self, cart_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update cart data"""
        table = self.tables['cart']
        
        # Build update expression
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for key, value in update_data.items():
            if key not in ['user_id', 'session_id']:  # Don't update the key
                update_expression += f"#{key} = :{key}, "
                expression_attribute_values[f":{key}"] = value
                expression_attribute_names[f"#{key}"] = key
        
        # Remove trailing comma
        update_expression = update_expression.rstrip(", ")
        
        response = table.update_item(
            Key={'user_id': cart_id} if 'user_id' in update_data else {'session_id': cart_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues='ALL_NEW'
        )
        return self.serialize_item(response['Attributes'])

    # Order operations
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order"""
        table = self.tables['orders']
        response = table.put_item(Item=order_data)
        return self.serialize_item(order_data)

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        table = self.tables['orders']
        response = table.get_item(Key={'order_id': order_id})
        return self.serialize_item(response['Item']) if 'Item' in response else None

    def get_user_orders(self, user_id: str, limit: int = 20, last_key: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get orders for a user"""
        table = self.tables['orders']
        
        query_params = {
            'IndexName': 'user-id-index',
            'KeyConditionExpression': 'user_id = :user_id',
            'ExpressionAttributeValues': {':user_id': user_id},
            'Limit': limit,
            'ScanIndexForward': False  # Most recent first
        }
        
        if last_key:
            query_params['ExclusiveStartKey'] = last_key
        
        response = table.query(**query_params)
        
        return {
            'items': [self.serialize_item(item) for item in response['Items']],
            'last_evaluated_key': response.get('LastEvaluatedKey'),
            'count': response['Count']
        }

    # Analytics operations
    def create_analytics_record(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create analytics record"""
        table = self.tables['analytics']
        response = table.put_item(Item=analytics_data)
        return self.serialize_item(analytics_data)

    def get_analytics(self, metric_type: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get analytics data for a date range"""
        table = self.tables['analytics']
        
        response = table.query(
            IndexName='metric-type-date-index',
            KeyConditionExpression='metric_type = :metric_type AND #date BETWEEN :start_date AND :end_date',
            ExpressionAttributeNames={'#date': 'date'},
            ExpressionAttributeValues={
                ':metric_type': metric_type,
                ':start_date': start_date,
                ':end_date': end_date
            }
        )
        
        return [self.serialize_item(item) for item in response['Items']]

    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get user by phone using GSI"""
        table = self.tables['users']
        response = table.query(
            IndexName='phone-index',
            KeyConditionExpression='phone = :phone',
            ExpressionAttributeValues={':phone': phone}
        )
        return self.serialize_item(response['Items'][0]) if response['Items'] else None

    def get_wishlist(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get wishlist for user or session"""
        table = self.tables['wishlist']
        
        if user_id:
            response = table.get_item(Key={'user_id': user_id})
        elif session_id:
            response = table.get_item(Key={'session_id': session_id})
        else:
            return None
        
        return self.serialize_item(response['Item']) if 'Item' in response else None

    def create_wishlist(self, wishlist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new wishlist"""
        table = self.tables['wishlist']
        response = table.put_item(Item=wishlist_data)
        return self.serialize_item(wishlist_data)

    def update_wishlist(self, wishlist_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update wishlist data"""
        table = self.tables['wishlist']
        
        # Build update expression
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for key, value in update_data.items():
            if key not in ['user_id', 'session_id']:  # Don't update the key
                update_expression += f"#{key} = :{key}, "
                expression_attribute_values[f":{key}"] = value
                expression_attribute_names[f"#{key}"] = key
        
        # Remove trailing comma
        update_expression = update_expression.rstrip(", ")
        
        response = table.update_item(
            Key={'user_id': wishlist_id} if 'user_id' in update_data else {'session_id': wishlist_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues='ALL_NEW'
        )
        return self.serialize_item(response['Attributes'])
