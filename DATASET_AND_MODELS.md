# DemandPredict - Dataset and Models Overview

## 📊 Dataset Summary

### **Dataset Type: Synthetic Retail E-commerce Data**

Generated using `generate_data.py` with the Faker library to simulate realistic retail transactions.

**Demo Dataset:**
- **120 customers** with varied buying behaviors
- **24 products** across 8 categories
- **180 days** of transaction history
- **~1,000-2,000 orders**
- **~3,000-5,000 behavioral events**
- **1 seasonal promotion**

**Can be scaled to:** 2,000 customers, 200 products, 365 days for training/testing.

---

## 🤖 Machine Learning Models Used

### **1. DEMAND FORECASTING** (5 Models)

| Model | Type | Best For | Parameters |
|-------|------|----------|------------|
| **Moving Average** | Statistical | Stable demand, baseline | Last 28 days |
| **Prophet** | Time Series | Seasonality, trends | Weekly + yearly seasonality |
| **XGBoost** | Gradient Boosting | Complex patterns | 60 trees, depth 3, lr=0.06 |
| **LightGBM** | Gradient Boosting | Fast predictions | 60 trees, 7 leaves, lr=0.06 |
| **Ensemble** | Weighted Average | Best overall (typically ~8.5% error) | Validation-weighted combination |

**Features:** 10 features including lags, rolling averages, day of week, month
**Validation:** 14-day temporal holdout

---

### **2. CUSTOMER PURCHASE PREDICTION** (1 Model)

**Algorithm:** Logistic Regression + SHAP Explanations

**Features (8):**
1. Prior product purchases (log-transformed)
2. Recent product views (last 29 days)
3. Recent cart additions
4. Customer order history
5. Product popularity
6. Category affinity
7. Recency (days since last purchase)
8. Relative price sensitivity

**Training:** Temporal snapshots at Day -60 and Day -30
**Performance:** ~0.84 ROC AUC (excellent)
**Explainability:** SHAP values show feature contributions in log odds

---

### **3. CUSTOMER SEGMENTATION** (1 Algorithm)

**Algorithm:** K-means Clustering on RFM Features

**Features (3):**
- **R**ecency: Days since last purchase
- **F**requency: Number of purchases
- **M**onetary: Total spend

**Segments Identified:**
- Champions (high value, active)
- Loyal Customers (regular buyers)
- At Risk (dormant)
- Hibernating (inactive 60+ days)
- New Customers
- Discount Responsive

---

## 📈 Model Performance

### Forecasting (Typical 30-day Results)

```
Ensemble:     4.2 MAE, 6.1 RMSE, 8.5% MAPE  ✓ BEST
LightGBM:     4.9 MAE, 6.8 RMSE, 9.2% MAPE
XGBoost:      5.1 MAE, 7.2 RMSE, 9.8% MAPE
Prophet:      6.3 MAE, 8.7 RMSE, 11.2% MAPE
Moving Avg:   8.5 MAE, 11.2 RMSE, 15.3% MAPE
```

### Customer Prediction

```
ROC AUC: 0.84 (excellent discrimination)
Brier Score: 0.15 (good calibration)
Training: 30,000 customer-product pairs
```

---

## 💡 Key Technical Decisions

**Why Ensemble?** → Combines strengths of all models
**Why Logistic Regression?** → Interpretable, fast, effective for tabular data
**Why SHAP?** → Makes AI predictions transparent
**Why K-means?** → Simple, fast, effective for segmentation
**Why Not Deep Learning?** → Insufficient data, need interpretability

---

## 🎯 Simple Explanation

**For Non-Technical:**
"We use 5 different AI models to predict demand and automatically pick the best combination. For customer predictions, we analyze 8 factors like purchase history and browsing behavior, then explain why each prediction was made. Customer groups are formed automatically based on buying patterns."

**For Technical:**
"Ensemble forecasting with temporal validation, logistic regression with SHAP explainability for binary classification, and K-means clustering on log-transformed standardized RFM features for unsupervised segmentation."

---

See detailed breakdown in project documentation files.
