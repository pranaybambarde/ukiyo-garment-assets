'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, AuthResponse, LoginCredentials, ApiResponse } from '@/types';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  loginWithApple: () => Promise<void>;
  sendOTP: (phone: string) => Promise<void>;
  verifyOTP: (phone: string, otp: string) => Promise<void>;
  sendMagicLink: (email: string) => Promise<void>;
  verifyMagicLink: (token: string) => Promise<void>;
  logout: () => void;
  updateProfile: (profile: Partial<User>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = !!user;
  const isAdmin = user?.role === 'admin';

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        if (token) {
          const response = await fetch('/api/auth/me', {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (response.ok) {
            const userData = await response.json();
            setUser(userData.data);
          } else {
            localStorage.removeItem('auth_token');
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        localStorage.removeItem('auth_token');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      const result: ApiResponse<AuthResponse> = await response.json();

      if (result.success) {
        localStorage.setItem('auth_token', result.data.token);
        setUser(result.data.user);
        toast.success('Login successful!');
        router.push('/');
      } else {
        throw new Error(result.error || 'Login failed');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Login failed');
      throw error;
    }
  };

  const loginWithGoogle = async () => {
    try {
      // In a real implementation, this would redirect to Google OAuth
      // For now, we'll simulate the flow
      window.location.href = '/api/auth/google';
    } catch (error) {
      toast.error('Google login failed');
      throw error;
    }
  };

  const loginWithApple = async () => {
    try {
      // In a real implementation, this would redirect to Apple OAuth
      // For now, we'll simulate the flow
      window.location.href = '/api/auth/apple';
    } catch (error) {
      toast.error('Apple login failed');
      throw error;
    }
  };

  const sendOTP = async (phone: string) => {
    try {
      const response = await fetch('/api/auth/send-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone }),
      });

      const result: ApiResponse<{ message: string }> = await response.json();

      if (result.success) {
        toast.success('OTP sent to your phone');
      } else {
        throw new Error(result.error || 'Failed to send OTP');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to send OTP');
      throw error;
    }
  };

  const verifyOTP = async (phone: string, otp: string) => {
    try {
      const response = await fetch('/api/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, otp }),
      });

      const result: ApiResponse<AuthResponse> = await response.json();

      if (result.success) {
        localStorage.setItem('auth_token', result.data.token);
        setUser(result.data.user);
        toast.success('Phone verification successful!');
        router.push('/');
      } else {
        throw new Error(result.error || 'OTP verification failed');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'OTP verification failed');
      throw error;
    }
  };

  const sendMagicLink = async (email: string) => {
    try {
      const response = await fetch('/api/auth/send-magic-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const result: ApiResponse<{ message: string }> = await response.json();

      if (result.success) {
        toast.success('Magic link sent to your email');
      } else {
        throw new Error(result.error || 'Failed to send magic link');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to send magic link');
      throw error;
    }
  };

  const verifyMagicLink = async (token: string) => {
    try {
      const response = await fetch('/api/auth/verify-magic-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });

      const result: ApiResponse<AuthResponse> = await response.json();

      if (result.success) {
        localStorage.setItem('auth_token', result.data.token);
        setUser(result.data.user);
        toast.success('Email verification successful!');
        router.push('/');
      } else {
        throw new Error(result.error || 'Magic link verification failed');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Magic link verification failed');
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
    toast.success('Logged out successfully');
    router.push('/');
  };

  const updateProfile = async (profile: Partial<User>) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(profile),
      });

      const result: ApiResponse<User> = await response.json();

      if (result.success) {
        setUser(result.data);
        toast.success('Profile updated successfully');
      } else {
        throw new Error(result.error || 'Failed to update profile');
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update profile');
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    isAdmin,
    login,
    loginWithGoogle,
    loginWithApple,
    sendOTP,
    verifyOTP,
    sendMagicLink,
    verifyMagicLink,
    logout,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
