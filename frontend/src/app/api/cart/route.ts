import { NextRequest, NextResponse } from 'next/server';
import { CartItem } from '@/types';

// Mock cart data - in a real app, this would be stored in a database
let mockCart: CartItem[] = [];

export async function GET() {
  try {
    return NextResponse.json({
      success: true,
      data: mockCart,
    });
  } catch (error) {
    console.error('Error fetching cart:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch cart' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { productId, size, color, quantity = 1 } = body;
    
    // In a real app, you would:
    // 1. Validate the product exists
    // 2. Check stock availability
    // 3. Get user ID from authentication
    // 4. Store in database
    
    const newItem: CartItem = {
      id: `${productId}-${size}-${color}-${Date.now()}`,
      productId,
      product: {
        id: productId,
        name: 'Mock Product',
        description: 'Mock product description',
        price: 1999,
        images: ['/placeholder-product.svg'],
        category: 'clothing',
        sizes: [size],
        colors: [color],
        fabric: 'cotton',
        occasion: ['casual'],
        inStock: true,
        stock: { [size]: 10 },
        featured: false,
        newArrival: false,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      size,
      color,
      quantity,
      price: 1999,
    };
    
    // Check if item already exists
    const existingItemIndex = mockCart.findIndex(
      item => item.productId === productId && item.size === size && item.color === color
    );
    
    if (existingItemIndex >= 0) {
      mockCart[existingItemIndex].quantity += quantity;
    } else {
      mockCart.push(newItem);
    }
    
    return NextResponse.json({
      success: true,
      data: mockCart,
    });
  } catch (error) {
    console.error('Error adding to cart:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to add to cart' },
      { status: 500 }
    );
  }
}

export async function DELETE() {
  try {
    mockCart = [];
    return NextResponse.json({
      success: true,
      data: [],
    });
  } catch (error) {
    console.error('Error clearing cart:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to clear cart' },
      { status: 500 }
    );
  }
}
