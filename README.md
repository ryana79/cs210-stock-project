# CS 210 Course Project

**Stock Market Trend Analysis and Prediction Using Financial Data**

**Team:** Ryan Amir, Gian Cases

**Demo Video:** https://youtu.be/s8H6e7xGIFA

This project implements the three required course components in one end-to-end pipeline:

1. **Database** — relational SQLite schema with normalization, foreign keys, and 11 SQL queries
2. **Data Science** — 8-rule data validation pipeline, 11 exploratory visualizations, descriptive statistics
3. **Machine Learning** — feature engineering, 3 classification models + naive baseline, ROC curves

## Project Structure

```text
data/
  raw/         Raw downloaded stock CSV files
  processed/   Cleaned datasets, featured datasets, SQLite database, validation report
docs/          Data dictionary and contribution notes
outputs/
  figures/     15 saved visualizations (11 EDA + 4 ML)
  metrics/     Evaluation outputs, SQL summaries, classification reports
reports/       Final report (Markdown + PDF)
sql/           Database schema and 11 documented SQL queries
src/
  analysis/    EDA and plotting scripts
  data/        Downloading, cleaning, validation, and constants
  db/          Database creation and query execution
  models/      Feature engineering and model training
```

## Dataset Scope

- **Stocks**: `AAPL` (Apple), `MSFT` (Microsoft), `TSLA` (Tesla)
- **Date range**: 2018-01-02 through present (~2,090 trading days per stock)
- **Data source**: Yahoo Finance via `yfinance`
- **Prediction target**: next-day price direction (binary classification)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start — Full Project (One Command)

Run the entire project pipeline (data management + ML) with a single command:

```bash
python3 run_all.py
```

To skip the data download and reuse existing raw CSVs:

```bash
python3 run_all.py --skip-download
```

This executes all 8 steps in order:

| Step | Script | What it does |
| --- | --- | --- |
| 1 | `src/data/download_data.py` | Download raw stock data from Yahoo Finance |
| 2 | `src/data/clean_data.py` | Clean and validate into a single CSV |
| 3 | `src/db/create_database.py` | Create and populate the SQLite database |
| 4 | `src/analysis/generate_eda.py` | Generate 11 EDA figures |
| 5 | `src/db/run_queries.py` | Export 10 SQL report query results |
| 6 | `src/analysis/export_eda_summary.py` | Export EDA summary tables and statistics |
| 7 | `src/models/feature_engineering.py` | Engineer 11 ML features + target variable |
| 8 | `src/models/train_models.py` | Train 3 models + baseline, generate ROC curves |

### Running Pipelines Separately

Ryan's data pipeline only:

```bash
python3 run_pipeline.py
python3 run_pipeline.py --skip-download  # reuse existing raw data
```

Gian's ML pipeline only (requires step 2 output):

```bash
python3 run_ml_pipeline.py
```

## Database Design

Two normalized tables:

- **`stocks`** — one row per ticker (ticker, company name, sector)
- **`daily_prices`** — one row per stock per trading day (prices, volume)

Key constraints: UNIQUE ticker, UNIQUE (stock_id, trade_date), FOREIGN KEY referencing stocks, INDEX on (stock_id, trade_date).

Schema: `sql/schema.sql` | Documented queries: `sql/report_queries.sql`

## Machine Learning Approach

- **Features**: 11 engineered features (daily return, lag prices, moving averages, volatility, volume change)
- **Target**: binary classification — will tomorrow's close be higher than today's?
- **Models**: Logistic Regression, Decision Tree, Random Forest (+ naive majority-class baseline)
- **Split**: chronological 80/20 within each ticker (prevents future-data leakage)
- **Evaluation**: accuracy, precision, recall, F1, confusion matrices, classification reports, ROC curves with AUC

## Key Finding

All models achieve ~50% accuracy, consistent with the **Efficient Market Hypothesis**: historical price and volume data alone cannot reliably predict short-term stock price direction because this information is already reflected in current prices. This is a valid and well-documented result in quantitative finance.

## Documentation

| File | Purpose |
| --- | --- |
| `docs/data_dictionary.md` | Canonical field-by-field dataset, database, and output reference |
| `reports/final_report.md` | Complete project report |

## Reproducibility

- Raw data stored separately from processed outputs
- Cleaning is deterministic — same input always produces same output
- Database rebuilt from scratch each run (DROP + CREATE)
- Chronological train/test split prevents future-data leakage
- `run_all.py` executes the full pipeline end-to-end
- Dependencies pinned in `requirements.txt`

## Team Ownership

### Ryan Amir

- Data acquisition, cleaning, and 8-rule data validation pipeline (with synthetic-fixture self-test)
- Database schema design with sector normalization, loading, and verification
- 11 SQL queries (basic aggregates + correlated subqueries + sector analysis)
- 11 EDA visualizations + descriptive statistics export
- Master pipeline scripts (`run_pipeline.py`, `run_all.py`)
- All project documentation

### Gian Cases

- Feature engineering (11 features + binary target variable)
- Model training (Logistic Regression, Decision Tree, Random Forest)
- Naive baseline evaluation
- Model evaluation (accuracy, precision, recall, F1, confusion matrices, classification reports, ROC/AUC)
- 4 ML visualizations (feature importance, feature correlation, model comparison, ROC curves)
- ML pipeline script (`run_ml_pipeline.py`)
