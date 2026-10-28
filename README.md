# DemandPredict

A complete local retail analytics application built with React, TypeScript, FastAPI, SQLite, and Python machine learning. The dashboard uses imported records throughout; no screen uses hardcoded business results.

## Run locally

Requires **Python 3.11**, **Node.js 22.12+** (or Node 24), and npm. Run these commands from the project root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip setuptools
.venv\Scripts\python -m pip install -r requirements.txt
npm --prefix frontend ci
npm run dev
```

Open **http://127.0.0.1:5173**. Both servers stay in the terminal; press Ctrl+C to stop. Backend code changes require a restart. API documentation is at **http://127.0.0.1:8000/docs**.

On macOS/Linux, use `.venv/bin/python` instead of `.venv\Scripts\python`; the remaining commands are the same.

1. Open **Settings** and click **Load demo dataset** for 120 fictional customers, 24 products, and 180 days of history.
2. Alternatively, upload your CSV files using the provided schema examples. Upload customers, products, and promotions before or together with events and orders.
3. Explore Overview, Forecast, Customer, Segments, and Insights. Reports can be downloaded as CSV.

Demo data loads only into an empty database. Existing data is never silently replaced. To keep real uploads separate from the demo, set `DATABASE_URL=sqlite:///data/my-store.db` in `.env` and restart; this creates a separate database. Imported IDs perform upserts, so repeating an import does not duplicate records. Imports are transactional: all supplied files succeed together or none are saved.

## Features

- **Overview:** sales, units, customer counts, recent daily demand, and category revenue.
- **Forecast:** product/category daily forecasts for 1-90 days; moving average, Prophet, XGBoost, LightGBM, and a validation-weighted ensemble; error comparisons and approximate residual bands.
- **Customer:** search by name, ID, or email; purchase propensity, probability-weighted expected quantities/revenue, linear SHAP drivers, and recent activity.
- **Segments:** RFM features, K-means clusters with descriptive behavior labels, recommendations, and paginated member lists.
- **Insights:** stockout/overstock risks, rising/falling demand, and reorder quantities for the chosen planning horizon.
- **Settings:** multi-file CSV upload, validation feedback, example downloads, data counts, and demo loading.
- Responsive navigation, light/dark themes, loading/error/empty states, CSV exports, and API documentation.

## Data and import rules

Schemas and example rows are available in Settings and `/api/v1/upload/schema/{table}`. Download an example with `/api/v1/upload/template/{table}`. Supported tables: customers, products, promotions, events, orders.

- All documented columns are required; optional values may be blank. Unknown columns are rejected.
- IDs are strings, including leading zeros. Customer emails must be valid and unique.
- Dates use ISO format and are normalized to timezone-naive UTC.
- Booleans accept true/false or 1/0. Lists use literal brackets, e.g. `[10, 11, 12]` or `["Electronics"]`.
- Order quantities must be positive integers; monetary values must be finite. Stock and reorder points cannot be negative.
- Order/event customer and product references, and optional promotion references, must exist after the import.
- Returns can use positive or negative event quantities; zero is rejected. Sales metrics exclude returned and cancelled orders and exclude pending orders. Mark the associated order returned to remove it from sales; a return event alone does not change an order's status.
- Individual uploads default to a 100 MB limit. Invalid records return HTTP 422 with row-specific validation messages (up to 25 per file).
- All monetary values are treated as **INR**. Currency conversion is not performed.

## Models and interpretation

**Forecast origin:** predictions begin after the latest order/event date in the dataset, which is displayed in the UI. Historical data is not represented as a forecast from today's date. Missing days inside the observed history are filled with zero; the series is limited to the last 730 days. Product history begins no earlier than launch.

**Forecast validation:** the latest 14 days (or a shorter holdout for limited history) are excluded from model fitting when computing metrics. Ensemble weights are chosen using an earlier, separate 14-day window, with equal weights for shorter series. Final forecasts refit on the full observed series. Tree models recursively use lag, rolling, and calendar features. Fewer than 49 days or constant demand trigger an explicit moving-average fallback. Fewer than 14 days have no validation metrics. MAPE excludes actual-zero days; WMAPE is omitted for an all-zero holdout. Residual bands are approximate ranges, not calibrated guarantees. Accuracy is measured from each uploaded dataset rather than promised in advance.

**Customer model:** regularized logistic regression learns from uniformly sampled customer/product pairs at temporal cutoffs. Features contain only information available at each cutoff. The subsequent 30 days define the label. An earlier window trains the validation model; a later window evaluates it. The final model refits on both completed windows. The report exposes Brier score, a constant-probability baseline, and ROC AUC when both classes are present. Insufficient history uses an explicitly labeled smoothed-history estimate. Non-30-day probabilities assume a constant purchase hazard. Linear SHAP values explain 30-day log odds relative to the training feature means under an independent-feature assumption; these are associations, not causal claims.

**Segmentation:** K-means uses standardized log recency, frequency, and monetary values of purchasers; customers without purchases are grouped separately. Cluster profiles receive descriptive labels; purchasers inactive for at least 60 days are explicitly marked at risk. Promotion-heavy occasional purchasers can form a promotion-responsive group. Imported latent segment labels do not drive these assignments.

**Inventory:** recommendations use the last 28 days' mean daily units, a 20% buffer, and the product reorder point. Stock is assumed to describe the dataset's final date. These are planning suggestions and never place orders. Lead times, inbound purchase orders, and stockout-censored demand are not modeled.

The application is intended for a local project/demo or trusted single-user environment. It has no login or multi-tenant authorization. Both the local launcher and Docker ports bind to localhost. Internet deployment requires authentication and HTTPS before exposing customer data. Data and model training currently run within the API process; larger production workloads need background jobs and scalable storage.

## Generate a larger dataset and train

```powershell
.venv\Scripts\python generate_data.py --customers 2000 --products 200 --days 365 --seed 42
.venv\Scripts\python -m backend.app.core.database
.venv\Scripts\python -m ml.training.train_pipeline
```

Generation refuses to overwrite CSVs unless `--force` is supplied. Use `--end-date YYYY-MM-DD` for exactly reproducible dates or `--output-dir` for another directory. The seed command imports the five CSVs from `data/` with the same validation used by the API.

Training writes `models/purchase_propensity.joblib` and `models/evaluation.json`. The API trains/caches its own model against a fingerprint of current imported data, so imports invalidate the cached result automatically. It does not load arbitrary joblib files. `notebooks/exploration.ipynb` provides an optional walkthrough of the same code; install Jupyter separately if needed.

## Verification

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m pip check
npm run build
npm run lint
npm run test:e2e
```

Browser tests use installed Google Chrome. To install it for tests, use `npx --prefix frontend playwright install chrome`, or change the channel in `frontend/playwright.config.ts`. The end-to-end suite starts servers if needed and loads demo data only when the database is empty. Run it against an empty/demo database, not important customer data: it exercises a rejected CSV import and demo setup. Screenshots/traces are written to `frontend/test-results/`.

Optional Python formatting/audit tools: install `requirements-dev.txt`, then run `.venv\Scripts\python -m ruff check backend ml tests generate_data.py` and `.venv\Scripts\python -m pip_audit`. Frontend formatting: `npm --prefix frontend run format:check`.

Backend tests use isolated in-memory databases and cover all forecast options, chronological features, recommendation probabilities, endpoints, pagination, imports, atomic rollback, malicious list values, and upload size limits.

## Docker

```powershell
docker compose up --build
```

Open http://localhost:5173. The frontend is a compiled production build served by Nginx, including SPA route fallback and an API proxy. SQLite and trained artifacts persist in `data/` and `models/` on the host. Optional batch evaluation:

```powershell
docker compose --profile training run --rm ml-trainer
```

Docker is optional. The configuration is supplied, but a container build must be verified on a machine with Docker installed.

## Configuration and layout

Copy `.env.example` to `.env` to override `DATABASE_URL`, `CORS_ORIGINS`, or `MAX_UPLOAD_SIZE_MB`. The default SQLite path is anchored to this project. The frontend uses `/api/v1` through the development/Nginx proxy. For a separate API host, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL`, then rebuild. `API_PROXY_TARGET` can override the development proxy target.

```text
backend/app/api/         HTTP routes
backend/app/core/        Database lifecycle
backend/app/models/      SQLAlchemy tables
backend/app/services/    CSV validation and analytics
ml/forecasting.py         Forecast models and validation
ml/recommendations.py     Temporal propensity model and explanations
ml/training/             Batch training/evaluation entry point
frontend/src/            Dashboard and shared components
frontend/e2e/            Browser workflow tests
tests/                   Backend and model regression tests
scripts/dev.mjs          Local two-server launcher
```

Prophet 1.1.7 uses a compatible pinned CmdStanPy 1.2.5 runtime; newer CmdStanPy rejects its bundled distribution ([upstream issue](https://github.com/facebook/prophet/issues/2697)). Frontend styling follows the [Tailwind v4 PostCSS installation](https://tailwindcss.com/docs/installation/using-postcss).
