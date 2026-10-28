import csv
import io
import math
import pytest


def test_empty_workspace_and_health(client):
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/health/db").json()["status"] == "healthy"
    assert client.get("/api/v1/health/ready").json()["status"] == "ready"
    assert client.get("/api/v1/overview").json()["orders"] == 0
    assert client.get("/api/v1/segments").json()["segments"] == []
    assert client.get("/api/v1/data/status").json()["demo_available"]
    assert client.get("/api/v1/insights").status_code == 409
    assert client.get("/api/v1/predict/customer/missing").status_code == 404
    assert client.get("/api/v1/forecast/product/missing").status_code == 404


def test_overview_matches_valid_orders(populated, dataset):
    result = populated.get("/api/v1/overview").json()
    sales = dataset["orders"][dataset["orders"].status == "delivered"]
    assert result["orders"] == len(dataset["orders"])
    assert result["units"] == sales.quantity.sum()
    assert result["revenue"] == round(sales.total_amount.sum(), 2)
    assert len(result["trend"]) == 90
    assert result["as_of"] == "2025-06-30"


@pytest.mark.parametrize("model", ["ma", "prophet", "xgboost", "lightgbm", "ensemble"])
def test_forecasts_are_finite_nonnegative_and_dated(populated, model):
    response = populated.get(f"/api/v1/forecast/product/PROD_000001?horizon=7&model={model}")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["model_used"] == model
    assert len(result["forecast"]) == 7
    assert result["forecast"][0]["date"] == "2025-07-01"
    for row in result["forecast"]:
        assert 0 <= row["lower"] <= row["predicted_demand"] <= row["upper"]
        assert all(math.isfinite(row[key]) for key in ["lower", "predicted_demand", "upper"])
    assert set(result["model_metrics"]) == {"ma", "prophet", "xgboost", "lightgbm", "ensemble"}
    assert result["validation_days"] == 14


def test_category_forecast_and_validation(populated):
    response = populated.get("/api/v1/forecast/category/Home%20%26%20Kitchen?horizon=14&model=ma")
    assert response.status_code == 200, response.text
    assert len(response.json()["forecast"]) == 14
    assert populated.get("/api/v1/forecast/category/unknown").status_code == 404
    assert populated.get("/api/v1/forecast/product/PROD_000001?horizon=0").status_code == 422
    assert populated.get("/api/v1/forecast/product/PROD_000001?model=bogus").status_code == 422


def test_customer_predictions_and_batch(populated):
    result = populated.get("/api/v1/predict/customer/CUST_000001?top_n=4").json()
    assert len(result["recommendations"]) == 4
    assert result["model_report"]["method"] == "logistic_regression"
    probabilities = [row["purchase_probability"] for row in result["recommendations"]]
    assert probabilities == sorted(probabilities, reverse=True)
    for row in result["recommendations"]:
        assert 0 <= row["purchase_probability"] <= 1
        assert row["expected_revenue"] == pytest.approx(row["expected_quantity"] * row["price"])
        assert len(row["shap_explanations"]) == 5
    short = populated.get(
        "/api/v1/predict/customer/CUST_000001/propensity?product_id=PROD_000001&horizon_days=7"
    ).json()
    long = populated.get(
        "/api/v1/predict/customer/CUST_000001/propensity?product_id=PROD_000001&horizon_days=90"
    ).json()
    assert short["purchase_probability"] <= long["purchase_probability"]
    assert (
        populated.get(
            "/api/v1/predict/customer/CUST_000001/propensity?product_id=unknown"
        ).status_code
        == 404
    )
    batch = populated.get(
        "/api/v1/predict/batch?customer_ids=CUST_000001,CUST_000002&top_n=3"
    ).json()
    assert len(batch["predictions"]) == 2
    assert populated.get("/api/v1/predict/batch?customer_ids=").status_code == 422
    assert (
        populated.get(
            "/api/v1/predict/batch?customer_ids=" + ",".join(str(i) for i in range(51))
        ).status_code
        == 422
    )


def test_segments_and_pagination(populated):
    result = populated.get("/api/v1/segments").json()
    assert sum(row["size"] for row in result["segments"]) == 20
    for segment in result["segments"]:
        name = segment["segment"]
        members = populated.get(f"/api/v1/segments/{name}/customers?limit=2").json()
        assert members["total"] == segment["size"]
        assert len(members["customers"]) <= 2
        assert populated.get(f"/api/v1/segments/{name}").status_code == 200
    assert populated.get("/api/v1/segments/missing").status_code == 404
    assert populated.get("/api/v1/segments/new/customers?limit=-1").status_code == 422


def test_inventory_horizons(populated):
    short = populated.get("/api/v1/insights?days_ahead=7").json()
    long = populated.get("/api/v1/insights?days_ahead=90").json()
    short_map = {row["product_id"]: row for row in short["inventory_recommendations"]}
    for row in long["inventory_recommendations"]:
        assert row["suggested_reorder_qty"] >= short_map[row["product_id"]]["suggested_reorder_qty"]
        assert row["predicted_demand"] >= short_map[row["product_id"]]["predicted_demand"]
    for endpoint in ["stockout-risk", "overstock-risk", "trending", "reorder-recommendations"]:
        assert populated.get(f"/api/v1/insights/{endpoint}").status_code == 200


def test_catalog_search_profile_and_demo_guard(populated):
    assert populated.get("/api/v1/products?limit=2").json()["total"] == 16
    assert len(populated.get("/api/v1/products?limit=2").json()["products"]) == 2
    assert populated.get("/api/v1/customers?q=CUST_000001").json()["total"] == 1
    assert populated.get("/api/v1/customers/CUST_000001").json()["timeline"]
    assert len(populated.get("/api/v1/categories").json()["categories"]) == 8
    assert populated.post("/api/v1/data/demo").status_code == 409


def test_templates_are_valid_csv(client):
    for name in ["customers", "products", "events", "orders", "promotions"]:
        response = client.get(f"/api/v1/upload/template/{name}")
        assert response.status_code == 200
        parsed = list(csv.DictReader(io.StringIO(response.text)))
        assert len(parsed) == 1
        assert set(parsed[0]) == set(
            client.get(f"/api/v1/upload/schema/{name}").json()["required_columns"]
        )
