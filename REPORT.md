# Bikeshare Demand Forecasting Capstone Report

## Results

The pipeline was evaluated on a strict temporal split (`train`: 2011, $n = 348$; `valid`: H1 2012, $n = 182$; `test`: H2 2012, $n = 184$) using leak-free calendar, weather, and lagged-demand predictors derived from `FORBIDDEN` in `src/config.py`. For **Exercise 1**, `cnt_lag_3` (`cnt.shift(3)` on the gap-free calendar index, inside the existing `LAG_WARMUP = 7`) was added via `/new-feature` after verifying its availability at prediction time (day $d-3$ total rides are recorded three days before day $d$) and writing a failing hand-computed date test in `tests/test_leakage.py` first.

| Model / Baseline | Feature Set | Valid $R^2$ | Valid MAE | Test $R^2$ | Test MAE |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `baseline_mean` | Intercept only (2011 mean = 3493) | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| `baseline_persistence` | `cnt_lag_1` only | 0.4507 | 900.6 | 0.5099 | 840.1 |
| `ridge` (before Exercise 1) | 14 features (no `cnt_lag_3`) | 0.6475 | 832.9 | 0.5833 | 947.1 |
| `hgb` (before Exercise 1) | 14 features (no `cnt_lag_3`) | 0.2185 | 1296.6 | -0.4975 | 2020.4 |
| **`ridge` (committed `metrics.json`)** | **15 features (`+ cnt_lag_3`)** | **0.6462** | **835.2** | **0.5813** | **947.4** |
| **`hgb` (committed `metrics.json`)** | **15 features (`+ cnt_lag_3`)** | **0.1891** | **1318.2** | **-0.5653** | **2025.5** |

Adding `cnt_lag_3` produced a negative validation delta of **$-0.0013$ $R^2$** ($0.6475 \to 0.6462$) and **$+2.3$ MAE** ($832.9 \to 835.2$) for `ridge`, and **$-0.0294$ $R^2$** ($0.2185 \to 0.1891$) and **$+21.6$ MAE** ($1296.6 \to 1318.2$) for `hgb`. Because `cnt_lag_1`, `cnt_lag_7`, and `cnt_roll_7` already capture short- and weekly-horizon autocorrelation, `cnt_lag_3` adds collinear noise; per `/new-feature` rules (changes below $0.01$ $R^2$ are noise), it is flagged `RECOMMEND DROP` in `docs/DECISIONS.md` while remaining in `src/features.py` so the committed `reports/metrics.json` reproduces the exact post-Exercise-1 state.

---

## Headline finding

Gradient-boosted regression trees (`HistGradientBoostingRegressor`) fail catastrophically on 2012 test demand (**Test $R^2 = -0.5653$**, **MAE $= 2025.5$**, worse than `baseline_persistence` at $R^2 = 0.5099$ and only ahead of predicting the 2011 mean at $R^2 = -2.1441$) because **regression trees cannot extrapolate beyond the target range seen in training**.

Daily ridership grew by ~73% between 2011 (`train` mean $= 3493$) and H2 2012 (`test` mean $= 6043$). Every leaf in `hgb` outputs a weighted average of 2011 training targets, structurally capping predictions near the 2011 ceiling and creating a **$-1882.6$ rides/day test-set level bias**. A regime decomposition shows that `hgb` actually beats both `baseline_mean` and `ridge` on the 17 abrupt test-set jump days (MAE $1556.7$ vs. $2110.8$ and $1706.3$), but loses badly on the 167 steady high-demand days (MAE $2073.2$ vs. persistence $677.6$). By contrast, standardized `ridge` extrapolates linearly through `cnt_lag_1` and `cnt_roll_7`, achieving Test $R^2 = 0.5813$.

---

## Exercise 4: target transformation

To test whether a target transformation allows `hgb` to compete across the 2011–2012 growth shift without target leakage, we evaluated transformations using `sklearn.compose.TransformedTargetRegressor` (and exact inverse reconstruction using only training targets or strictly prior `cnt_lag_1`) on `valid` first, touching `test` once at the end (`experiments/transform_targets.py`). Every metric below is evaluated on **original `cnt` units** after inverse transformation:

| Model & Transform | Valid $R^2$ | Valid MAE | Test $R^2$ (touched once) | Test MAE | Test Bias |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `ridge` — identity (committed) | 0.6462 | 835.2 | 0.5813 | 947.4 | -553.5 |
| `ridge` — `sqrt(cnt)` / `square` | **0.6897** | **716.7** | **0.6486** | **804.6** | **+28.2** |
| `ridge` — `log1p(cnt)` / `expm1` | 0.1033 | 1184.7 | -0.7177 | 1844.7 | +1429.0 |
| `hgb` — identity (committed) | 0.1891 | 1318.2 | -0.5653 | 2025.5 | -1882.6 |
| `hgb` — `sqrt(cnt)` / `square` | 0.1557 | 1349.5 | -0.5865 | 2027.7 | -1910.4 |
| `hgb` — `log1p(cnt)` / `expm1` | 0.1309 | 1376.9 | -0.6423 | 2062.4 | -1945.2 |
| `hgb` — `diff(cnt - cnt_lag_1)` | **0.6076** | **837.6** | **0.5569** | **917.4** | **-18.4** |
| `ridge` — `diff(cnt - cnt_lag_1)` | 0.6462 | 834.9 | 0.5837 | 943.3 | -31.2 |

**Key findings & defensibility:**
1. **Monotone transforms (`sqrt`, `log1p`) cannot rescue trees:** Any strictly increasing map $g(y)$ preserves target ordering, so tree splits still partition 2011 values and plateau at the 2011 leaf maximum (`hgb` test $R^2$ remains $-0.5865$ under `sqrt` and $-0.6423$ under `log1p`). For `ridge`, `sqrt` eliminates downward level bias ($-553.5 \to +28.2$ rides/day) and lifts test $R^2$ to $0.6486$ (test MAE $804.6$), whereas `log1p` fits well in log space but causes severe exponential overshoot ($+1429.0$ bias) upon `expm1` retransformation.
2. **First-differencing (`y_trans = cnt - cnt_lag_1`, inverted via `cnt_lag_1 + y_pred`) lets `hgb` compete:** Because day-over-day increments $\Delta y_t = y_t - y_{t-1}$ are stationary across 2011 and 2012, `hgb` jumps from Valid $R^2 = 0.1891$ to **$0.6076$** (MAE $1318.2 \to 837.6$) and achieves **Test $R^2 = 0.5569$** (Test MAE $917.4$), beating both `baseline_persistence` ($R^2 = 0.5099$) and untransformed `ridge` on MAE ($917.4$ vs. $947.4$).
3. **Is target differencing defensible?** Econometrically and temporally, yes: `cnt_lag_1` is strictly known prior to day $d$, so predicting $\Delta y_t$ and adding `cnt_lag_1` back introduces zero leakage and is standard ARIMA/boosting practice for trended series. However, it reduces the tree to learning short-term weather/calendar adjustments around persistence rather than modeling level demand directly—and if multi-day horizons were required, errors would accumulate recursively. Per assignment instructions, `reports/metrics.json` remains on the untransformed baseline pipeline.

---

## Exercise 5: ridge vs persistence

Untransformed `ridge` should **not** be deployed over `baseline_persistence` without the `sqrt` level correction, because its higher aggregate Test $R^2$ ($0.5813$ vs. $0.5099$, a $+0.0714$ gain) masks inferior accuracy on normal operating days (`ridge` Test MAE $= 947.4$ vs. persistence Test MAE $= 840.1$, a $-107.3$ ride penalty; Test MedAE $= 918.0$ vs. $506.5$). Decomposing H2 2012 test errors by regime explains why: on the **167 steady days** (91% of the test set), persistence achieves an MAE of **$677.6$**, beating `ridge` (**$870.1$**) by nearly $200$ rides/day because `ridge` suffers from a **$-553.5$ rides/day downward level bias** inherited from 2011 training levels. `ridge` only wins on squared-error $R^2$ because squared loss heavily penalizes the **17 large-swing days** (weather shocks and holidays, excluding the unforecastable Hurricane Sandy drop to 22 rides where every model misses by $>4,000$), where persistence lags behind with an MAE of **$2436.6$** versus `ridge`'s **$1706.3$**. For operational bike-rebalancing where typical daily error (MAE/MedAE) governs staffing and van routing, `baseline_persistence` dominates untransformed `ridge`; only after applying the `sqrt` target transform—which collapses level bias to $+28.2$ rides/day and cuts steady-day MAE to $716.4$—does `ridge` beat persistence on both Test MAE ($804.6$ vs. $840.1$) and Test $R^2$ ($0.6486$ vs. $0.5099$).

---

## Attribution

* **Model used:** `qwen3` hosted by NRP.
* **Agent-generated artifacts:**
  * Scaffolding and test implementation for `cnt_lag_3` in `src/features.py` and `tests/test_leakage.py` via `/new-feature`.
  * Raw-column contract test `test_all_raw_columns_classified` in `tests/test_contract.py`.
  * Target-transformation evaluation harness in `experiments/transform_targets.py`, invoked through our custom `/evaluate-experiment` skill (`.claude/skills/evaluate-experiment/SKILL.md`).
  * Automated leakage audits (`/leakage-auditor` on teammate repo in `docs/AUDIT.md` and `agent/audit.py` batch self-audit in `reports/audit.jsonl`).
  * Used Gemini on browser to review and polish the report, and for assistance when stuck on certian steps.
* **Human decisions and verification:**
  * **Problem framing & leakage boundary:** Defined daily `cnt` forecasting, enforced exclusion of `casual`, `registered`, `cnt_2d_bfr`, and time indexes (`instant`, `yr`, `days_since_2011`), and designed the raw-schema completeness contract test.
  * **Temporal split & single-touch test discipline:** Enforced strict chronological splits (`2011` / `H1 2012` / `H2 2012`) and held out `H2 2012` until validation model/transform selection was complete.
  * **Fault seeding & defense verification:** Manually seeded and verified all four faults in `docs/SEEDED_FAULTS.md`, identifying the blind spot where Bash `cp` into `data/raw/` bypasses the `Edit|Write` `PostToolUse` hook.
  * **Audit reconciliation:** Reviewed every finding in `docs/AUDIT.md` and `reports/audit.jsonl`. Notably, `agent/audit.py` flagged that `tests/test_contract.py::test_beats_the_mean_baseline` reads test-set $R^2 > 0.4$ during `make test` and that `src/features.py::encode_weather`'s `ValueError` guard lacked a dedicated unit test; both are documented transparently rather than silently altered after the audit run.