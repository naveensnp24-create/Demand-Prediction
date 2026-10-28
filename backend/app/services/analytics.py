"""Analytics computed from imported records, with explicit dataset-relative dates."""

from datetime import datetime
import math
import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy import select
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from backend.app.models.database import Customer, Product, Order, Event
from ml.forecasting import forecast_cached

LABELS = {
    "loyal_high": "Loyal high spenders",
    "discount_hunter": "Promotion responsive",
    "at_risk": "At risk",
    "new": "New or unconverted",
    "occasional": "Occasional buyers",
}
ACTIONS = {
    "loyal_high": "Offer loyalty benefits and relevant new arrivals.",
    "discount_hunter": "Test targeted promotions and measure incremental purchases.",
    "at_risk": "Run a win-back campaign and ask for feedback.",
    "new": "Help customers discover products with onboarding recommendations.",
    "occasional": "Use category-specific reminders to encourage repeat visits.",
}


class Dataset:
    def __init__(self, db):
        self.customers = pd.read_sql(select(Customer), db.connection())
        self.products = pd.read_sql(select(Product), db.connection())
        self.orders = pd.read_sql(select(Order), db.connection())
        self.events = pd.read_sql(select(Event), db.connection())
        for frame, column in [
            (self.orders, "order_date"),
            (self.events, "timestamp"),
            (self.customers, "signup_date"),
            (self.products, "launch_date"),
        ]:
            frame[column] = pd.to_datetime(frame[column])
        times = [
            frame[column].max()
            for frame, column in [(self.orders, "order_date"), (self.events, "timestamp")]
            if not frame.empty
        ]
        self.as_of = max(times).normalize() if times else pd.Timestamp.now().normalize()
        self.sales = self.orders[
            self.orders.status.isin(["confirmed", "shipped", "delivered"])
        ].copy()
        self.rfm = None

    def product(self, product_id):
        found = self.products[self.products.product_id == product_id]
        if found.empty:
            raise HTTPException(404, "Product not found")
        return found.iloc[0]

    def customer(self, customer_id):
        found = self.customers[self.customers.customer_id == customer_id]
        if found.empty:
            raise HTTPException(404, "Customer not found")
        return found.iloc[0]

    def series(self, product_ids=None):
        if self.orders.empty:
            raise HTTPException(409, "Import order history before generating forecasts")
        start = self.orders.order_date.min().normalize()
        sales = self.sales
        if product_ids is not None:
            sales = sales[sales.product_id.isin(product_ids)]
            launches = self.products[self.products.product_id.isin(product_ids)].launch_date
            if not launches.empty:
                start = max(start, min(launches.min().normalize(), self.as_of))
        start = max(start, self.as_of - pd.Timedelta(days=729))
        index = pd.date_range(start, self.as_of)
        daily = sales.groupby(sales.order_date.dt.normalize()).quantity.sum()
        return daily.reindex(index, fill_value=0).astype(float)

    def forecast(self, horizon, model, product_id=None, category=None):
        if product_id:
            product = self.product(product_id)
            ids = [product_id]
        else:
            found = self.products[self.products.category == category]
            if found.empty:
                raise HTTPException(404, "Category not found")
            ids = found.product_id.tolist()
        series = self.series(ids)
        response = dict(forecast_cached(tuple(series), series.index[0].isoformat(), horizon, model))
        response.update(
            historical_data=[
                {"date": date.date().isoformat(), "demand": value} for date, value in series.items()
            ],
            category=product.category if product_id else category,
            as_of=self.as_of.date().isoformat(),
            generated_at=datetime.utcnow(),
        )
        if product_id:
            response.update(product_id=product_id, product_name=product["name"])
        return response

    def customer_features(self):
        if self.rfm is not None:
            return self.rfm
        data = self.customers[
            [
                "customer_id",
                "first_name",
                "last_name",
                "signup_date",
                "price_sensitivity",
                "promo_responsiveness",
            ]
        ].copy()
        aggregated = self.sales.groupby("customer_id").agg(
            last_order=("order_date", "max"),
            frequency=("session_id", "nunique"),
            monetary=("total_amount", "sum"),
        )
        data = data.join(aggregated, on="customer_id")
        data["recency"] = (self.as_of - data.last_order.dt.normalize()).dt.days
        data["recency"] = data.recency.fillna((self.as_of - data.signup_date).dt.days).clip(lower=0)
        data[["frequency", "monetary"]] = data[["frequency", "monetary"]].fillna(0.0)
        data["avg_order_value"] = data.monetary / data.frequency.clip(lower=1)
        data["segment"] = "occasional"
        data["cluster"] = 0
        buyers = data[data.frequency > 0]
        if not buyers.empty:
            features = np.log1p(buyers[["recency", "frequency", "monetary"]])
            scaled = StandardScaler().fit_transform(features)
            count = min(4, len(np.unique(scaled, axis=0)))
            labels = KMeans(n_clusters=count, random_state=42, n_init=10).fit_predict(scaled)
            data.loc[buyers.index, "cluster"] = labels
            profiles = (
                data.loc[buyers.index]
                .groupby("cluster")[["recency", "frequency", "monetary"]]
                .mean()
            )
            # Label clusters by observed behavior, with recency taking precedence.
            for cluster, profile in profiles.iterrows():
                label = "occasional"
                if profile.recency > max(60, float(buyers.recency.median()) * 1.5):
                    label = "at_risk"
                elif (
                    profile.frequency >= buyers.frequency.median()
                    and profile.monetary >= buyers.monetary.median()
                ):
                    label = "loyal_high"
                data.loc[(data.cluster == cluster) & (data.frequency > 0), "segment"] = label
            discounted = (
                self.sales.assign(discounted=self.sales.discount_amount > 0)
                .groupby("customer_id")
                .discounted.mean()
            )
            promotion_share = data.customer_id.map(discounted).fillna(0.0)
            data.loc[(promotion_share >= 0.5) & (data.segment == "occasional"), "segment"] = (
                "discount_hunter"
            )
        data.loc[(data.frequency > 0) & (data.recency >= 60), "segment"] = "at_risk"
        data.loc[data.frequency == 0, "segment"] = "new"
        self.rfm = data
        return data

    def segments(self):
        data = self.customer_features()
        summaries = []
        for segment, group in data.groupby("segment"):
            summaries.append(
                dict(
                    segment=segment,
                    label=LABELS[segment],
                    size=len(group),
                    percentage=round(100 * len(group) / max(1, len(data)), 2),
                    avg_recency=round(float(group.recency.mean()), 2),
                    avg_frequency=round(float(group.frequency.mean()), 2),
                    avg_monetary=round(float(group.monetary.mean()), 2),
                    avg_order_value=round(float(group.avg_order_value.mean()), 2),
                    price_sensitivity=float(group.price_sensitivity.fillna(0.5).mean()),
                    promo_responsiveness=float(group.promo_responsiveness.fillna(0.5).mean()),
                    characteristics=[ACTIONS[segment]],
                )
            )
        return {
            "segments": summaries,
            "total_customers": len(data),
            "generated_at": datetime.utcnow(),
            "as_of": self.as_of.date().isoformat(),
            "method": "K-means on standardized log RFM, with descriptive labels",
        }

    def inventory(self, horizon=30, overstock_days=90, trend_days=30):
        rows = []
        for _, product in self.products[self.products.is_active].iterrows():
            series = self.series([product.product_id])
            daily = float(series.tail(28).mean())
            demand = daily * horizon
            recent = float(series.tail(trend_days).mean())
            previous = series.iloc[
                max(0, len(series) - trend_days * 2) : max(0, len(series) - trend_days)
            ]
            prior = float(previous.mean()) if len(previous) else recent
            trend = (
                "rising"
                if recent > prior * 1.15
                else "falling"
                if recent < prior * 0.85
                else "stable"
            )
            stock = int(product.stock_quantity)
            cover = stock / daily if daily > 0 else None
            risk = (
                "high"
                if demand > stock
                else "medium"
                if demand * 1.2 > stock and demand > 0
                else "low"
            )
            overstock = "high" if stock > 0 and (cover is None or cover > overstock_days) else "low"
            reorder = (
                max(0, math.ceil(demand * 1.2 + int(product.reorder_point) - stock)) if daily else 0
            )
            rows.append(
                dict(
                    product_id=product.product_id,
                    product_name=product["name"],
                    category=product.category,
                    current_stock=stock,
                    predicted_demand_30d=round(daily * 30, 2),
                    predicted_demand=round(demand, 2),
                    stockout_risk=risk,
                    overstock_risk=overstock,
                    suggested_reorder_qty=reorder,
                    trend=trend,
                    revenue_potential=round(demand * product.price, 2),
                    days_of_stock=cover,
                )
            )
        return sorted(rows, key=lambda row: row["revenue_potential"], reverse=True)

    def insights(self, horizon=30):
        if self.orders.empty:
            raise HTTPException(409, "Import order history to calculate inventory insights")
        rows = self.inventory(horizon)
        return dict(
            top_rising_products=[r for r in rows if r["trend"] == "rising"][:20],
            top_falling_products=[r for r in rows if r["trend"] == "falling"][:20],
            stockout_risk_products=[r for r in rows if r["stockout_risk"] != "low"],
            overstock_risk_products=[r for r in rows if r["overstock_risk"] == "high"],
            inventory_recommendations=rows,
            horizon_days=horizon,
            as_of=self.as_of.date().isoformat(),
            generated_at=datetime.utcnow(),
            method="28-day moving average; reorder includes 20% demand buffer plus reorder point",
        )

    def overview(self):
        categories, trend = [], []
        if not self.orders.empty:
            daily = self.series()
            trend = [
                {"date": date.date().isoformat(), "demand": value}
                for date, value in daily.tail(90).items()
            ]
            for category in sorted(self.products.category.unique()):
                products = self.products[self.products.category == category]
                sales = self.sales[self.sales.product_id.isin(products.product_id)]
                categories.append(
                    {
                        "category": category,
                        "units": int(sales.quantity.sum()),
                        "revenue": round(float(sales.total_amount.sum()), 2),
                    }
                )
        return dict(
            customers=len(self.customers),
            products=len(self.products),
            orders=len(self.orders),
            events=len(self.events),
            revenue=round(float(self.sales.total_amount.sum()), 2),
            units=int(self.sales.quantity.sum()),
            as_of=self.as_of.date().isoformat(),
            trend=trend,
            categories=categories,
            forecast_30d=round(float(self.series().tail(28).mean()) * 30, 2)
            if not self.orders.empty
            else 0,
            at_risk_customers=int((self.customer_features().segment == "at_risk").sum()),
        )
