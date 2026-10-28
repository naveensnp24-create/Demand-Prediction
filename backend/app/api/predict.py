from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.analytics import Dataset
from ml.recommendations import recommend

router = APIRouter()


def prediction(data, customer_id, horizon, top_n):
    data.customer(customer_id)
    features = data.customer_features().set_index("customer_id").loc[customer_id]
    recommendations, report = recommend(data, customer_id, horizon, top_n)
    return {
        "customer_id": customer_id,
        "segment": features.segment,
        "rfm_scores": {key: float(features[key]) for key in ["recency", "frequency", "monetary"]},
        "recommendations": recommendations,
        "model_report": report,
        "horizon_days": horizon,
        "as_of": data.as_of.date().isoformat(),
        "generated_at": datetime.utcnow(),
    }


@router.get("/predict/customer/{customer_id}")
def predict_customer(
    customer_id: str,
    horizon_days: int = Query(30, ge=1, le=90),
    top_n: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return prediction(Dataset(db), customer_id, horizon_days, top_n)


@router.get("/predict/customer/{customer_id}/propensity")
def propensity(
    customer_id: str,
    product_id: str,
    horizon_days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
):
    results, report = recommend(Dataset(db), customer_id, horizon_days, 1, product_id)
    return {"customer_id": customer_id, **results[0], "model_report": report}


@router.get("/predict/batch")
def batch(
    customer_ids: str,
    horizon_days: int = Query(30, ge=1, le=90),
    top_n: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    ids = list(dict.fromkeys(value.strip() for value in customer_ids.split(",") if value.strip()))
    if not 1 <= len(ids) <= 50:
        raise HTTPException(422, "Provide between 1 and 50 customer IDs")
    data = Dataset(db)
    return {"predictions": [prediction(data, value, horizon_days, top_n) for value in ids]}
