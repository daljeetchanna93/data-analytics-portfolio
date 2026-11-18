# Results — Employee Attrition Analysis

**Population:** 1,470 employees · 237 leavers · overall attrition 16.1% (fictional IBM dataset)

## Highest-attrition groups
| Group | Attrition |
|---|---|
| Sales Representatives | 39.8% |
| Age 18–25 | 35.8% |
| First year at company | 34.9% |
| Low job involvement | 33.7% |
| Bad work-life balance | 31.2% |
| Overtime | 30.5% |
| Lowest income quartile | 29.3% |
| Frequent travelers | 24.9% |
| No stock options | 24.4% |

## Logistic regression (odds multipliers)
| Factor | Odds |
|---|---|
| Overtime: Yes (vs No) | 4.2x |
| Travel frequently (vs non-travel) | 4.0x |
| Travel rarely (vs non-travel) | 2.1x |
| Single (vs divorced) | 2.1x |
| Number of previous employers (per SD) | 1.5x |
| Years since last promotion (per SD) | 1.5x |
| Environment satisfaction (per SD) | 0.69x |
| Job involvement (per SD) | 0.70x |
| Research & Development dept (vs HR) | 0.59x |

Model quality: test ROC-AUC 0.823 · 5-fold CV AUC 0.818 ± 0.012

## Risk tiers
| Tier | Employees | Actual attrition | Share of all leavers |
|---|---|---|---|
| High | 326 | 49.4% | 67.9% |
| Medium | 478 | 10.0% | 20.3% |
| Low | 666 | 4.2% | 11.8% |

## Cost (assumes replacement cost = 50% of annual salary)
- Total: ~$6.8M · average ~$28.7K per leaver
- Excess leavers linked to overtime: ~84 (~$2.4M)
- Savings from a 20% attrition reduction: ~$1.4M
