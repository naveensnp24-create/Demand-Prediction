"""Liveness and database readiness probes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.database import Customer, Product

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "demand-prediction-api"}


@router.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(503, "Database is unavailable") from None
    return {"status": "healthy", "database": "connected"}


@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        return {
            "status": "ready",
            "database": "connected",
            "customers": db.query(Customer).count(),
            "products": db.query(Product).count(),
        }
    except SQLAlchemyError:
        raise HTTPException(503, "Database schema is not ready") from None
