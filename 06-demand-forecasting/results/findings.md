# Results — Daily Demand Forecasting (Capital Bikeshare)

**Back-test:** trained Jan 2011 – Sep 2012 · tested on 92 days, Oct–Dec 2012

| Method | MAE (bikes/day) | RMSE | WAPE | Bias |
|---|---|---|---|---|
| Ridge regression | 942 | 1,329 | 18.2% | +5.6% |
| Gradient boosting | 1,097 | 1,515 | 21.2% | +11.3% |
| Last year × growth (current approach) | 1,288 | 1,690 | 24.9% | +11.5% |
| Last week, same weekday | 1,458 | 2,047 | 28.2% | +8.5% |
| Last year, same day | 1,982 | 2,306 | 38.4% | −34.1% |

- Ridge vs the current approach: average error −27%; median daily error 542 vs 977 bikes; days missed by more than 1,500 bikes: 16 vs 31
- Weather effects (other factors equal): rain/snow −1,670 bikes/day, mist −430 bikes/day vs a clear day
- Trend: about +2,000 bikes/day per year; 2012 demand +65% vs 2011
- Casual riders: 32% of weekend demand vs 13% on working days
- Largest misses: Hurricane Sandy (29–30 Oct 2012), Thanksgiving (22 Nov), Christmas week
