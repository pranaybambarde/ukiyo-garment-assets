'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { TrashIcon, MinusIcon, PlusIcon } from '@heroicons/react/24/outline';
import { CartItem as CartItemType } from '@/types';
import { useCart } from '@/context/CartContext';

interface CartItemProps {
  item: CartItemType;
}

export function CartItem({ item }: CartItemProps) {
  const { updateQuantity, removeFromCart } = useCart();

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity <= 0) {
      removeFromCart(item.id);
    } else {
      updateQuantity(item.id, newQuantity);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-start space-x-4">
        {/* Product Image */}
        <Link href={`/products/${item.productId}`} className="flex-shrink-0">
          <div className="relative w-24 h-24 rounded-lg overflow-hidden bg-gray-100">
            <Image
              src={item.product.images[0] || '/placeholder-product.svg'}
              alt={item.product.name}
              fill
              className="object-cover"
            />
          </div>
        </Link>

        {/* Product Details */}
        <div className="flex-1 min-w-0">
          <Link href={`/products/${item.productId}`}>
            <h3 className="text-lg font-medium text-gray-900 hover:text-gray-600 transition-colors">
              {item.product.name}
            </h3>
          </Link>
          
          <div className="mt-1 text-sm text-gray-500">
            <p>Size: {item.size}</p>
            <p>Color: {item.color}</p>
            <p>Fabric: {item.product.fabric}</p>
          </div>

          <div className="mt-2 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* Quantity Controls */}
              <div className="flex items-center border border-gray-300 rounded-lg">
                <button
                  onClick={() => handleQuantityChange(item.quantity - 1)}
                  className="p-2 hover:bg-gray-50 transition-colors"
                  disabled={item.quantity <= 1}
                >
                  <MinusIcon className="h-4 w-4 text-gray-600" />
                </button>
                
                <span className="px-3 py-2 text-sm font-medium text-gray-900 min-w-[3rem] text-center">
                  {item.quantity}
                </span>
                
                <button
                  onClick={() => handleQuantityChange(item.quantity + 1)}
                  className="p-2 hover:bg-gray-50 transition-colors"
                >
                  <PlusIcon className="h-4 w-4 text-gray-600" />
                </button>
              </div>

              {/* Price */}
              <div className="text-lg font-semibold text-gray-900">
                {formatPrice(item.price * item.quantity)}
              </div>
            </div>

            {/* Remove Button */}
            <button
              onClick={() => removeFromCart(item.id)}
              className="p-2 text-gray-400 hover:text-red-500 transition-colors"
              aria-label="Remove item"
            >
              <TrashIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Stock Status */}
          {!item.product.inStock && (
            <div className="mt-2 text-sm text-red-600">
              This item is currently out of stock
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
