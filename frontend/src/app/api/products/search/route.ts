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
];

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q');
    
    if (!query || query.length < 2) {
      return NextResponse.json({
        success: true,
        data: [],
      });
    }
    
    const searchTerm = query.toLowerCase();
    
    // Simple search implementation
    const results = mockProducts.filter(product => {
      const searchableText = [
        product.name,
        product.description,
        product.category,
        product.subcategory,
        product.fabric,
        ...product.occasion,
        ...product.colors,
      ].join(' ').toLowerCase();
      
      return searchableText.includes(searchTerm);
    });
    
    // Limit results for search suggestions
    const limitedResults = results.slice(0, 8);
    
    return NextResponse.json({
      success: true,
      data: limitedResults,
    });
    
  } catch (error) {
    console.error('Error searching products:', error);
    return NextResponse.json(
      { success: false, error: 'Search failed' },
      { status: 500 }
    );
  }
}
