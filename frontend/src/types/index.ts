// User and Authentication Types
export interface User {
  id: string;
  email: string;
  name: string;
  phone?: string;
  role: 'user' | 'admin';
  profile?: UserProfile;
  createdAt: string;
  updatedAt: string;
}

export interface UserProfile {
  skinTone?: 'light' | 'medium' | 'dark' | 'deep';
  bodyShape?: 'pear' | 'apple' | 'hourglass' | 'rectangle' | 'inverted-triangle';
  height?: number;
  preferences?: {
    size?: string;
    colors?: string[];
    styles?: string[];
  };
}

// Product Types
export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  originalPrice?: number;
  images: string[];
  category: string;
  subcategory?: string;
  sizes: string[];
  colors: string[];
  fabric: string;
  occasion: string[];
  skinTone?: string[];
  bodyShape?: string[];
  inStock: boolean;
  stock: Record<string, number>;
  featured: boolean;
  newArrival: boolean;
  rating?: number;
  reviewCount?: number;
  createdAt: string;
  updatedAt: string;
}

export interface ProductVariant {
  id: string;
  productId: string;
  size: string;
  color: string;
  price: number;
  stock: number;
  images: string[];
}

// Cart and Wishlist Types
export interface CartItem {
  id: string;
  productId: string;
  product: Product;
  size: string;
  color: string;
  quantity: number;
  price: number;
}

export interface WishlistItem {
  id: string;
  productId: string;
  product: Product;
  addedAt: string;
}

// Order Types
export interface Order {
  id: string;
  userId: string;
  items: OrderItem[];
  shippingAddress: Address;
  billingAddress?: Address;
  subtotal: number;
  shipping: number;
  tax: number;
  total: number;
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  paymentStatus: 'pending' | 'paid' | 'failed' | 'refunded';
  paymentMethod: string;
  trackingNumber?: string;
  createdAt: string;
  updatedAt: string;
}

export interface OrderItem {
  id: string;
  productId: string;
  product: Product;
  size: string;
  color: string;
  quantity: number;
  price: number;
}

export interface Address {
  id?: string;
  name: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  isDefault?: boolean;
}

// Filter Types
export interface ProductFilters {
  category?: string;
  subcategory?: string;
  priceMin?: number;
  priceMax?: number;
  size?: string[];
  color?: string[];
  fabric?: string[];
  occasion?: string[];
  skinTone?: string[];
  bodyShape?: string[];
  inStock?: boolean;
  featured?: boolean;
  newArrival?: boolean;
  search?: string;
  sortBy?: 'price-asc' | 'price-desc' | 'newest' | 'popular' | 'rating';
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Auth Types
export interface LoginCredentials {
  email?: string;
  phone?: string;
  password?: string;
  otp?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken?: string;
}

// Checkout Types
export interface CheckoutData {
  contactInfo: {
    email: string;
    phone: string;
  };
  shippingAddress: Address;
  billingAddress?: Address;
  shippingMethod: string;
  paymentMethod: string;
  notes?: string;
}

// Admin Types
export interface AnalyticsData {
  totalSales: number;
  totalOrders: number;
  totalUsers: number;
  topProducts: Array<{
    productId: string;
    product: Product;
    sales: number;
  }>;
  salesOverTime: Array<{
    date: string;
    sales: number;
    orders: number;
  }>;
}

export interface ReturnRequest {
  id: string;
  orderId: string;
  order: Order;
  items: Array<{
    orderItemId: string;
    product: Product;
    quantity: number;
    reason: string;
  }>;
  status: 'pending' | 'approved' | 'rejected' | 'processed';
  reason: string;
  createdAt: string;
  updatedAt: string;
}
