import { NextRequest, NextResponse } from 'next/server';
import { Product } from '@/types';

// Mock data - in a real app, this would come from a database
const mockProducts: Product[] = [
  {
    id: '1',
    name: 'Premium Yoga Leggings',
    description: 'High-waisted leggings with four-way stretch and moisture-wicking fabric',
    price: 2999,
    originalPrice: 3999,
    images: ['/products/leggings-1.jpg', '/products/leggings-2.jpg'],
    category: 'clothing',
    subcategory: 'leggings',
    sizes: ['S', 'M', 'L', 'XL'],
    colors: ['black', 'navy', 'gray'],
    fabric: 'polyester',
    occasion: ['yoga', 'gym', 'casual'],
    skinTone: ['light', 'medium', 'dark'],
    bodyShape: ['pear', 'hourglass', 'rectangle'],
    inStock: true,
    stock: { 'S': 10, 'M': 15, 'L': 12, 'XL': 8 },
    featured: true,
    newArrival: true,
    rating: 4.8,
    reviewCount: 124,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    name: 'Luxury Sports Bra',
    description: 'Wireless sports bra with maximum support and comfort',
    price: 1999,
    images: ['/products/bra-1.jpg', '/products/bra-2.jpg'],
    category: 'clothing',
    subcategory: 'sports-bra',
    sizes: ['S', 'M', 'L'],
    colors: ['white', 'black', 'pink'],
    fabric: 'spandex',
    occasion: ['yoga', 'gym'],
    skinTone: ['light', 'medium', 'dark'],
    bodyShape: ['pear', 'apple', 'hourglass'],
    inStock: true,
    stock: { 'S': 8, 'M': 12, 'L': 10 },
    featured: false,
    newArrival: false,
    rating: 4.6,
    reviewCount: 89,
    createdAt: '2024-01-10T10:00:00Z',
    updatedAt: '2024-01-10T10:00:00Z',
  },
  {
    id: '3',
    name: 'Elegant Work Blouse',
    description: 'Professional blouse perfect for office and evening wear',
    price: 3999,
    images: ['/products/blouse-1.jpg', '/products/blouse-2.jpg'],
    category: 'clothing',
    subcategory: 'blouse',
    sizes: ['XS', 'S', 'M', 'L', 'XL'],
    colors: ['white', 'navy', 'beige'],
    fabric: 'silk',
    occasion: ['work', 'evening'],
    skinTone: ['light', 'medium', 'dark'],
    bodyShape: ['pear', 'hourglass', 'rectangle'],
    inStock: true,
    stock: { 'XS': 5, 'S': 8, 'M': 12, 'L': 10, 'XL': 6 },
    featured: true,
    newArrival: false,
    rating: 4.9,
    reviewCount: 156,
    createdAt: '2024-01-05T10:00:00Z',
    updatedAt: '2024-01-05T10:00:00Z',
  },
  {
    id: '4',
    name: 'Comfortable Yoga Top',
    description: 'Breathable and stretchy top perfect for yoga and pilates',
    price: 2499,
    images: ['/products/top-1.jpg', '/products/top-2.jpg'],
    category: 'clothing',
    subcategory: 'top',
    sizes: ['S', 'M', 'L', 'XL'],
    colors: ['white', 'black', 'gray'],
    fabric: 'modal',
    occasion: ['yoga', 'gym', 'casual'],
    skinTone: ['light', 'medium', 'dark'],
    bodyShape: ['pear', 'apple', 'hourglass', 'rectangle'],
    inStock: true,
    stock: { 'S': 12, 'M': 15, 'L': 10, 'XL': 8 },
    featured: false,
    newArrival: true,
    rating: 4.7,
    reviewCount: 98,
    createdAt: '2024-01-12T10:00:00Z',
    updatedAt: '2024-01-12T10:00:00Z',
  },
  {
    id: '5',
    name: 'Luxury Evening Dress',
    description: 'Elegant dress perfect for special occasions and evening events',
    price: 5999,
    images: ['/products/dress-1.jpg', '/products/dress-2.jpg'],
    category: 'clothing',
    subcategory: 'dress',
    sizes: ['XS', 'S', 'M', 'L', 'XL'],
    colors: ['black', 'navy', 'burgundy'],
    fabric: 'silk',
    occasion: ['evening', 'work'],
    skinTone: ['light', 'medium', 'dark'],
    bodyShape: ['pear', 'hourglass', 'rectangle'],
    inStock: true,
    stock: { 'XS': 3, 'S': 6, 'M': 8, 'L': 5, 'XL': 4 },
    featured: true,
    newArrival: false,
    rating: 4.9,
    reviewCount: 203,
    createdAt: '2024-01-08T10:00:00Z',
    updatedAt: '2024-01-08T10:00:00Z',
  },
];

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const relatedTo = searchParams.get('relatedTo');
    const limit = Number(searchParams.get('limit')) || 8;
    
    let recommendations = [...mockProducts];
    
    // If related products are specified, filter to show complementary items
    if (relatedTo) {
      const relatedIds = relatedTo.split(',');
      const relatedProducts = mockProducts.filter(p => relatedIds.includes(p.id));
      
      if (relatedProducts.length > 0) {
        // Simple recommendation logic: show products from different categories
        const relatedCategories = relatedProducts.map(p => p.category);
        recommendations = mockProducts.filter(p => 
          !relatedIds.includes(p.id) && 
          !relatedCategories.includes(p.category)
        );
      }
    }
    
    // Shuffle and limit results
    const shuffled = recommendations.sort(() => 0.5 - Math.random());
    const limited = shuffled.slice(0, limit);
    
    return NextResponse.json({
      success: true,
      data: limited,
    });
    
  } catch (error) {
    console.error('Error fetching recommendations:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch recommendations' },
      { status: 500 }
    );
  }
}
