from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.analytics import Dataset
from ml.forecasting import MODEL_NAMES

router = APIRouter()


@router.get("/forecast/models")
def list_forecast_models():
    return {
        "models": [{"id": key, "name": value} for key, value in MODEL_NAMES.items()],
        "default": "ensemble",
    }


@router.get("/forecast/product/{product_id}")
def forecast_product(
    product_id: str,
    horizon: int = Query(30, ge=1, le=90),
    model: str = Query("ensemble", pattern="^(ma|prophet|xgboost|lightgbm|ensemble)$"),
    db: Session = Depends(get_db),
):
    return Dataset(db).forecast(horizon, model, product_id=product_id)


@router.get("/forecast/category/{category_name}")
def forecast_category(
    category_name: str,
    horizon: int = Query(30, ge=1, le=90),
    model: str = Query("ensemble", pattern="^(ma|prophet|xgboost|lightgbm|ensemble)$"),
    db: Session = Depends(get_db),
):
    return Dataset(db).forecast(horizon, model, category=category_name)
