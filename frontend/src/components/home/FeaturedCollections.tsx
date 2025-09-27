import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ChevronRightIcon } from '@heroicons/react/24/outline';

const collections = [
  {
    id: 'workwear-edit',
    title: 'Workwear Edit',
    description: 'Professional pieces that transition seamlessly from office to evening',
    image: '/collections/workwear-edit.jpg',
    href: '/products?category=workwear',
    featured: true,
  },
  {
    id: 'yoga-essentials',
    title: 'Yoga Essentials',
    description: 'Comfortable and breathable pieces for your practice',
    image: '/collections/yoga-essentials.jpg',
    href: '/products?category=yoga',
  },
  {
    id: 'evening-luxury',
    title: 'Evening Luxury',
    description: 'Elegant pieces for special occasions and evening wear',
    image: '/collections/evening-luxury.jpg',
    href: '/products?occasion=evening',
  },
];

export function FeaturedCollections() {
  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Featured Collections
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Curated collections designed for different moments in your life
          </p>
        </div>

        {/* Collections Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {collections.map((collection) => (
            <Link
              key={collection.id}
              href={collection.href}
              className={`group relative overflow-hidden rounded-2xl ${
                collection.featured ? 'md:col-span-2' : ''
              }`}
            >
              <div className="relative h-64 md:h-80">
                <Image
                  src={collection.image}
                  alt={collection.title}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-black bg-opacity-20 group-hover:bg-opacity-30 transition-opacity" />
              </div>
              
              {/* Content */}
              <div className="absolute inset-0 flex items-end p-6 md:p-8">
                <div className="text-white">
                  <h3 className="text-2xl md:text-3xl font-bold mb-2 group-hover:translate-y-[-4px] transition-transform">
                    {collection.title}
                  </h3>
                  <p className="text-gray-200 mb-4 text-sm md:text-base group-hover:translate-y-[-4px] transition-transform">
                    {collection.description}
                  </p>
                  <div className="inline-flex items-center text-white font-medium group-hover:translate-y-[-4px] transition-transform">
                    Shop Collection
                    <ChevronRightIcon className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Ukiyo Studio Section */}
        <div className="mt-16 bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl p-8 md:p-12 text-center text-white">
          <h3 className="text-2xl md:text-3xl font-bold mb-4">
            Ukiyo Studio
          </h3>
          <p className="text-gray-300 mb-8 max-w-2xl mx-auto">
            Discover styling tips, care guides, and inspiration from our team of experts. 
            Learn how to make the most of your Ukiyo pieces.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/studio"
              className="inline-flex items-center px-6 py-3 bg-white text-gray-900 font-semibold rounded-lg hover:bg-gray-100 transition-colors"
            >
              Explore Studio
              <ChevronRightIcon className="ml-2 h-4 w-4" />
            </Link>
            <Link
              href="/size-guide"
              className="inline-flex items-center px-6 py-3 border-2 border-white text-white font-semibold rounded-lg hover:bg-white hover:text-gray-900 transition-colors"
            >
              Size Guide
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
