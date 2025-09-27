import json
import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Import shared modules
import sys
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from database import DynamoDBClient
from auth import AuthManager
from models import Product, ProductFilter, APIResponse, PaginatedResponse
from utils import generate_id, create_response, build_filter_expression, paginate_results

app = FastAPI()
db = DynamoDBClient()
auth_manager = AuthManager()

class ProductResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

@app.get("/products", response_model=ProductResponse)
async def get_products(
    category: Optional[str] = Query(None),
    subcategory: Optional[str] = Query(None),
    skin_tone: Optional[str] = Query(None),
    body_shape: Optional[str] = Query(None),
    fabric_type: Optional[str] = Query(None),
    occasions: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    size: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    search_query: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get products with filtering and pagination"""
    try:
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
        if subcategory:
            filters['subcategory'] = subcategory
        if skin_tone:
            filters['skin_tone'] = skin_tone
        if body_shape:
            filters['body_shape'] = body_shape
        if fabric_type:
            filters['fabric_type'] = fabric_type.split(',')
        if occasions:
            filters['occasions'] = occasions.split(',')
        if min_price is not None:
            filters['min_price'] = min_price
        if max_price is not None:
            filters['max_price'] = max_price
        if size:
            filters['size'] = size
        if color:
            filters['color'] = color
        if featured is not None:
            filters['featured'] = featured
        if search_query:
            filters['search_query'] = search_query
        
        # Get products from database
        result = db.get_products(filters, limit, None)
        
        # Paginate results
        paginated_result = paginate_results(result['items'], page, limit)
        
        return ProductResponse(
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
        return ProductResponse(
            success=False,
            message="Failed to retrieve products",
            error=str(e)
        )

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get single product by ID"""
    try:
        product = db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return ProductResponse(
            success=True,
            message="Product retrieved successfully",
            data={'product': product}
        )
        
    except Exception as e:
        return ProductResponse(
            success=False,
            message="Failed to retrieve product",
            error=str(e)
        )

@app.get("/products/{product_id}/recommendations", response_model=ProductResponse)
async def get_product_recommendations(product_id: str, limit: int = Query(5, ge=1, le=20)):
    """Get product recommendations"""
    try:
        # Get the product to understand its category and price
        product = db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Build recommendation filters
        filters = {
            'category': product['category'],
            'featured': True
        }
        
        # Get recommended products
        result = db.get_products(filters, limit, None)
        
        # Filter out the current product
        recommendations = [p for p in result['items'] if p['product_id'] != product_id]
        
        return ProductResponse(
            success=True,
            message="Recommendations retrieved successfully",
            data={'recommendations': recommendations[:limit]}
        )
        
    except Exception as e:
        return ProductResponse(
            success=False,
            message="Failed to retrieve recommendations",
            error=str(e)
        )

@app.get("/products/categories", response_model=ProductResponse)
async def get_categories():
    """Get all product categories"""
    try:
        # Get all products to extract categories
        result = db.get_products({}, 1000, None)  # Get more products to get all categories
        
        categories = set()
        subcategories = set()
        
        for product in result['items']:
            if product.get('category'):
                categories.add(product['category'])
            if product.get('subcategory'):
                subcategories.add(product['subcategory'])
        
        return ProductResponse(
            success=True,
            message="Categories retrieved successfully",
            data={
                'categories': sorted(list(categories)),
                'subcategories': sorted(list(subcategories))
            }
        )
        
    except Exception as e:
        return ProductResponse(
            success=False,
            message="Failed to retrieve categories",
            error=str(e)
        )

@app.get("/products/search", response_model=ProductResponse)
async def search_products(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Search products by query"""
    try:
        filters = {'search_query': q}
        result = db.get_products(filters, limit, None)
        
        # Paginate results
        paginated_result = paginate_results(result['items'], page, limit)
        
        return ProductResponse(
            success=True,
            message="Search completed successfully",
            data={
                'products': paginated_result['items'],
                'query': q,
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
        return ProductResponse(
            success=False,
            message="Search failed",
            error=str(e)
        )

@app.get("/products/featured", response_model=ProductResponse)
async def get_featured_products(limit: int = Query(10, ge=1, le=50)):
    """Get featured products"""
    try:
        filters = {'featured': True}
        result = db.get_products(filters, limit, None)
        
        return ProductResponse(
            success=True,
            message="Featured products retrieved successfully",
            data={'products': result['items']}
        )
        
    except Exception as e:
        return ProductResponse(
            success=False,
            message="Failed to retrieve featured products",
            error=str(e)
        )

@app.get("/products/new-arrivals", response_model=ProductResponse)
async def get_new_arrivals(limit: int = Query(10, ge=1, le=50)):
    """Get new arrival products"""
    try:
        # Get products sorted by creation date (newest first)
        result = db.get_products({}, limit, None)
        
        # Sort by created_at descending
        sorted_products = sorted(
            result['items'], 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )
        
        return ProductResponse(
            success=True,
            message="New arrivals retrieved successfully",
            data={'products': sorted_products[:limit]}
        )
        
    except Exception as e:
        return ProductResponse(
            success=False,
            message="Failed to retrieve new arrivals",
            error=str(e)
        )

# Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    handler = Mangum(app)
    return handler(event, context)
