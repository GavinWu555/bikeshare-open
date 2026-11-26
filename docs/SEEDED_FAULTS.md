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