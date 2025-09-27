'use client';

import React from 'react';
import Link from 'next/link';
import { useCart } from '@/context/CartContext';
import { useAuth } from '@/context/AuthContext';

export function CartSummary() {
  const { total, itemCount } = useCart();
  const { isAuthenticated } = useAuth();

  const subtotal = total;
  const shipping = subtotal >= 2000 ? 0 : 200; // Free shipping over ₹2,000
  const tax = Math.round(subtotal * 0.18); // 18% GST
  const finalTotal = subtotal + shipping + tax;

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sticky top-8">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Order Summary</h2>

      {/* Order Details */}
      <div className="space-y-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Subtotal ({itemCount} items)</span>
          <span className="font-medium">{formatPrice(subtotal)}</span>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Shipping</span>
          <span className="font-medium">
            {shipping === 0 ? (
              <span className="text-green-600">Free</span>
            ) : (
              formatPrice(shipping)
            )}
          </span>
        </div>

        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Tax (GST)</span>
          <span className="font-medium">{formatPrice(tax)}</span>
        </div>

        <div className="border-t border-gray-200 pt-4">
          <div className="flex justify-between text-lg font-semibold">
            <span>Total</span>
            <span>{formatPrice(finalTotal)}</span>
          </div>
        </div>

        {/* Free Shipping Notice */}
        {shipping > 0 && (
          <div className="text-sm text-gray-500 text-center">
            Add {formatPrice(2000 - subtotal)} more for free shipping
          </div>
        )}

        {shipping === 0 && (
          <div className="text-sm text-green-600 text-center font-medium">
            🎉 You qualify for free shipping!
          </div>
        )}
      </div>

      {/* Checkout Button */}
      <div className="mt-6 space-y-3">
        <Link
          href="/checkout"
          className="w-full flex justify-center items-center px-4 py-3 bg-gray-900 text-white font-medium rounded-lg hover:bg-gray-800 transition-colors"
        >
          Proceed to Checkout
        </Link>

        {!isAuthenticated && (
          <Link
            href="/login"
            className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
          >
            Log in for faster checkout
          </Link>
        )}
      </div>

      {/* Security Notice */}
      <div className="mt-6 text-xs text-gray-500 text-center">
        <div className="flex items-center justify-center space-x-2">
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
          </svg>
          <span>Secure checkout with 256-bit SSL encryption</span>
        </div>
      </div>

      {/* Payment Methods */}
      <div className="mt-4">
        <p className="text-xs text-gray-500 text-center mb-2">We accept</p>
        <div className="flex justify-center space-x-2">
          <div className="w-8 h-5 bg-gray-200 rounded text-xs flex items-center justify-center">VISA</div>
          <div className="w-8 h-5 bg-gray-200 rounded text-xs flex items-center justify-center">MC</div>
          <div className="w-8 h-5 bg-gray-200 rounded text-xs flex items-center justify-center">UPI</div>
          <div className="w-8 h-5 bg-gray-200 rounded text-xs flex items-center justify-center">RZP</div>
        </div>
      </div>
    </div>
  );
}
