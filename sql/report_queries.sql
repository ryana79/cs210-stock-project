-- =============================================================
-- BASIC AGGREGATE QUERIES
-- =============================================================

-- Query 1: row count per stock
SELECT
    s.ticker,
    s.company_name,
    COUNT(*) AS row_count
FROM daily_prices dp
JOIN stocks s
    ON dp.stock_id = s.stock_id
GROUP BY s.ticker
ORDER BY s.ticker;

-- Query 2: latest available close price per stock
SELECT
    s.ticker,
    dp.trade_date,
    ROUND(dp.close_price, 2) AS close_price
FROM daily_prices dp
JOIN stocks s
    ON dp.stock_id = s.stock_id
WHERE (dp.stock_id, dp.trade_date) IN (
    SELECT stock_id, MAX(trade_date)
    FROM daily_prices
    GROUP BY stock_id
)
ORDER BY s.ticker;

-- Query 3: average close price and average volume per stock
SELECT
    s.ticker,
    ROUND(AVG(dp.close_price), 2) AS avg_close_price,
    ROUND(AVG(dp.volume), 2) AS avg_volume
FROM daily_prices dp
JOIN stocks s
    ON dp.stock_id = s.stock_id
GROUP BY s.ticker
ORDER BY s.ticker;

-- Query 4: yearly average close price per stock
SELECT
    s.ticker,
    SUBSTR(dp.trade_date, 1, 4) AS year,
    ROUND(AVG(dp.close_price), 2) AS avg_close_price
FROM daily_prices dp
JOIN stocks s
    ON dp.stock_id = s.stock_id
GROUP BY s.ticker, year
ORDER BY s.ticker, year;

-- Query 5: price range (min and max close) per stock
SELECT
    s.ticker,
    ROUND(MIN(dp.close_price), 2) AS min_close,
    ROUND(MAX(dp.close_price), 2) AS max_close,
    ROUND(MAX(dp.close_price) - MIN(dp.close_price), 2) AS price_range
FROM daily_prices dp
JOIN stocks s
    ON dp.stock_id = s.stock_id
GROUP BY s.ticker
ORDER BY s.ticker;

-- Query 6: date coverage per stock
SELECT
    s.ticker,
    MIN(dp.trade_date) AS first_date,
    MAX(dp.trade_date) AS last_date,
    COUNT(DISTINCT dp.trade_date) AS trading_days
FROM daily_prices dp
JOIN stocks s
    ON dp.stock_id = s.stock_id
GROUP BY s.ticker
ORDER BY s.ticker;

-- Query 7: total database summary
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT dp.stock_id) AS stock_count,
    MIN(dp.trade_date) AS earliest_date,
    MAX(dp.trade_date) AS latest_date
FROM daily_prices dp;

-- =============================================================
-- ADVANCED QUERIES (window functions, subqueries)
-- =============================================================

-- Query 8: daily return (percent change) using window function LAG
-- Shows the 10 biggest single-day gains across all stocks
SELECT
    s.ticker,
    dp.trade_date,
    ROUND(dp.close_price, 2) AS close_price,
    ROUND(prev.close_price, 2) AS prev_close,
    ROUND(
        (dp.close_price - prev.close_price) / prev.close_price * 100, 2
    ) AS daily_return_pct
FROM daily_prices dp
JOIN stocks s ON dp.stock_id = s.stock_id
JOIN daily_prices prev ON dp.stock_id = prev.stock_id
    AND prev.trade_date = (
        SELECT MAX(p2.trade_date)
        FROM daily_prices p2
        WHERE p2.stock_id = dp.stock_id
          AND p2.trade_date < dp.trade_date
    )
ORDER BY daily_return_pct DESC
LIMIT 10;

-- Query 9: 10 biggest single-day losses across all stocks
SELECT
    s.ticker,
    dp.trade_date,
    ROUND(dp.close_price, 2) AS close_price,
    ROUND(prev.close_price, 2) AS prev_close,
    ROUND(
        (dp.close_price - prev.close_price) / prev.close_price * 100, 2
    ) AS daily_return_pct
FROM daily_prices dp
JOIN stocks s ON dp.stock_id = s.stock_id
JOIN daily_prices prev ON dp.stock_id = prev.stock_id
    AND prev.trade_date = (
        SELECT MAX(p2.trade_date)
        FROM daily_prices p2
        WHERE p2.stock_id = dp.stock_id
          AND p2.trade_date < dp.trade_date
    )
ORDER BY daily_return_pct ASC
LIMIT 10;

-- Query 10: quarterly average close price per stock
SELECT
    s.ticker,
    SUBSTR(dp.trade_date, 1, 4) AS year,
    CASE
        WHEN CAST(SUBSTR(dp.trade_date, 6, 2) AS INTEGER) <= 3  THEN 'Q1'
        WHEN CAST(SUBSTR(dp.trade_date, 6, 2) AS INTEGER) <= 6  THEN 'Q2'
        WHEN CAST(SUBSTR(dp.trade_date, 6, 2) AS INTEGER) <= 9  THEN 'Q3'
        ELSE 'Q4'
    END AS quarter,
    COUNT(*) AS trading_days,
    ROUND(AVG(dp.close_price), 2) AS avg_close_price,
    ROUND(AVG(dp.volume), 0) AS avg_volume
FROM daily_prices dp
JOIN stocks s ON dp.stock_id = s.stock_id
GROUP BY s.ticker, year, quarter
ORDER BY s.ticker, year, quarter;

-- Query 11: sector-level performance summary
SELECT
    s.sector,
    COUNT(DISTINCT s.ticker) AS stock_count,
    COUNT(*) AS total_trading_days,
    ROUND(AVG(dp.close_price), 2) AS avg_close_price,
    ROUND(AVG(dp.volume), 0) AS avg_daily_volume,
    ROUND(MIN(dp.close_price), 2) AS sector_min_price,
    ROUND(MAX(dp.close_price), 2) AS sector_max_price
FROM daily_prices dp
JOIN stocks s ON dp.stock_id = s.stock_id
GROUP BY s.sector
ORDER BY s.sector;
