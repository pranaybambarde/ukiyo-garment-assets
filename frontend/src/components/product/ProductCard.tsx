'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { HeartIcon, EyeIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import { Product } from '@/types';
import { useCart } from '@/context/CartContext';
import { useAuth } from '@/context/AuthContext';
import toast from 'react-hot-toast';

interface ProductCardProps {
  product: Product;
  showQuickActions?: boolean;
  className?: string;
}

export function ProductCard({ 
  product, 
  showQuickActions = true, 
  className = '' 
}: ProductCardProps) {
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const { addToCart, isInCart } = useCart();
  const { isAuthenticated } = useAuth();

  const handleAddToWishlist = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!isAuthenticated) {
      toast.error('Please log in to save items to your wishlist');
      return;
    }

    // TODO: Implement wishlist functionality
    setIsWishlisted(!isWishlisted);
    toast.success(isWishlisted ? 'Removed from wishlist' : 'Added to wishlist');
  };

  const handleQuickAdd = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!product.inStock) {
      toast.error('This item is out of stock');
      return;
    }

    const defaultSize = product.sizes[0];
    const defaultColor = product.colors[0];
    
    if (isInCart(product.id, defaultSize, defaultColor)) {
      toast.error('Item already in cart');
      return;
    }

    await addToCart(product, defaultSize, defaultColor);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div 
      className={`group relative ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Link href={`/products/${product.id}`}>
        {/* Image Container */}
        <div className="relative aspect-square overflow-hidden rounded-lg bg-gray-100 mb-4">
            <Image
              src={product.images[0] || '/placeholder-product.svg'}
              alt={product.name}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
            />
          
          {/* Badges */}
          <div className="absolute top-3 left-3 flex flex-col gap-2">
            {product.newArrival && (
              <span className="bg-green-500 text-white text-xs font-semibold px-2 py-1 rounded-full">
                New
              </span>
            )}
            {product.featured && (
              <span className="bg-red-500 text-white text-xs font-semibold px-2 py-1 rounded-full">
                Sale
              </span>
            )}
            {!product.inStock && (
              <span className="bg-gray-500 text-white text-xs font-semibold px-2 py-1 rounded-full">
                Out of Stock
              </span>
            )}
          </div>

          {/* Quick Actions */}
          {showQuickActions && isHovered && (
            <div className="absolute top-3 right-3 flex flex-col gap-2">
              <button
                onClick={handleAddToWishlist}
                className="p-2 bg-white rounded-full shadow-md hover:bg-gray-50 transition-colors"
                aria-label={isWishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
              >
                {isWishlisted ? (
                  <HeartSolidIcon className="h-4 w-4 text-red-500" />
                ) : (
                  <HeartIcon className="h-4 w-4 text-gray-600" />
                )}
              </button>
              <button
                className="p-2 bg-white rounded-full shadow-md hover:bg-gray-50 transition-colors"
                aria-label="Quick view"
              >
                <EyeIcon className="h-4 w-4 text-gray-600" />
              </button>
            </div>
          )}

          {/* Quick Add Button */}
          {showQuickActions && isHovered && product.inStock && (
            <div className="absolute bottom-3 left-3 right-3">
              <button
                onClick={handleQuickAdd}
                className="w-full bg-gray-900 text-white py-2 px-4 rounded-lg font-medium hover:bg-gray-800 transition-colors"
              >
                Quick Add
              </button>
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="space-y-2">
          <h3 className="font-medium text-gray-900 group-hover:text-gray-600 transition-colors line-clamp-2">
            {product.name}
          </h3>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-lg font-semibold text-gray-900">
                {formatPrice(product.price)}
              </span>
              {product.originalPrice && product.originalPrice > product.price && (
                <span className="text-sm text-gray-500 line-through">
                  {formatPrice(product.originalPrice)}
                </span>
              )}
            </div>
            
            {product.rating && (
              <div className="flex items-center space-x-1">
                <span className="text-sm text-gray-500">
                  {product.rating.toFixed(1)}
                </span>
                <div className="flex">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <span
                      key={i}
                      className={`text-xs ${
                        i < Math.floor(product.rating || 0)
                          ? 'text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    >
                      ★
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Color Options */}
          {product.colors.length > 1 && (
            <div className="flex space-x-1">
              {product.colors.slice(0, 4).map((color, index) => (
                <div
                  key={index}
                  className="w-4 h-4 rounded-full border border-gray-300"
                  style={{ backgroundColor: color.toLowerCase() }}
                  title={color}
                />
              ))}
              {product.colors.length > 4 && (
                <span className="text-xs text-gray-500">
                  +{product.colors.length - 4}
                </span>
              )}
            </div>
          )}

          {/* Additional Info */}
          <div className="text-sm text-gray-500">
            {product.fabric} • {product.category}
          </div>
        </div>
      </Link>
    </div>
  );
}
