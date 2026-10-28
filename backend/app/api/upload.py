"""CSV uploads with bounded reads, unique temporary files and atomic writes."""

import csv
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.upload_service import upload_multiple_csvs, REQUIRED_COLUMNS
from backend.app.schemas.schemas import UploadResponse

router = APIRouter()
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100")) * 1024 * 1024


async def import_files(db, files):
    if not files:
        raise HTTPException(400, "Select at least one CSV file")
    try:
        with TemporaryDirectory(prefix="demand-upload-") as directory:
            paths = {}
            for table, upload in files.items():
                if Path(upload.filename or "").suffix.lower() != ".csv":
                    raise HTTPException(400, "Only CSV files are accepted")
                size = 0
                path = Path(directory) / f"{table}.csv"
                with path.open("wb") as output:
                    while chunk := await upload.read(1024 * 1024):
                        size += len(chunk)
                        if size > MAX_FILE_SIZE:
                            raise HTTPException(413, "CSV exceeds the upload size limit")
                        output.write(chunk)
                paths[table] = str(path)
            result = upload_multiple_csvs(db, paths)
            if result["errors"]:
                raise HTTPException(422, result["errors"])
            return dict(message=f"Imported {result['rows_processed']} rows", **result)
    finally:
        for upload in files.values():
            await upload.close()


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(
    customers: UploadFile = File(None),
    products: UploadFile = File(None),
    events: UploadFile = File(None),
    orders: UploadFile = File(None),
    promotions: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    return await import_files(
        db,
        {
            key: value
            for key, value in dict(
                customers=customers,
                products=products,
                promotions=promotions,
                events=events,
                orders=orders,
            ).items()
            if value
        },
    )


@router.post("/upload/single/{table_name}", response_model=UploadResponse)
async def upload_single_table(
    table_name: str, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    if table_name not in REQUIRED_COLUMNS:
        raise HTTPException(404, "Unknown table")
    return await import_files(db, {table_name: file})


@router.get("/upload/schema/{table_name}")
def get_table_schema(table_name: str):
    if table_name not in REQUIRED_COLUMNS:
        raise HTTPException(404, "Unknown table")
    return {
        "table": table_name,
        "required_columns": REQUIRED_COLUMNS[table_name],
        "example_row": get_example_row(table_name),
    }


@router.get("/upload/template/{table_name}")
def download_template(table_name: str):
    schema = get_table_schema(table_name)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=schema["required_columns"])
    writer.writeheader()
    writer.writerow(
        {
            key: json.dumps(value) if isinstance(value, list) else value
            for key, value in schema["example_row"].items()
        }
    )
    return Response(
        stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{table_name}.csv"'},
    )


def get_example_row(table_name: str) -> Dict:
    """Get an example row for a table."""
    examples = {
        "customers": {
            "customer_id": "CUST_000001",
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "age": 35,
            "city": "Mumbai",
            "state": "Maharashtra",
            "signup_date": "2023-01-15",
            "segment": "loyal_high",
            "avg_order_value": 2500.0,
            "purchase_frequency_days": 15.5,
            "price_sensitivity": 0.3,
            "promo_responsiveness": 0.4,
            "is_active": True,
        },
        "products": {
            "product_id": "PROD_000001",
            "name": "Wireless Headphones Pro",
            "category": "Electronics",
            "subcategory": "Audio",
            "brand": "SoundMax",
            "price": 4999.0,
            "cost": 2500.0,
            "margin": 0.5,
            "launch_date": "2023-01-01",
            "is_seasonal": True,
            "seasonal_peaks": [10, 11, 12],
            "is_active": True,
            "stock_quantity": 500,
            "reorder_point": 50,
        },
        "events": {
            "event_id": "EVT_00000001",
            "customer_id": "CUST_000001",
            "product_id": "PROD_000001",
            "session_id": "SESS_00000001",
            "event_type": "view",
            "timestamp": "2023-01-15 10:30:00",
            "value": 0.0,
            "quantity": 0,
        },
        "orders": {
            "order_id": "ORD_00000001",
            "customer_id": "CUST_000001",
            "product_id": "PROD_000001",
            "session_id": "SESS_00000001",
            "order_date": "2023-01-15 10:35:00",
            "quantity": 1,
            "unit_price": 4999.0,
            "total_amount": 4999.0,
            "discount_amount": 0.0,
            "promo_id": None,
            "status": "delivered",
            "payment_method": "upi",
            "shipping_city": "Mumbai",
            "shipping_state": "Maharashtra",
        },
        "promotions": {
            "promo_id": "PROMO_0001",
            "name": "Diwali Sale",
            "type": "percentage_discount",
            "discount_value": 0.25,
            "start_date": "2023-11-05",
            "end_date": "2023-11-15",
            "applicable_categories": ["Electronics", "Clothing", "Home & Kitchen"],
            "min_order_value": 1000.0,
            "max_discount": 5000.0,
            "is_active": True,
        },
    }
    return examples.get(table_name, {})
