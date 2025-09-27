import { NextResponse } from 'next/server';
import { User } from '@/types';

export async function GET() {
  try {
    // In a real app, you would:
    // 1. Verify the JWT token from the Authorization header
    // 2. Extract user ID from the token
    // 3. Fetch user data from database
    
    // For now, return a mock user
    const mockUser: User = {
      id: '1',
      email: 'user@example.com',
      name: 'John Doe',
      phone: '+91 98765 43210',
      role: 'user',
      profile: {
        skinTone: 'medium',
        bodyShape: 'hourglass',
        height: 165,
        preferences: {
          size: 'M',
          colors: ['black', 'navy', 'white'],
          styles: ['minimalist', 'elegant'],
        },
      },
      createdAt: '2024-01-01T10:00:00Z',
      updatedAt: '2024-01-01T10:00:00Z',
    };
    
    return NextResponse.json({
      success: true,
      data: mockUser,
    });
  } catch (error) {
    console.error('Error fetching user:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch user' },
      { status: 500 }
    );
  }
}
