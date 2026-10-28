import numpy as np
import pandas as pd
from types import SimpleNamespace
from ml.forecasting import forecast_cached, metrics
from ml.recommendations import FeatureSnapshot, _training_window


def test_short_history_fallback_and_zero_demand():
    result = forecast_cached((0.0,) * 10, "2025-01-01", 7, "xgboost")
    assert result["model_used"] == "ma"
    assert result["model_metrics"] == {}
    assert all(row["predicted_demand"] == 0 for row in result["forecast"])


def test_metrics_handle_zero_denominators():
    assert metrics([0, 0], [0, 1]) == {"mae": 0.5, "rmse": 0.7071}
    assert metrics([1, 2], [1, 2])["wmape"] == 0


def test_features_do_not_leak_future_activity(dataset):
    data = SimpleNamespace(
        customers=dataset["customers"],
        products=dataset["products"],
        events=dataset["events"].copy(),
        sales=dataset["orders"].query("status == 'delivered'").copy(),
    )
    cutoff = pd.Timestamp("2025-05-01")
    original = FeatureSnapshot(data, cutoff).row("CUST_000001", "PROD_000001")
    future = data.events.timestamp > cutoff + pd.Timedelta(days=1)
    data.events.loc[future, "event_type"] = "add_to_cart"
    data.sales.loc[data.sales.order_date > cutoff + pd.Timedelta(days=1), "quantity"] = 99999
    assert FeatureSnapshot(data, cutoff).row("CUST_000001", "PROD_000001") == original
    x, y = _training_window(data, cutoff, 42)
    assert x.shape[1] == 8
    assert len(y) == len(x)
    assert np.isfinite(x).all()
