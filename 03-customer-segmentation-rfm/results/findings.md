# Results — Customer Segmentation (RFM + K-Means)

**Data:** 391,150 clean transaction lines · 4,334 customers · £8.74M revenue · 1 Dec 2010 – 9 Dec 2011 · snapshot date 10 Dec 2011

## Segment summary
| Segment | Customers | % customers | Avg days since last order | Avg orders | Avg spend | % revenue |
|---|---|---|---|---|---|---|
| Champions | 655 | 15.1% | 6 | 12.2 | £6,640 | 49.8% |
| Loyal Customers | 798 | 18.4% | 33 | 6.4 | £2,776 | 25.4% |
| At Risk | 587 | 13.5% | 153 | 2.9 | £1,073 | 7.2% |
| Hibernating | 1,074 | 24.8% | 217 | 1.1 | £479 | 5.9% |
| Potential Loyalists | 484 | 11.2% | 16 | 2.0 | £1,022 | 5.7% |
| Can't Lose Them | 63 | 1.5% | 134 | 8.3 | £2,728 | 2.0% |
| About to Sleep | 348 | 8.0% | 52 | 1.1 | £469 | 1.9% |
| Need Attention | 189 | 4.4% | 51 | 2.3 | £827 | 1.8% |
| Promising | 90 | 2.1% | 23 | 1.0 | £288 | 0.3% |
| New Customers | 46 | 1.1% | 7 | 1.0 | £355 | 0.2% |

## K-means validation (k = 4)
| Cluster | Customers | Median days since order | Median orders | Median spend | % revenue |
|---|---|---|---|---|---|
| VIP | 686 | 8 | 10 | £3,715 | 64.0% |
| Regular mid-value | 1,182 | 52 | 4 | £1,358 | 24.4% |
| New / developing | 820 | 17 | 2 | £467 | 5.1% |
| Lost low-value | 1,646 | 173 | 1 | £297 | 6.5% |

76% of Champions fall in the VIP cluster, and 96% of Hibernating customers fall in the Lost low-value cluster.

## Retention
- Month-1 retention for new cohorts: median 20% (range 15–37%)
- Dec 2010 cohort (existing accounts): 50% still active in Nov 2011

## Priority actions
1. Protect Champions and Loyal Customers (75% of revenue) with VIP perks instead of discounts.
2. Run a win-back campaign for At Risk and Can't Lose Them: 650 customers, £802K historical revenue.
3. Add a 30-day second-order incentive to raise month-1 retention above 20%.
4. Time re-activation offers before the Sep–Nov peak.
