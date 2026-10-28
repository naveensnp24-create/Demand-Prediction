from tempfile import TemporaryDirectory
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.database import Customer, Product, Order, Event, Promotion
from backend.app.services.analytics import Dataset

router = APIRouter()


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    return Dataset(db).overview()


@router.get("/products")
def products(
    q: str = "",
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active.is_(True))
    if q:
        query = query.filter(or_(Product.name.ilike(f"%{q}%"), Product.product_id.ilike(f"%{q}%")))
    return {
        "total": query.count(),
        "products": [
            dict(
                product_id=p.product_id,
                name=p.name,
                category=p.category,
                price=p.price,
                stock_quantity=p.stock_quantity,
            )
            for p in query.order_by(Product.product_id).offset(offset).limit(limit)
        ],
    }


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    return {
        "categories": [
            row[0] for row in db.query(Product.category).distinct().order_by(Product.category)
        ]
    }


@router.get("/customers")
def customers(
    q: str = "",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Customer)
    if q:
        query = query.filter(
            or_(
                Customer.customer_id.ilike(f"%{q}%"),
                Customer.email.ilike(f"%{q}%"),
                Customer.first_name.ilike(f"%{q}%"),
                Customer.last_name.ilike(f"%{q}%"),
            )
        )
    return {
        "total": query.count(),
        "customers": [
            dict(customer_id=c.customer_id, name=f"{c.first_name} {c.last_name}", email=c.email)
            for c in query.order_by(Customer.customer_id).offset(offset).limit(limit)
        ],
    }


@router.get("/customers/{customer_id}")
def customer_profile(customer_id: str, db: Session = Depends(get_db)):
    data = Dataset(db)
    customer = data.customer(customer_id)
    events = (
        data.events[data.events.customer_id == customer_id]
        .sort_values("timestamp", ascending=False)
        .head(50)
    )
    events = events.merge(data.products[["product_id", "name"]], on="product_id", how="left")
    return {
        "customer_id": customer_id,
        "name": f"{customer.first_name} {customer.last_name}",
        "email": customer.email,
        "city": customer.city,
        "signup_date": customer.signup_date.isoformat(),
        "timeline": [
            dict(
                date=row.timestamp.isoformat(),
                event=row.event_type,
                product=row["name"],
                value=float(row.value),
            )
            for _, row in events.iterrows()
        ],
    }


@router.get("/data/status")
def status(db: Session = Depends(get_db)):
    counts = {
        model.__tablename__: db.query(model).count()
        for model in [Customer, Product, Order, Event, Promotion]
    }
    return {"counts": counts, "demo_available": not any(counts.values())}


@router.post("/data/demo")
def demo(db: Session = Depends(get_db)):
    if not status(db)["demo_available"]:
        raise HTTPException(409, "Demo data can only be loaded into an empty database")
    from generate_data import generate_dataset, save_dataset
    from backend.app.services.upload_service import upload_multiple_csvs

    with TemporaryDirectory(prefix="demand-demo-") as directory:
        result = upload_multiple_csvs(db, save_dataset(generate_dataset(), directory))
    if result["errors"]:
        raise HTTPException(422, result["errors"])
    return {"message": "Synthetic demonstration dataset loaded", **result}
