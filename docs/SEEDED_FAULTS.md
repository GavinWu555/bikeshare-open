## Exercise 1: Failing Test Output Before Implementation (510f880)
```
Error: Exit code 2
python -m pytest tests/ -q
........FF......                                                         [100%]
=================================== FAILURES ===================================
______________________ test_lag_3_is_a_true_calendar_lag _______________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_lag_3_is_a_true_calendar_lag(feats):
        """cnt_lag_3 for date d must equal cnt on d-3, in calendar days."""
        by_date = feats.set_index("dteday")[TARGET]
        checked = 0
>       for date, lag in feats.set_index("dteday").cnt_lag_3.items():
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_leakage.py:54:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self =             instant  season      yr  ... cnt_lag_1 cnt_lag_7   cnt_roll_7
dteday                               ...    ... 1787.0  1530.142857
2012-12-31    731.0  WINTER  2012.0  ...    1796.0     920.0  1531.428571

[714 rows x 27 columns]
name = 'cnt_lag_3'

    @final
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'DataFrame' object has no attribute 'cnt_lag_3'. Did you mean '.cnt_lag_1' instead of '.cnt_lag_3'?

.venv/lib/python3.15/site-packages/pandas/core/generic.py:6194: AttributeError
_________________________ test_lag_3_is_not_the_target _________________________

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_lag_3_is_not_the_target(feats):
>       assert not (feats.cnt_lag_3 == feats[TARGET]).all()
                    ^^^^^^^^^^^^^^^

tests/test_leakage.py:63:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]
name = 'cnt_lag_3'

    @final
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'DataFrame' object has no attribute 'cnt_lag_3'. Did you mean '.cnt_lag_1' instead of '.cnt_lag_3'?

.venv/lib/python3.15/site-packages/pandas/core/generic.py:6194: AttributeError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_lag_3_is_a_true_calendar_lag - AttributeEr...
FAILED tests/test_leakage.py::test_lag_3_is_not_the_target - AttributeError: ...
2 failed, 14 passed in 4.33s
make: *** [test] Error 1

```

## Fault 1: Forbidden Column Added to `feature_columns`

### Exact Change Seeded

In `src/features.py`, I appended `"casual"` a forbidden column to the
output of `feature_columns`.

```
-    return [c for c in numeric if c not in FORBIDDEN]
+    return [c for c in numeric if c not in FORBIDDEN] + ["casual"]
```

### Red Test Output:
```
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_3', 'cnt_lag_7', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py

```

### Hook
```
Leakage tests failed after editing /Users/gavinwu/desktop/bikeshare-open/src/features.py:
feats =         dteday  instant  season  ...  cnt_lag_3 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...     1510.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     3095.0     920.0  1531.428571

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_3', 'cnt_lag_7', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 8 passed in 0.46s

```

### Diagnosis:

The failure was real leakage, not an environment quirk. src/features.py:85 had been changed to:

return [c for c in numeric if c not in FORBIDDEN] + ["casual"]

feature_columns() is the only gate between the dataframe and the model — build_features never drops casual, it just declines to select it. Appending casual after the filter re-admits it past FORBIDDEN, which is precisely the class of edit test_no_forbidden_features exists to catch. The test did its job:

### Turns to Fix: 1

## Fault 2: Removed '.shift(1)` from `cnt_roll_7`

### Exact Change Seeded
In `src/features.py` removed `.shift(1)` from `cnt_roll_7` so same-day `cnt` is included in the 7-day rolling mean:

```
-    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
+    out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
```

### Red Test Output:
```
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py
```

### Hook:
```
Leakage tests failed after editing /Users/gavinwu/desktop/bikeshare-open/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:73: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 8 passed in 0.89s
```

### Diagnosis:

Not the same fault as last time. This one was at src/features.py:77, in the rolling mean:

out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()          # broken
out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()  # restored

The .shift(1) was dropped, so the window covered days d−6 … d including today's count instead of d−7 … d−1. That is direct target leakage — the feature carries roughly 1/7 of the value being predicted, computed at a time when it could not possibly be known.

The failing test named it exactly: test_rolling_mean_excludes_today. On the sampled date it wanted 4414.857 but got 4389.0 — the mismatch is what pinpoints inclusion of today rather than a random misalignment.

I checked the reason this one is quieter than the casual leak and it's worth stating: it inflates scores by a fraction, not to 1.0, so it can look like a genuine gain. On this data it was not caught by the gate test (test_no_forbidden_features) at all — the forbidden-column gate only guards which columns reach the model, not whether a column was computed honestly. Only the value-level date check caught it. That's the strongest argument in the repo for why the lag tests hand-compute from calendar dates instead of just checking column names.

### Turns to Fix: 1

## Fault 3: Removed `ValueError`  in `encode_weather`
In `src/features.py`, removed `if unknown: raise ValueError(...)` from `encode_weather()` so unseen weather labels silently map to `NaN` instead of failing loudly:

```
    unknown = set(known.unique()) - set(WEATHER_ORDER)
-       if unknown:
-           raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
        return series.map(WEATHER_ORDER).astype(float)
```
### Red Test Output:

Interestingly, all tests passed even after removing the `raise`:

```
................                                                         [100%]
16 passed in 1.86s
```

### Hook:

No output, as all tests passed.

### Prompt:
encode_weather in src/features.py allows for invalid weather labels to fail silently instead of raising ValueError. Restore the guard and check if any test covers it.

### Diagnosis:

Guard restored

src/features.py:27-31 is back to matching HEAD — the two-line check that was left behind as dead code now actually fires again:

known = series.dropna()
unknown = set(known.unique()) - set(WEATHER_ORDER)
if unknown:
    raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
return series.map(WEATHER_ORDER).astype(float)

Directly verified: encode_weather(pd.Series(["GOOD", "SNOW", None])) now raises unmapped weather labels: ['SNOW'], while the real labels still encode to [0.0, 1.0, 2.0, nan]. make features && make test && make train → 16 passed, validation unchanged at ridge 0.6462 / hgb 0.1891. No commit.

What was deleted was only the if unknown: raise. The unknown = ... line stayed, so the function kept computing the answer and discarding it — which makes this the most evasive of the three faults so far: it reads as if the check is still there unless you look at whether unknown is used.

No test covers it

Zero hits for weather (case-insensitive) across all three test files — test_leakage.py, test_contract.py, test_split.py. encode_weather is never imported or named in a test, and there is no pytest.raises anywhere in the suite. The 16 passing tests pass identically with the guard present or absent.

The reason nothing catches it is worth stating plainly: on this data the guard is unreachable. The mirror contains exactly ['BAD', 'GOOD', 'MISTY'] with 0 NaN weather across 728 rows, so .map() never produces a stray NaN and dropna() deletes nothing. Removing the guard changes no output on the current file — which is precisely why make features printed OK ... 714 rows both before and after. The docstring's horror story (20 BAD days vanishing silently) is a future-data hazard: it triggers when someone refreshes the mirror or swaps in the UCI original, whose weather column uses codes 1–4 (src/config.py:16). Every label there is "unseen," every row maps to NaN, and the whole dataset disappears with no error. That is the scenario the test needs to cover, and no test does.

So the guard is currently the only thing standing between a data swap and a silently empty training set, and it has zero test coverage — a gap in exactly the protection mechanism the repo's own docstring argues for.

Two cheap backstops, if you want them:

1. A unit test that needs no data — encode_weather takes a Series, so this is two lines and the honest version of test-first: it passes today and would go red the moment someone deletes the raise again.
def test_unmapped_weather_label_raises():
    with pytest.raises(ValueError, match="unmapped weather labels"):
        encode_weather(pd.Series(["GOOD", "SNOW"]))
   Worth pairing with an assertion that known labels pass through unmapped, so the test can't be satisfied by an unconditional raise.
2. flake8/ruff would flag the dead unknown assignment (F841, local variable never used) — but there's no lint target in the Makefile, so this only helps if you want one added.

I've left the tree at the restore you asked for and haven't written the test — say which and I'll do it test-first, showing red before green.

### Turns to Fix: 1

## Fault 4: Unmonitored `cp` into `data/raw/` via Bash

### Command and Output
```text
$ printf 'corrupted,data\n1,2\n' > /tmp/corrupted_raw.csv
$ cp /tmp/corrupted_raw.csv data/raw/corrupted_raw.csv
$ ls -la data/raw/
$ make test
$ rm data/raw/corrupted_raw.csv /tmp/corrupted_raw.csv
$ git status
total 184
drwxr-xr-x@ 4 gavinwu  staff    128 Nov 25 20:52 .
drwxr-xr-x@ 4 gavinwu  staff    128 Nov 24 00:11 ..
-rw-r--r--@ 1 gavinwu  staff  86325 Nov 10 09:52 bike_daily.csv
-rw-r--r--  1 gavinwu  staff     19 Nov 25 20:52 corrupted_raw.csv
python -m pytest tests/ -q
................                                                         [100%]
16 passed in 1.89s

```
### What Happened:

`.claude/settings.json` scopes `PostToolUse` exclusively to `Edit|Write`, so `Bash` commands do not invoke `.claude/hooks/check_leakage.sh`. Similarly, `permissions.deny` blocks `Write(./data/raw/**)` and `Edit(./data/raw/**)` at the file-tool level, leaving shell operations (`cp`, `mv`, `>`, `tee`) unrestricted. Because `src/ingest.py` reads `data/raw/bike_daily.csv` directly without checking the directory manifest or file hash, extra files (or a silent overwrite of `bike_daily.csv` via `cp`) pass `make test` unnoticed.

### What Would Have Caught It
1. **SHA-256 digest and directory manifest test:** Pin the expected SHA-256 checksum of `data/raw/bike_daily.csv` and assert the exact set of filenames in `data/raw/` inside `tests/test_contract.py` (and before `make features` or `make train` runs).
2. **OS-level read-only permissions + `PreToolUse` Bash guard:** Set `chmod 444 data/raw/bike_daily.csv` and `chmod 555 data/raw/` on disk (causing shell `cp` to fail with `Permission denied`) and add a `PreToolUse` hook on `Bash` rejecting commands that target `data/raw/`.

