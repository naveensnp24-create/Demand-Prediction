"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from enum import Enum


class EventType(str, Enum):
    VIEW = "view"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    WISHLIST = "wishlist"
    PURCHASE = "purchase"
    RETURN = "return"


class PromoType(str, Enum):
    PERCENTAGE_DISCOUNT = "percentage_discount"
    FLAT_DISCOUNT = "flat_discount"
    BUY_X_GET_Y = "buy_x_get_y"
    FREE_SHIPPING = "free_shipping"


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class CustomerSegment(str, Enum):
    LOYAL_HIGH = "loyal_high"
    DISCOUNT_HUNTER = "discount_hunter"
    AT_RISK = "at_risk"
    NEW = "new"
    OCCASIONAL = "occasional"


# Customer schemas
class CustomerBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    age: Optional[int] = Field(None, ge=13, le=120)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    age: Optional[int] = Field(None, ge=13, le=120)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    segment: Optional[CustomerSegment] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    customer_id: str
    signup_date: datetime
    segment: Optional[str] = None
    avg_order_value: float = 0.0
    purchase_frequency_days: float = 0.0
    price_sensitivity: float = 0.5
    promo_responsiveness: float = 0.5
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Product schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    price: float = Field(..., gt=0)
    cost: float = Field(..., gt=0)
    is_seasonal: bool = False
    seasonal_peaks: List[int] = Field(default_factory=list)
    stock_quantity: int = Field(default=0, ge=0)
    reorder_point: int = Field(default=10, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    cost: Optional[float] = Field(None, gt=0)
    is_seasonal: Optional[bool] = None
    seasonal_peaks: Optional[List[int]] = None
    is_active: Optional[bool] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)


class ProductResponse(ProductBase):
    product_id: str
    margin: float
    launch_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Promotion schemas
class PromotionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: PromoType
    discount_value: float = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    applicable_categories: List[str] = Field(default_factory=list)
    min_order_value: float = Field(default=0, ge=0)
    max_discount: float = Field(default=0, ge=0)


class PromotionCreate(PromotionBase):
    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        values = info.data
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class PromotionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[PromoType] = None
    discount_value: Optional[float] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    applicable_categories: Optional[List[str]] = None
    min_order_value: Optional[float] = Field(None, ge=0)
    max_discount: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


class PromotionResponse(PromotionBase):
    promo_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Event schemas
class EventBase(BaseModel):
    customer_id: str
    product_id: str
    session_id: str
    event_type: EventType
    timestamp: datetime
    value: float = 0.0
    quantity: int = 0


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    event_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Order schemas
class OrderBase(BaseModel):
    customer_id: str
    product_id: str
    session_id: str
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    total_amount: float = Field(..., gt=0)
    discount_amount: float = Field(default=0, ge=0)
    promo_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    payment_method: Optional[str] = Field(None, max_length=50)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    total_amount: Optional[float] = Field(None, gt=0)
    discount_amount: Optional[float] = Field(None, ge=0)
    promo_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)


class OrderResponse(OrderBase):
    order_id: str
    order_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Forecast schemas
class ForecastRequest(BaseModel):
    horizon: int = Field(default=30, ge=1, le=90)
    model: Optional[str] = Field(
        default="ensemble", pattern="^(ma|prophet|xgboost|lightgbm|ensemble)$"
    )


class ProductForecastResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    historical_data: List[Dict[str, Any]]  # [{"date": "...", "demand": 10}, ...]
    forecast: List[
        Dict[str, Any]
    ]  # [{"date": "...", "predicted_demand": 10, "lower": 5, "upper": 15}, ...]
    model_metrics: Dict[str, Dict[str, float]]  # {"ma": {"mae": 2.5, "rmse": 3.1}, ...}
    generated_at: datetime


class CategoryForecastResponse(BaseModel):
    category: str
    historical_data: List[Dict[str, Any]]
    forecast: List[Dict[str, Any]]
    model_metrics: Dict[str, Dict[str, float]]
    generated_at: datetime


# Customer prediction schemas
class CustomerPredictionRequest(BaseModel):
    horizon_days: int = Field(default=30, ge=1, le=90)
    top_n: int = Field(default=10, ge=1, le=100)


class ProductRecommendation(BaseModel):
    product_id: str
    product_name: str
    category: str
    price: float
    purchase_probability: float = Field(..., ge=0, le=1)
    expected_quantity: float = Field(..., ge=0)
    expected_revenue: float = Field(..., ge=0)
    shap_explanations: List[Dict[str, Any]] = Field(default_factory=list)


class CustomerPredictionResponse(BaseModel):
    customer_id: str
    segment: str
    rfm_scores: Dict[str, float]
    recommendations: List[ProductRecommendation]
    generated_at: datetime


# Segment schemas
class SegmentSummary(BaseModel):
    segment: str
    label: str
    size: int
    percentage: float
    avg_recency: float
    avg_frequency: float
    avg_monetary: float
    avg_order_value: float
    price_sensitivity: float
    promo_responsiveness: float
    characteristics: List[str]


class SegmentsResponse(BaseModel):
    segments: List[SegmentSummary]
    total_customers: int
    generated_at: datetime


# Insights schemas
class ProductInsight(BaseModel):
    product_id: str
    product_name: str
    category: str
    current_stock: int
    predicted_demand_30d: float
    stockout_risk: str  # "high", "medium", "low"
    overstock_risk: str
    suggested_reorder_qty: int
    trend: str  # "rising", "falling", "stable"
    revenue_potential: float


class InsightsResponse(BaseModel):
    top_rising_products: List[ProductInsight]
    top_falling_products: List[ProductInsight]
    stockout_risk_products: List[ProductInsight]
    overstock_risk_products: List[ProductInsight]
    inventory_recommendations: List[Dict[str, Any]]
    generated_at: datetime


# Upload schemas
class UploadResponse(BaseModel):
    message: str
    rows_processed: int
    tables_updated: List[str]
    errors: List[str] = Field(default_factory=list)


# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    detail: List[Dict[str, Any]]
