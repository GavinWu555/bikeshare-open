# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.
- 2026-11-25 — Added `cnt_lag_3` (`cnt.shift(3)`, inside the existing `LAG_WARMUP = 7`, no warmup change): available at prediction time because the day d-3 count is recorded 3 days before the forecast. **RECOMMEND DROP** -- validation R^2 went *down* for both models (ridge 0.6475 -> 0.6462, -0.0013; hgb 0.2185 -> 0.1891, -0.0294), MAE up for both (ridge 832.9 -> 835.2; hgb 1296.6 -> 1318.2), and rows unchanged at 714. `cnt_lag_1` already carries the short-horizon signal, so lag 3 is redundant columns plus noise for the booster.
