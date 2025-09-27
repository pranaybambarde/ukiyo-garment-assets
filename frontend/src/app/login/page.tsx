'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { OAuthButtons } from '@/components/auth/OAuthButtons';
import { OTPInput } from '@/components/auth/OTPInput';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

type AuthMethod = 'email' | 'phone' | 'otp';

export default function LoginPage() {
  const [authMethod, setAuthMethod] = useState<AuthMethod>('email');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [isOTPSent, setIsOTPSent] = useState(false);
  const { sendOTP, verifyOTP, sendMagicLink, isLoading } = useAuth();
  const router = useRouter();

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await sendMagicLink(email);
      // Show success message
    } catch {
      // Error is handled in the context
    }
  };

  const handlePhoneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await sendOTP(phone);
      setIsOTPSent(true);
    } catch {
      // Error is handled in the context
    }
  };

  const handleOTPSubmit = async (otp: string) => {
    try {
      await verifyOTP(phone, otp);
      router.push('/');
    } catch {
      // Error is handled in the context
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Back button */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-1" />
            Back to home
          </Link>
        </div>

        {/* Logo */}
        <div className="text-center">
          <Link href="/" className="text-3xl font-bold text-gray-900">
            Ukiyo
          </Link>
          <h2 className="mt-6 text-2xl font-bold text-gray-900">
            Welcome back
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to your account or create a new one
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {/* OAuth Buttons */}
          <OAuthButtons />

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or continue with</span>
              </div>
            </div>
          </div>

          {/* Auth Method Tabs */}
          <div className="mt-6">
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setAuthMethod('email')}
                className={`flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors ${
                  authMethod === 'email'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Email
              </button>
              <button
                onClick={() => setAuthMethod('phone')}
                className={`flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors ${
                  authMethod === 'phone'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Phone
              </button>
            </div>
          </div>

          {/* Forms */}
          <div className="mt-6">
            {authMethod === 'email' && !isOTPSent && (
              <form onSubmit={handleEmailSubmit} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    Email address
                  </label>
                  <div className="mt-1">
                    <input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-gray-900 focus:border-gray-900 sm:text-sm"
                      placeholder="Enter your email"
                    />
                  </div>
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Sending...' : 'Send Magic Link'}
                  </button>
                </div>
              </form>
            )}

            {authMethod === 'phone' && !isOTPSent && (
              <form onSubmit={handlePhoneSubmit} className="space-y-4">
                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                    Phone number
                  </label>
                  <div className="mt-1">
                    <input
                      id="phone"
                      name="phone"
                      type="tel"
                      autoComplete="tel"
                      required
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-gray-900 focus:border-gray-900 sm:text-sm"
                      placeholder="+91 98765 43210"
                    />
                  </div>
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Sending...' : 'Send OTP'}
                  </button>
                </div>
              </form>
            )}

            {isOTPSent && (
              <div className="space-y-4">
                <div className="text-center">
                  <h3 className="text-lg font-medium text-gray-900">
                    Enter verification code
                  </h3>
                  <p className="mt-2 text-sm text-gray-600">
                    We sent a 6-digit code to {phone}
                  </p>
                </div>

                <OTPInput
                  onComplete={handleOTPSubmit}
                  isLoading={isLoading}
                />

                <div className="text-center">
                  <button
                    onClick={() => setIsOTPSent(false)}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Change phone number
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sign up link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Don&apos;t have an account?{' '}
              <Link
                href="/signup"
                className="font-medium text-gray-900 hover:text-gray-700"
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
