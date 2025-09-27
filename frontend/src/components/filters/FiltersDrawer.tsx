'use client';

import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { ProductFilters } from '@/types';
import { FiltersSidebar } from './FiltersSidebar';

interface FiltersDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  filters: ProductFilters;
  onFiltersChange: (filters: Partial<ProductFilters>) => void;
  onClearFilters: () => void;
}

export function FiltersDrawer({
  isOpen,
  onClose,
  filters,
  onFiltersChange,
  onClearFilters,
}: FiltersDrawerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-25"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 w-full max-w-sm bg-white shadow-xl">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Filters Content */}
          <div className="flex-1 overflow-y-auto p-4">
            <FiltersSidebar
              filters={filters}
              onFiltersChange={onFiltersChange}
              onClearFilters={onClearFilters}
            />
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 p-4 space-y-3">
            <button
              onClick={onClearFilters}
              className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Clear All Filters
            </button>
            <button
              onClick={onClose}
              className="w-full px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
