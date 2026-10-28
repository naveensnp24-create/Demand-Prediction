import pytest
from backend.app.services.upload_service import parse_csv_file


def upload(client, table, frame):
    return client.post(
        f"/api/v1/upload/single/{table}",
        files={"file": (f"{table}.csv", frame.to_csv(index=False), "text/csv")},
    )


def test_single_import_is_idempotent_and_updates(client, dataset):
    original = dataset["products"].copy()
    assert upload(client, "products", original).status_code == 200
    assert upload(client, "products", original).status_code == 200
    assert client.get("/api/v1/data/status").json()["counts"]["products"] == len(original)
    original.loc[0, "price"] = 9999
    assert upload(client, "products", original).status_code == 200
    assert client.get("/api/v1/products?q=PROD_000001").json()["products"][0]["price"] == 9999


def test_multi_file_foreign_key_failure_is_atomic(client, dataset):
    orders = dataset["orders"].iloc[:1].copy()
    orders.loc[:, "customer_id"] = "missing"
    response = client.post(
        "/api/v1/upload",
        files={
            "products": ("products.csv", dataset["products"].to_csv(index=False)),
            "orders": ("orders.csv", orders.to_csv(index=False)),
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]
    assert client.get("/api/v1/data/status").json()["counts"]["products"] == 0


@pytest.mark.parametrize(
    "table,column,value",
    [
        ("products", "price", "not-a-number"),
        ("products", "stock_quantity", -1),
        ("products", "seasonal_peaks", "[0, 15]"),
        ("products", "is_active", "maybe"),
        ("customers", "signup_date", "tomorrowish"),
        ("customers", "email", "not-an-email"),
        ("customers", "price_sensitivity", float("inf")),
        ("orders", "quantity", 1.5),
        ("events", "event_type", "unknown"),
        ("promotions", "applicable_categories", "[1]"),
    ],
)
def test_invalid_values_report_errors_without_writes(client, dataset, table, column, value):
    frame = dataset[table].iloc[:1].astype(object).copy()
    frame.loc[frame.index[0], column] = value
    response = upload(client, table, frame)
    assert response.status_code == 422, response.text
    assert client.get("/api/v1/data/status").json()["demo_available"]


def test_missing_duplicate_empty_and_extension(client, dataset):
    products = dataset["products"]
    assert upload(client, "products", products.drop(columns=["price"])).status_code == 422
    assert upload(client, "products", products.iloc[[0, 0]]).status_code == 422
    assert upload(client, "products", products.iloc[:0]).status_code == 422
    assert client.post("/api/v1/upload").status_code == 400
    assert (
        client.post(
            "/api/v1/upload/single/products", files={"file": ("bad.txt", "bad")}
        ).status_code
        == 400
    )
    assert (
        client.post("/api/v1/upload/single/missing", files={"file": ("bad.csv", "bad")}).status_code
        == 404
    )


def test_list_payload_is_never_executed(tmp_path, dataset):
    marker = tmp_path / "executed.txt"
    frame = dataset["products"].iloc[:1].copy()
    frame.loc[0, "seasonal_peaks"] = (
        f"__import__('pathlib').Path({str(marker)!r}).write_text('unsafe')"
    )
    csv = tmp_path / "products.csv"
    frame.to_csv(csv, index=False)
    _, errors = parse_csv_file(csv, "products")
    assert errors
    assert not marker.exists()


def test_unique_email_conflict_rolls_back(client, dataset):
    original = dataset["customers"].iloc[:1].copy()
    assert upload(client, "customers", original).status_code == 200
    other = original.copy()
    other.loc[0, "customer_id"] = "another-id"
    assert upload(client, "customers", other).status_code == 422
    assert client.get("/api/v1/data/status").json()["counts"]["customers"] == 1


def test_size_limit_enforced(client, monkeypatch):
    from backend.app.api import upload as module

    monkeypatch.setattr(module, "MAX_FILE_SIZE", 10)
    response = client.post(
        "/api/v1/upload/single/products", files={"file": ("products.csv", "a" * 11)}
    )
    assert response.status_code == 413
