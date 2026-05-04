DEFAULT_TICKERS = ["AAPL", "MSFT", "TSLA"]

BASE_PRICE_COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]
RAW_REQUIRED_COLUMNS = [*BASE_PRICE_COLUMNS, "ticker"]
NUMERIC_COLUMNS = ["open", "high", "low", "close", "adj_close", "volume"]

TICKER_TO_COMPANY = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "TSLA": "Tesla, Inc.",
}

TICKER_TO_SECTOR = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "TSLA": "Automotive / Technology",
}
