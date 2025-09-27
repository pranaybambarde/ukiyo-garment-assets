'use client';

import React from 'react';
import Link from 'next/link';
import { XMarkIcon, UserIcon, HeartIcon, ShoppingBagIcon } from '@heroicons/react/24/outline';
import { User } from '@/types';
import { useCart } from '@/context/CartContext';

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  navigation: Array<{ name: string; href: string }>;
  isAuthenticated: boolean;
  user: User | null;
  onLogout: () => void;
}

export function MobileMenu({
  isOpen,
  onClose,
  navigation,
  isAuthenticated,
  user,
  onLogout,
}: MobileMenuProps) {
  const { itemCount } = useCart();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-25"
        onClick={onClose}
      />

      {/* Menu panel */}
      <div className="fixed inset-y-0 right-0 w-full max-w-sm bg-white shadow-xl">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <span className="text-xl font-bold text-gray-900">Menu</span>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-4">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className="block text-lg font-medium text-gray-700 hover:text-gray-900 transition-colors"
              >
                {item.name}
              </Link>
            ))}
          </nav>

          {/* User section */}
          <div className="border-t border-gray-200 p-4 space-y-4">
            {isAuthenticated ? (
              <>
                <div className="flex items-center space-x-3">
                  <UserIcon className="h-6 w-6 text-gray-400" />
                  <div>
                    <p className="font-medium text-gray-900">{user?.name}</p>
                    <p className="text-sm text-gray-500">{user?.email}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Link
                    href="/profile"
                    onClick={onClose}
                    className="flex items-center space-x-3 text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    <UserIcon className="h-5 w-5" />
                    <span>Profile</span>
                  </Link>
                  <Link
                    href="/orders"
                    onClick={onClose}
                    className="flex items-center space-x-3 text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    <span>Orders</span>
                  </Link>
                  <button
                    onClick={onLogout}
                    className="flex items-center space-x-3 text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    <span>Logout</span>
                  </button>
                </div>
              </>
            ) : (
              <Link
                href="/login"
                onClick={onClose}
                className="flex items-center space-x-3 text-gray-700 hover:text-gray-900 transition-colors"
              >
                <UserIcon className="h-5 w-5" />
                <span>Login / Sign Up</span>
              </Link>
            )}

            {/* Quick actions */}
            <div className="space-y-2">
              <Link
                href="/wishlist"
                onClick={onClose}
                className="flex items-center space-x-3 text-gray-700 hover:text-gray-900 transition-colors"
              >
                <HeartIcon className="h-5 w-5" />
                <span>Wishlist</span>
              </Link>
              <Link
                href="/cart"
                onClick={onClose}
                className="flex items-center space-x-3 text-gray-700 hover:text-gray-900 transition-colors"
              >
                <ShoppingBagIcon className="h-5 w-5" />
                <span>Cart ({itemCount})</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
