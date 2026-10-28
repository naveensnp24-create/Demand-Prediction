"""Purchase propensity trained on temporal customer/product snapshots.

Linear SHAP values use an independent-feature background in standardized feature
space and explain log odds. Horizon conversion assumes a constant hazard.
"""

import hashlib
from threading import RLock
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, brier_score_loss

FEATURES = [
    "prior_product_purchases",
    "recent_product_views",
    "recent_cart_additions",
    "customer_order_count",
    "product_order_count",
    "category_affinity",
    "days_since_product_purchase",
    "relative_price",
]
_CACHE = {}
_LOCK = RLock()


class FeatureSnapshot:
    def __init__(self, data, cutoff):
        self.cutoff = cutoff
        sales = data.sales[data.sales.order_date < cutoff + pd.Timedelta(days=1)]
        events = data.events[
            (data.events.timestamp < cutoff + pd.Timedelta(days=1))
            & (data.events.timestamp >= cutoff - pd.Timedelta(days=29))
        ]
        self.pairs = sales.groupby(["customer_id", "product_id"]).size().to_dict()
        self.last = sales.groupby(["customer_id", "product_id"]).order_date.max().to_dict()
        self.customer = sales.groupby("customer_id").size().to_dict()
        self.product = sales.groupby("product_id").size().to_dict()
        self.views = (
            events[events.event_type.isin(["view", "click"])]
            .groupby(["customer_id", "product_id"])
            .size()
            .to_dict()
        )
        self.carts = (
            events[events.event_type.isin(["add_to_cart", "wishlist"])]
            .groupby(["customer_id", "product_id"])
            .size()
            .to_dict()
        )
        joined = sales.merge(data.products[["product_id", "category"]], on="product_id")
        self.categories = joined.groupby(["customer_id", "category"]).size().to_dict()
        self.product_categories = data.products.set_index("product_id").category.to_dict()
        self.prices = data.products.set_index("product_id").price.to_dict()
        self.spend = sales.groupby("customer_id").unit_price.mean().to_dict()
        self.median_price = float(data.products.price.median()) if len(data.products) else 1.0

    def row(self, customer_id, product_id):
        pair = (customer_id, product_id)
        last = self.last.get(pair)
        recency = (
            min(365, max(0, (self.cutoff - last.normalize()).days)) if last is not None else 365
        )
        return [
            np.log1p(self.pairs.get(pair, 0)),
            np.log1p(self.views.get(pair, 0)),
            np.log1p(self.carts.get(pair, 0)),
            np.log1p(self.customer.get(customer_id, 0)),
            np.log1p(self.product.get(product_id, 0)),
            self.categories.get((customer_id, self.product_categories[product_id]), 0)
            / max(1, self.customer.get(customer_id, 0)),
            recency / 365,
            np.log1p(
                self.prices[product_id] / max(1, self.spend.get(customer_id, self.median_price))
            ),
        ]


def _training_window(data, cutoff, seed):
    customers = data.customers[data.customers.signup_date <= cutoff].customer_id.to_numpy()
    products = data.products[data.products.launch_date <= cutoff].product_id.to_numpy()
    if not len(customers) or not len(products):
        return np.empty((0, len(FEATURES))), np.array([])
    # Uniform pair sampling preserves prevalence, unlike sampling extra positives.
    count = min(30000, len(customers) * len(products))
    indices = np.random.default_rng(seed).choice(
        len(customers) * len(products), count, replace=False
    )
    target = data.sales[
        (data.sales.order_date >= cutoff + pd.Timedelta(days=1))
        & (data.sales.order_date < cutoff + pd.Timedelta(days=31))
    ]
    positives = set(zip(target.customer_id, target.product_id))
    snapshot = FeatureSnapshot(data, cutoff)
    pairs = [(customers[i // len(products)], products[i % len(products)]) for i in indices]
    return np.array([snapshot.row(*pair) for pair in pairs]), np.array(
        [int(pair in positives) for pair in pairs]
    )


def train(data):
    report = {
        "method": "smoothed_history",
        "validation": {},
        "training_examples": 0,
        "note": "Insufficient temporal labels; estimates use smoothed purchase history.",
    }
    if data.sales.empty or (data.as_of - data.sales.order_date.min()).days < 90:
        return {"report": report}
    x_train, y_train = _training_window(data, data.as_of - pd.Timedelta(days=60), 42)
    x_test, y_test = _training_window(data, data.as_of - pd.Timedelta(days=30), 43)
    if len(np.unique(y_train)) < 2 or len(x_test) == 0:
        return {"report": report}
    scaler = StandardScaler().fit(x_train)
    estimator = LogisticRegression(C=1.0, max_iter=500, random_state=42).fit(
        scaler.transform(x_train), y_train
    )
    probabilities = estimator.predict_proba(scaler.transform(x_test))[:, 1]
    validation = {
        "brier_score": float(brier_score_loss(y_test, probabilities)),
        "positive_rate": float(y_test.mean()),
        "examples": len(y_test),
        "constant_baseline_brier": float(
            brier_score_loss(y_test, np.full(len(y_test), y_train.mean()))
        ),
    }
    if len(np.unique(y_test)) == 2:
        validation["roc_auc"] = float(roc_auc_score(y_test, probabilities))
    combined_x = np.concatenate([x_train, x_test])
    combined_y = np.concatenate([y_train, y_test])
    scaler = StandardScaler().fit(combined_x)
    estimator = LogisticRegression(C=1.0, max_iter=500, random_state=42).fit(
        scaler.transform(combined_x), combined_y
    )
    report = {
        "method": "logistic_regression",
        "validation": validation,
        "training_examples": len(combined_y),
        "features": FEATURES,
        "note": "Validation is a later 30-day window. Final model refits on both completed windows.",
    }
    return {"model": estimator, "scaler": scaler, "report": report}


def trained_model(data):
    digest = hashlib.sha256()
    for frame in [data.sales, data.events, data.products, data.customers]:
        digest.update(pd.util.hash_pandas_object(frame.astype(str), index=False).values.tobytes())
    key = digest.hexdigest()
    with _LOCK:
        if key not in _CACHE:
            if len(_CACHE) >= 3:
                _CACHE.pop(next(iter(_CACHE)))
            _CACHE[key] = train(data)
        return _CACHE[key]


def recommend(data, customer_id, horizon=30, top_n=10, product_id=None):
    data.customer(customer_id)
    if product_id:
        data.product(product_id)
    products = (
        data.products[data.products.product_id == product_id]
        if product_id
        else data.products[data.products.is_active]
    )
    trained = trained_model(data)
    snapshot = FeatureSnapshot(data, data.as_of)
    recommendations = []
    if products.empty:
        return recommendations, trained["report"]
    matrix = np.array([snapshot.row(customer_id, p) for p in products.product_id])
    if "model" in trained:
        scaled = trained["scaler"].transform(matrix)
        probabilities = trained["model"].predict_proba(scaled)[:, 1]
        contributions = scaled * trained["model"].coef_[0]
    else:
        days = (
            max(30, (data.as_of - data.sales.order_date.min()).days + 1)
            if not data.sales.empty
            else 30
        )
        probabilities = []
        for product in products.product_id:
            baseline = snapshot.product.get(product, 0) / max(1, len(data.customers))
            rate = (snapshot.pairs.get((customer_id, product), 0) + baseline) / (days * 2)
            probabilities.append(float(1 - np.exp(-rate * 30)))
        contributions = None
    quantities = data.sales.groupby(["customer_id", "product_id"]).quantity.mean().to_dict()
    for index, (_, product) in enumerate(products.iterrows()):
        probability = float(1 - (1 - float(probabilities[index])) ** (horizon / 30))
        quantity = probability * quantities.get((customer_id, product.product_id), 1.0)
        explanations = []
        if contributions is not None:
            for feature_index in np.argsort(np.abs(contributions[index]))[::-1][:5]:
                explanations.append(
                    {
                        "feature": FEATURES[feature_index],
                        "value": float(matrix[index, feature_index]),
                        "shap_value": float(contributions[index, feature_index]),
                        "unit": "log_odds",
                        "method": "linear_interventional_shap",
                    }
                )
        recommendations.append(
            dict(
                product_id=product.product_id,
                product_name=product["name"],
                category=product.category,
                price=float(product.price),
                purchase_probability=probability,
                expected_quantity=float(quantity),
                expected_revenue=float(quantity * product.price),
                shap_explanations=explanations,
            )
        )
    return sorted(recommendations, key=lambda row: row["purchase_probability"], reverse=True)[
        :top_n
    ], trained["report"]
