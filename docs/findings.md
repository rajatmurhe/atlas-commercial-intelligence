# Findings from the seeded simulation

All numbers below are computed from seed 422804, version seed-422804-v1-1bc1b098ff34. They describe fictional data, not MSD performance.

## Review the concentrated shortfall

Q3 2026 revenue is $17,386,643.78, 95.95% of target, with a signed gap of $-733,028.18. Revenue grew 2.89% versus the same quarter last year. Kuwait's gap is $-769,759.66; positive gaps elsewhere offset part of it.

**Decision supported:** prioritize the Kuwait review and its product contributions. Investigate order timing and operations before attributing a cause. Growth and target attainment answer different questions; positive growth does not mean the plan was met.

## Choose forecasts using out-of-sample evidence

| Model | Held-out MAPE | Held-out WAPE | Held-out MAE (USD) |
|---|---:|---:|---:|
| seasonal_naive | 4.70% | 4.83% | 299,351.79 |
| ets | 1.25% | 1.22% | 75,877.65 |

The validation-selected model is ets. ETS beats the seasonal-naive test MAPE. Selection uses validation MAE, before examining April–September 2026 test results.

**Decision supported:** use the baseline comparison to decide whether additional model complexity is justified. Evaluation is rolling one-month ahead; three-month forecast bands are exploratory and are not validated coverage guarantees.

## Investigate unusual declines

Kuwait's latest robust year-over-year-change score is -18.83; the −3 threshold is breached.

**Decision supported:** add the flagged market to the review queue. The screen does not identify a cause or a real-world operational failure.

## Evaluate the randomized promotion simulation

The treated-minus-control pre/post growth difference is 17.47 percentage points. Exact two-sided permutation p = 0.000155; approximate Welch 95% interval: 14.22 to 20.71 pp. Assignment is randomized over 16 territories.

**Decision supported:** demonstrate how an experiment could inform whether to test a campaign further. The effect was deliberately simulated; it is not evidence for spending money on a real pharmaceutical promotion.
