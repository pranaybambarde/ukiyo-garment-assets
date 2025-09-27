#!/bin/bash

# Ukiyo Backend Deployment Script
# This script deploys the Ukiyo e-commerce backend infrastructure and Lambda functions

set -e

# Configuration
ENVIRONMENT=${1:-production}
REGION=${2:-us-east-1}
STACK_PREFIX="ukiyo"
PROFILE=${3:-default}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is installed and configured
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity --profile $PROFILE &> /dev/null; then
        print_error "AWS CLI is not configured or profile '$PROFILE' does not exist."
        exit 1
    fi
    
    print_status "AWS CLI is configured and ready."
}

# Function to check if required parameters are set
check_parameters() {
    if [ -z "$JWT_SECRET" ]; then
        print_error "JWT_SECRET environment variable is not set."
        exit 1
    fi
    
    if [ -z "$GOOGLE_CLIENT_ID" ]; then
        print_error "GOOGLE_CLIENT_ID environment variable is not set."
        exit 1
    fi
    
    if [ -z "$APPLE_CLIENT_ID" ]; then
        print_error "APPLE_CLIENT_ID environment variable is not set."
        exit 1
    fi
    
    print_status "Required parameters are set."
}

# Function to create S3 bucket for Lambda deployment packages
create_deployment_bucket() {
    BUCKET_NAME="${STACK_PREFIX}-deployment-${ENVIRONMENT}-$(date +%s)"
    
    print_status "Creating S3 bucket for deployment packages: $BUCKET_NAME"
    
    aws s3 mb s3://$BUCKET_NAME --region $REGION --profile $PROFILE
    
    echo $BUCKET_NAME > .deployment-bucket
    print_status "Deployment bucket created: $BUCKET_NAME"
}

# Function to package and upload Lambda functions
package_lambda_functions() {
    BUCKET_NAME=$(cat .deployment-bucket)
    
    print_status "Packaging Lambda functions..."
    
    # Create deployment packages for each Lambda function
    for lambda_dir in lambdas/*/; do
        lambda_name=$(basename $lambda_dir)
        print_status "Packaging $lambda_name..."
        
        # Create deployment package
        cd $lambda_dir
        zip -r ../../deployment-packages/${lambda_name}.zip . -x "*.pyc" "__pycache__/*"
        cd ../..
        
        # Upload to S3
        aws s3 cp deployment-packages/${lambda_name}.zip s3://$BUCKET_NAME/lambda-functions/ --profile $PROFILE
        print_status "Uploaded $lambda_name.zip to S3"
    done
}

# Function to deploy DynamoDB tables
deploy_dynamodb() {
    print_status "Deploying DynamoDB tables..."
    
    aws cloudformation deploy \
        --template-file infrastructure/dynamodb-tables.yaml \
        --stack-name ${STACK_PREFIX}-dynamodb-${ENVIRONMENT} \
        --region $REGION \
        --profile $PROFILE \
        --capabilities CAPABILITY_IAM
    
    print_status "DynamoDB tables deployed successfully."
}

# Function to deploy Lambda functions
deploy_lambda_functions() {
    BUCKET_NAME=$(cat .deployment-bucket)
    
    print_status "Deploying Lambda functions..."
    
    aws cloudformation deploy \
        --template-file infrastructure/lambda-functions.yaml \
        --stack-name ${STACK_PREFIX}-lambda-${ENVIRONMENT} \
        --region $REGION \
        --profile $PROFILE \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
            Environment=$ENVIRONMENT \
            JWTSecret=$JWT_SECRET \
            GoogleClientId=$GOOGLE_CLIENT_ID \
            AppleClientId=$APPLE_CLIENT_ID \
            FrontendUrl=$FRONTEND_URL
    
    print_status "Lambda functions deployed successfully."
}

# Function to deploy API Gateway
deploy_api_gateway() {
    print_status "Deploying API Gateway..."
    
    aws cloudformation deploy \
        --template-file infrastructure/api-gateway.yaml \
        --stack-name ${STACK_PREFIX}-api-${ENVIRONMENT} \
        --region $REGION \
        --profile $PROFILE \
        --capabilities CAPABILITY_IAM \
        --parameter-overrides \
            Environment=$ENVIRONMENT
    
    print_status "API Gateway deployed successfully."
}

# Function to update Lambda function code
update_lambda_code() {
    BUCKET_NAME=$(cat .deployment-bucket)
    
    print_status "Updating Lambda function code..."
    
    # Get Lambda function names from the stack
    LAMBDA_FUNCTIONS=(
        "ukiyo-google-auth"
        "ukiyo-phone-auth"
        "ukiyo-email-auth"
        "ukiyo-products"
        "ukiyo-cart"
        "ukiyo-wishlist"
        "ukiyo-checkout"
        "ukiyo-admin-inventory"
        "ukiyo-admin-analytics"
        "ukiyo-admin-returns"
        "ukiyo-user-profile"
    )
    
    for func_name in "${LAMBDA_FUNCTIONS[@]}"; do
        print_status "Updating $func_name..."
        
        # Get the corresponding zip file name
        zip_name=$(echo $func_name | sed 's/ukiyo-//' | sed 's/-/_/g').zip
        
        aws lambda update-function-code \
            --function-name $func_name \
            --s3-bucket $BUCKET_NAME \
            --s3-key lambda-functions/$zip_name \
            --region $REGION \
            --profile $PROFILE
        
        print_status "Updated $func_name"
    done
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Install test dependencies
    pip install -r requirements.txt
    
    # Run tests (if test files exist)
    if [ -d "tests" ]; then
        python -m pytest tests/ -v
    else
        print_warning "No tests found. Skipping test execution."
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up temporary files..."
    
    rm -rf deployment-packages/
    rm -f .deployment-bucket
    
    print_status "Cleanup completed."
}

# Function to show deployment summary
show_summary() {
    print_status "Deployment Summary:"
    echo "==================="
    echo "Environment: $ENVIRONMENT"
    echo "Region: $REGION"
    echo "Profile: $PROFILE"
    echo ""
    
    # Get API Gateway URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name ${STACK_PREFIX}-api-${ENVIRONMENT} \
        --region $REGION \
        --profile $PROFILE \
        --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
        --output text)
    
    echo "API Endpoint: $API_URL"
    echo ""
    echo "Available endpoints:"
    echo "- POST $API_URL/auth/google"
    echo "- POST $API_URL/auth/phone/send-otp"
    echo "- POST $API_URL/auth/phone/verify-otp"
    echo "- GET $API_URL/products"
    echo "- GET $API_URL/cart"
    echo "- POST $API_URL/cart/add"
    echo "- GET $API_URL/wishlist"
    echo "- POST $API_URL/wishlist/add"
    echo "- POST $API_URL/checkout/create-order"
    echo "- GET $API_URL/admin/products"
    echo "- GET $API_URL/user/profile"
    echo ""
    print_status "Deployment completed successfully!"
}

# Main deployment function
main() {
    print_status "Starting Ukiyo backend deployment..."
    print_status "Environment: $ENVIRONMENT"
    print_status "Region: $REGION"
    print_status "Profile: $PROFILE"
    
    # Check prerequisites
    check_aws_cli
    check_parameters
    
    # Create deployment directory
    mkdir -p deployment-packages
    
    # Deploy infrastructure
    create_deployment_bucket
    package_lambda_functions
    deploy_dynamodb
    deploy_lambda_functions
    deploy_api_gateway
    
    # Update Lambda code
    update_lambda_code
    
    # Run tests
    run_tests
    
    # Show summary
    show_summary
    
    # Cleanup
    cleanup
}

# Handle script arguments
case "${1:-}" in
    "deploy")
        main
        ;;
    "update")
        print_status "Updating Lambda function code..."
        check_aws_cli
        package_lambda_functions
        update_lambda_code
        cleanup
        print_status "Update completed!"
        ;;
    "test")
        print_status "Running tests..."
        run_tests
        ;;
    "cleanup")
        print_status "Cleaning up resources..."
        # Add cleanup logic here
        ;;
    *)
        echo "Usage: $0 {deploy|update|test|cleanup} [environment] [region] [profile]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the entire infrastructure"
        echo "  update   - Update Lambda function code only"
        echo "  test     - Run tests"
        echo "  cleanup  - Clean up resources"
        echo ""
        echo "Environment variables required:"
        echo "  JWT_SECRET        - JWT secret for token signing"
        echo "  GOOGLE_CLIENT_ID  - Google OAuth client ID"
        echo "  APPLE_CLIENT_ID   - Apple Sign-In client ID"
        echo "  FRONTEND_URL      - Frontend URL for CORS (optional)"
        echo ""
        echo "Examples:"
        echo "  $0 deploy production us-east-1 default"
        echo "  $0 update"
        echo "  $0 test"
        exit 1
        ;;
esac
