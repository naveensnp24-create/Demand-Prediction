"""Generate reproducible synthetic retail CSVs. See --help for dataset sizing."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from faker import Faker

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Home & Kitchen",
    "Beauty & Personal Care",
    "Sports & Fitness",
    "Books & Media",
    "Toys & Games",
    "Grocery & Gourmet",
]
NAMES = [
    "Wireless headphones",
    "Cotton shirt",
    "Kitchen storage set",
    "Daily moisturizer",
    "Training mat",
    "Paperback collection",
    "Strategy board game",
    "Roasted coffee",
]


def generate_dataset(customers=120, products=24, days=180, seed=42, end_date=None):
    if customers < 1 or products < 1 or days < 1:
        raise ValueError("customers, products and days must be positive")
    rng = np.random.default_rng(seed)
    fake = Faker("en_IN")
    fake.seed_instance(seed)
    end = pd.Timestamp(end_date or (datetime.now().date() - timedelta(days=1))).normalize()
    start = end - pd.Timedelta(days=days - 1)
    customer_rows, product_rows, order_rows, event_rows = [], [], [], []
    segments = ["loyal_high", "discount_hunter", "at_risk", "new", "occasional"]
    for i in range(customers):
        segment = segments[i % len(segments)]
        customer_rows.append(
            dict(
                customer_id=f"CUST_{i + 1:06d}",
                email=f"customer{i + 1}@example.com",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                gender=str(rng.choice(["M", "F", "Other"])),
                age=int(rng.integers(18, 70)),
                city=fake.city(),
                state=fake.state(),
                signup_date=start - pd.Timedelta(days=int(rng.integers(1, 365))),
                segment=segment,
                avg_order_value=0.0,
                purchase_frequency_days=0.0,
                price_sensitivity=0.8 if segment == "discount_hunter" else 0.3,
                promo_responsiveness=0.85 if segment == "discount_hunter" else 0.4,
                is_active=True,
            )
        )
    for i in range(products):
        price = float(rng.integers(200, 7000))
        cost = round(price * 0.55, 2)
        product_rows.append(
            dict(
                product_id=f"PROD_{i + 1:06d}",
                name=f"{NAMES[i % 8]} {i // 8 + 1}",
                category=CATEGORIES[i % 8],
                subcategory=NAMES[i % 8],
                brand=f"Brand {i % 5 + 1}",
                price=price,
                cost=cost,
                margin=round((price - cost) / price, 3),
                launch_date=start - pd.Timedelta(days=30),
                is_seasonal=i % 3 == 0,
                seasonal_peaks=[10, 11, 12] if i % 3 == 0 else [],
                is_active=True,
                stock_quantity=int(rng.choice([2, 8, 20, 70, 250])),
                reorder_point=10,
            )
        )
    promos = [
        dict(
            promo_id="PROMO_0001",
            name="Synthetic seasonal promotion",
            type="percentage_discount",
            discount_value=0.15,
            start_date=start,
            end_date=end + pd.Timedelta(days=1),
            applicable_categories=CATEGORIES,
            min_order_value=0.0,
            max_discount=5000.0,
            is_active=True,
        )
    ]
    for day in range(days):
        date = start + pd.Timedelta(days=day)
        for customer_index in rng.choice(customers, max(1, customers // 4), replace=False):
            customer = customer_rows[customer_index]
            segment = customer["segment"]
            if segment == "at_risk" and day > days * 0.65:
                continue
            if segment == "new" and day < days * 0.8:
                continue
            preferred = [i for i in range(products) if i % 8 == customer_index % 8]
            index = int(
                rng.choice(preferred if preferred and rng.random() < 0.75 else range(products))
            )
            product = product_rows[index]
            session = f"SESS_{len(event_rows) + 1:08d}"
            time = date + pd.Timedelta(hours=int(rng.integers(8, 22)))

            def event(kind, value=0.0, quantity=0):
                event_rows.append(
                    dict(
                        event_id=f"EVT_{len(event_rows) + 1:08d}",
                        customer_id=customer["customer_id"],
                        product_id=product["product_id"],
                        session_id=session,
                        event_type=kind,
                        timestamp=time,
                        value=value,
                        quantity=quantity,
                    )
                )

            event("view")
            event("click")
            probability = 0.7 if segment == "loyal_high" else 0.4
            probability *= 1.2 if date.dayofweek >= 5 else 1.0
            probability *= (
                1.25 if product["is_seasonal"] and date.month in product["seasonal_peaks"] else 1.0
            )
            if rng.random() < probability:
                event("add_to_cart", quantity=1)
                if rng.random() < 0.7:
                    quantity = int(rng.integers(1, 4))
                    discount = (
                        product["price"] * quantity * 0.15
                        if segment == "discount_hunter" or rng.random() < 0.15
                        else 0.0
                    )
                    total = round(product["price"] * quantity - discount, 2)
                    returned = rng.random() < 0.03
                    order_rows.append(
                        dict(
                            order_id=f"ORD_{len(order_rows) + 1:08d}",
                            customer_id=customer["customer_id"],
                            product_id=product["product_id"],
                            session_id=session,
                            order_date=time,
                            quantity=quantity,
                            unit_price=product["price"],
                            total_amount=total,
                            discount_amount=round(discount, 2),
                            promo_id="PROMO_0001" if discount else None,
                            status="returned" if returned else "delivered",
                            payment_method="upi",
                            shipping_city=customer["city"],
                            shipping_state=customer["state"],
                        )
                    )
                    event("purchase", total, quantity)
                    if returned:
                        event("return", -total, -quantity)
    from backend.app.services.upload_service import REQUIRED_COLUMNS

    return {
        name: pd.DataFrame(rows, columns=REQUIRED_COLUMNS[name])
        for name, rows in dict(
            customers=customer_rows,
            products=product_rows,
            promotions=promos,
            events=event_rows,
            orders=order_rows,
        ).items()
    }


def save_dataset(dataset, output_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, frame in dataset.items():
        path = output / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = str(path)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--products", type=int, default=200)
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--end-date", help="YYYY-MM-DD; defaults to yesterday")
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--force", action="store_true", help="Replace existing generated CSV files")
    args = parser.parse_args()
    output = Path(args.output_dir)
    if not args.force and any(
        (output / f"{name}.csv").exists()
        for name in ["customers", "products", "events", "orders", "promotions"]
    ):
        parser.error("CSV files already exist; choose another --output-dir or use --force")
    dataset = generate_dataset(args.customers, args.products, args.days, args.seed, args.end_date)
    save_dataset(dataset, output)
    print({name: len(frame) for name, frame in dataset.items()})


if __name__ == "__main__":
    main()
