from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

class AuthProvider(str, Enum):
    GOOGLE = "google"
    APPLE = "apple"
    PHONE = "phone"
    EMAIL = "email"

class SkinTone(str, Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    DARK = "dark"

class BodyShape(str, Enum):
    PEAR = "pear"
    APPLE = "apple"
    HOURGLASS = "hourglass"
    RECTANGLE = "rectangle"
    INVERTED_TRIANGLE = "inverted_triangle"

class FabricType(str, Enum):
    COTTON = "cotton"
    SILK = "silk"
    LINEN = "linen"
    WOOL = "wool"
    POLYESTER = "polyester"
    RAYON = "rayon"
    BAMBOO = "bamboo"

class Occasion(str, Enum):
    CASUAL = "casual"
    WORK = "work"
    PARTY = "party"
    FESTIVE = "festive"
    WEDDING = "wedding"
    TRAVEL = "travel"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class ReturnStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"

# User Models
class UserProfile(BaseModel):
    user_id: str
    email: str
    phone: Optional[str] = None
    name: str
    role: UserRole = UserRole.CUSTOMER
    skin_tone: Optional[SkinTone] = None
    body_shape: Optional[BodyShape] = None
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class UserAuth(BaseModel):
    user_id: str
    provider: AuthProvider
    provider_id: str  # Google ID, Apple ID, phone number, or email
    created_at: datetime

# Product Models
class ProductVariant(BaseModel):
    variant_id: str
    color: str
    size: str
    sku: str
    price: float
    stock_quantity: int
    images: List[str] = []
    is_available: bool = True

class Product(BaseModel):
    product_id: str
    name: str
    description: str
    brand: str = "Ukiyo"
    category: str
    subcategory: str
    base_price: float
    variants: List[ProductVariant] = []
    fabric_type: List[FabricType] = []
    occasions: List[Occasion] = []
    care_instructions: str = ""
    size_chart: Dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []
    featured: bool = False

class ProductFilter(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    skin_tone: Optional[SkinTone] = None
    body_shape: Optional[BodyShape] = None
    fabric_type: Optional[List[FabricType]] = None
    occasions: Optional[List[Occasion]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    size: Optional[str] = None
    color: Optional[str] = None
    featured: Optional[bool] = None
    search_query: Optional[str] = None

# Cart and Wishlist Models
class CartItem(BaseModel):
    item_id: str
    product_id: str
    variant_id: str
    quantity: int
    added_at: datetime

class Cart(BaseModel):
    cart_id: str
    user_id: Optional[str] = None  # None for guest users
    session_id: Optional[str] = None  # For guest users
    items: List[CartItem] = []
    created_at: datetime
    updated_at: datetime

class WishlistItem(BaseModel):
    item_id: str
    product_id: str
    added_at: datetime

class Wishlist(BaseModel):
    wishlist_id: str
    user_id: Optional[str] = None  # None for guest users
    session_id: Optional[str] = None  # For guest users
    items: List[WishlistItem] = []
    created_at: datetime
    updated_at: datetime

# Order Models
class ShippingAddress(BaseModel):
    name: str
    phone: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"

class OrderItem(BaseModel):
    product_id: str
    variant_id: str
    quantity: int
    price: float
    product_name: str
    variant_details: str

class Order(BaseModel):
    order_id: str
    user_id: Optional[str] = None
    email: str
    items: List[OrderItem]
    shipping_address: ShippingAddress
    subtotal: float
    shipping_cost: float
    tax: float
    total: float
    status: OrderStatus
    payment_id: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ReturnRequest(BaseModel):
    return_id: str
    order_id: str
    user_id: str
    items: List[OrderItem]
    reason: str
    status: ReturnStatus
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# API Response Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

# Analytics Models
class SalesAnalytics(BaseModel):
    total_sales: float
    total_orders: int
    average_order_value: float
    period: str  # daily, weekly, monthly
    date: datetime

class ProductAnalytics(BaseModel):
    product_id: str
    views: int
    add_to_cart: int
    purchases: int
    conversion_rate: float
    period: str
    date: datetime
