#!/usr/bin/env python3
"""
Local development server for Ukiyo backend
This runs the FastAPI application locally for development
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment variables for local development
os.environ.setdefault('ENVIRONMENT', 'development')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('JWT_SECRET', 'ukiyo-jwt-secret-key-2024')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'your-google-client-id')
os.environ.setdefault('APPLE_CLIENT_ID', 'your-apple-client-id')
os.environ.setdefault('FRONTEND_URL', 'http://localhost:3000')

# Import the main FastAPI app
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="Ukiyo E-commerce API",
    description="Backend API for Ukiyo activewear e-commerce platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include lambda function apps
try:
    from lambdas.products.products import app as products_app
    from lambdas.cart.cart import app as cart_app
    from lambdas.wishlist.wishlist import app as wishlist_app
    from lambdas.auth.email_auth import app as email_auth_app
    from lambdas.auth.phone_auth import app as phone_auth_app
    from lambdas.auth.google_auth import app as google_auth_app
    from lambdas.checkout.checkout import app as checkout_app
    from lambdas.user.profile import app as user_app
    from lambdas.admin.inventory import app as admin_inventory_app
    from lambdas.admin.analytics import app as admin_analytics_app
    from lambdas.admin.returns import app as admin_returns_app
    
    # Mount all lambda apps as sub-applications
    app.mount("/api/products", products_app)
    app.mount("/api/cart", cart_app)
    app.mount("/api/wishlist", wishlist_app)
    app.mount("/api/auth/email", email_auth_app)
    app.mount("/api/auth/phone", phone_auth_app)
    app.mount("/api/auth/google", google_auth_app)
    app.mount("/api/checkout", checkout_app)
    app.mount("/api/user", user_app)
    app.mount("/api/admin/inventory", admin_inventory_app)
    app.mount("/api/admin/analytics", admin_analytics_app)
    app.mount("/api/admin/returns", admin_returns_app)
    
    print("✅ All API routes loaded successfully")
    
except ImportError as e:
    print(f"⚠️  Some routes could not be loaded: {e}")
    print("This is expected if lambda functions are not fully implemented yet")

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Ukiyo E-commerce API",
        "status": "running",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development")
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ukiyo-backend"}

if __name__ == "__main__":
    print("🚀 Starting Ukiyo Backend Development Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print("🔧 Environment: development")
    print("-" * 50)
    
    uvicorn.run(
        "local_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
