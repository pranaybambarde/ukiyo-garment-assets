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
from models import Product, ProductVariant, APIResponse
from utils import generate_id, create_response, paginate_results

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class CreateProductRequest(BaseModel):
    name: str
    description: str
    category: str
    subcategory: str
    base_price: float
    fabric_type: List[str]
    occasions: List[str]
    care_instructions: str = ""
    size_chart: Dict[str, Any] = {}
    tags: List[str] = []
    featured: bool = False

class UpdateProductRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    base_price: Optional[float] = None
    fabric_type: Optional[List[str]] = None
    occasions: Optional[List[str]] = None
    care_instructions: Optional[str] = None
    size_chart: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    featured: Optional[bool] = None
    is_active: Optional[bool] = None

class CreateVariantRequest(BaseModel):
    product_id: str
    color: str
    size: str
    sku: str
    price: float
    stock_quantity: int
    images: List[str] = []

class UpdateVariantRequest(BaseModel):
    color: Optional[str] = None
    size: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    images: Optional[List[str]] = None
    is_available: Optional[bool] = None

class AdminResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

def require_admin(authorization: str):
    """Require admin authentication"""
    user_info = auth_manager.require_admin(authorization)
    return user_info

@app.get("/admin/products", response_model=AdminResponse)
async def get_all_products(
    authorization: str = Header(...),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get all products for admin"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Build filters
        filters = {}
        if search:
            filters['search_query'] = search
        if category:
            filters['category'] = category
        if is_active is not None:
            filters['is_active'] = is_active
        
        # Get products
        result = db.get_products(filters, limit, None)
        
        # Paginate results
        paginated_result = paginate_results(result['items'], page, limit)
        
        return AdminResponse(
            success=True,
            message="Products retrieved successfully",
            data={
                'products': paginated_result['items'],
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
            message="Failed to retrieve products",
            error=str(e)
        )

@app.get("/admin/products/{product_id}", response_model=AdminResponse)
async def get_product_details(
    product_id: str,
    authorization: str = Header(...)
):
    """Get product details for admin"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get product
        product = db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return AdminResponse(
            success=True,
            message="Product retrieved successfully",
            data={'product': product}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to retrieve product",
            error=str(e)
        )

@app.post("/admin/products", response_model=AdminResponse)
async def create_product(
    request: CreateProductRequest,
    authorization: str = Header(...)
):
    """Create new product"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Create product
        product_id = generate_id('product_')
        product_data = {
            'product_id': product_id,
            'name': request.name,
            'description': request.description,
            'brand': 'Ukiyo',
            'category': request.category,
            'subcategory': request.subcategory,
            'base_price': request.base_price,
            'variants': [],
            'fabric_type': request.fabric_type,
            'occasions': request.occasions,
            'care_instructions': request.care_instructions,
            'size_chart': request.size_chart,
            'is_active': True,
            'created_at': auth_manager.datetime.utcnow().isoformat(),
            'updated_at': auth_manager.datetime.utcnow().isoformat(),
            'tags': request.tags,
            'featured': request.featured,
            'searchable_text': f"{request.name} {request.description} {request.category} {request.subcategory}".lower()
        }
        
        product = db.create_product(product_data)
        
        return AdminResponse(
            success=True,
            message="Product created successfully",
            data={'product': product}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to create product",
            error=str(e)
        )

@app.put("/admin/products/{product_id}", response_model=AdminResponse)
async def update_product(
    product_id: str,
    request: UpdateProductRequest,
    authorization: str = Header(...)
):
    """Update product"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get existing product
        product = db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Prepare update data
        update_data = {}
        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        # Update searchable text if name or description changed
        if 'name' in update_data or 'description' in update_data:
            name = update_data.get('name', product['name'])
            description = update_data.get('description', product['description'])
            category = update_data.get('category', product['category'])
            subcategory = update_data.get('subcategory', product['subcategory'])
            update_data['searchable_text'] = f"{name} {description} {category} {subcategory}".lower()
        
        update_data['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        
        # Update product
        updated_product = db.update_product(product_id, update_data)
        
        return AdminResponse(
            success=True,
            message="Product updated successfully",
            data={'product': updated_product}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to update product",
            error=str(e)
        )

@app.delete("/admin/products/{product_id}", response_model=AdminResponse)
async def delete_product(
    product_id: str,
    authorization: str = Header(...)
):
    """Delete product (soft delete)"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get existing product
        product = db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Soft delete by setting is_active to False
        update_data = {
            'is_active': False,
            'updated_at': auth_manager.datetime.utcnow().isoformat()
        }
        
        updated_product = db.update_product(product_id, update_data)
        
        return AdminResponse(
            success=True,
            message="Product deleted successfully",
            data={'product': updated_product}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to delete product",
            error=str(e)
        )

@app.post("/admin/products/{product_id}/variants", response_model=AdminResponse)
async def create_variant(
    product_id: str,
    request: CreateVariantRequest,
    authorization: str = Header(...)
):
    """Create product variant"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get existing product
        product = db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Create variant
        variant_id = generate_id('variant_')
        variant_data = {
            'variant_id': variant_id,
            'color': request.color,
            'size': request.size,
            'sku': request.sku,
            'price': request.price,
            'stock_quantity': request.stock_quantity,
            'images': request.images,
            'is_available': request.stock_quantity > 0
        }
        
        # Add variant to product
        product['variants'].append(variant_data)
        product['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        
        # Update product
        updated_product = db.update_product(product_id, {'variants': product['variants']})
        
        return AdminResponse(
            success=True,
            message="Variant created successfully",
            data={'product': updated_product}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to create variant",
            error=str(e)
        )

@app.put("/admin/products/{product_id}/variants/{variant_id}", response_model=AdminResponse)
async def update_variant(
    product_id: str,
    variant_id: str,
    request: UpdateVariantRequest,
    authorization: str = Header(...)
):
    """Update product variant"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get existing product
        product = db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Find variant
        variant_found = False
        for i, variant in enumerate(product['variants']):
            if variant['variant_id'] == variant_id:
                # Update variant
                for field, value in request.dict(exclude_unset=True).items():
                    if value is not None:
                        variant[field] = value
                
                # Update availability based on stock
                if 'stock_quantity' in request.dict(exclude_unset=True):
                    variant['is_available'] = variant['stock_quantity'] > 0
                
                variant_found = True
                break
        
        if not variant_found:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        # Update product
        product['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        updated_product = db.update_product(product_id, {'variants': product['variants']})
        
        return AdminResponse(
            success=True,
            message="Variant updated successfully",
            data={'product': updated_product}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to update variant",
            error=str(e)
        )

@app.delete("/admin/products/{product_id}/variants/{variant_id}", response_model=AdminResponse)
async def delete_variant(
    product_id: str,
    variant_id: str,
    authorization: str = Header(...)
):
    """Delete product variant"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get existing product
        product = db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Remove variant
        variant_found = False
        for i, variant in enumerate(product['variants']):
            if variant['variant_id'] == variant_id:
                product['variants'].pop(i)
                variant_found = True
                break
        
        if not variant_found:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        # Update product
        product['updated_at'] = auth_manager.datetime.utcnow().isoformat()
        updated_product = db.update_product(product_id, {'variants': product['variants']})
        
        return AdminResponse(
            success=True,
            message="Variant deleted successfully",
            data={'product': updated_product}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to delete variant",
            error=str(e)
        )

@app.get("/admin/analytics/inventory", response_model=AdminResponse)
async def get_inventory_analytics(
    authorization: str = Header(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get inventory analytics"""
    try:
        # Require admin access
        require_admin(authorization)
        
        # Get all products
        result = db.get_products({}, 1000, None)
        
        # Calculate analytics
        total_products = len(result['items'])
        active_products = len([p for p in result['items'] if p['is_active']])
        total_variants = sum(len(p['variants']) for p in result['items'])
        low_stock_products = []
        
        for product in result['items']:
            for variant in product['variants']:
                if variant['stock_quantity'] < 10:  # Low stock threshold
                    low_stock_products.append({
                        'product_id': product['product_id'],
                        'product_name': product['name'],
                        'variant_id': variant['variant_id'],
                        'color': variant['color'],
                        'size': variant['size'],
                        'stock_quantity': variant['stock_quantity']
                    })
        
        analytics = {
            'total_products': total_products,
            'active_products': active_products,
            'inactive_products': total_products - active_products,
            'total_variants': total_variants,
            'low_stock_products': low_stock_products,
            'low_stock_count': len(low_stock_products)
        }
        
        return AdminResponse(
            success=True,
            message="Inventory analytics retrieved successfully",
            data={'analytics': analytics}
        )
        
    except Exception as e:
        return AdminResponse(
            success=False,
            message="Failed to retrieve inventory analytics",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
