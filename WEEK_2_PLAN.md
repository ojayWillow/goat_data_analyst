# Week 2 Plan: Anomaly Detection + Prediction (Dec 11-15, 2025)

## Overview
5 new agents to build. 1 agent per day.

---

## Day 1 (Dec 11): AnomalyDetector Agent

**Goal:** Detect anomalies using 3 algorithms + ensemble

**Workers (4):**
- IsolationForest
- LocalOutlierFactor (LOF)
- OneClassSVM
- Ensemble (voting)

**Key Methods:**
- `detect_isolation_forest(contamination=0.1)`
- `detect_lof(n_neighbors=20)`
- `detect_ocsvm(nu=0.05)`
- `detect_ensemble()` - all 3 algorithms

**Tests:** 10 tests

---

## Day 2 (Dec 12): Predictor Agent

**Goal:** Time series forecasting with 4 models

**Workers (4):**
- LinearRegression
- ARIMA
- ExponentialSmoothing
- Prophet

**Key Methods:**
- `predict_linear(periods=10)`
- `predict_arima(periods=10)`
- `predict_exponential(periods=10)`
- `predict_prophet(periods=10)`

**Tests:** 10 tests

---

## Day 3 (Dec 13): Recommender Agent

**Goal:** Feature recommendations and patterns

**Workers (3):**
- CorrelationRecommender
- VolumeRecommender
- PatternRecommender

**Key Methods:**
- `recommend_by_correlation()`
- `recommend_by_volume()`
- `recommend_patterns()`

**Tests:** 8 tests

---

## Day 4 (Dec 14): Reporter Agent

**Goal:** Generate data reports

**Workers (3):**
- HTMLReporter
- PDFReporter
- MarkdownReporter

**Key Methods:**
- `generate_html_report()`
- `generate_pdf_report()`
- `generate_markdown_report()`

**Tests:** 8 tests

---

## Day 5 (Dec 15): Visualizer Agent

**Goal:** Create data visualizations

**Workers (5):**
- LineChart
- BarChart
- ScatterPlot
- Heatmap
- Distribution

**Key Methods:**
- `plot_line()`
- `plot_bar()`
- `plot_scatter()`
- `plot_heatmap()`
- `plot_distribution()`

**Tests:** 10 tests

---

## Summary

| Day | Agent | Workers | Tests |
|-----|-------|---------|-------|
| 1 | AnomalyDetector | 4 | 10 |
| 2 | Predictor | 4 | 10 |
| 3 | Recommender | 3 | 8 |
| 4 | Reporter | 3 | 8 |
| 5 | Visualizer | 5 | 10 |
| **TOTAL** | **5 agents** | **19 workers** | **46 tests** |

**Week 2 Target:** 46 new tests, all passing ✅

---

## Start

Ready to begin Day 1 (AnomalyDetector)?
