"""Strict CSV validation and atomic, idempotent dataset imports."""

import ast
import math
import pandas as pd
from pydantic import TypeAdapter, EmailStr
from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, JSON, String
from sqlalchemy.exc import IntegrityError
from backend.app.models.database import Customer, Product, Event, Order, Promotion

MODELS = {
    "customers": Customer,
    "products": Product,
    "promotions": Promotion,
    "events": Event,
    "orders": Order,
}
REQUIRED_COLUMNS = {
    "customers": [
        "customer_id",
        "email",
        "first_name",
        "last_name",
        "gender",
        "age",
        "city",
        "state",
        "signup_date",
        "segment",
        "avg_order_value",
        "purchase_frequency_days",
        "price_sensitivity",
        "promo_responsiveness",
        "is_active",
    ],
    "products": [
        "product_id",
        "name",
        "category",
        "subcategory",
        "brand",
        "price",
        "cost",
        "margin",
        "launch_date",
        "is_seasonal",
        "seasonal_peaks",
        "is_active",
        "stock_quantity",
        "reorder_point",
    ],
    "events": [
        "event_id",
        "customer_id",
        "product_id",
        "session_id",
        "event_type",
        "timestamp",
        "value",
        "quantity",
    ],
    "orders": [
        "order_id",
        "customer_id",
        "product_id",
        "session_id",
        "order_date",
        "quantity",
        "unit_price",
        "total_amount",
        "discount_amount",
        "promo_id",
        "status",
        "payment_method",
        "shipping_city",
        "shipping_state",
    ],
    "promotions": [
        "promo_id",
        "name",
        "type",
        "discount_value",
        "start_date",
        "end_date",
        "applicable_categories",
        "min_order_value",
        "max_discount",
        "is_active",
    ],
}


def _convert(value, column):
    if pd.isna(value):
        if not column.nullable and column.default is None:
            raise ValueError("value is required")
        return None
    kind = column.type
    if isinstance(kind, Enum):
        return kind.enum_class(str(value)).value
    if isinstance(kind, Boolean):
        normalized = str(value).strip().lower()
        if normalized not in {"true", "false", "1", "0"}:
            raise ValueError("expected true/false or 1/0")
        return normalized in {"true", "1"}
    if isinstance(kind, DateTime):
        return pd.to_datetime(value, utc=True, errors="raise").tz_convert(None).to_pydatetime()
    if isinstance(kind, JSON):
        parsed = ast.literal_eval(value) if isinstance(value, str) else value
        if not isinstance(parsed, list):
            raise ValueError("expected a list")
        return parsed
    if isinstance(kind, (Integer, Float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("expected a finite number")
        if isinstance(kind, Integer):
            if not number.is_integer():
                raise ValueError("expected an integer")
            return int(number)
        return number
    text = str(value).strip()
    if not text or (isinstance(kind, String) and kind.length and len(text) > kind.length):
        raise ValueError("empty or overlong text")
    return text


def _validate_record(row, table):
    def check(condition, message):
        if not condition:
            raise ValueError(message)

    for key in ["price", "unit_price", "total_amount"]:
        if key in row:
            check(row[key] > 0, f"{key} must be positive")
    for key in [
        "cost",
        "stock_quantity",
        "reorder_point",
        "discount_amount",
        "min_order_value",
        "max_discount",
        "avg_order_value",
        "purchase_frequency_days",
    ]:
        if key in row and row[key] is not None:
            check(row[key] >= 0, f"{key} must be nonnegative")
    if table == "customers":
        TypeAdapter(EmailStr).validate_python(row["email"])
        check(row["age"] is None or 13 <= row["age"] <= 120, "age must be 13-120")
        for key in ["price_sensitivity", "promo_responsiveness"]:
            check(0 <= row[key] <= 1, f"{key} must be 0-1")
    if table == "products":
        check(
            all(type(v) is int and 1 <= v <= 12 for v in row["seasonal_peaks"]),
            "seasonal_peaks must contain month numbers 1-12",
        )
    if table == "orders":
        check(row["quantity"] > 0, "quantity must be positive")
    if table == "events":
        kind = row["event_type"]
        check(
            row["quantity"] != 0 if kind == "return" else row["quantity"] >= 0,
            "invalid event quantity",
        )
        if kind == "purchase":
            check(row["quantity"] > 0, "purchase quantity must be positive")
    if table == "promotions":
        check(row["end_date"] > row["start_date"], "end_date must follow start_date")
        check(
            all(isinstance(v, str) for v in row["applicable_categories"]),
            "applicable_categories must contain strings",
        )
        check(row["discount_value"] > 0, "discount must be positive")
        if row["type"] == "percentage_discount":
            check(row["discount_value"] <= 1, "percentage discount must be 0-1")


def parse_csv_file(file_path, table_name):
    if table_name not in MODELS:
        return pd.DataFrame(), ["Unknown table"]
    try:
        # Read IDs as strings, retaining leading zeros and literal identifiers like NA.
        frame = pd.read_csv(file_path, dtype=str, keep_default_na=False)
        frame = frame.replace("", None)
    except (ValueError, OSError, UnicodeError) as exc:
        return pd.DataFrame(), [f"Invalid CSV: {exc}"]
    missing = set(REQUIRED_COLUMNS[table_name]) - set(frame.columns)
    unknown = set(frame.columns) - set(REQUIRED_COLUMNS[table_name])
    if missing or unknown:
        return frame, [f"Missing columns: {sorted(missing)}; unknown columns: {sorted(unknown)}"]
    if frame.empty:
        return frame, ["CSV must contain at least one row"]
    primary = list(MODELS[table_name].__table__.primary_key)[0].name
    if frame[primary].duplicated().any():
        return frame, [f"Duplicate {primary} values"]
    records, errors = [], []
    columns = MODELS[table_name].__table__.columns
    for index, source in enumerate(frame.to_dict("records"), start=2):
        try:
            row = {key: _convert(value, columns[key]) for key, value in source.items()}
            _validate_record(row, table_name)
            records.append(row)
        except (ValueError, TypeError, SyntaxError, OverflowError) as exc:
            errors.append(f"Row {index}: {str(exc).splitlines()[0]}")
            if len(errors) >= 25:
                break
    result = pd.DataFrame(records, dtype=object)
    return result, errors


def upload_multiple_csvs(db, file_paths):
    result = {"rows_processed": 0, "tables_updated": [], "errors": []}
    frames = {}
    for table, path in file_paths.items():
        frames[table], errors = parse_csv_file(path, table)
        result["errors"].extend(f"{table}: {message}" for message in errors)
    if result["errors"]:
        return result
    try:
        for table in MODELS:
            if table not in frames:
                continue
            model = MODELS[table]
            records = frames[table].to_dict("records")
            # Flush parent tables first; all files commit together or all roll back.
            if db.bind.dialect.name == "sqlite":
                from sqlalchemy.dialects.sqlite import insert

                primary = list(model.__table__.primary_key)[0].name
                statement = insert(model)
                update = {
                    key: statement.excluded[key]
                    for key in REQUIRED_COLUMNS[table]
                    if key != primary
                }
                statement = statement.on_conflict_do_update(index_elements=[primary], set_=update)
                for offset in range(0, len(records), 1000):
                    db.execute(statement, records[offset : offset + 1000])
            else:
                for row in records:
                    db.merge(model(**row))
            db.flush()
            result["rows_processed"] += len(records)
            result["tables_updated"].append(table)
        db.commit()
    except IntegrityError:
        db.rollback()
        return {
            "rows_processed": 0,
            "tables_updated": [],
            "errors": [
                "Import rolled back: duplicate unique values or unknown customer, product, or promotion reference."
            ],
        }
    except Exception:
        db.rollback()
        raise
    return result


def upload_csv_to_db(db, file_path, table_name, batch_size=1000):
    result = upload_multiple_csvs(db, {table_name: file_path})
    return result["rows_processed"], result["errors"]
