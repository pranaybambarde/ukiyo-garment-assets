import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

def generate_id(prefix: str = '') -> str:
    """Generate a unique ID with optional prefix"""
    unique_id = str(uuid.uuid4())
    return f"{prefix}{unique_id}" if prefix else unique_id

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate Indian phone number format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Indian mobile number (10 digits starting with 6-9)
    if len(digits_only) == 10 and digits_only[0] in '6789':
        return True
    
    # Check if it's a valid Indian mobile number with country code (+91)
    if len(digits_only) == 12 and digits_only.startswith('91') and digits_only[2] in '6789':
        return True
    
    return False

def format_phone(phone: str) -> str:
    """Format phone number to standard format"""
    digits_only = re.sub(r'\D', '', phone)
    
    if len(digits_only) == 10:
        return f"+91{digits_only}"
    elif len(digits_only) == 12 and digits_only.startswith('91'):
        return f"+{digits_only}"
    else:
        return phone

def validate_pincode(pincode: str) -> bool:
    """Validate Indian pincode format"""
    return re.match(r'^[1-9][0-9]{5}$', pincode) is not None

def calculate_tax(amount: float, tax_rate: float = 0.18) -> float:
    """Calculate tax amount (18% GST for India)"""
    return round(amount * tax_rate, 2)

def calculate_shipping_cost(amount: float, free_shipping_threshold: float = 2000.0) -> float:
    """Calculate shipping cost based on order amount"""
    if amount >= free_shipping_threshold:
        return 0.0
    return 100.0  # Standard shipping cost

def format_currency(amount: float, currency: str = 'INR') -> str:
    """Format amount as currency"""
    return f"₹{amount:,.2f}"

def create_searchable_text(text: str) -> str:
    """Create searchable text by removing special characters and converting to lowercase"""
    # Remove special characters and convert to lowercase
    searchable = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    # Remove extra spaces
    searchable = re.sub(r'\s+', ' ', searchable).strip()
    return searchable

def build_filter_expression(filters: Dict[str, Any]) -> tuple:
    """Build DynamoDB filter expression from filters"""
    filter_expressions = []
    expression_values = {}
    expression_names = {}
    
    for key, value in filters.items():
        if value is not None:
            if key == 'min_price':
                filter_expressions.append('base_price >= :min_price')
                expression_values[':min_price'] = value
            elif key == 'max_price':
                filter_expressions.append('base_price <= :max_price')
                expression_values[':max_price'] = value
            elif key == 'search_query':
                filter_expressions.append('contains(searchable_text, :search_query)')
                expression_values[':search_query'] = create_searchable_text(value)
            elif key in ['category', 'subcategory', 'fabric_type', 'occasions']:
                if isinstance(value, list):
                    # Handle list values (e.g., fabric_type: ['cotton', 'silk'])
                    placeholders = []
                    for i, v in enumerate(value):
                        placeholder = f":{key}_{i}"
                        placeholders.append(placeholder)
                        expression_values[placeholder] = v
                    filter_expressions.append(f"#{key} IN ({', '.join(placeholders)})")
                    expression_names[f"#{key}"] = key
                else:
                    # Handle single values
                    filter_expressions.append(f"#{key} = :{key}")
                    expression_values[f":{key}"] = value
                    expression_names[f"#{key}"] = key
            else:
                # Handle other attributes
                filter_expressions.append(f"#{key} = :{key}")
                expression_values[f":{key}"] = value
                expression_names[f"#{key}"] = key
    
    return ' AND '.join(filter_expressions), expression_values, expression_names

def paginate_results(items: List[Any], page: int = 1, limit: int = 20) -> Dict[str, Any]:
    """Paginate results"""
    total = len(items)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    
    paginated_items = items[start_index:end_index]
    
    return {
        'items': paginated_items,
        'total': total,
        'page': page,
        'limit': limit,
        'has_next': end_index < total,
        'has_prev': page > 1,
        'total_pages': (total + limit - 1) // limit
    }

def create_response(success: bool, message: str, data: Any = None, error: str = None) -> Dict[str, Any]:
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    if error:
        response['error'] = error
    
    return response

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate required fields and return missing fields"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    return missing_fields

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    if not isinstance(text, str):
        return text
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'<[^>]*>', '', text)  # Remove HTML tags
    sanitized = re.sub(r'[<>"\']', '', sanitized)  # Remove dangerous characters
    return sanitized.strip()

def generate_recommendations(product_id: str, category: str, price_range: tuple) -> List[str]:
    """Generate product recommendations based on category and price"""
    # This is a placeholder implementation
    # In a real system, you'd use ML models or collaborative filtering
    
    recommendations = []
    
    # Simple category-based recommendations
    if category == 'tops':
        recommendations.extend(['blouse_001', 'shirt_002', 'tank_003'])
    elif category == 'bottoms':
        recommendations.extend(['pants_001', 'skirt_002', 'shorts_003'])
    elif category == 'dresses':
        recommendations.extend(['dress_001', 'maxi_002', 'midi_003'])
    
    # Filter by price range (simplified)
    # In reality, you'd query the database for products in the price range
    
    return recommendations[:5]  # Return top 5 recommendations

def calculate_order_summary(items: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate order summary (subtotal, tax, shipping, total)"""
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    tax = calculate_tax(subtotal)
    shipping = calculate_shipping_cost(subtotal)
    total = subtotal + tax + shipping
    
    return {
        'subtotal': round(subtotal, 2),
        'tax': round(tax, 2),
        'shipping': round(shipping, 2),
        'total': round(total, 2)
    }

def validate_address(address: Dict[str, Any]) -> List[str]:
    """Validate shipping address"""
    errors = []
    required_fields = ['name', 'phone', 'address_line_1', 'city', 'state', 'pincode']
    
    missing_fields = validate_required_fields(address, required_fields)
    if missing_fields:
        errors.extend([f"Missing required field: {field}" for field in missing_fields])
    
    if address.get('phone') and not validate_phone(address['phone']):
        errors.append("Invalid phone number format")
    
    if address.get('pincode') and not validate_pincode(address['pincode']):
        errors.append("Invalid pincode format")
    
    return errors

def create_analytics_record(metric_type: str, value: float, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create analytics record"""
    return {
        'record_id': generate_id('analytics_'),
        'metric_type': metric_type,
        'value': value,
        'metadata': metadata or {},
        'date': datetime.utcnow().isoformat(),
        'created_at': datetime.utcnow().isoformat()
    }
