import { NextRequest, NextResponse } from 'next/server';
import { Product, ProductFilters, PaginatedResponse } from '@/types';

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
  // Add more mock products...
];

function filterProducts(products: Product[], filters: ProductFilters): Product[] {
  return products.filter(product => {
    // Category filter
    if (filters.category && product.category !== filters.category) return false;
    
    // Subcategory filter
    if (filters.subcategory && product.subcategory !== filters.subcategory) return false;
    
    // Price range filter
    if (filters.priceMin && product.price < filters.priceMin) return false;
    if (filters.priceMax && product.price > filters.priceMax) return false;
    
    // Size filter
    if (filters.size && filters.size.length > 0) {
      const hasMatchingSize = filters.size.some(size => product.sizes.includes(size));
      if (!hasMatchingSize) return false;
    }
    
    // Color filter
    if (filters.color && filters.color.length > 0) {
      const hasMatchingColor = filters.color.some(color => product.colors.includes(color));
      if (!hasMatchingColor) return false;
    }
    
    // Fabric filter
    if (filters.fabric && filters.fabric.length > 0) {
      if (!filters.fabric.includes(product.fabric)) return false;
    }
    
    // Occasion filter
    if (filters.occasion && filters.occasion.length > 0) {
      const hasMatchingOccasion = filters.occasion.some(occasion => 
        product.occasion.includes(occasion)
      );
      if (!hasMatchingOccasion) return false;
    }
    
    // Skin tone filter
    if (filters.skinTone && filters.skinTone.length > 0 && product.skinTone) {
      const hasMatchingSkinTone = filters.skinTone.some(tone => product.skinTone?.includes(tone));
      if (!hasMatchingSkinTone) return false;
    }
    
    // Body shape filter
    if (filters.bodyShape && filters.bodyShape.length > 0 && product.bodyShape) {
      const hasMatchingBodyShape = filters.bodyShape.some(shape => product.bodyShape?.includes(shape));
      if (!hasMatchingBodyShape) return false;
    }
    
    // Stock filter
    if (filters.inStock && !product.inStock) return false;
    
    // Featured filter
    if (filters.featured && !product.featured) return false;
    
    // New arrival filter
    if (filters.newArrival && !product.newArrival) return false;
    
    // Search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      const searchableText = [
        product.name,
        product.description,
        product.category,
        product.subcategory,
        product.fabric,
        ...product.occasion,
      ].join(' ').toLowerCase();
      
      if (!searchableText.includes(searchTerm)) return false;
    }
    
    return true;
  });
}

function sortProducts(products: Product[], sortBy: string): Product[] {
  switch (sortBy) {
    case 'price-asc':
      return [...products].sort((a, b) => a.price - b.price);
    case 'price-desc':
      return [...products].sort((a, b) => b.price - a.price);
    case 'newest':
      return [...products].sort((a, b) => 
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
    case 'popular':
      return [...products].sort((a, b) => (b.reviewCount || 0) - (a.reviewCount || 0));
    case 'rating':
      return [...products].sort((a, b) => (b.rating || 0) - (a.rating || 0));
    default:
      return products;
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    
    // Parse filters from query parameters
    const filters: ProductFilters = {
      category: searchParams.get('category') || undefined,
      subcategory: searchParams.get('subcategory') || undefined,
      priceMin: searchParams.get('priceMin') ? Number(searchParams.get('priceMin')) : undefined,
      priceMax: searchParams.get('priceMax') ? Number(searchParams.get('priceMax')) : undefined,
      size: searchParams.get('size')?.split(',').filter(Boolean) || undefined,
      color: searchParams.get('color')?.split(',').filter(Boolean) || undefined,
      fabric: searchParams.get('fabric')?.split(',').filter(Boolean) || undefined,
      occasion: searchParams.get('occasion')?.split(',').filter(Boolean) || undefined,
      skinTone: searchParams.get('skinTone')?.split(',').filter(Boolean) || undefined,
      bodyShape: searchParams.get('bodyShape')?.split(',').filter(Boolean) || undefined,
      inStock: searchParams.get('inStock') === 'true' ? true : undefined,
      featured: searchParams.get('featured') === 'true' ? true : undefined,
      newArrival: searchParams.get('newArrival') === 'true' ? true : undefined,
      search: searchParams.get('search') || undefined,
      sortBy: (searchParams.get('sortBy') as ProductFilters['sortBy']) || 'newest',
    };
    
    // Pagination
    const page = Number(searchParams.get('page')) || 1;
    const limit = Number(searchParams.get('limit')) || 12;
    const offset = (page - 1) * limit;
    
    // Filter and sort products
    let filteredProducts = filterProducts(mockProducts, filters);
    filteredProducts = sortProducts(filteredProducts, filters.sortBy || 'newest');
    
    // Paginate results
    const total = filteredProducts.length;
    const paginatedProducts = filteredProducts.slice(offset, offset + limit);
    
    const response: PaginatedResponse<Product> = {
      data: paginatedProducts,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
    
    return NextResponse.json({
      success: true,
      data: response.data,
      pagination: response.pagination,
    });
    
  } catch (error) {
    console.error('Error fetching products:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch products' },
      { status: 500 }
    );
  }
}