# Ukiyo E-commerce Backend

This is the backend implementation for the Ukiyo e-commerce platform, built with AWS Lambda and DynamoDB. The backend provides all the necessary APIs to support the frontend application as described in the WebsiteImplementation.md document.

## Architecture Overview

The backend is built using:
- **AWS Lambda** for serverless compute
- **DynamoDB** for NoSQL database
- **API Gateway** for REST API endpoints
- **Python 3.9** with FastAPI and Mangum for Lambda functions

## Project Structure

```
backend/
├── shared/                    # Shared modules
│   ├── models.py             # Pydantic models
│   ├── database.py           # DynamoDB client
│   ├── auth.py               # Authentication utilities
│   └── utils.py              # Utility functions
├── lambdas/                  # Lambda functions
│   ├── auth/                 # Authentication lambdas
│   │   ├── google_auth.py    # Google OAuth
│   │   ├── phone_auth.py     # Phone OTP
│   │   └── email_auth.py     # Email authentication
│   ├── products/             # Product management
│   │   └── products.py       # Product CRUD and filtering
│   ├── cart/                 # Shopping cart
│   │   └── cart.py           # Cart management
│   ├── wishlist/             # Wishlist management
│   │   └── wishlist.py       # Wishlist operations
│   ├── checkout/             # Checkout and orders
│   │   └── checkout.py       # Order processing
│   ├── admin/                # Admin panel
│   │   ├── inventory.py      # Inventory management
│   │   ├── analytics.py      # Analytics dashboard
│   │   └── returns.py        # Returns management
│   └── user/                 # User management
│       └── profile.py        # User profiles and preferences
├── infrastructure/           # Infrastructure as Code
│   ├── dynamodb-tables.yaml  # DynamoDB table definitions
│   ├── lambda-functions.yaml # Lambda function definitions
│   └── api-gateway.yaml      # API Gateway configuration
├── requirements.txt          # Python dependencies
├── deploy.sh                 # Deployment script
└── README.md                 # This file
```

## Features Implemented

### Authentication
- Google OAuth integration
- Apple Sign-In integration
- Phone number OTP authentication
- Email magic link authentication
- JWT token management

### Product Management
- Product CRUD operations
- Advanced filtering and search
- Product recommendations
- Category management
- Inventory tracking

### Shopping Cart & Wishlist
- Guest and authenticated user support
- Cart and wishlist management
- Session-based storage for guests
- User account integration

### Checkout & Orders
- Multi-step checkout process
- Order management
- Payment integration (Razorpay)
- Order tracking
- Return management

### Admin Panel
- Inventory management
- Analytics dashboard
- Returns processing
- User management
- Product management

### Personalization
- User profile management
- Personalized recommendations
- Address management
- User preferences

## API Endpoints

### Authentication
- `POST /auth/google` - Google OAuth authentication
- `POST /auth/phone/send-otp` - Send OTP to phone
- `POST /auth/phone/verify-otp` - Verify OTP
- `POST /auth/email/send-magic-link` - Send magic link
- `POST /auth/email/verify-magic-link` - Verify magic link

### Products
- `GET /products` - Get products with filtering
- `GET /products/{id}` - Get product details
- `GET /products/{id}/recommendations` - Get product recommendations
- `GET /products/search` - Search products
- `GET /products/featured` - Get featured products
- `GET /products/new-arrivals` - Get new arrivals

### Cart
- `GET /cart` - Get cart contents
- `POST /cart/add` - Add item to cart
- `PUT /cart/update` - Update cart item
- `DELETE /cart/remove/{id}` - Remove item from cart
- `DELETE /cart/clear` - Clear cart
- `POST /cart/merge` - Merge guest cart with user cart

### Wishlist
- `GET /wishlist` - Get wishlist contents
- `POST /wishlist/add` - Add item to wishlist
- `DELETE /wishlist/remove/{id}` - Remove item from wishlist
- `DELETE /wishlist/clear` - Clear wishlist
- `POST /wishlist/add-all-to-cart` - Add all items to cart

### Checkout
- `POST /checkout/create-order` - Create order
- `POST /checkout/confirm-payment` - Confirm payment
- `GET /orders/{id}` - Get order details
- `GET /orders` - Get user orders
- `POST /orders/{id}/cancel` - Cancel order
- `POST /orders/{id}/return` - Initiate return

### Admin
- `GET /admin/products` - Get all products (admin)
- `POST /admin/products` - Create product (admin)
- `PUT /admin/products/{id}` - Update product (admin)
- `DELETE /admin/products/{id}` - Delete product (admin)
- `GET /admin/analytics/dashboard` - Get analytics (admin)
- `GET /admin/returns` - Get returns (admin)
- `PUT /admin/returns/{id}` - Update return status (admin)

### User Profile
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update user profile
- `GET /user/recommendations` - Get personalized recommendations
- `GET /user/orders` - Get user orders
- `GET /user/addresses` - Get saved addresses
- `POST /user/addresses` - Add address
- `DELETE /user/addresses/{id}` - Delete address

## Database Schema

### DynamoDB Tables

1. **ukiyo-users** - User profiles and information
2. **ukiyo-user-auth** - Authentication providers and tokens
3. **ukiyo-products** - Product catalog
4. **ukiyo-cart** - Shopping cart data
5. **ukiyo-wishlist** - Wishlist data
6. **ukiyo-orders** - Order information
7. **ukiyo-returns** - Return requests
8. **ukiyo-analytics** - Analytics data
9. **ukiyo-otp-sessions** - OTP verification sessions
10. **ukiyo-magic-link-sessions** - Magic link sessions
11. **ukiyo-user-addresses** - User saved addresses
12. **ukiyo-user-preferences** - User preferences

## Deployment

### Prerequisites

1. AWS CLI installed and configured
2. Python 3.9+ installed
3. Required environment variables set:
   - `JWT_SECRET` - JWT secret for token signing
   - `GOOGLE_CLIENT_ID` - Google OAuth client ID
   - `APPLE_CLIENT_ID` - Apple Sign-In client ID
   - `FRONTEND_URL` - Frontend URL for CORS (optional)

### Deployment Steps

1. **Set environment variables:**
   ```bash
   export JWT_SECRET="your-jwt-secret"
   export GOOGLE_CLIENT_ID="your-google-client-id"
   export APPLE_CLIENT_ID="your-apple-client-id"
   export FRONTEND_URL="https://your-frontend-url.com"
   ```

2. **Deploy the entire infrastructure:**
   ```bash
   ./deploy.sh deploy production us-east-1 default
   ```

3. **Update Lambda function code only:**
   ```bash
   ./deploy.sh update
   ```

4. **Run tests:**
   ```bash
   ./deploy.sh test
   ```

### Manual Deployment

If you prefer to deploy manually:

1. **Deploy DynamoDB tables:**
   ```bash
   aws cloudformation deploy \
     --template-file infrastructure/dynamodb-tables.yaml \
     --stack-name ukiyo-dynamodb-production \
     --region us-east-1 \
     --capabilities CAPABILITY_IAM
   ```

2. **Deploy Lambda functions:**
   ```bash
   aws cloudformation deploy \
     --template-file infrastructure/lambda-functions.yaml \
     --stack-name ukiyo-lambda-production \
     --region us-east-1 \
     --capabilities CAPABILITY_IAM \
     --parameter-overrides \
       Environment=production \
       JWTSecret=$JWT_SECRET \
       GoogleClientId=$GOOGLE_CLIENT_ID \
       AppleClientId=$APPLE_CLIENT_ID
   ```

3. **Deploy API Gateway:**
   ```bash
   aws cloudformation deploy \
     --template-file infrastructure/api-gateway.yaml \
     --stack-name ukiyo-api-production \
     --region us-east-1 \
     --capabilities CAPABILITY_IAM
   ```

## Environment Variables

Each Lambda function uses the following environment variables:

- `JWT_SECRET` - Secret key for JWT token signing
- `ENVIRONMENT` - Environment name (development/staging/production)
- `AWS_REGION` - AWS region
- `USERS_TABLE` - DynamoDB users table name
- `PRODUCTS_TABLE` - DynamoDB products table name
- `CART_TABLE` - DynamoDB cart table name
- `WISHLIST_TABLE` - DynamoDB wishlist table name
- `ORDERS_TABLE` - DynamoDB orders table name
- `RETURNS_TABLE` - DynamoDB returns table name
- `ANALYTICS_TABLE` - DynamoDB analytics table name

## Security

- All API endpoints use JWT tokens for authentication
- Admin endpoints require admin role verification
- CORS is configured for frontend domain
- Input validation using Pydantic models
- SQL injection prevention through DynamoDB
- XSS protection through input sanitization

## Monitoring and Logging

- CloudWatch logs for all Lambda functions
- CloudWatch metrics for API Gateway
- DynamoDB metrics and alarms
- Error tracking and alerting

## Development

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up local DynamoDB (optional):
   ```bash
   # Install DynamoDB Local
   # Configure AWS CLI to use local DynamoDB
   ```

3. Run tests:
   ```bash
   python -m pytest tests/
   ```

### Adding New Features

1. Create new Lambda function in appropriate directory
2. Add API Gateway routes in `infrastructure/api-gateway.yaml`
3. Update deployment script if needed
4. Add tests for new functionality
5. Update this README with new endpoints

## Troubleshooting

### Common Issues

1. **Lambda function timeout:**
   - Increase timeout in CloudFormation template
   - Optimize function code

2. **DynamoDB throttling:**
   - Increase provisioned capacity
   - Optimize query patterns

3. **API Gateway CORS issues:**
   - Check CORS configuration
   - Verify preflight request handling

4. **Authentication failures:**
   - Verify JWT secret configuration
   - Check token expiration

### Debugging

1. Check CloudWatch logs for Lambda functions
2. Monitor API Gateway logs
3. Use AWS X-Ray for distributed tracing
4. Check DynamoDB metrics

## Support

For issues and questions:
1. Check the logs in CloudWatch
2. Review the API Gateway logs
3. Check DynamoDB metrics
4. Contact the development team

## License

This project is proprietary and confidential.
