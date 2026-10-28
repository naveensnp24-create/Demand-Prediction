from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.analytics import Dataset, LABELS, ACTIONS

router = APIRouter()


@router.get("/segments")
def get_segments(db: Session = Depends(get_db)):
    return Dataset(db).segments()


def members(data, segment):
    if segment not in LABELS:
        raise HTTPException(404, "Unknown segment")
    frame = data.customer_features()
    return frame[frame.segment == segment]


@router.get("/segments/{segment_name}")
def get_segment_details(segment_name: str, db: Session = Depends(get_db)):
    data = Dataset(db)
    frame = members(data, segment_name)
    return {
        "segment": segment_name,
        "label": LABELS[segment_name],
        "size": len(frame),
        "recommended_action": ACTIONS[segment_name],
    }


@router.get("/segments/{segment_name}/customers")
def get_segment_customers(
    segment_name: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    frame = members(Dataset(db), segment_name)
    fields = [
        "customer_id",
        "first_name",
        "last_name",
        "recency",
        "frequency",
        "monetary",
        "cluster",
    ]
    return {
        "total": len(frame),
        "customers": frame.iloc[offset : offset + limit][fields].to_dict("records"),
    }
