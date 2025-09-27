import React from 'react';
import { 
  SparklesIcon, 
  HeartIcon, 
  TruckIcon, 
  ArrowPathIcon 
} from '@heroicons/react/24/outline';

const features = [
  {
    icon: SparklesIcon,
    title: 'Premium Quality Fabric',
    description: 'Carefully selected materials that provide comfort, durability, and style for every occasion.',
  },
  {
    icon: HeartIcon,
    title: 'Customized Fit Advice',
    description: 'Personalized recommendations based on your body shape, skin tone, and style preferences.',
  },
  {
    icon: TruckIcon,
    title: 'Free Shipping & Returns',
    description: 'Complimentary shipping on orders over ₹2,000 with easy 30-day returns for your peace of mind.',
  },
  {
    icon: ArrowPathIcon,
    title: 'Sustainable Practices',
    description: 'Ethically sourced materials and eco-friendly production processes for a better tomorrow.',
  },
];

export function ValueProposition() {
  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Why Choose Ukiyo?
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            We believe in creating more than just clothing. Our commitment to quality, 
            sustainability, and personalized service sets us apart in the world of activewear.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="text-center group">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-6 group-hover:bg-gray-900 transition-colors">
                <feature.icon className="h-8 w-8 text-gray-600 group-hover:text-white transition-colors" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                {feature.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* Additional Info */}
        <div className="mt-16 bg-gray-50 rounded-2xl p-8 md:p-12">
          <div className="max-w-4xl mx-auto text-center">
            <h3 className="text-2xl md:text-3xl font-bold text-gray-900 mb-6">
              Designed for the Modern Indian Woman
            </h3>
            <p className="text-lg text-gray-600 mb-8 leading-relaxed">
              Our designs celebrate the strength, grace, and versatility of contemporary women. 
              From yoga sessions to boardroom meetings, Ukiyo adapts to your dynamic lifestyle 
              while maintaining the highest standards of comfort and style.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <div>
                <div className="text-3xl font-bold text-gray-900 mb-2">100%</div>
                <div className="text-gray-600">Premium Materials</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 mb-2">30</div>
                <div className="text-gray-600">Day Returns</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 mb-2">24/7</div>
                <div className="text-gray-600">Customer Support</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
