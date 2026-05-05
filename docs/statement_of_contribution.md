# Statement of Contribution

Project: **Stock Market Trend Analysis and Prediction Using Financial Data**

Team members: **Ryan Amir** (me) and **Gian Cases**

## Ryan Amir

Most of what I handled was pulling the dataset together into something we could actually use downstream. I downloaded historical daily stocks from Yahoo Finance for AAPL, MSFT, and TSLA (`yfinance`), then wrote and ran `clean_data.py` so the raw CSV became one cleaned file with sane types, duplicates removed if they ever appeared, and a validation report exported for grading.

After that I built out the relational database pieces: drafted `schema.sql`, loaded cleaned data through `create_database.py`, and wrote/run the SQL analyses in `report_queries.sql` with outputs exported to CSV. I also did the exploratory work in `generate_eda.py` (figures in `outputs/figures`) plus the summaries/stats outputs. On the organization side I kept the runnable pipeline cohesive (`run_all.py`, README, data dictionary) and drafted the written report PDF.

## Gian Cases

Gian focused on modeling. He engineered the features (`feature_engineering.py`) like lagged closes, rolling averages/volatility, daily returns / volume deltas, defined the binary “next-day up” label, trained the sklearn models (`train_models.py`) including logistic regression, decision trees, random forests alongside a naive baseline, and exported the comparisons, confusion matrices, classification reports, and ROC curves. Gian also produced the ML plots (heatmap, model comparison bars, ROC, feature importance) and summarized what the scores implied (basically noisy short-term forecasting and how that lines up with the efficient markets idea).

## How we collaborated

This was intentionally one pipeline end-to-end, so questions about features, leakage, chronological splits, and what to highlight in visuals crossed back and forth, but responsibilities split roughly along “data/database/EDA/reporting vs ML training/evaluation/interpretation” as outlined above.
