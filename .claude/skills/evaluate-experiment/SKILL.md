---
name: evaluate-experiment
description: Run and evaluate a controlled modelling or target-transformation experiment against baselines on validation and test splits. Use whenever testing target transforms, comparing models against baselines, or diagnosing why a model beats or loses to persistence.
allowed-tools: Read, Edit, Bash(python*), Bash(make*)
---

# Current baseline metrics

!`python -c "import json, pathlib; p = pathlib.Path('reports/metrics.json'); print(json.dumps(json.loads(p.read_text()), indent=2) if p.exists() else 'No reports/metrics.json yet')"`

# Experiment: $ARGUMENTS

Work in this order. Do not skip any step.

1. **State the hypothesis and scale invariant.** Define what change is under test (e.g., target transformation `log1p`/`sqrt` or model comparison) and verify that every evaluation metric (R^2, MAE) is computed on the **original target scale (`cnt`)** after inverse transformation—never on transformed units.

2. **Check leakage and split integrity.** Confirm `src/train.py` fits any target transform, scaler, or model exclusively on `train` rows (`dteday <= TRAIN_END`), with no peeking at `valid` or `test`.

3. **Run the pipeline and inspect both splits.** Run `make features && make test && make train` (or a non-destructive evaluation script if comparing variants). Report `valid` and `test` R^2 and MAE side-by-side against `baseline_mean` and `baseline_persistence`.

4. **Diagnose error regimes.** When comparing two models (such as Ridge vs. persistence), break down errors across regimes (e.g., year-over-year level shift between 2011 and 2012, large demand jumps vs. steady days, or squared-error outliers vs. median/MAE) rather than stopping at a single aggregate score.

5. **Record the decision** in `docs/DECISIONS.md` (and `docs/EXPERIMENTS.md` if applicable): state the exact validation and test deltas, whether the change improved generalization on original `cnt` units, and whether to keep or revert it.
