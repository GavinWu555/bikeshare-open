## Link:

https://github.com/t6chow/dsc180a-ma6

## Output Verbatim

```text
---

Finding 1 (blocking) — the diff's only functional change tests a column that was never built

/Users/gavinwu/Desktop/bikeshare-open/teammate-audit/tests/test_leakage.py:60-66 (test_rolling_14_excludes_today) is the sole code change between 954f07f and HEAD; the rest of the diff is .gitignore. It reads feats.set_index("dteday").cnt_roll_14 with a member-access ., which raises before the assertion can run:

AttributeError: 'DataFrame' object has no attribute 'cnt_roll_14'. Did you mean '.cnt_roll_7'?
1 failed, 14 passed

grep -rn roll_14 over the whole repo (excluding .git) returns only these two lines — src/features.py:74-76 builds cnt_lag_1, cnt_lag_7, cnt_roll_7, nothing 14-day. So step 2 of .claude/skills/new-feature/SKILL.md (failing test first) was done and step 3 (implement) was not, and it was committed red.

Two consequences that change numbers, not just CI colour:

- make train cannot run. Makefile has no features dependency on test, but data/processed/ does not exist in this checkout, and the pipeline's own gate is make test. So reports/metrics.json was never produced — the path is absent from the git tree at both 954f07f and HEAD. Every figure in docs/DECISIONS.md:6,10 is therefore a bare claim with no artifact behind it. I reran the scoring logic in memory rather than trusting the docstring: persistence test R² 0.5099 / MAE 840.1 reproduces DECISIONS.md:10 exactly (0.510 / 840), and honest ridge test R² is 0.5833 (DECISIONS.md:6 says 0.583), leaky casual+registered+temp+hum R² = 1.000000 via src/leakage_demo.py. Those claims hold; the gap is that nothing in the repo pins them.
- Implementing the feature as specified silently moves the split. The test's literal 3645.285714285714 is the mean of the 14 strictly-prior calendar days 2012-02-16..2012-02-29 (I computed it both ways: shift-then-roll gives 3645.285714285714, roll-including-today gives 3787.0714285714284, so the test does discriminate the leak). But a 14-day window needs 14 warm-up days while src/config.py:55 keeps LAG_WARMUP = 7. Adding only the column drops 28 rows against the 7 + 7*1 = 14 bound in tests/test_contract.py:39-43, failing it. Raising LAG_WARMUP to 14 passes the bound but moves the first modelled date from 2011-01-10 to 2011-01-17, shrinking train 348 → 334 rows and re-dating the fitted Ridge/HGB — i.e. it perturbs the 0.583 and 0.510 you are comparing against.

Minimal fix, in order: add to src/features.py after line 76
out["cnt_roll_14"] = out[TARGET].shift(1).rolling(14).mean()
change src/config.py:55 to LAG_WARMUP = 14 (the comment at src/features.py:73 and the test_contract.py:36-38 docstring already say this is the required pairing), then re-run make features && make test && make train and restate the DECISIONS.md numbers against the new 334-row train set rather than reusing 0.583/0.510. Do not delete or xfail the test — a None would pass == pytest.approx(...), so if the column is built with a NaN-producing misalignment (e.g. built from a merge, or cnt_lag_1.rolling(14) after a dropna), use an explicit in guard so the test fails rather than passing on a missing key.

Checks 2-5: pass on the committed code

Verified, not read:

- Target leakage. feature_columns (src/features.py:81-84) yields 14 columns, derived from FORBIDDEN, with no hand-typed list. I ran a least-squares identity scan over all 1-, 2-, 3-column subsets of those 14 against cnt: no exact linear restatement (casual/registered never enter; they are numeric so the filter is what keeps them out, and test_no_forbidden_features guards it). test_leakage_identity_holds confirms casual+registered == cnt on all 714 rows, and the identity UNVERIFIED_COLS reason at src/config.py:39-43 is accurate — cnt_2d_bfr is a genuine 2-day lag, not a restatement, and it is excluded.
- Temporal ordering. cnt_lag_1, cnt_lag_7 are pure shifts; cnt_roll_7 shifts before rolling (src/features.py:76). Split is by date (temporal_split, src/train.py:56-62), yielding contiguous disjoint 2011-01-10..2011-12-31 / H1 2012 / H2 2012 (348/182/184 rows). The only fitted transformer, StandardScaler, sits inside a pipeline .fit() on train[cols] only (src/train.py:78); PersistenceBaseline fits nothing. Refitting the shared MODELS["ridge"] object across tests is numerically identical (0.5833 both times), so no cross-test contamination.
- Calendar gaps. reindex_to_calendar runs first (src/features.py:54), and the gap day 2011-03-10 is the only absent date in the mirror. test_lags_are_true_calendar_lags compares each lag against the value at d-1 in calendar days for 600+ rows, so a row-shift masquerading as a day-shift cannot survive.
- Silent row loss. 728 → 714 rows is accounted for exactly: 7 warm-up days plus the 7 days downstream of 2011-03-10. I checked the dropped dates individually — the 2011-03-10 block extends to 03-17, one day beyond what the test_contract.py:34-36 accounting text justifies (it says m+1..m+7, omitting m+1's own NaN cnt_lag_1), but the numeric bound 7 + 7*1 = 14 ≥ 14 still holds, so no row can vanish unaccounted. encode_weather raises on unseen labels (src/features.py:28-30) and there are zero nulls in the raw file, so the "20 BAD days disappear" scenario it defends against is closed.
- Baselines. Both baseline_mean and baseline_persistence are in MODELS and scored on valid and test like every model, so they appear next to both scores in metrics.json. Reproduced: mean test R² −2.1441 (MAE 2847.7), persistence test R² 0.5099 (MAE 840.1) versus ridge test R² 0.5833 (MAE 947.1) and HGB test R² −0.4975. The uncomfortable result is reported, not hidden: ridge beats persistence by 0.07 R² and loses to it on MAE, and HGB is below the mean baseline. Two soft notes tied to that, neither a wrong number: test_beats_the_mean_baseline (tests/test_contract.py:46-52) asserts ridge_test_r2 > 0.4, an absolute threshold that never touches the baselines, so a model scoring 0.41 against a persistence of 0.51 would still pass it; and the PersistenceBaseline("cnt_lag_1") column name is a second hand-typed reference to a feature built at src/features.py:74, which CLAUDE.md's "nothing is hardcoded twice" rule is about.

---

```

## Verdict:

The discrepency in numbers is caused by feature `cnt_roll_14`. In the repo, it was tested
without being implemented, which caused methods like `train` to be unable to run.
Additionally, the variable `LAG_WARMUP` was still 7, thus it would not work for 
feature `cnt_roll_14` that requires the last 14 days of data. 
