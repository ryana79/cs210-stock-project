PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS daily_prices;
DROP TABLE IF EXISTS stocks;

CREATE TABLE stocks (
    stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL UNIQUE,
    company_name TEXT NOT NULL,
    sector TEXT NOT NULL
);

CREATE TABLE daily_prices (
    price_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER NOT NULL,
    trade_date TEXT NOT NULL,
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    adjusted_close REAL NOT NULL,
    volume INTEGER NOT NULL,
    FOREIGN KEY (stock_id) REFERENCES stocks(stock_id),
    UNIQUE (stock_id, trade_date)
);

CREATE INDEX idx_daily_prices_stock_date
    ON daily_prices (stock_id, trade_date);
