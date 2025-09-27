'use client';

import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

interface FilterOption {
  value: string;
  label: string;
}

interface FilterOptionGroupProps {
  title: string;
  type: 'radio' | 'checkbox' | 'range';
  options?: FilterOption[];
  min?: number;
  max?: number;
  step?: number;
  value: unknown;
  onChange: (value: unknown) => void;
}

export function FilterOptionGroup({
  title,
  type,
  options = [],
  min = 0,
  max = 1000,
  step = 1,
  value,
  onChange,
}: FilterOptionGroupProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const handleRadioChange = (optionValue: string) => {
    onChange(optionValue === value ? undefined : optionValue);
  };

  const handleCheckboxChange = (optionValue: string) => {
    const currentValues = Array.isArray(value) ? value : [];
    const newValues = currentValues.includes(optionValue)
      ? currentValues.filter((v: string) => v !== optionValue)
      : [...currentValues, optionValue];
    onChange(newValues);
  };

  const handleRangeChange = (newValue: [number, number]) => {
    onChange(newValue);
  };

  const getActiveCount = () => {
    if (type === 'range') {
      const rangeValue = value as [number, number] | undefined;
      const [minVal, maxVal] = rangeValue || [min, max];
      return minVal > min || maxVal < max ? 1 : 0;
    }
    if (type === 'radio') {
      return value ? 1 : 0;
    }
    return Array.isArray(value) ? value.length : 0;
  };

  return (
    <div className="border-b border-gray-200 pb-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <h3 className="font-medium text-gray-900">
          {title}
          {getActiveCount() > 0 && (
            <span className="ml-2 text-xs bg-gray-900 text-white rounded-full px-2 py-1">
              {getActiveCount()}
            </span>
          )}
        </h3>
        {isExpanded ? (
          <ChevronUpIcon className="h-4 w-4 text-gray-400" />
        ) : (
          <ChevronDownIcon className="h-4 w-4 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-3">
          {type === 'range' ? (
            <RangeSlider
              min={min}
              max={max}
              step={step}
              value={(value as [number, number]) || [min, max]}
              onChange={handleRangeChange}
            />
          ) : type === 'radio' ? (
            <div className="space-y-2">
              {options.map((option) => (
                <label
                  key={option.value}
                  className="flex items-center space-x-3 cursor-pointer"
                >
                  <input
                    type="radio"
                    name={title}
                    value={option.value}
                    checked={value === option.value}
                    onChange={() => handleRadioChange(option.value)}
                    className="h-4 w-4 text-gray-900 focus:ring-gray-900 border-gray-300"
                  />
                  <span className="text-sm text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {options.map((option) => (
                <label
                  key={option.value}
                  className="flex items-center space-x-3 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    value={option.value}
                    checked={Array.isArray(value) && value.includes(option.value)}
                    onChange={() => handleCheckboxChange(option.value)}
                    className="h-4 w-4 text-gray-900 focus:ring-gray-900 border-gray-300 rounded"
                  />
                  <span className="text-sm text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface RangeSliderProps {
  min: number;
  max: number;
  step: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
}

function RangeSlider({ min, max, step, value, onChange }: RangeSliderProps) {
  const [localValue, setLocalValue] = useState<[number, number]>(value);

  const handleMinChange = (newMin: number) => {
    const newValue: [number, number] = [Math.min(newMin, localValue[1]), localValue[1]];
    setLocalValue(newValue);
    onChange(newValue);
  };

  const handleMaxChange = (newMax: number) => {
    const newValue: [number, number] = [localValue[0], Math.max(newMax, localValue[0])];
    setLocalValue(newValue);
    onChange(newValue);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <label className="block text-xs text-gray-500 mb-1">Min</label>
          <input
            type="number"
            min={min}
            max={max}
            step={step}
            value={localValue[0]}
            onChange={(e) => handleMinChange(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-gray-900 focus:border-gray-900"
          />
        </div>
        <div className="flex-1">
          <label className="block text-xs text-gray-500 mb-1">Max</label>
          <input
            type="number"
            min={min}
            max={max}
            step={step}
            value={localValue[1]}
            onChange={(e) => handleMaxChange(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-gray-900 focus:border-gray-900"
          />
        </div>
      </div>
      
      <div className="text-center text-sm text-gray-500">
        {formatCurrency(localValue[0])} - {formatCurrency(localValue[1])}
      </div>
    </div>
  );
}
