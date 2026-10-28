"""Train propensity and evaluate category forecasts: python -m ml.training.train_pipeline."""

import json
from pathlib import Path
import joblib
from backend.app.core.database import init_db, SessionLocal
from backend.app.services.analytics import Dataset
from ml.recommendations import train


def main():
    init_db()
    with SessionLocal() as db:
        data = Dataset(db)
        if data.orders.empty:
            raise SystemExit(
                "Import orders first (Settings or python -m backend.app.core.database)."
            )
        output = Path("models")
        output.mkdir(exist_ok=True)
        trained = train(data)
        joblib.dump(trained, output / "purchase_propensity.joblib")
        reports = {
            category: data.forecast(30, "ensemble", category=category)
            for category in sorted(data.products.category.unique())
        }
        report = {
            "as_of": data.as_of.isoformat(),
            "purchase_propensity": trained["report"],
            "categories": reports,
        }
        (output / "evaluation.json").write_text(json.dumps(report, default=str, indent=2))
        print(f"Training complete: {output.resolve()}; method={trained['report']['method']}")


if __name__ == "__main__":
    main()
