'use client';

import React from 'react';
import { ProductFilters } from '@/types';
import { FilterOptionGroup } from './FilterOptionGroup';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface FiltersSidebarProps {
  filters: ProductFilters;
  onFiltersChange: (filters: Partial<ProductFilters>) => void;
  onClearFilters: () => void;
}

const filterOptions = {
  category: {
    title: 'Category',
    type: 'radio' as const,
    options: [
      { value: 'clothing', label: 'Clothing' },
      { value: 'accessories', label: 'Accessories' },
      { value: 'yoga', label: 'Yoga' },
      { value: 'workwear', label: 'Workwear' },
      { value: 'evening', label: 'Evening' },
    ],
  },
  size: {
    title: 'Size',
    type: 'checkbox' as const,
    options: [
      { value: 'XS', label: 'XS' },
      { value: 'S', label: 'S' },
      { value: 'M', label: 'M' },
      { value: 'L', label: 'L' },
      { value: 'XL', label: 'XL' },
      { value: 'XXL', label: 'XXL' },
    ],
  },
  color: {
    title: 'Color',
    type: 'checkbox' as const,
    options: [
      { value: 'black', label: 'Black' },
      { value: 'white', label: 'White' },
      { value: 'navy', label: 'Navy' },
      { value: 'gray', label: 'Gray' },
      { value: 'beige', label: 'Beige' },
      { value: 'pink', label: 'Pink' },
      { value: 'blue', label: 'Blue' },
      { value: 'green', label: 'Green' },
    ],
  },
  fabric: {
    title: 'Fabric',
    type: 'checkbox' as const,
    options: [
      { value: 'cotton', label: 'Cotton' },
      { value: 'polyester', label: 'Polyester' },
      { value: 'spandex', label: 'Spandex' },
      { value: 'modal', label: 'Modal' },
      { value: 'bamboo', label: 'Bamboo' },
      { value: 'silk', label: 'Silk' },
    ],
  },
  occasion: {
    title: 'Occasion',
    type: 'checkbox' as const,
    options: [
      { value: 'work', label: 'Work' },
      { value: 'yoga', label: 'Yoga' },
      { value: 'gym', label: 'Gym' },
      { value: 'evening', label: 'Evening' },
      { value: 'casual', label: 'Casual' },
      { value: 'travel', label: 'Travel' },
    ],
  },
  skinTone: {
    title: 'Skin Tone',
    type: 'radio' as const,
    options: [
      { value: 'light', label: 'Light' },
      { value: 'medium', label: 'Medium' },
      { value: 'dark', label: 'Dark' },
      { value: 'deep', label: 'Deep' },
    ],
  },
  bodyShape: {
    title: 'Body Shape',
    type: 'radio' as const,
    options: [
      { value: 'pear', label: 'Pear' },
      { value: 'apple', label: 'Apple' },
      { value: 'hourglass', label: 'Hourglass' },
      { value: 'rectangle', label: 'Rectangle' },
      { value: 'inverted-triangle', label: 'Inverted Triangle' },
    ],
  },
  price: {
    title: 'Price Range',
    type: 'range' as const,
    min: 0,
    max: 10000,
    step: 100,
  },
  availability: {
    title: 'Availability',
    type: 'checkbox' as const,
    options: [
      { value: 'inStock', label: 'In Stock' },
      { value: 'featured', label: 'Featured' },
      { value: 'newArrival', label: 'New Arrivals' },
    ],
  },
};

export function FiltersSidebar({ filters, onFiltersChange, onClearFilters }: FiltersSidebarProps) {
  const handleFilterChange = (key: string, value: unknown) => {
    onFiltersChange({ [key]: value });
  };

  const handlePriceChange = (value: unknown) => {
    const [min, max] = value as [number, number];
    onFiltersChange({
      priceMin: min > 0 ? min : undefined,
      priceMax: max < 10000 ? max : undefined,
    });
  };

  const getActiveFiltersCount = () => {
    return Object.values(filters).filter(
      value => value !== undefined && value !== null && value !== ''
    ).length;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        {getActiveFiltersCount() > 0 && (
          <button
            onClick={onClearFilters}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1"
          >
            <XMarkIcon className="h-4 w-4" />
            <span>Clear all</span>
          </button>
        )}
      </div>

      {/* Filter Groups */}
      <div className="space-y-6">
        {/* Category */}
        <FilterOptionGroup
          title={filterOptions.category.title}
          type={filterOptions.category.type}
          options={filterOptions.category.options}
          value={filters.category}
          onChange={(value) => handleFilterChange('category', value)}
        />

        {/* Price Range */}
        <FilterOptionGroup
          title={filterOptions.price.title}
          type={filterOptions.price.type}
          min={filterOptions.price.min}
          max={filterOptions.price.max}
          step={filterOptions.price.step}
          value={[filters.priceMin || 0, filters.priceMax || 10000]}
          onChange={handlePriceChange}
        />

        {/* Size */}
        <FilterOptionGroup
          title={filterOptions.size.title}
          type={filterOptions.size.type}
          options={filterOptions.size.options}
          value={filters.size || []}
          onChange={(value) => handleFilterChange('size', value)}
        />

        {/* Color */}
        <FilterOptionGroup
          title={filterOptions.color.title}
          type={filterOptions.color.type}
          options={filterOptions.color.options}
          value={filters.color || []}
          onChange={(value) => handleFilterChange('color', value)}
        />

        {/* Fabric */}
        <FilterOptionGroup
          title={filterOptions.fabric.title}
          type={filterOptions.fabric.type}
          options={filterOptions.fabric.options}
          value={filters.fabric || []}
          onChange={(value) => handleFilterChange('fabric', value)}
        />

        {/* Occasion */}
        <FilterOptionGroup
          title={filterOptions.occasion.title}
          type={filterOptions.occasion.type}
          options={filterOptions.occasion.options}
          value={filters.occasion || []}
          onChange={(value) => handleFilterChange('occasion', value)}
        />

        {/* Skin Tone */}
        <FilterOptionGroup
          title={filterOptions.skinTone.title}
          type={filterOptions.skinTone.type}
          options={filterOptions.skinTone.options}
          value={filters.skinTone}
          onChange={(value) => handleFilterChange('skinTone', value)}
        />

        {/* Body Shape */}
        <FilterOptionGroup
          title={filterOptions.bodyShape.title}
          type={filterOptions.bodyShape.type}
          options={filterOptions.bodyShape.options}
          value={filters.bodyShape}
          onChange={(value) => handleFilterChange('bodyShape', value)}
        />

        {/* Availability */}
        <FilterOptionGroup
          title={filterOptions.availability.title}
          type={filterOptions.availability.type}
          options={filterOptions.availability.options}
          value={[
            ...(filters.inStock ? ['inStock'] : []),
            ...(filters.featured ? ['featured'] : []),
            ...(filters.newArrival ? ['newArrival'] : []),
          ]}
          onChange={(value) => {
            const values = value as string[];
            onFiltersChange({
              inStock: values.includes('inStock'),
              featured: values.includes('featured'),
              newArrival: values.includes('newArrival'),
            });
          }}
        />
      </div>
    </div>
  );
}
