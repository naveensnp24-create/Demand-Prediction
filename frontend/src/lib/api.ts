/**
 * Legacy API exports - maintained for backward compatibility
 * New code should import from @/services, @/hooks, @/utils, and @/types
 */

// Re-export from organized modules
export { api, API_URL } from '@/services'
export { useData } from '@/hooks'
export { number, money, exportCSV } from '@/utils'
export type {
  Product,
  OverviewData,
  ForecastData,
  Segment,
  Recommendation,
  Prediction,
  Profile,
  Insight,
  InsightsData,
} from '@/types'
