'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { CartItem, Product } from '@/types';
import { useAuth } from './AuthContext';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

interface CartContextType {
  items: CartItem[];
  itemCount: number;
  total: number;
  isLoading: boolean;
  addToCart: (product: Product, size: string, color: string, quantity?: number) => Promise<void>;
  removeFromCart: (itemId: string) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  clearCart: () => Promise<void>;
  mergeGuestCart: () => Promise<void>;
  isInCart: (productId: string, size: string, color: string) => boolean;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

const CART_STORAGE_KEY = 'ukiyo_guest_cart';

export function CartProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const [guestCart, setGuestCart] = useState<CartItem[]>([]);

  // Load guest cart from localStorage on mount
  useEffect(() => {
    if (!isAuthenticated) {
      const savedCart = localStorage.getItem(CART_STORAGE_KEY);
      if (savedCart) {
        try {
          setGuestCart(JSON.parse(savedCart));
        } catch (error) {
          console.error('Error loading guest cart:', error);
        }
      }
    }
  }, [isAuthenticated]);

  // Save guest cart to localStorage whenever it changes
  useEffect(() => {
    if (!isAuthenticated && guestCart.length > 0) {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(guestCart));
    }
  }, [guestCart, isAuthenticated]);

  // Fetch cart for authenticated users
  const { data: serverCart = [], isLoading } = useQuery({
    queryKey: ['cart'],
    queryFn: async () => {
      const response = await fetch('/api/cart');
      const result = await response.json();
      return result.data || [];
    },
    enabled: isAuthenticated,
  });

  const items = isAuthenticated ? serverCart : guestCart;
  const itemCount = items.reduce((sum: number, item: CartItem) => sum + item.quantity, 0);
  const total = items.reduce((sum: number, item: CartItem) => sum + (item.price * item.quantity), 0);

  // Add to cart mutation for authenticated users
  const addToCartMutation = useMutation({
    mutationFn: async ({ product, size, color, quantity = 1 }: {
      product: Product;
      size: string;
      color: string;
      quantity: number;
    }) => {
      const response = await fetch('/api/cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ productId: product.id, size, color, quantity }),
      });
      const result = await response.json();
      if (!result.success) throw new Error(result.error);
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      toast.success('Added to cart');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to add to cart');
    },
  });

  // Remove from cart mutation for authenticated users
  const removeFromCartMutation = useMutation({
    mutationFn: async (itemId: string) => {
      const response = await fetch(`/api/cart/${itemId}`, {
        method: 'DELETE',
      });
      const result = await response.json();
      if (!result.success) throw new Error(result.error);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      toast.success('Removed from cart');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to remove from cart');
    },
  });

  // Update quantity mutation for authenticated users
  const updateQuantityMutation = useMutation({
    mutationFn: async ({ itemId, quantity }: { itemId: string; quantity: number }) => {
      const response = await fetch(`/api/cart/${itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity }),
      });
      const result = await response.json();
      if (!result.success) throw new Error(result.error);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to update quantity');
    },
  });

  // Clear cart mutation for authenticated users
  const clearCartMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/cart', {
        method: 'DELETE',
      });
      const result = await response.json();
      if (!result.success) throw new Error(result.error);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      toast.success('Cart cleared');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to clear cart');
    },
  });

  // Merge guest cart with server cart
  const mergeGuestCartMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/cart/merge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: guestCart }),
      });
      const result = await response.json();
      if (!result.success) throw new Error(result.error);
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] });
      setGuestCart([]);
      localStorage.removeItem(CART_STORAGE_KEY);
      toast.success('Cart merged successfully');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Failed to merge cart');
    },
  });

  const addToCart = async (product: Product, size: string, color: string, quantity = 1) => {
    if (isAuthenticated) {
      await addToCartMutation.mutateAsync({ product, size, color, quantity });
    } else {
      // Add to guest cart
      const existingItem = guestCart.find(
        item => item.productId === product.id && item.size === size && item.color === color
      );

      if (existingItem) {
        setGuestCart(prev =>
          prev.map(item =>
            item.id === existingItem.id
              ? { ...item, quantity: item.quantity + quantity }
              : item
          )
        );
      } else {
        const newItem: CartItem = {
          id: `${product.id}-${size}-${color}-${Date.now()}`,
          productId: product.id,
          product,
          size,
          color,
          quantity,
          price: product.price,
        };
        setGuestCart(prev => [...prev, newItem]);
      }
      toast.success('Added to cart (temporary)');
    }
  };

  const removeFromCart = async (itemId: string) => {
    if (isAuthenticated) {
      await removeFromCartMutation.mutateAsync(itemId);
    } else {
      setGuestCart(prev => prev.filter(item => item.id !== itemId));
      toast.success('Removed from cart');
    }
  };

  const updateQuantity = async (itemId: string, quantity: number) => {
    if (quantity <= 0) {
      await removeFromCart(itemId);
      return;
    }

    if (isAuthenticated) {
      await updateQuantityMutation.mutateAsync({ itemId, quantity });
    } else {
      setGuestCart(prev =>
        prev.map(item =>
          item.id === itemId ? { ...item, quantity } : item
        )
      );
    }
  };

  const clearCart = async () => {
    if (isAuthenticated) {
      await clearCartMutation.mutateAsync();
    } else {
      setGuestCart([]);
      localStorage.removeItem(CART_STORAGE_KEY);
      toast.success('Cart cleared');
    }
  };

  const mergeGuestCart = async () => {
    if (isAuthenticated && guestCart.length > 0) {
      await mergeGuestCartMutation.mutateAsync();
    }
  };

  const isInCart = (productId: string, size: string, color: string) => {
    return items.some(
      (item: CartItem) => item.productId === productId && item.size === size && item.color === color
    );
  };

  const value: CartContextType = {
    items,
    itemCount,
    total,
    isLoading: isAuthenticated ? isLoading : false,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart,
    mergeGuestCart,
    isInCart,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}
