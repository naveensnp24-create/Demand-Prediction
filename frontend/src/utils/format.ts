/**
 * Formatting utilities for numbers and currency
 */

/**
 * Format a number with Indian locale formatting
 * @param value - The number to format
 * @returns Formatted number string with 1 decimal place max
 */
export const number = (value: number): string =>
  new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 }).format(value)

/**
 * Format a number as Indian Rupees (INR)
 * @param value - The amount to format
 * @returns Formatted currency string in INR
 */
export const money = (value: number): string =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
