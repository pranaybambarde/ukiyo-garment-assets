'use client';

import React, { useState, useEffect } from 'react';
import { XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { Product } from '@/types';
import Link from 'next/link';
import Image from 'next/image';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Search products
  const { data: searchResults = [], isLoading } = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery.trim()) return [];
      const response = await fetch(`/api/products/search?q=${encodeURIComponent(debouncedQuery)}`);
      const result = await response.json();
      return result.data || [];
    },
    enabled: debouncedQuery.length > 2,
  });

  // Close modal on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      const input = document.getElementById('search-input');
      input?.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-x-0 top-0 bg-white shadow-lg">
        <div className="max-w-4xl mx-auto">
          {/* Search input */}
          <div className="flex items-center p-4 border-b border-gray-200">
            <MagnifyingGlassIcon className="h-6 w-6 text-gray-400 mr-3" />
            <input
              id="search-input"
              type="text"
              placeholder="Search products..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 text-lg outline-none placeholder-gray-400"
            />
            <button
              onClick={onClose}
              className="ml-3 p-2 text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Search results */}
          <div className="max-h-96 overflow-y-auto">
            {query.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <MagnifyingGlassIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Start typing to search products</p>
              </div>
            ) : query.length < 3 ? (
              <div className="p-8 text-center text-gray-500">
                <p>Type at least 3 characters to search</p>
              </div>
            ) : isLoading ? (
              <div className="p-8 text-center text-gray-500">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
                <p className="mt-2">Searching...</p>
              </div>
            ) : searchResults.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <p>No products found for &quot;{query}&quot;</p>
              </div>
            ) : (
              <div className="p-4 space-y-4">
                <p className="text-sm text-gray-500">
                  {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} for &quot;{query}&quot;
                </p>
                {searchResults.map((product: Product) => (
                  <Link
                    key={product.id}
                    href={`/products/${product.id}`}
                    onClick={onClose}
                    className="flex items-center space-x-4 p-3 hover:bg-gray-50 rounded-lg transition-colors"
                  >
                    <div className="relative w-16 h-16 flex-shrink-0">
                      <Image
                        src={product.images[0] || '/placeholder-product.svg'}
                        alt={product.name}
                        fill
                        className="object-cover rounded-md"
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {product.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {product.category} • {product.fabric}
                      </p>
                      <p className="text-sm font-medium text-gray-900">
                        ₹{product.price.toLocaleString()}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
