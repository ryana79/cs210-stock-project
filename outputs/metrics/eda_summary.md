# EDA Summary

## Dataset Coverage

- Total rows: 6270
- Date range: 2018-01-02 to 2026-04-27
- Stocks analyzed: AAPL, MSFT, TSLA

## Key Findings

- `MSFT` has the highest average closing price at 276.22.
- `TSLA` has the highest average trading volume at 121734167.35.
- Row counts are very similar across the 3 selected stocks, which helps keep comparisons balanced.
- The price trend plots show substantial long-term growth across all three companies, with different levels of volatility.
- Indexed adjusted price plots are more informative than raw price levels when comparing growth across different stocks.
- Yearly average comparisons should use complete years only because the current year is still partial.

## Summary Table

| Ticker | Company | Rows | First Date | Last Date | Avg Close | Min Close | Max Close | Avg Volume |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| AAPL | Apple Inc. | 2090 | 2018-01-02 | 2026-04-27 | 142.36 | 35.55 | 286.19 | 92616127.16 |
| MSFT | Microsoft Corporation | 2090 | 2018-01-02 | 2026-04-27 | 276.22 | 85.01 | 542.07 | 27992616.16 |
| TSLA | Tesla, Inc. | 2090 | 2018-01-02 | 2026-04-27 | 191.12 | 11.93 | 489.88 | 121734167.35 |

## Ryan-Side Takeaway

The current data management and EDA pipeline successfully downloads, cleans, stores, and summarizes multi-year stock data in a reproducible way. This prepares a stable input for the machine learning stage while also satisfying the course database and data science requirements.
