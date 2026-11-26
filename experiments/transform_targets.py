"""Target-transform experiment: log1p(cnt) and sqrt(cnt) vs identity.

Non-destructive: this never writes reports/metrics.json and never edits
src/. It reuses src.train.temporal_split and src.features.feature_columns
so the split and the audited feature list are the real ones, and scores
every variant with TransformedTargetRegressor so predictions are
inverse-transformed back to cnt units BEFORE r2_score/mean_absolute_error.

Run: python experiments/transform_targets.py
"""
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, median_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import PROCESSED, TARGET
from src.features import feature_columns
from src.train import PersistenceBaseline, temporal_split

TRANSFORMS = {
    "identity": (None, None),
    "log1p": (np.log1p, np.expm1),
    "sqrt": (np.sqrt, lambda y: np.square(y)),
}


def base_model(kind: str):
    if kind == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    return HistGradientBoostingRegressor(random_state=0, max_iter=300)


def score(y_true, y_pred) -> dict:
    """All metrics on the ORIGINAL cnt scale; y_pred comes back from
    TransformedTargetRegressor already inverse-transformed.

    `bias` is mean(prediction) - mean(actual). A concave transform with a
    naive inverse retransformation bias (Jensen), which R^2/MAE alone would
    hide. Positive = systematically too high.
    """
    resid = y_true.to_numpy(dtype=float) - np.asarray(y_pred, dtype=float)
    return {
        "r2": round(float(r2_score(y_true, y_pred)), 4),
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 1),
        "medae": round(float(median_absolute_error(y_true, y_pred)), 1),
        "bias": round(float(np.mean(y_pred) - np.mean(y_true)), 1),
    }


def build(kind: str, transform: str):
    """Variant by name; the 'baseline_*' keys need no transform branch."""
    if kind == "baseline_mean":
        return DummyRegressor(strategy="mean")
    if kind == "baseline_persistence":
        return PersistenceBaseline("cnt_lag_1")
    fwd, inv = TRANSFORMS[transform]
    if fwd is None:
        return base_model(kind)
    return TransformedTargetRegressor(regressor=base_model(kind),
                                      func=fwd, inverse_func=inv)


# Baselines first, then every model across every transform, so both
# baselines sit beside every score (CLAUDE.md non-negotiable) and the
# regime table below can reuse the identical fitted objects.
VARIANTS = (
    [("baseline_mean", "-"), ("baseline_persistence", "-")]
    + [(k, t) for k in ("ridge", "hgb") for t in TRANSFORMS]
)


def main() -> None:
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    train, valid, test = temporal_split(df)

    rows, fitted = [], []
    for kind, tname in VARIANTS:
        mdl = build(kind, tname)
        mdl.fit(train[cols], train[TARGET])
        fitted.append((f"{kind}/{tname}", mdl))
        rows.append(
            {"model": kind, "transform": tname}
            | {"valid": score(valid[TARGET], mdl.predict(valid[cols])),
               "test": score(test[TARGET], mdl.predict(test[cols]))}
        )

    print(f"n_train={len(train)} n_valid={len(valid)} n_test={len(test)} "
          f"(train mean cnt {train[TARGET].mean():.0f}, "
          f"valid {valid[TARGET].mean():.0f}, test {test[TARGET].mean():.0f})")
    print(f"{'model':<22}{'transform':<10}{'v_r2':>8}{'v_mae':>9}{'v_medae':>9}"
          f"{'v_bias':>8}{'t_r2':>8}{'t_mae':>9}{'t_medae':>9}{'t_bias':>9}")
    for r in rows:
        print(f"{r['model']:<22}{r['transform']:<10}"
              f"{r['valid']['r2']:>8}{r['valid']['mae']:>9}{r['valid']['medae']:>9}"
              f"{r['valid']['bias']:>8}"
              f"{r['test']['r2']:>8}{r['test']['mae']:>9}{r['test']['medae']:>9}"
              f"{r['test']['bias']:>9}")

    # --- Regime decomposition on test, baselines included ----------------
    print("\nTest-set regimes (all metrics in cnt units):")
    sandy = pd.Timestamp("2012-10-29")
    actual = test[TARGET].to_numpy(dtype=float)
    lag1 = test["cnt_lag_1"].to_numpy(dtype=float)
    jump = np.abs(actual - lag1) > 0.5 * lag1          # >50% move vs yesterday
    not_sandy = (test.dteday != sandy).to_numpy()
    sandy_at = (test.dteday == sandy).to_numpy()
    print(f"{'variant':<28}{'mae_all':>9}{'mae_no_sandy':>14}{'sandy_pred':>12}"
          f"{'mae_jump':>10}{'mae_steady':>12}")
    for label, mdl in fitted:
        pred_all = np.asarray(mdl.predict(test[cols]), dtype=float)
        resid = actual - pred_all
        print(f"{label:<28}"
              f"{float(np.abs(resid).mean()):>9.1f}"
              f"{float(np.abs(resid[not_sandy]).mean()):>14.1f}"
              f"{float(pred_all[sandy_at][0]):>12.0f}"
              f"{float(np.abs(resid[jump]).mean()):>10.1f}"
              f"{float(np.abs(resid[~jump]).mean()):>12.1f}")
    print(f"(jump-day n={int(jump.sum())}, steady-day n={int((~jump).sum())}; "
          f"Sandy actual = 22)")


if __name__ == "__main__":
    print("OK experiment: target transforms, scored on original cnt scale")
    main()
