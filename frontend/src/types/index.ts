// API Response Types

export interface Product {
  product_id: string
  name: string
  category: string
  price: number
  stock_quantity: number
}

export interface OverviewData {
  customers: number
  products: number
  orders: number
  events: number
  revenue: number
  units: number
  as_of: string
  forecast_30d: number
  at_risk_customers: number
  trend: { date: string; demand: number }[]
  categories: { category: string; units: number; revenue: number }[]
}

export interface ForecastData {
  product_name?: string
  category: string
  as_of: string
  model_used: string
  validation_days: number
  notes: string[]
  historical_data: { date: string; demand: number }[]
  forecast: { date: string; predicted_demand: number; lower: number; upper: number }[]
  model_metrics: Record<string, { mae: number; rmse: number; mape?: number; wmape?: number }>
}

export interface Segment {
  segment: string
  label: string
  size: number
  percentage: number
  avg_recency: number
  avg_frequency: number
  avg_monetary: number
  avg_order_value: number
  characteristics: string[]
}

export interface Recommendation {
  product_id: string
  product_name: string
  category: string
  price: number
  purchase_probability: number
  expected_quantity: number
  expected_revenue: number
  shap_explanations: { feature: string; shap_value: number; unit: string }[]
}

export interface Prediction {
  customer_id: string
  segment: string
  rfm_scores: Record<string, number>
  as_of: string
  recommendations: Recommendation[]
  model_report: {
    method: string
    note: string
    validation: { roc_auc?: number; brier_score?: number }
  }
}

export interface Profile {
  customer_id: string
  name: string
  email: string
  city: string
  signup_date: string
  timeline: { date: string; event: string; product: string; value: number }[]
}

export interface Insight {
  product_id: string
  product_name: string
  category: string
  current_stock: number
  predicted_demand: number
  stockout_risk: string
  overstock_risk: string
  suggested_reorder_qty: number
  trend: string
  revenue_potential: number
}

export interface InsightsData {
  inventory_recommendations: Insight[]
  stockout_risk_products: Insight[]
  overstock_risk_products: Insight[]
  top_rising_products: Insight[]
  top_falling_products: Insight[]
  as_of: string
  method: string
}
