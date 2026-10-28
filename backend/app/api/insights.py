from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.analytics import Dataset

router = APIRouter()


@router.get("/insights")
def get_insights(days_ahead: int = Query(30, ge=1, le=90), db: Session = Depends(get_db)):
    return Dataset(db).insights(days_ahead)


@router.get("/insights/stockout-risk")
def stockout(threshold_days: int = Query(30, ge=1, le=90), db: Session = Depends(get_db)):
    return [row for row in Dataset(db).inventory(threshold_days) if row["stockout_risk"] != "low"]


@router.get("/insights/overstock-risk")
def overstock(threshold_days: int = Query(90, ge=30, le=365), db: Session = Depends(get_db)):
    return [
        row
        for row in Dataset(db).inventory(overstock_days=threshold_days)
        if row["overstock_risk"] == "high"
    ]


@router.get("/insights/trending")
def trending(
    period_days: int = Query(30, ge=7, le=90),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = Dataset(db).inventory(trend_days=period_days)
    return {
        "rising": [r for r in rows if r["trend"] == "rising"][:limit],
        "falling": [r for r in rows if r["trend"] == "falling"][:limit],
    }


@router.get("/insights/reorder-recommendations")
def reorders(horizon_days: int = Query(30, ge=1, le=90), db: Session = Depends(get_db)):
    return {"horizon_days": horizon_days, "recommendations": Dataset(db).inventory(horizon_days)}
