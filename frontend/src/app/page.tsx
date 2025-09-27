import React from 'react';
import { HeroBanner } from '@/components/home/HeroBanner';
import { NewArrivals } from '@/components/home/NewArrivals';
import { ValueProposition } from '@/components/home/ValueProposition';
import { FeaturedCollections } from '@/components/home/FeaturedCollections';

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <HeroBanner />
      <NewArrivals />
      <ValueProposition />
      <FeaturedCollections />
    </div>
  );
}