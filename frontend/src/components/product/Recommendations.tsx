'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Product } from '@/types';
import { ProductCard } from './ProductCard';

interface RecommendationsProps {
  title: string;
  subtitle?: string;
  productIds?: string[];
  limit?: number;
  className?: string;
}

export function Recommendations({
  title,
  subtitle,
  productIds = [],
  limit = 8,
  className = '',
}: RecommendationsProps) {
  const { data: products = [], isLoading } = useQuery({
    queryKey: ['recommendations', productIds, limit],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (productIds.length > 0) {
        params.set('relatedTo', productIds.join(','));
      }
      params.set('limit', limit.toString());
      
      const response = await fetch(`/api/products/recommendations?${params.toString()}`);
      const result = await response.json();
      return result.data || [];
    },
  });

  if (isLoading) {
    return (
      <div className={`${className}`}>
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
          {subtitle && (
            <p className="text-gray-600">{subtitle}</p>
          )}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="bg-gray-300 aspect-square rounded-lg mb-4"></div>
              <div className="h-4 bg-gray-300 rounded mb-2"></div>
              <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (products.length === 0) {
    return null;
  }

  return (
    <div className={`${className}`}>
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
        {subtitle && (
          <p className="text-gray-600">{subtitle}</p>
        )}
      </div>

      {/* Desktop: Show all products in a grid */}
      <div className="hidden md:grid grid-cols-2 lg:grid-cols-4 gap-6">
        {products.map((product: Product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>

      {/* Mobile: Horizontal scroll */}
      <div className="md:hidden">
        <div className="flex space-x-4 overflow-x-auto pb-4">
          {products.map((product: Product) => (
            <div key={product.id} className="flex-shrink-0 w-48">
              <ProductCard product={product} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
