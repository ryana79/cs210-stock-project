# Data Dictionary

## Project Scope

This project analyzes daily historical stock data for:

- `AAPL` — Apple Inc. (Technology)
- `MSFT` — Microsoft Corporation (Technology)
- `TSLA` — Tesla, Inc. (Automotive / Technology)

The data is downloaded from Yahoo Finance, cleaned into a consolidated CSV, stored in a relational SQLite database, and summarized through SQL and EDA outputs. Feature engineering and machine learning stages then use the cleaned dataset to train and evaluate predictive models.

## Raw Data Files

Files:

- `data/raw/aapl_raw.csv`
- `data/raw/msft_raw.csv`
- `data/raw/tsla_raw.csv`

Raw columns:

| Column | Type | Description |
| --- | --- | --- |
| `date` | date | Trading day |
| `open` | float | Opening stock price for the day |
| `high` | float | Highest stock price for the day |
| `low` | float | Lowest stock price for the day |
| `close` | float | Closing stock price for the day |
| `adj_close` | float | Adjusted closing price |
| `volume` | integer | Number of shares traded |
| `ticker` | string | Stock ticker symbol |

## Cleaned Dataset

File:

- `data/processed/cleaned_stock_prices.csv`

Cleaned columns:

| Column | Type | Description |
| --- | --- | --- |
| `date` | string (`YYYY-MM-DD`) | Standardized trading date |
| `open` | float | Opening price |
| `high` | float | Highest daily price |
| `low` | float | Lowest daily price |
| `close` | float | Closing price |
| `adj_close` | float | Adjusted closing price |
| `volume` | integer | Trading volume |
| `ticker` | string | Stock ticker |
| `company_name` | string | Full company name |

Cleaning guarantees (validated by 8 explicit rules in `src/data/clean_data.py`):

**Hard checks (drop rows that fail):**

- all 8 required columns are present (raises if not)
- duplicate `(ticker, date)` rows are removed
- rows with any missing required price/volume/date are removed
- rows with non-positive prices are removed
- rows that violate price-relationship invariants (`low ≤ open, close ≤ high`) are removed

**Soft checks (flag and report only):**

- zero-volume days are flagged (possible halts)
- daily returns above ±50% are flagged (likely unadjusted splits)
- date gaps > 5 calendar days within a ticker are flagged

Per-rule audit log: `data/processed/data_validation_report.csv`

Self-test on synthetic dirty data: `python3 src/data/test_cleaning_on_dirty_fixture.py`

## Feature-Engineered Dataset

File:

- `data/processed/featured_stock_prices.csv`

Additional columns (appended to cleaned columns):

| Column | Type | Description |
| --- | --- | --- |
| `daily_return` | float | Percent change in closing price from previous day |
| `lag_1` – `lag_5` | float | Closing prices from 1 to 5 days prior |
| `ma_5` | float | 5-day simple moving average of close |
| `ma_10` | float | 10-day simple moving average of close |
| `ma_20` | float | 20-day simple moving average of close |
| `volatility_10` | float | Rolling 10-day standard deviation of daily returns |
| `volume_change` | float | Percent change in trading volume from previous day |
| `target_next_day_up` | int (0/1) | 1 if next day's close > today's close, else 0 |

Summary file:

- `data/processed/featured_data_summary.csv` — row counts, date ranges, and up-day rates per ticker

## Cleaning Validation Output

File:

- `data/processed/data_validation_report.csv`

Columns:

| Column | Type | Description |
| --- | --- | --- |
| `check_name` | string | Name of the data quality rule (e.g., `duplicate_ticker_date`) |
| `rows_evaluated` | integer | Number of rows the check was applied to |
| `rows_failed` | integer | Number of rows that failed the check |
| `action` | string | `drop_duplicates`, `drop_rows`, `raise_if_missing`, or `flag_only` |
| `description` | string | Human-readable rationale for the rule |

## Database Tables

Database file:

- `data/processed/stocks.db`

### `stocks`

| Column | Type | Description |
| --- | --- | --- |
| `stock_id` | integer | Primary key |
| `ticker` | text | Unique stock ticker |
| `company_name` | text | Full company name |
| `sector` | text | Industry sector |

### `daily_prices`

| Column | Type | Description |
| --- | --- | --- |
| `price_id` | integer | Primary key |
| `stock_id` | integer | Foreign key to `stocks.stock_id` |
| `trade_date` | text | Trading date |
| `open_price` | real | Opening price |
| `high_price` | real | Highest daily price |
| `low_price` | real | Lowest daily price |
| `close_price` | real | Closing price |
| `adjusted_close` | real | Adjusted closing price |
| `volume` | integer | Trading volume |

Database constraints:

- `ticker` is unique in `stocks`
- `(stock_id, trade_date)` is unique in `daily_prices`
- `daily_prices.stock_id` references `stocks.stock_id`

## Output Tables

### SQL Summary Outputs (Basic)

- `outputs/metrics/database_row_counts.csv`
- `outputs/metrics/latest_close_prices.csv`
- `outputs/metrics/stock_summary_stats.csv`
- `outputs/metrics/yearly_average_close.csv`
- `outputs/metrics/price_range_by_stock.csv`
- `outputs/metrics/date_coverage_by_stock.csv`

### SQL Summary Outputs (Advanced)

- `outputs/metrics/top_10_daily_gains.csv`
- `outputs/metrics/top_10_daily_losses.csv`
- `outputs/metrics/quarterly_average_close.csv`
- `outputs/metrics/sector_performance_summary.csv`

### EDA Summary Outputs

- `outputs/metrics/eda_summary_by_stock.csv`
- `outputs/metrics/eda_summary.md`
- `outputs/metrics/descriptive_statistics.csv`

### ML Evaluation Outputs

- `outputs/metrics/model_comparison.csv` — accuracy, precision, recall, F1 for all models including naive baseline
- `outputs/metrics/roc_auc_scores.csv` — AUC scores per model
- `outputs/metrics/confusion_matrix_naive_baseline.csv`
- `outputs/metrics/confusion_matrix_logistic_regression.csv`
- `outputs/metrics/confusion_matrix_decision_tree.csv`
- `outputs/metrics/confusion_matrix_random_forest.csv`
- `outputs/metrics/classification_report_logistic_regression.csv`
- `outputs/metrics/classification_report_decision_tree.csv`
- `outputs/metrics/classification_report_random_forest.csv`

### Figures — Price and Volume Trends (Ryan)

- `outputs/figures/closing_price_trends.png`
- `outputs/figures/adjusted_closing_price_trends.png`
- `outputs/figures/indexed_adjusted_close_growth.png`
- `outputs/figures/trading_volume_trends.png`
- `outputs/figures/rolling_30d_volume_trends.png`

### Figures — Summary and Comparison (Ryan)

- `outputs/figures/row_count_per_stock.png`
- `outputs/figures/average_closing_price_by_stock.png`
- `outputs/figures/yearly_average_closing_price_trend.png`

### Figures — Returns and Volatility Analysis (Ryan)

- `outputs/figures/daily_returns_distribution.png`
- `outputs/figures/daily_returns_correlation.png`
- `outputs/figures/monthly_returns_boxplot.png`

### Figures — Machine Learning (Gian)

- `outputs/figures/feature_correlation_heatmap.png`
- `outputs/figures/model_comparison.png`
- `outputs/figures/feature_importance.png`
- `outputs/figures/roc_curves.png`
