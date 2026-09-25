# Forecast Results — Sales Pipeline & Quota Attainment

2-quarter forecast (Jan–Jun 2026) from a seasonal-trend decomposition trained on Jan 2024–Dec 2025. Attainment % = forecast bookings ÷ forecast quota.

## Backtest accuracy (hold out last 2 quarters)

| Segment | MAPE |
|---|---|
| Enterprise | 12.4% |
| Mid-Market | 8.9% |
| SMB | 7.0% |

## Monthly forecast

| Month | Segment | Forecast bookings | Forecast quota | Attainment % | Win-rate assumption | Pipeline needed |
|---|---|---|---|---|---|---|
| 2026-01 | Enterprise | $317,578 | $487,232 | 65.2% | 22.9% | $2,124,867 |
| 2026-02 | Enterprise | $338,950 | $490,121 | 69.2% | 22.9% | $2,137,466 |
| 2026-03 | Enterprise | $350,469 | $493,019 | 71.1% | 22.9% | $2,150,105 |
| 2026-04 | Enterprise | $441,893 | $495,926 | 89.1% | 22.9% | $2,162,782 |
| 2026-05 | Enterprise | $392,994 | $496,082 | 79.2% | 22.9% | $2,163,463 |
| 2026-06 | Enterprise | $374,535 | $496,330 | 75.5% | 22.9% | $2,164,544 |
| 2026-01 | Mid-Market | $279,665 | $374,902 | 74.6% | 28.4% | $1,319,768 |
| 2026-02 | Mid-Market | $304,117 | $379,628 | 80.1% | 28.4% | $1,336,405 |
| 2026-03 | Mid-Market | $365,932 | $384,359 | 95.2% | 28.4% | $1,353,059 |
| 2026-04 | Mid-Market | $391,671 | $389,092 | 100.7% | 28.4% | $1,369,721 |
| 2026-05 | Mid-Market | $345,949 | $392,556 | 88.1% | 28.4% | $1,381,915 |
| 2026-06 | Mid-Market | $423,574 | $396,018 | 107.0% | 28.4% | $1,394,102 |
| 2026-01 | SMB | $184,910 | $251,834 | 73.4% | 33.9% | $743,861 |
| 2026-02 | SMB | $227,103 | $255,009 | 89.1% | 33.9% | $753,239 |
| 2026-03 | SMB | $244,034 | $258,186 | 94.5% | 33.9% | $762,623 |
| 2026-04 | SMB | $265,349 | $261,366 | 101.5% | 33.9% | $772,016 |
| 2026-05 | SMB | $267,456 | $263,693 | 101.4% | 33.9% | $778,889 |
| 2026-06 | SMB | $260,452 | $266,018 | 97.9% | 33.9% | $785,757 |

## H1 2026 summary

| Segment | Forecast bookings | Forecast quota | Attainment % | Status |
|---|---|---|---|---|
| Enterprise | $2,216,419 | $2,958,710 | 74.9% | AT RISK |
| Mid-Market | $2,110,908 | $2,316,555 | 91.1% | WATCH |
| SMB | $1,449,304 | $1,556,106 | 93.1% | WATCH |

_Pipeline needed = forecast quota ÷ trailing 6-month win rate. Segments below 90% attainment are flagged AT RISK; 90–99% are WATCH._
