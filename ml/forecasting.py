"""Daily demand models with chronological validation and recursive forecasts."""

from functools import lru_cache
import logging
import numpy as np
import pandas as pd

MODEL_NAMES = {
    "ma": "Moving average",
    "prophet": "Prophet",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "ensemble": "Validation-weighted ensemble",
}


def features(history, date):
    values = np.asarray(history, dtype=float)
    return [
        values[-1],
        values[-7],
        values[-14],
        values[-7:].mean(),
        values[-14:].mean(),
        values[-28:].mean(),
        values[-7:].std(),
        date.dayofweek,
        date.month,
        date.dayofyear,
    ]


def predict(values, start, horizon, model):
    values = np.asarray(values, dtype=float)
    dates = pd.date_range(start, periods=len(values))
    future = pd.date_range(dates[-1] + pd.Timedelta(days=1), periods=horizon)
    if model == "ma" or len(values) < 35 or np.all(values == values[0]):
        return np.full(horizon, float(np.mean(values[-28:])))
    if model == "prophet":
        from prophet import Prophet

        logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
        estimator = Prophet(
            yearly_seasonality=len(values) >= 365,
            weekly_seasonality=True,
            daily_seasonality=False,
            uncertainty_samples=0,
        )
        estimator.fit(pd.DataFrame({"ds": dates, "y": values}))
        return np.maximum(0, estimator.predict(pd.DataFrame({"ds": future}))["yhat"].to_numpy())
    x = np.array([features(values[:i], dates[i]) for i in range(28, len(values))])
    y = values[28:]
    if model == "xgboost":
        from xgboost import XGBRegressor

        estimator = XGBRegressor(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.06,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=1,
        )
    elif model == "lightgbm":
        from lightgbm import LGBMRegressor

        estimator = LGBMRegressor(
            n_estimators=60,
            max_depth=3,
            num_leaves=7,
            min_child_samples=5,
            learning_rate=0.06,
            verbosity=-1,
            random_state=42,
            n_jobs=1,
        )
    else:
        raise ValueError(f"Unknown model: {model}")
    estimator.fit(x, y)
    history = values.tolist()
    for date in future:
        row = np.array([features(history, date)])
        result = estimator.booster_.predict(row) if model == "lightgbm" else estimator.predict(row)
        history.append(max(0.0, float(result[0])))
    return np.array(history[-horizon:])


def metrics(actual, predicted):
    error = np.asarray(actual) - np.asarray(predicted)
    nonzero = np.asarray(actual) > 0
    result = {"mae": float(np.abs(error).mean()), "rmse": float(np.sqrt(np.mean(error**2)))}
    if nonzero.any():
        result["mape"] = float(np.mean(np.abs(error[nonzero] / np.asarray(actual)[nonzero])) * 100)
    if np.sum(actual) > 0:
        result["wmape"] = float(np.sum(np.abs(error)) / np.sum(actual) * 100)
    return {key: round(value, 4) for key, value in result.items()}


@lru_cache(maxsize=128)
def forecast_cached(values, start, horizon, model):
    values = np.asarray(values)
    candidates = (
        ["ma", "prophet", "xgboost", "lightgbm"]
        if len(values) >= 49 and np.ptp(values) > 0
        else ["ma"]
    )
    holdout = min(14, len(values) // 4)
    scores, validation_predictions = {}, {}
    if len(values) >= 14:
        for name in candidates:
            predicted = predict(values[:-holdout], start, holdout, name)
            validation_predictions[name] = predicted
            scores[name] = metrics(values[-holdout:], predicted)
    weight_scores = {}
    if len(values) >= 70:
        for name in candidates:
            tuning = predict(values[: -2 * holdout], start, holdout, name)
            weight_scores[name] = metrics(values[-2 * holdout : -holdout], tuning)
    weights = np.array(
        [1 / max(weight_scores.get(name, {}).get("mae", 1), 0.01) for name in candidates]
    )
    weights /= weights.sum()
    if validation_predictions:
        combined = np.average(list(validation_predictions.values()), axis=0, weights=weights)
        scores["ensemble"] = metrics(values[-holdout:], combined)
    selected = model if model in candidates else "ma"
    if model == "ensemble":
        predictions = np.average(
            [predict(values, start, horizon, name) for name in candidates], axis=0, weights=weights
        )
        residuals = (
            values[-holdout:] - combined if validation_predictions else values - values.mean()
        )
    else:
        predictions = predict(values, start, horizon, selected)
        residuals = (
            values[-holdout:] - validation_predictions[selected]
            if validation_predictions
            else values - values.mean()
        )
    # Approximate residual bands, explicitly not calibrated probability intervals.
    scale = float(np.sqrt(np.mean(residuals**2))) if len(residuals) else 0.0
    dates = pd.date_range(pd.Timestamp(start) + pd.Timedelta(days=len(values)), periods=horizon)
    result = []
    for i, (date, value) in enumerate(zip(dates, predictions)):
        width = 1.96 * scale * np.sqrt(1 + i / max(len(values), 1))
        result.append(
            {
                "date": date.date().isoformat(),
                "predicted_demand": round(float(value), 3),
                "lower": round(max(0.0, float(value) - width), 3),
                "upper": round(float(value) + width, 3),
            }
        )
    return {
        "forecast": result,
        "model_metrics": scores,
        "model_used": "ensemble" if model == "ensemble" else selected,
        "ensemble_weights": dict(zip(candidates, weights.tolist())) if model == "ensemble" else {},
        "validation_days": holdout if scores else 0,
        "weight_selection": "Earlier 14-day window" if weight_scores else "Equal weights",
        "notes": [
            "Forecast origin is the last date in the uploaded dataset.",
            "Bands are approximate 95% residual ranges, not calibrated guarantees.",
        ]
        + (
            ["Short or constant history: moving-average fallback is used."]
            if candidates == ["ma"]
            else []
        ),
    }
